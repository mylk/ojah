from django.contrib import admin
from .models.source import Source
from .models.newsitem import NewsItem
from .models.corpus import Corpus


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'score', 'published')
    list_filter = ['score']
    search_fields = ['title']
    ordering = ['-added_at']


admin.site.register(Source)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(Corpus)
