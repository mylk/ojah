import pika

from django.conf import settings
from django.core import serializers
from django.contrib import admin


def corpus_activate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = True

        publish = True if corpus.positive else False
        corpus.news_item.published = publish
        corpus.news_item.save()

        corpus.save()

        enqueue_train(corpus)

corpus_activate.short_description = 'Activate'


def corpus_deactivate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = False
        corpus.save()

        enqueue_train(corpus)

corpus_deactivate.short_description = 'Deactivate'


def corpus_convert_to_positive(model_admin, request, query_set):
    for corpus in query_set:
        corpus.positive = True
        corpus.save()

        if corpus.news_item.published:
            enqueue_train(corpus)

corpus_convert_to_positive.short_description = 'Convert to positive'


def corpus_convert_to_negative(model_admin, request, query_set):
    for corpus in query_set:
        corpus.positive = False
        corpus.save()

        if corpus.news_item.published:
            enqueue_train(corpus)

corpus_convert_to_negative.short_description = 'Convert to negative'


def enqueue_train(corpus):
    body = serializers.serialize('json', [corpus])

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
    channel = connection.channel()
    channel.queue_declare(queue=settings.QUEUE_NAME_TRAIN, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=settings.QUEUE_NAME_TRAIN,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2)
    )


class CorpusAdmin(admin.ModelAdmin):
    @staticmethod
    def get_news_item_title(obj):
        return obj.news_item.title

    readonly_fields = ('news_item_link',)
    fields = ('news_item_link', 'positive', 'active', 'added_at')
    list_display = ['get_news_item_title', 'positive', 'active', 'added_at']
    list_filter = ['positive', 'active']
    ordering = ['-added_at']
    actions = [
        corpus_activate,
        corpus_deactivate,
        corpus_convert_to_positive,
        corpus_convert_to_negative
    ]
