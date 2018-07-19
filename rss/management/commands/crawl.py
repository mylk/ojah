from django.core.management.base import BaseCommand
from rss.models.source import Source
from rss.models.newsitem import NewsItem
import feedparser
from textblob.classifiers import NaiveBayesClassifier
from nltk.corpus import twitter_samples
from random import shuffle


class Command(BaseCommand):
    help = 'Crawl RSS feeds and perform sentiment analysis on news items'
    classifier = None

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

    def get_classifier(self):
        if self.classifier is not None:
            return self.classifier

        tweets_pos = twitter_samples.strings('positive_tweets.json')[:200]
        tweets_neg = twitter_samples.strings('negative_tweets.json')[:200]
        tweets_classified = list()
        for tweet in tweets_pos:
            tweets_classified.append((tweet, 'pos'))
        for tweet in tweets_neg:
            tweets_classified.append((tweet, 'neg'))
        shuffle(tweets_classified)

        self.classifier = NaiveBayesClassifier(tweets_classified)
        return self.classifier

    def crawl(self, source):
        self.stdout.write('Training classifier...')
        classifier = self.get_classifier()
        self.stdout.write('Classifier is ready!')

        self.stdout.write('Crawling \'%s\'...' % source.name)
        try:
            feed = feedparser.parse(source.url)
        except RuntimeError:
            self.stdout.write(self.style.ERROR('Could not crawl \'%s\'' % source.name))

        for entry in feed['entries']:
            description = entry['summary'] if 'summary' in entry else entry['title']

            if NewsItem.exists(entry['title'], entry['updated'], source):
                continue

            score = 1 if classifier.classify(entry['title']) == 'pos' else 0

            news_item = NewsItem()
            news_item.title = entry['title']
            news_item.description = description
            news_item.url = entry['link']
            news_item.source = source
            news_item.score = score
            news_item.added_at = entry['updated']
            news_item.save()

            source.crawled()

        self.stdout.write(self.style.SUCCESS('Successfully crawled \'%s\'' % source.name))
