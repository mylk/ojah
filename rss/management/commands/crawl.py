from django.core.management.base import BaseCommand
from django.conf import settings
from rss.models.source import Source
from rss.models.newsitem import NewsItem
import feedparser
from textblob.classifiers import NaiveBayesClassifier
from random import shuffle
import pika
import json


class Command(BaseCommand):
    help = 'Crawl RSS feeds'

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', type=str)

    def handle(self, *args, **options):
        name = options['name']

        if name:
            sources = Source.objects.filter(name=name)
            if not sources:
                self.stdout.write(self.style.ERROR('Could not find source \'%s\'.' % name))
        else:
            sources = Source.objects.all()

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)

        for source in sources:
            self.crawl(source, channel)

    def crawl(self, source, channel):
        self.stdout.write('Crawling \'%s\'...' % source.name)
        try:
            feed = feedparser.parse(source.url)
        except RuntimeError:
            self.stdout.write(self.style.ERROR('Could not crawl \'%s\'.' % source.name))
            return

        for entry in feed['entries']:
            if NewsItem.exists(entry['title'], entry['updated'], source):
                continue

            description = entry['summary'] if 'summary' in entry else entry['title']

            news_item = NewsItem()
            news_item.title = entry['title']
            news_item.description = description
            news_item.url = entry['link']
            news_item.source = source
            news_item.score = None
            news_item.added_at = entry['updated']
            news_item.save()

            body = json.dumps({'id': news_item.id, 'title': news_item.title})
            channel.basic_publish(
                exchange='',
                routing_key=settings.QUEUE_NAME_CLASSIFY,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2)
            )

        source.crawled()

        self.stdout.write(self.style.SUCCESS('Successfully crawled \'%s\'!' % source.name))
