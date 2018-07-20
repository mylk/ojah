from django.contrib import admin
from .models.source import Source
from .models.newsitem import NewsItem
from .models.corpus import Corpus

admin.site.register(Source)
admin.site.register(NewsItem)
admin.site.register(Corpus)
