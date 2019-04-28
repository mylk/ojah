from django.db import connection
from core.models.newsitem import NewsItem


class NewsItemMetric(NewsItem):

    class Meta:
        proxy = True
        verbose_name = 'news item metric'
        verbose_name_plural = 'news item metrics'

    @staticmethod
    def to_dict(cursor):
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_accuracy(self, date_range):
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT (
                    100 - ROUND(errors.error, 2)
                ) AS accuracy,
                added_at
                FROM (
                    SELECT (
                        (counts.corpus_count / counts.news_count) * 100
                    ) AS error,
                    added_at
                    FROM (
                        SELECT
                        COUNT(news_and_corpora.news_item_id) AS news_count,
                        COUNT(news_and_corpora.corpus_id) AS corpus_count,
                        added_at
                        FROM (
                            SELECT ni.id AS news_item_id, c.id AS corpus_id, DATE_FORMAT(ni.added_at, "%%Y-%%m-%%d") AS added_at
                            FROM news_item AS ni
                            LEFT JOIN corpus AS c ON c.news_item_id = ni.id
                            WHERE ni.added_at BETWEEN %s AND %s
                            AND NOT ni.score IS NULL
                        ) AS news_and_corpora
                        GROUP BY added_at
                    ) AS counts
                    GROUP BY added_at
                ) AS errors;
            ''', (date_range['date_from'], date_range['date_to']))
            return self.to_dict(cursor)

    def get_accuracy_total(self, date_range):
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT (
                    100 - ROUND(errors.error, 2)
                ) AS accuracy
                FROM (
                    SELECT (
                        (counts.corpus_count / counts.news_count) * 100
                    ) AS error
                    FROM (
                        SELECT
                        COUNT(news_and_corpora.news_item_id) AS news_count,
                        COUNT(news_and_corpora.corpus_id) AS corpus_count
                        FROM (
                            SELECT ni.id AS news_item_id, c.id AS corpus_id
                            FROM news_item AS ni
                            LEFT JOIN corpus AS c ON c.news_item_id = ni.id
                            WHERE ni.added_at BETWEEN %s AND %s
                            AND NOT ni.score IS NULL
                        ) AS news_and_corpora
                    ) AS counts
                ) AS errors;
            ''', (date_range['date_from'], date_range['date_to']))
            return self.to_dict(cursor)[0]['accuracy']
