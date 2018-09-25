from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from rss.models.newsitem import NewsItem
from rss.models.corpus import Corpus
from textblob.classifiers import NaiveBayesClassifier
from random import shuffle
import pika
import threading
import logging
import time


class Command(BaseCommand):
    help = 'Perform sentiment analysis on news items'
    logger = logging.getLogger('rss')
    classifier = None

    def handle(self, *args, **options):
        self.logger.info('Training classifier...')
        self.classifier = self.get_classifier()
        self.logger.info('Classifier is ready!')

        thread_classify = threading.Thread(target=self.classify_consumer, args=(), name='classify')
        thread_classify.start()

        thread_train = threading.Thread(target=self.train_consumer, args=(), name='train')
        thread_train.start()

    def classify_consumer(self):
        channel = self.get_consumer(settings.QUEUE_NAME_CLASSIFY, self.classify_callback)
        try:
            channel.start_consuming()
        except Exception as e:
            self.logger.error(str(e))

    def train_consumer(self):
        channel = self.get_consumer(settings.QUEUE_NAME_TRAIN, self.train_callback)
        try:
            channel.start_consuming()
        except Exception as e:
            self.logger.error(str(e))

    def get_consumer(self, queue, callback):
        try:
            params = pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME, heartbeat_interval=600, blocked_connection_timeout=300)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(callback, queue=queue)
        except Exception as e:
            self.logger.error(str(e))

        return channel

    def get_classifier(self):
        corpora_classified = list()
        for corpus in Corpus.objects.all():
            corpora_classified.append((corpus.news_item.title, corpus.get_classification()))

        shuffle(corpora_classified)

        return NaiveBayesClassifier(corpora_classified)

    def classify_callback(self, channel, method, properties, body):
        if self.classifier:
            try:
                queue_items = serializers.deserialize('json', body)
                queue_item = next(queue_items).object

                self.logger.info('Classifying #%s...' % queue_item.id)
                classification = self.classifier.classify(queue_item.title)

                queue_item.score = 1 if classification == 'pos' else 0
                queue_item.save()

                channel.basic_ack(delivery_tag=method.delivery_tag)

                self.logger.info('Classified #{} "{}" as "{}"!'.format(queue_item.id, queue_item.title, classification))
            except Exception as e:
                channel.basic_nack(delivery_tag=method.delivery_tag)
                self.logger.error('Could not classify #{}, due to "{}"'.format(queue_item.id, str(e)))
        else:
            channel.basic_nack(delivery_tag=method.delivery_tag)
            self.logger.warn('Classifier was not ready when started to classify.')
            # sleep to wait for classifier's training
            time.sleep(10)

    def train_callback(self, channel, method, properties, body):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        channel.queue_purge(queue=settings.QUEUE_NAME_TRAIN)

        self.classifier = None
        self.logger.info('train_callback(): Starting training...')
        self.classifier = self.get_classifier()
        self.logger.info('train_callback(): Finished training!')
