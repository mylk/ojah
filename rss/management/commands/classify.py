from django.core.management.base import BaseCommand
from django.conf import settings
from rss.models.newsitem import NewsItem
from rss.models.corpus import Corpus
from textblob.classifiers import NaiveBayesClassifier
from random import shuffle
import pika
import json


class Command(BaseCommand):
    help = 'Perform sentiment analysis on news items'
    classifier = None

    def handle(self, *args, **options):
        self.stdout.write('Training classifier...')
        self.classifier = self.get_classifier()
        self.stdout.write('Classifier is ready!')

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(self.classify, queue=settings.QUEUE_NAME_CLASSIFY)
        self.stdout.write('Waiting for messages...')
        channel.start_consuming()

    def get_classifier(self):
        corpora_classified = list()
        for corpus in Corpus.objects.all():
            corpora_classified.append((corpus.news_item.title, corpus.get_classification()))

        shuffle(corpora_classified)

        return NaiveBayesClassifier(corpora_classified)

    def classify(self, channel, method, properties, body):
        if not self.classifier:
            self.stdout.write(self.style.ERROR('Classifier was not ready when started to classify.'))
            return

        queue_item = json.loads(body)
        try:
            self.stdout.write('Classifying #%s...' % queue_item['id'])
            classification = self.classifier.classify(queue_item['title'])

            news_item = NewsItem.objects.get(pk=queue_item['id'])
            news_item.score = 1 if classification == 'pos' else 0
            news_item.save()

            channel.basic_ack(delivery_tag=method.delivery_tag)
        except RuntimeError:
            self.stdout.write(self.style.ERROR('Could not classify #%s.' % queue_item['id']))
            return

        self.stdout.write(self.style.SUCCESS('Successfully classified #{} "{}" as "{}"!'.format(queue_item['id'], queue_item['title'], classification)))
