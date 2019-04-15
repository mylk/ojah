from rss.templatetags.percent_of import percent_of
import unittest


class PercentOfTestCase(unittest.TestCase):

    def test_percent_of_returns_percentage_when_not_divide_by_zero(self):
        self.assertEquals('5.0%', percent_of(10, 200))

    def test_percent_of_returns_percentage_with_one_decimal_place_when_more_than_one_decimal_places(self):
        self.assertEquals('4.7%', percent_of(10, 211))

    def test_percent_of_returns_none_when_divide_by_zero(self):
        self.assertEquals(None, percent_of(1, 0))
