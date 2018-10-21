from django.contrib import admin
from django.conf import settings
from rss.models.newsitem import NewsItem
from rss.models.corpus import Corpus


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

        return response
