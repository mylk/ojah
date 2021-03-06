import logging
import os
import pickle
from random import shuffle
import re
import threading
import time

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.core.management.base import BaseCommand
from django.core import serializers
from django.core.serializers.base import DeserializationError
from django.db import utils, connection
from nltk.corpus import stopwords
import pika
from pika.exceptions import AMQPChannelError, AMQPConnectionError, ChannelClosed, \
ConnectionClosed, DuplicateConsumerTag, NoFreeChannels
from textblob.classifiers import NaiveBayesClassifier

from core.models.corpus import Corpus
from core.models.newsitem import NewsItem
from cli.management.handlers.publish_handler import PublishHandler
from cli.management.handlers.corpus_handler import CorpusHandler


class Command(BaseCommand):
    help = 'Perform sentiment analysis on news items'
    classifier = None

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def handle(self, *args, **options):
        try:
            channel = self.get_channel()
            if channel:
                channel.queue_purge(queue=settings.QUEUE_NAME_TRAIN)

            should_train_classifier = True
            if os.path.isfile(settings.CLASSIFIER_DUMP_FILEPATH):
                should_train_classifier = False

                self.logger.info('Classifier dump found!')
                try:
                    self.classifier = pickle.load(open(settings.CLASSIFIER_DUMP_FILEPATH, 'rb'))
                except EOFError as eof_error:
                    should_train_classifier = True
                    self.logger.error('Could not load dump because of: {}'.format(str(eof_error)))
            else:
                self.logger.info('Classifier dump not found.')

            if should_train_classifier:
                self.classifier = self.get_classifier()

        except (utils.Error, utils.DataError, utils.DatabaseError) as ex_db:
            self.logger.error('Failed to train the classifier.')
            return

        self.logger.info('Classifier is ready!')

        thread_classify = threading.Thread(target=self.classify_consumer, args=(), name='classify')
        thread_classify.start()

        thread_train = threading.Thread(target=self.train_consumer, args=(), name='train')
        thread_train.start()

    def classify_consumer(self):
        channel = self.get_consumer(settings.QUEUE_NAME_CLASSIFY, self.classify_decorator)
        try:
            channel.start_consuming()
        except (
                AMQPConnectionError, AMQPChannelError, ChannelClosed, ConnectionClosed,
                NoFreeChannels
        ) as ex_consume:
            self.logger.error(str(ex_consume))

    def train_consumer(self):
        channel = self.get_consumer(settings.QUEUE_NAME_TRAIN, self.train_callback)
        try:
            channel.start_consuming()
        except (
                AMQPConnectionError, AMQPChannelError, ChannelClosed, ConnectionClosed,
                NoFreeChannels
        ) as ex_consume:
            self.logger.error(str(ex_consume))

    def get_channel(self):
        try:
            params = pika.ConnectionParameters(
                host=settings.QUEUE_HOSTNAME,
                heartbeat_interval=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
        except (
                AMQPConnectionError, AMQPChannelError, ChannelClosed, ConnectionClosed,
                NoFreeChannels
        ) as ex_channel:
            self.logger.error(str(ex_channel))
            return None

        return channel

    def get_consumer(self, queue, callback):
        try:
            channel = self.get_channel()
            if channel is None:
                return None

            channel.queue_declare(queue=queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(callback, queue=queue)
        except DuplicateConsumerTag as ex_consumer:
            self.logger.error(str(ex_consumer))
            return None

        return channel

    def get_classifier(self):
        self.logger.info('Training classifier...')

        stopwords_blacklisted = self.get_stopwords()
        stopwords_pattern = re.compile(r'\b(' + r'|'.join(stopwords_blacklisted) + r')\b\s*')

        corpora_classified = list()
        for corpus in Corpus.objects.filter(active=True):
            title = stopwords_pattern.sub('', corpus.news_item.title)
            corpora_classified.append((title, corpus.get_classification()))

        for news_item in NewsItem.find_neutral():
            title = stopwords_pattern.sub('', news_item.title)
            corpora_classified.append((title, 'neu'))

        corpora_classified = list(set(corpora_classified))
        shuffle(corpora_classified)

        classifier = NaiveBayesClassifier(corpora_classified)

        self.logger.info('Dumping classifier.')
        pickle.dump(classifier, open(settings.CLASSIFIER_DUMP_FILEPATH, 'wb'))
        self.logger.info('Classifier dumped!')

        return classifier

    def classify_decorator(self, channel, method, properties, body):
        self.classify_callback(channel, method, properties, body)
        connection.close()
        return

    def classify_callback(self, channel, method, properties, body):
        if self.classifier:
            try:
                queue_items = serializers.deserialize('json', body)
            except DeserializationError as ex_deserialize:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier failed to deserialize body.')
                return

            try:
                queue_item = next(queue_items).object
                is_self_train = properties.headers['x-is-self-train']
            except (StopIteration, RuntimeError) as ex_item:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier failed to get object from deserialized body.')
                return

            self.logger.info('Classifying #%s...', queue_item.id)
            classification = self.classifier.classify(queue_item.title)

            # self training will create corpus, crawl will update the news item
            handler = CorpusHandler() if is_self_train else PublishHandler()

            try:
                handler.run(queue_item, classification)
            except (FieldDoesNotExist, FieldError, ValidationError) as ex_save:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier could not handle the item due to "%s"', str(ex_save))
                return

            try:
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except (
                    AMQPConnectionError, AMQPChannelError, ChannelClosed,
                    ConnectionClosed, NoFreeChannels
            ) as ex_ack:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier could not acknowledge item due to "%s"', str(ex_ack))
                return

            self.logger.info(
                'Classified #%s "%s" as "%s"!', queue_item.id, queue_item.title, classification
            )
        else:
            self.reject_queue_item(channel, method)
            self.logger.warning('Classifier was not ready when started to classify.')
            # sleep to wait for classifier's training
            # basic_consume() will call this method again as we nacked
            time.sleep(10)

    def train_callback(self, channel, method, properties, body):
        channel.queue_purge(queue=settings.QUEUE_NAME_TRAIN)

        self.classifier = None
        self.logger.info('train_callback(): Starting training...')
        try:
            self.classifier = self.get_classifier()
            self.logger.info('train_callback(): Finished training!')
        except (utils.Error, utils.DataError, utils.DatabaseError) as ex_db:
            self.logger.error('Failed to train the classifier.')

    @staticmethod
    def get_stopwords():
        stopwords_whitelisted = [
            'above', 'out', 'off', 'again', 'against', 'why', 'few', 'more', 'most', 'no', 'nor',
            'not', 'only', 'don', 'don\'t', 'should', 'should\'ve', 'ain', 'aren', 'aren\'t',
            'couldn', 'couldn\'t', 'didn', 'didn\'t', 'doesn', 'doesn\'t', 'hadn', 'hadn\'t',
            'hasn', 'hasn\'t', 'haven', 'haven\'t', 'isn', 'isn\'t', 'mightn', 'mightn\'t',
            'needn', 'needn\'t', 'shan', 'shan\'t', 'shouldn', 'shouldn\'t', 'wasn', 'wasn\'t',
            'weren', 'weren\'t', 'won', 'won\'t', 'wouldn', 'wouldn\'t'
        ]

        stopwords_diff = [
            stopword for stopword in stopwords.words('english') \
            if stopword not in stopwords_whitelisted
        ]
        return stopwords_diff

    def reject_queue_item(self, channel, method):
        try:
            channel.basic_nack(delivery_tag=method.delivery_tag)
        except (
                AMQPConnectionError, AMQPChannelError, ChannelClosed, ConnectionClosed,
                NoFreeChannels
        ) as ex_ack:
            self.logger.error('Classifier could not nack message.')
