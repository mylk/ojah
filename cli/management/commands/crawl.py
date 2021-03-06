from dateutil.parser import parse
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from django.utils import timezone
import feedparser
import pika

from core.models.source import Source
from core.models.newsitem import NewsItem


class Command(BaseCommand):
    help = 'Crawl RSS feeds'
    logger = None

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', type=str)

    def handle(self, *args, **options):
        name = options['name']

        if name:
            sources = Source.objects.filter(name=name)
        else:
            sources = Source.objects.filter(active=True)

        if not sources:
            self.logger.error('No source(s) found.')
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME)
        )
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)

        for source in sources:
            if not source.pending or source.is_stale():
                self.crawl(source, channel)

    def crawl(self, source, channel):
        source.crawling()

        self.logger.info('Crawling \'%s\'...', source.name)

        try:
            feedparser.USER_AGENT = settings.RSS_CRAWL_USER_AGENT
            feed = feedparser.parse(source.url)
        except RuntimeError:
            self.logger.error('Could not crawl \'%s\'.', source.name)
            return

        for entry in feed['entries']:
            if 'published' in entry:
                pass
            elif 'updated' in entry:
                entry['published'] = entry['updated']
            else:
                entry['published'] = timezone.now().isoformat()

            if NewsItem.exists(entry['title'], parse(entry['published']), source):
                continue

            description = entry['summary'] if 'summary' in entry else entry['title']

            news_item = NewsItem()
            news_item.title = entry['title']
            news_item.description = description
            news_item.url = entry['link']
            news_item.source = source
            news_item.score = None
            news_item.added_at = parse(entry['published'])
            news_item.save()

            body = serializers.serialize('json', [news_item])
            channel.basic_publish(
                exchange='',
                routing_key=settings.QUEUE_NAME_CLASSIFY,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers={'x-is-self-train': False}
                )
            )

        source.crawled()

        self.logger.info('Successfully crawled \'%s\'!', source.name)
