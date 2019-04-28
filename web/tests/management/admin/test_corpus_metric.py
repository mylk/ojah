from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from web.management.admin.corpus_metric import CorpusMetricAdmin
from core.models.corpus import Corpus
from core.models.corpus_metric import CorpusMetric
from core.models.newsitem import NewsItem


class CorpusMetricAdminTestCase(TestCase):
    factory = RequestFactory()

    def setUp(self):
        self.admin = CorpusMetricAdmin(CorpusMetric, AdminSite())

    def create_superuser(self, username):
        return User.objects.create_superuser(username=username, email='foo@bar.baz', password='qwerty')

    def mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request

    def test_changelist_view_returns_no_metrics_when_no_corpora_exist(self):
        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = []
        expected_metrics_total = {
            'total': 0
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])

    def test_changelist_view_returns_positive_metrics_when_only_positive_corpora_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = [{
            'positive': True,
            'total': 1
        }]
        expected_metrics_total = {
            'total': 1
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])

    def test_changelist_view_returns_negative_metrics_when_only_negative_corpora_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = [{
            'positive': False,
            'total': 1
        }]
        expected_metrics_total = {
            'total': 1
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])

    def test_changelist_view_returns_positive_and_negative_metrics_when_positive_and_negative_corpora_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

        news_item = NewsItem()
        news_item.title = 'bar'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = [
            {
                'positive': True,
                'total': 1
            },
            {
                'positive': False,
                'total': 1
            }
        ]
        expected_metrics_total = {
            'total': 2
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])

    def test_changelist_view_returns_no_metrics_when_corpora_exist_but_query_is_out_of_the_added_at_date(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.added_at = '2018-12-02 21:00:00+00:00'
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/?added_at__month=11&added_at__year=2018', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = []
        expected_metrics_total = {
            'total': 0
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])

    def test_changelist_view_returns_metrics_when_corpora_exist_and_query_is_on_the_added_at_date(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.save()

        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.added_at = '2018-12-02 21:00:00+00:00'
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/corpusmetric/?added_at__month=12&added_at__year=2018', superuser)
        response = self.admin.changelist_view(request)

        expected_metrics = [{
            'positive': True,
            'total': 1
        }]
        expected_metrics_total = {
            'total': 1
        }

        self.assertEquals(expected_metrics, response.context_data['corpus_metrics'])
        self.assertEquals(expected_metrics_total, response.context_data['corpus_metrics_total'])
