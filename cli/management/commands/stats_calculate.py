from datetime import datetime
import logging
import pika

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models.newsitem import NewsItem
from core.models.corpus import Corpus
from core.models.newsitem_metric import NewsItemMetric
from core.models.source import Source
from core.models.statistic import Statistic


class Command(BaseCommand):
    help = 'Pre-calculate stats shown in about page'

    def __init__(self):
        super(Command, self).__init__()
        self.logger = logging.getLogger('web')

    def handle(self, *args, **options):
        self.logger.info('Pre-calculating stats!')

        now = datetime.now()

        news_item_metric = NewsItemMetric()
        accuracy_total = news_item_metric.get_accuracy_total({
            'date_from': '2018-01-01 00:00:00',
            'date_to': '{}-{:02d}-{:02d} 23:59:59'.format(
                now.year, int(now.month), int(now.day)
            )
        })
        accuracy_total = round(accuracy_total)

        news_items_count = NewsItem.objects.all().count()
        corpora_count = Corpus.objects.filter(active=True).count()
        sources_count = Source.objects.filter(active=True).count()

        # news_items pending classification
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
        channel = connection.channel()
        queue = channel.queue_declare(
            queue=settings.QUEUE_NAME_CLASSIFY,
            durable=True,
            exclusive=False,
            auto_delete=False
        )
        pending_classify_count = queue.method.message_count

        statistic = Statistic()
        statistic.accuracy_total = accuracy_total
        statistic.news_items_count = news_items_count
        statistic.pending_classify_count = pending_classify_count
        statistic.corpora_count = corpora_count
        statistic.sources_count = sources_count
        statistic.save()

        self.logger.info('Stats pre-calculated!')
