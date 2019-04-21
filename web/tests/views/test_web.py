from django.http.response import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from core.models.newsitem import NewsItem
from core.models.source import Source


class WebTestCase(TestCase):

    def get_news(self):
        headers = { 'user_agent': 'test-browser' }
        response = self.client.get('/web/', **headers)
        return response

    def get_about(self):
        headers = { 'user_agent': 'test-browser' }
        response = self.client.get('/about/', **headers)
        return response

    def test_news_returns_http_response_with_empty_template_when_no_newsitems_exist(self):
        # make request to news view
        response = self.get_news()

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
        response = self.get_news()

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
        response = self.get_news()

        # returns an instance of HttpResponse
        self.assertTrue(type(response) is HttpResponse)

        # request didn't fail
        self.assertEquals(200, response.status_code)

        # response contains news items
        content = response.getvalue()
        self.assertTrue('news-item' in str(content))

    def test_about_returns_http_response_with_stats(self):
        # create a news item
        news_item = NewsItem()
        news_item.title = 'foo'
        news_item.score = 1
        news_item.published = False
        news_item.save()

        # create a source
        source = Source()
        source.name = 'foo'
        source.url = 'http://www.google.com'
        source.homepage = 'http://www.google.com'
        source.save()

        # make request to news view
        response = self.get_about()

        # returns an instance of HttpResponse
        self.assertTrue(type(response) is HttpResponse)

        # request didn't fail
        self.assertEquals(200, response.status_code)

        # response does not contain any news items
        content = response.getvalue()
        self.assertTrue('Sources crawled</strong>: 1' in str(content))
        self.assertTrue('News classified</strong>: 1' in str(content))
        self.assertTrue('Corpora created</strong>: 0' in str(content))
        self.assertTrue('Classification accuracy</strong>: 100%' in str(content))
