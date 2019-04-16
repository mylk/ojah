import logging
import pika

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers

from core.models.newsitem import NewsItem


class Command(BaseCommand):
    help = 'Re-queue for classification the news items missing score'

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def handle(self, *args, **options):
        news_items = NewsItem.objects.filter(score=None)

        if not news_items:
            self.logger.info('All news items are already classified!')
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME)
        )
        channel = connection.channel()
        channel.queue_declare(queue=settings.QUEUE_NAME_CLASSIFY, durable=True)
        self.logger.info('Found %s news items that need to be classified.', len(news_items))

        for news_item in news_items:
            body = serializers.serialize('json', [news_item])
            channel.basic_publish(
                exchange='',
                routing_key=settings.QUEUE_NAME_CLASSIFY,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2)
            )

            self.logger.info('Successfully re-queued #%s "%s"!', news_item.id, news_item.title)
