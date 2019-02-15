from django.contrib import admin
from django.conf import settings
from rangefilter.filter import DateRangeFilter
import pika

from rss.models.corpus import Corpus


def news_item_publish(model_admin, request, query_set):
    for news_item in query_set:
        news_item.published = True
        news_item.save()


news_item_publish.short_description = 'Publish'


def news_item_unpublish(model_admin, request, query_set):
    for news_item in query_set:
        news_item.published = False
        news_item.save()


news_item_unpublish.short_description = 'Unpublish'


def corpus_create_positive(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

    if len(query_set):
        enqueue_corpus_creation()


corpus_create_positive.short_description = 'Corpus - Create positive'


def corpus_create_negative(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

    if len(query_set):
        enqueue_corpus_creation()


corpus_create_negative.short_description = 'Corpus - Create negative'


def news_item_publish_and_corpus_create_positive(model_admin, request, query_set):
    corpus_create_positive(model_admin, request, query_set)
    news_item_publish(model_admin, request, query_set)


news_item_publish_and_corpus_create_positive.short_description = 'Publish and create positive Corpus'


def news_item_unpublish_and_corpus_create_negative(model_admin, request, query_set):
    corpus_create_negative(model_admin, request, query_set)
    news_item_unpublish(model_admin, request, query_set)


news_item_unpublish_and_corpus_create_negative.short_description = 'Unpublish and create negative Corpus'


def enqueue_corpus_creation():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
    channel = connection.channel()
    channel.queue_declare(queue=settings.QUEUE_NAME_TRAIN, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=settings.QUEUE_NAME_TRAIN,
        body='',
        properties=pika.BasicProperties(delivery_mode=2)
    )


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'score', 'published', 'added_at')
    list_filter = ('score', 'published', 'source', ('added_at', DateRangeFilter))
    search_fields = ['title']
    ordering = ['-added_at']
    actions = [
        news_item_publish,
        news_item_unpublish,
        corpus_create_positive,
        corpus_create_negative,
        news_item_publish_and_corpus_create_positive,
        news_item_unpublish_and_corpus_create_negative
    ]
