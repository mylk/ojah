from django.test import TestCase
from rss.models.corpus import Corpus
from rss.models.newsitem import NewsItem


class CorpusTestCase(TestCase):

    corpus = None

    def setUp(self):
        news_item = NewsItem()
        self.corpus = Corpus()
        self.corpus.news_item = news_item

    def test_get_classification_returns_pos_when_positive_is_true(self):
        self.corpus.positive = True
        self.assertEquals('pos', self.corpus.get_classification())

    def test_get_classification_returns_neg_when_positive_is_false(self):
        self.corpus.positive = False
        self.assertEquals('neg', self.corpus.get_classification())

    def test_str_returns_newsitem_title_and_classification(self):
        self.corpus.positive = True
        self.corpus.news_item.title = 'foo'
        self.assertEquals('foo: POS', str(self.corpus))
