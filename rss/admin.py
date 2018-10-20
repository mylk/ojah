from django.contrib import admin
from django.conf import settings
from django.db.models import Count
from rangefilter.filter import DateRangeFilter
from .models.source import Source
from .models.newsitem import NewsItem
from .models.newsitem_metric import NewsItemMetric
from .models.corpus import Corpus
from .models.corpus_metric import CorpusMetric
import pika


def news_item_publish(model_admin, request, query_set):
    for news_item in query_set:
        news_item.published = True
        news_item.save()


news_item_publish.short_description = 'Publish'


def news_item_unpublish(model_admin, request, query_set):
    for news_item in query_set:
        news_item.published = False
        news_item.save()


news_item_unpublish.short_description = 'Unpublish'


def news_item_corpus_create_positive(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

    enqueue_corpus_creation()


news_item_corpus_create_positive.short_description = 'Corpus - Create positive'


def news_item_corpus_create_negative(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

    enqueue_corpus_creation()


news_item_corpus_create_negative.short_description = 'Corpus - Create negative'


def news_item_publish_and_corpus_create_positive(model_admin, request, query_set):
    news_item_corpus_create_positive(model_admin, request, query_set)
    news_item_publish(model_admin, request, query_set)


news_item_publish_and_corpus_create_positive.short_description = 'Publish and create positive Corpus'


def enqueue_corpus_creation():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
    channel = connection.channel()
    channel.queue_declare(queue=settings.QUEUE_NAME_TRAIN, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=settings.QUEUE_NAME_TRAIN,
        body='',
        properties=pika.BasicProperties(delivery_mode=2)
    )


class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_crawl')
    ordering = ['-last_crawl']


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'score', 'published', 'added_at')
    list_filter = ('score', 'published', 'source', ('added_at', DateRangeFilter))
    search_fields = ['title']
    ordering = ['-added_at']
    actions = [
        news_item_publish,
        news_item_unpublish,
        news_item_corpus_create_positive,
        news_item_corpus_create_negative,
        news_item_publish_and_corpus_create_positive
    ]


class CorpusAdmin(admin.ModelAdmin):

    def get_news_item_title(self, obj):
        return obj.news_item.title

    list_display = ['get_news_item_title', 'positive', 'added_at']
    list_filter = ['positive']
    ordering = ['-added_at']


class NewsItemMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/newsitem_metric_list.html'
    date_hierarchy = 'added_at'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        # get url query parameters
        params = dict()
        for k, v in request.GET.lists():
            params[k] = v[0]

        # query for the news items as initially scored
        params_positive = dict(params)
        params_positive['score__gte'] = settings.SENTIMENT_POLARITY_THRESHOLD
        news_items_count_positive = NewsItem.objects.filter(**params_positive).count()
        params_negative = dict(params)
        params_negative['score__lt'] = settings.SENTIMENT_POLARITY_THRESHOLD
        news_items_count_negative = NewsItem.objects.filter(**params_negative).count()

        # query for all news items and calculate possible unclassified
        news_items_count = NewsItem.objects.filter(**params).count()
        response.context_data['news_items_count'] = news_items_count

        news_items_count_unclassified = (news_items_count - (news_items_count_positive + news_items_count_negative))
        response.context_data['news_items_unclassified'] = news_items_count_unclassified

        response.context_data['classification_initial'] = {
            'positive': news_items_count_positive,
            'negative': news_items_count_negative,
         }

        # query for corpora
        params_corpus = dict(params)
        params_corpus['positive'] = True
        corpus_count_positive = Corpus.objects.filter(**params_corpus).count()
        params_corpus['positive'] = False
        corpus_count_negative = Corpus.objects.filter(**params_corpus).count()
        response.context_data['corpus_count'] = {
            'positive': corpus_count_positive,
            'negative': corpus_count_negative
        }

        # calculate news items after supervision
        response.context_data['classification_supervised'] = {
            'positive': ((news_items_count_positive - corpus_count_negative) + corpus_count_positive),
            'negative': ((news_items_count_negative - corpus_count_positive) + corpus_count_negative),
         }

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        return response


class CorpusMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/corpus_metric_list.html'
    date_hierarchy = 'added_at'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Count('id')
        }

        response.context_data['corpus_metrics'] = list(
            qs
                .values('positive')
                .annotate(**metrics)
                .order_by('-total')
        )

        response.context_data['corpus_metrics_total'] = dict(
            qs.aggregate(**metrics)
        )

        return response


admin.site.register(Source, SourceAdmin)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(NewsItemMetric, NewsItemMetricAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(CorpusMetric, CorpusMetricAdmin)
