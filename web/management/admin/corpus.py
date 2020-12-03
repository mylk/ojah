import pika

from django.conf import settings
from django.contrib import admin


def corpus_activate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = True
        corpus.save()

    if query_set:
        enqueue_corpus_activation()

corpus_activate.short_description = 'Activate'


def corpus_deactivate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = False
        corpus.save()

    if query_set:
        enqueue_corpus_activation()

corpus_deactivate.short_description = 'Deactivate'


def enqueue_corpus_activation():
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
    ]
