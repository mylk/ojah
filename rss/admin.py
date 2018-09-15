from django.contrib import admin
from .models.source import Source
from .models.newsitem import NewsItem
from .models.corpus import Corpus


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


class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_crawl')
    ordering = ['-last_crawl']


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'score', 'published', 'added_at')
    list_filter = ['score', 'published', 'source']
    search_fields = ['title']
    ordering = ['-added_at']
    actions = [news_item_publish, news_item_unpublish]


admin.site.register(Source, SourceAdmin)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(Corpus)
