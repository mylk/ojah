from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.template import loader

from core.models.newsitem import NewsItem
from core.models.statistic import Statistic


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
    today_midnight = '{}-{:02d}-{:02d} 00:00:00'.format(now.year, int(now.month), int(now.day))
    # get the latest of the created statistics for today
    statistics = Statistic.objects.filter(created_at__gte=today_midnight).order_by('-created_at')

    accuracy_total = '{}%'.format(statistics[0].accuracy_total) if statistics[0].accuracy_total else None

    context = {
        'accuracy_total': accuracy_total,
        'news_items_count': statistics[0].news_items_count,
        'pending_classify_count': statistics[0].pending_classify_count,
        'news_items_not_scored_count': statistics[0].news_items_not_scored_count,
        'corpora_count': statistics[0].corpora_count,
        'sources_count': statistics[0].sources_count,
        'created_at': statistics[0].created_at
    }

    return HttpResponse(template.render(context))
