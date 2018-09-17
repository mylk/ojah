from django.core.management.base import BaseCommand
from rss.models.source import Source
from rss.models.newsitem import NewsItem
from rss.models.corpus import Corpus
import feedparser
from textblob.classifiers import NaiveBayesClassifier
from random import shuffle
import sys


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

        corpora_classified = list()

        # train with custom corpora
        corpora = Corpus.objects.all()
        for corpus in corpora:
            corpora_classified.insert(0, (corpus.news_item.title, corpus.get_classification()))

        self.classifier = NaiveBayesClassifier(corpora_classified)
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
            sys.exit(1)

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
