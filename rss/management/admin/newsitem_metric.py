from django.contrib import admin
from django.conf import settings
from django.db import connection
from rss.models.newsitem import NewsItem
from rss.models.corpus import Corpus
from datetime import datetime
import calendar


class NewsItemMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/newsitem_metric_list.html'
    date_hierarchy = 'added_at'

    @staticmethod
    def dict_fetch_all(cursor):
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

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

        # calculate accuracy over time
        date_range = self.get_date_range(params)
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT
                (
                    100 - (
                        CASE errors.error
                        WHEN CAST(0 AS FLOAT)
                        THEN 100
                        ELSE PRINTF("%.2f", errors.error)
                        END
                    )
                ) AS accuracy,
                added_at
                FROM (
                    SELECT (
                        (CAST(counts.corpus_count AS FLOAT) / CAST(counts.news_count AS FLOAT)) * 100
                    ) AS error,
                    added_at
                    FROM (
                        SELECT
                        COUNT(news_and_corpora.news_item_id) AS news_count,
                        COUNT(news_and_corpora.corpus_id) AS corpus_count,
                        added_at
                        FROM (
                            SELECT ni.id AS news_item_id, c.id AS corpus_id, DATE(ni.added_at) AS added_at
                            FROM news_item AS ni
                            LEFT JOIN corpus AS c ON c.news_item_id = ni.id
                            WHERE ni.added_at BETWEEN %s AND %s
                        ) AS news_and_corpora
                        GROUP BY added_at
                    ) AS counts
                    GROUP BY added_at
                ) AS errors;
            ''', (date_range['date_from'], date_range['date_to']))
            response.context_data['accuracy'] = self.dict_fetch_all(cursor)
        return response
