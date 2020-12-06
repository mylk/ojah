import pika

from django.conf import settings
from django.contrib import admin


def corpus_activate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = True
        corpus.save()

    if query_set:
        enqueue_train()

corpus_activate.short_description = 'Activate'


def corpus_deactivate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = False
        corpus.save()

    if query_set:
        enqueue_train()

corpus_deactivate.short_description = 'Deactivate'


def corpus_convert_to_positive(model_admin, request, query_set):
    any_published = False

    for corpus in query_set:
        corpus.positive = True
        corpus.save()

        if corpus.published:
            any_published = True

    if any_published:
        enqueue_train()

corpus_convert_to_positive.short_description = 'Convert to positive'


def corpus_convert_to_negative(model_admin, request, query_set):
    any_published = False

    for corpus in query_set:
        corpus.positive = False
        corpus.save()

        if corpus.published:
            any_published = True

    if any_published:
        enqueue_train()

corpus_convert_to_negative.short_description = 'Convert to negative'


def enqueue_train():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.QUEUE_HOSTNAME))
    channel = connection.channel()
    channel.queue_declare(queue=settings.QUEUE_NAME_TRAIN, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=settings.QUEUE_NAME_TRAIN,
        body='',
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
