from django.contrib import admin
from .models.source import Source
from .models.newsitem import NewsItem
from .models.corpus import Corpus


class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_crawl')
    ordering = ['-last_crawl']


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'score', 'published', 'added_at')
    list_filter = ['score', 'published', 'source']
    search_fields = ['title']
    ordering = ['-added_at']


admin.site.register(Source, SourceAdmin)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(Corpus)
