from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.template import loader

from core.models.corpus import Corpus
from core.models.newsitem import NewsItem
from core.models.newsitem_metric import NewsItemMetric
from core.models.source import Source


def news(request):
    template = loader.get_template('web/news.html')

    news_items = NewsItem.find_positive(
        settings.SENTIMENT_POLARITY_THRESHOLD,
        settings.WEB_NEWS_ITEMS_COUNT
    )

    context = {
        'news_items': news_items
    }

    return HttpResponse(template.render(context))


def about(request):
    template = loader.get_template('web/about.html')
    now = datetime.now()

    news_item_metric = NewsItemMetric()
    accuracy_total = news_item_metric.get_accuracy_total({
        'date_from': '2018-01-01 00:00:00',
        'date_to': '{}-{:02d}-{:02d} 23:59:59'.format(
            now.year, int(now.month), int(now.day)
        )
    })
    news_items_count = NewsItem.objects.all().count()
    corpora_count = Corpus.objects.all().count()
    sources_count = Source.objects.all().count()

    context = {
        'accuracy_total': '{}%'.format(round(accuracy_total)),
        'news_items_count': news_items_count,
        'corpora_count': corpora_count,
        'sources_count': sources_count
    }

    return HttpResponse(template.render(context))
