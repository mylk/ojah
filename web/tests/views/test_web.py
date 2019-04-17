from django.http.response import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from core.models.newsitem import NewsItem


class WebTestCase(TestCase):

    def get(self):
        headers = { 'user_agent': 'test-browser' }
        response = self.client.get('/news/', **headers)
        return response

    def test_news_returns_http_response_with_empty_template_when_no_newsitems_exist(self):
        # make request to news view
        response = self.get()

        # returns an instance of HttpResponse
        self.assertTrue(type(response) is HttpResponse)

        # request didn't fail
        self.assertEquals(200, response.status_code)

        # response does not contain any news items
        content = response.getvalue()
        self.assertFalse('news-item' in str(content))

    def test_news_returns_http_response_with_empty_template_when_only_negative_newsitems_exist(self):
        # create a negative news item
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 0
        news_item.published = False
        news_item.save()

        # make request to news view
        response = self.get()

        # returns an instance of HttpResponse
        self.assertTrue(type(response) is HttpResponse)

        # request didn't fail
        self.assertEquals(200, response.status_code)

        # response does not contain any news items
        content = response.getvalue()
        self.assertFalse('news-item' in str(content))

    def test_news_returns_http_response_with_template_and_positive_newsitems_when_positive_newsitems_exist(self):
        # create a positive news item
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.published = True
        news_item.save()

        # make request to news view
        response = self.get()

        # returns an instance of HttpResponse
        self.assertTrue(type(response) is HttpResponse)

        # request didn't fail
        self.assertEquals(200, response.status_code)

        # response contains news items
        content = response.getvalue()
        self.assertTrue('news-item' in str(content))
