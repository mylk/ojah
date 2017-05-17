from django.core.management.base import BaseCommand, CommandError
from rss.models.source import Source
from rss.models.newsitem import NewsItem
import feedparser
from textblob import TextBlob


class Command(BaseCommand):
    help = 'Crawl RSS feeds and perform sentiment analysis on news items'

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', type=str)

    def handle(self, *args, **options):
        name = options['name']

        if name:
            sources = Source.objects.filter(name=name)
            if not sources:
                self.stdout.write(self.style.ERROR('Could not find source \'%s\'' % name))
        else:
            sources = Source.objects.all()

        for source in sources:
            self.crawl(source)

    def crawl(self, source):
        self.stdout.write('Crawling \'%s\'...' % source.name)

        try:
            feed = feedparser.parse(source.url)
        except:
            self.stdout.write(self.style.ERROR('Could not crawl \'%s\'' % source.name))

        for entry in feed['entries']:
            description = entry['summary'] if 'summary' in entry else entry['title']

            if NewsItem.exists(entry['title'], entry['updated'], source):
                continue

            score = TextBlob(entry['title']).sentiment.polarity

            news_item = NewsItem()
            news_item.title = entry['title']
            news_item.description = description
            news_item.url = entry['link']
            news_item.source = source
            news_item.score = score
            news_item.added_at = entry['updated']
            news_item.save()

        self.stdout.write(self.style.SUCCESS('Successfully crawled \'%s\'' % source.name))