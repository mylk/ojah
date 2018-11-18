from django.test import TestCase
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.core.handlers.wsgi import WSGIRequest
from datetime import datetime
import calendar
from rss.management.admin.newsitem_metric import NewsItemMetricAdmin
from rss.models.newsitem_metric import NewsItemMetric


class NewsItemMetricAdminTestCase(TestCase):

    admin = None
    site = AdminSite()

    def setUp(self):
        self.admin = NewsItemMetricAdmin(NewsItemMetric, self.site)

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
