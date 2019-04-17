import calendar
from datetime import datetime
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from web.management.admin.newsitem_metric import NewsItemMetricAdmin
from core.models.corpus import Corpus
from core.models.newsitem import NewsItem
from core.models.newsitem_metric import NewsItemMetric


class NewsItemMetricAdminTestCase(TestCase):

    admin = None
    factory = RequestFactory()

    def setUp(self):
        self.admin = NewsItemMetricAdmin(NewsItemMetric, AdminSite())

    def create_superuser(self, username):
        return User.objects.create_superuser(username=username, email='foo@bar.baz', password='qwerty')

    def mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request

    def test_get_date_range_returns_default_when_no_parameters_set(self):
        to_year = datetime.now().year
        to_month = datetime.now().month
        to_day = calendar.monthrange(int(to_year), int(to_month))[-1]
        expected_date_to = '{}-{:02d}-{:02d} 23:59:59'.format(to_year, int(to_month), int(to_day))

        params = []
        date_range = self.admin.get_date_range(params)
        self.assertEquals('2018-01-01 00:00:00', date_range['date_from'])
        self.assertEquals(expected_date_to, date_range['date_to'])

    def test_get_date_range_returns_default_when_year_parameter_set(self):
        to_month = datetime.now().month
        to_day = calendar.monthrange(2018, int(to_month))[-1]
        expected_date_to = '2018-{:02d}-{:02d} 23:59:59'.format(int(to_month), int(to_day))

        params = {
            'added_at__year': '2018'
        }
        date_range = self.admin.get_date_range(params)
        self.assertEquals('2018-01-01 00:00:00', date_range['date_from'])
        self.assertEquals(expected_date_to, date_range['date_to'])

    def test_get_date_range_returns_default_when_year_and_month_parameters_set(self):
        to_day = calendar.monthrange(2018, 11)[-1]
        expected_date_to = '2018-11-{:02d} 23:59:59'.format(int(to_day))

        params = {
            'added_at__year': '2018',
            'added_at__month': '11'
        }
        date_range = self.admin.get_date_range(params)
        self.assertEquals('2018-11-01 00:00:00', date_range['date_from'])
        self.assertEquals(expected_date_to, date_range['date_to'])

    def test_get_date_range_returns_default_when_year_and_month_and_day_parameters_set(self):
        expected_date_to = '2018-11-16 23:59:59'

        params = {
            'added_at__year': '2018',
            'added_at__month': '11',
            'added_at__day': '16'
        }
        date_range = self.admin.get_date_range(params)
        self.assertEquals('2018-11-16 00:00:00', date_range['date_from'])
        self.assertEquals(expected_date_to, date_range['date_to'])

    def test_get_request_params_while_query_string_empty(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'QUERY_STRING': '',
        })

        params = self.admin.get_request_params(request)
        self.assertEquals({}, params)

    def test_get_request_params_while_query_string_not_empty(self):
        request = WSGIRequest({
            'REQUEST_METHOD': 'GET',
            'wsgi.input': '',
            'QUERY_STRING': 'foo=bar&baz=foo',
        })

        params = self.admin.get_request_params(request)
        self.assertEquals('bar', params['foo'])
        self.assertEquals('foo', params['baz'])

    def test_changelist_view_returns_zero_metrics_when_no_newsitems_and_no_corpora_exist(self):
        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(0, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(0, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(0, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_unclassified_newsitems_exist_and_no_corpora(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = None
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(1, response.context_data['news_items_count'])
        self.assertEquals(1, response.context_data['news_items_unclassified'])
        self.assertEquals(0, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(0, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_newsitems_exist_but_no_corpora(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        news_item = NewsItem()
        news_item.title = 'bar'
        news_item.score = 0
        news_item.added_at = '2018-12-03 22:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(2, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(1, response.context_data['classification_initial']['positive'])
        self.assertEquals(1, response.context_data['classification_initial']['negative'])
        self.assertEquals(1, response.context_data['classification_supervised']['positive'])
        self.assertEquals(1, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 100.0, 'added_at': '2018-12-03'}], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_newsitems_exist_but_no_corpora_and_date_query_does_not_include_newsitem(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/?added_at__month=11&added_at__year=2018', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(0, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(0, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(0, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_newsitems_exist_but_no_corpora_and_date_query_includes_newsitem(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/?added_at__month=12&added_at__year=2018', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(1, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(1, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(1, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 100.0, 'added_at': '2018-12-03'}], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_negative_newsitem_and_positive_corpus_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 0
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.positive = True
        corpus.news_item = news_item
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(1, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(0, response.context_data['classification_initial']['positive'])
        self.assertEquals(1, response.context_data['classification_initial']['negative'])
        self.assertEquals(1, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(1, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 0, 'added_at': '2018-12-03'}], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_positive_newsitem_and_negative_corpus_exist(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.positive = False
        corpus.news_item = news_item
        corpus.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(1, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(1, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(0, response.context_data['classification_supervised']['positive'])
        self.assertEquals(1, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(1, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 0, 'added_at': '2018-12-03'}], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_accurate_and_inaccurate_newsitems_exist_and_finally_all_positive(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 0
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.positive = True
        corpus.news_item = news_item
        corpus.save()

        news_item = NewsItem()
        news_item.title = 'bar'
        news_item.score = 1
        news_item.added_at = '2018-12-03 22:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(2, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(1, response.context_data['classification_initial']['positive'])
        self.assertEquals(1, response.context_data['classification_initial']['negative'])
        self.assertEquals(2, response.context_data['classification_supervised']['positive'])
        self.assertEquals(0, response.context_data['classification_supervised']['negative'])
        self.assertEquals(1, response.context_data['corpus_count']['positive'])
        self.assertEquals(0, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 50, 'added_at': '2018-12-03'}], response.context_data['accuracy'])

    def test_changelist_view_returns_metrics_when_accurate_and_inaccurate_newsitems_exist_and_finally_one_of_each_class(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.added_at = '2018-12-03 21:00:00+00:00'
        news_item.save()

        corpus = Corpus()
        corpus.positive = False
        corpus.news_item = news_item
        corpus.save()

        news_item = NewsItem()
        news_item.title = 'bar'
        news_item.score = 1
        news_item.added_at = '2018-12-03 22:00:00+00:00'
        news_item.save()

        superuser = self.create_superuser('superuser')
        request = self.mocked_authenticated_request('/admin/rss/newsitemmetric/', superuser)
        response = self.admin.changelist_view(request)

        self.assertEquals(2, response.context_data['news_items_count'])
        self.assertEquals(0, response.context_data['news_items_unclassified'])
        self.assertEquals(2, response.context_data['classification_initial']['positive'])
        self.assertEquals(0, response.context_data['classification_initial']['negative'])
        self.assertEquals(1, response.context_data['classification_supervised']['positive'])
        self.assertEquals(1, response.context_data['classification_supervised']['negative'])
        self.assertEquals(0, response.context_data['corpus_count']['positive'])
        self.assertEquals(1, response.context_data['corpus_count']['negative'])
        self.assertEquals([{'accuracy': 50, 'added_at': '2018-12-03'}], response.context_data['accuracy'])
