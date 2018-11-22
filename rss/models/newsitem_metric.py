from django.db import connection
from rss.models.newsitem import NewsItem


class NewsItemMetric(NewsItem):

    class Meta:
        proxy = True
        verbose_name = 'news item metric'
        verbose_name_plural = 'news item metrics'

    @staticmethod
    def dict_fetch_all(cursor):
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_accuracy(self, date_range):
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
            return self.dict_fetch_all(cursor)
