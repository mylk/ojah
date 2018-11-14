from django.contrib import admin
from django.conf import settings
from rss.models.corpus import Corpus
from rangefilter.filter import DateRangeFilter
import pika


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


def news_item_corpus_create_positive(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = True
        corpus.save()

    enqueue_corpus_creation()


news_item_corpus_create_positive.short_description = 'Corpus - Create positive'


def news_item_corpus_create_negative(model_admin, request, query_set):
    for news_item in query_set:
        corpus = Corpus()
        corpus.news_item = news_item
        corpus.positive = False
        corpus.save()

    enqueue_corpus_creation()


news_item_corpus_create_negative.short_description = 'Corpus - Create negative'


def news_item_publish_and_corpus_create_positive(model_admin, request, query_set):
    news_item_corpus_create_positive(model_admin, request, query_set)
    news_item_publish(model_admin, request, query_set)


news_item_publish_and_corpus_create_positive.short_description = 'Publish and create positive Corpus'


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
        news_item_corpus_create_positive,
        news_item_corpus_create_negative,
        news_item_publish_and_corpus_create_positive
    ]