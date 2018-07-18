from django.core.management.base import BaseCommand
from rss.models.source import Source
from rss.models.newsitem import NewsItem
import feedparser
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from textblob.classifiers import NaiveBayesClassifier
from nltk.corpus import twitter_samples
from random import shuffle
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv
import os


class Command(BaseCommand):
    help = 'Crawl RSS feeds and perform sentiment analysis on news items'
    classifier = None

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', type=str)

    def handle(self, *args, **options):
        self.classifier = self.get_trained_classifier()
        name = options['name']

        if name:
            sources = Source.objects.filter(name=name)
            if not sources:
                self.stdout.write(self.style.ERROR('Could not find source \'%s\'' % name))
        else:
            sources = Source.objects.all()

        for source in sources:
            self.crawl(source)

    @staticmethod
    def get_trained_classifier():
        tweets_pos = twitter_samples.strings('positive_tweets.json')[:200]
        tweets_neg = twitter_samples.strings('negative_tweets.json')[:200]
        tweets_classified = list()
        for tweet in tweets_pos:
            tweets_classified.append((tweet, 'pos'))
        for tweet in tweets_neg:
            tweets_classified.append((tweet, 'neg'))
        shuffle(tweets_classified)

        # should clean tweets first?
        # should get only adjectives and verbs by tokenizing and then run part of speech tagging (pos_tag_sents)?
        classifier = NaiveBayesClassifier(tweets_classified)

        return classifier

    def crawl(self, source):
        self.stdout.write('Crawling \'%s\'...' % source.name)

        try:
            feed = feedparser.parse(source.url)
        except RuntimeError:
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

            source.crawled()

            self.log_comparison(entry['title'], score)

        self.stdout.write(self.style.SUCCESS('Successfully crawled \'%s\'' % source.name))

    def log_comparison(self, title, score):
        # naive bayes classifier
        classifier = self.classifier
        vader = SentimentIntensityAnalyzer()
        nb_analyzer_sentiment = TextBlob(title, analyzer=NaiveBayesAnalyzer()).sentiment

        # vader scores
        # positive: compound score >= 0.05
        # neutral: (compound score > -0.05) and (compound score < 0.05)
        # negative: compound score <= -0.05
        vader_scores = vader.polarity_scores(title)

        comparison_file = '/tmp/sentiment_analysis_comparison.csv'
        file_exists = os.path.isfile(comparison_file)
        csvfile = open(comparison_file, 'a', newline='')
        field_names = ['title', 'tb score', 'nb pos', 'nb neg', 'nb class', 'vdr comp', 'vdr pos', 'vdr neu', 'vdr neg']
        writer = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'title': title.replace(';', ' '),
            'tb score': score,
            'nb pos': nb_analyzer_sentiment.p_pos,
            'nb neg': nb_analyzer_sentiment.p_neg,
            'nb class': classifier.classify(title),
            'vdr comp': vader_scores['compound'],
            'vdr pos': vader_scores['pos'],
            'vdr neu': vader_scores['neu'],
            'vdr neg': vader_scores['neg'],
        })
