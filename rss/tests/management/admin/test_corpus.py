from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from rss.management.admin.corpus import CorpusAdmin
from core.models.corpus import Corpus
from core.models.newsitem import NewsItem


class CorpusAdminTestCase(TestCase):

    def test_get_newsitem_title_returns_title_when_news_item_is_not_none(self):
        news_item = NewsItem()
        news_item.title = 'foo'
        corpus = Corpus()
        corpus.news_item = news_item

        admin = CorpusAdmin(Corpus, AdminSite())
        self.assertEquals('foo', admin.get_news_item_title(corpus))
