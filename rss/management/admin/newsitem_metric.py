import calendar
from datetime import datetime

from django.contrib import admin
from django.conf import settings

from rss.models.newsitem import NewsItem
from rss.models.newsitem_metric import NewsItemMetric
from rss.models.corpus import Corpus


class NewsItemMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/newsitem_metric_list.html'
    date_hierarchy = 'added_at'

    @staticmethod
    def get_request_params(request):
        params = dict()
        for key, val in request.GET.lists():
            params[key] = val[0]
        return params

    @staticmethod
    def get_date_range(params):
        # set the defaults, if no range elements are selected
        from_year = 2018
        from_month = 1
        from_day = 1
        to_year = datetime.now().year
        to_month = datetime.now().month
        to_day = None

        if 'added_at__year' in params:
            from_year = params['added_at__year']
            to_year = params['added_at__year']

        if 'added_at__month' in params:
            from_month = params['added_at__month']
            to_month = params['added_at__month']

        if 'added_at__day' in params:
            from_day = params['added_at__day']
            to_day = params['added_at__day']
        else:
            # get the last day of the selected month
            to_day = calendar.monthrange(int(to_year), int(to_month))[-1]

        return {
            'date_from': '{}-{:02d}-{:02d} 00:00:00'.format(from_year, int(from_month), int(from_day)),
            'date_to': '{}-{:02d}-{:02d} 23:59:59'.format(to_year, int(to_month), int(to_day))
        }

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        # get url query parameters
        params = self.get_request_params(request)

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

        # calculate accuracy over time
        date_range = self.get_date_range(params)
        response.context_data['accuracy'] = NewsItemMetric().get_accuracy(date_range)

        return response
