from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from rss.models.source import Source
from rss.models.newsitem import NewsItem
import datetime
import feedparser
import pika
import logging


class Command(BaseCommand):
    help = 'Crawl RSS feeds'
    logger = logging.getLogger('rss')

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', type=str)

    def handle(self, *args, **options):
        name = options['name']

        if name:
            sources = Source.objects.filter(name=name)
            if not sources:
                self.logger.error('Could not find source \'%s\'.' % name)
                return
        else:
            sources = Source.objects.all()

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)

        for source in sources:
            self.crawl(source, channel)

    def crawl(self, source, channel):
        self.logger.info('Crawling \'%s\'...' % source.name)
        try:
            feedparser.USER_AGENT = settings.RSS_CRAWL_USER_AGENT
            feed = feedparser.parse(source.url)
        except RuntimeError:
            self.logger.error('Could not crawl \'%s\'.' % source.name)
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
            news_item.added_at = datetime.datetime.strptime(entry['updated'], '%Y-%m-%dT%H:%M:%S%z')
            news_item.save()

            body = serializers.serialize('json', [news_item])
            channel.basic_publish(
                exchange='',
                routing_key=settings.QUEUE_NAME_CLASSIFY,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2)
            )

        source.crawled()

        self.logger.info('Successfully crawled \'%s\'!' % source.name)
