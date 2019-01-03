from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from rss.models.newsitem import NewsItem


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
