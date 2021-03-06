import logging
import pika

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers

from core.models.newsitem import NewsItem


class Command(BaseCommand):
    help = 'Re-queue for classification the news items that have been previously scored as negative'

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def handle(self, *args, **options):
        news_items = NewsItem.find_negative(settings.SENTIMENT_POLARITY_THRESHOLD)

        if not news_items:
            self.logger.info('No news items found.')
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME)
        )
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)
        self.logger.info('Found %s negative news items that are going to be re-classified.', len(news_items))

        for news_item in news_items:
            body = serializers.serialize('json', [news_item])
            channel.basic_publish(
                exchange='',
                routing_key=settings.QUEUE_NAME_CLASSIFY,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers={'x-is-self-train': True}
                )
            )

            self.logger.info('Successfully re-queued #%s "%s"!', news_item.id, news_item.title)
