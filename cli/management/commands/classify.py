import logging
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


class Command(BaseCommand):
    help = 'Perform sentiment analysis on news items'
    classifier = None

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def handle(self, *args, **options):
        self.logger.info('Training classifier...')

        try:
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

    def get_consumer(self, queue, callback):
        try:
            params = pika.ConnectionParameters(
                host=settings.QUEUE_HOSTNAME,
                heartbeat_interval=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(callback, queue=queue)
        except DuplicateConsumerTag as ex_consumer:
            self.logger.error(str(ex_consumer))
            return None

        return channel

    def get_classifier(self):
        stopwords_blacklisted = self.get_stopwords()
        stopwords_pattern = re.compile(r'\b(' + r'|'.join(stopwords_blacklisted) + r')\b\s*')

        corpora_classified = list()
        for corpus in Corpus.objects.all():
            title = stopwords_pattern.sub('', corpus.news_item.title)
            corpora_classified.append((title, corpus.get_classification()))

        corpora_classified = list(set(corpora_classified))
        shuffle(corpora_classified)

        return NaiveBayesClassifier(corpora_classified)

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
            except (StopIteration, RuntimeError) as ex_item:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier failed to get object from deserialized body.')
                return

            self.logger.info('Classifying #%s...', queue_item.id)
            classification = self.classifier.classify(queue_item.title)

            try:
                queue_item.score = 1 if classification == 'pos' else 0
                queue_item.published = False
                if settings.AUTO_PUBLISH and classification == 'pos':
                    queue_item.published = True
                queue_item.save()
            except (FieldDoesNotExist, FieldError, ValidationError) as ex_save:
                self.reject_queue_item(channel, method)
                self.logger.error('Classifier could not save the item due to "%s"', str(ex_save))
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
        channel.basic_ack(delivery_tag=method.delivery_tag)
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