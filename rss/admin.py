from django.contrib import admin
from .models.source import Source
from .models.newsitem import NewsItem

admin.site.register(Source)
admin.site.register(NewsItem)
