from django.contrib import admin
from rss.models.source import Source
from rss.models.newsitem import NewsItem
from rss.models.newsitem_metric import NewsItemMetric
from rss.models.corpus import Corpus
from rss.models.corpus_metric import CorpusMetric
from rss.management.admin.source import SourceAdmin
from rss.management.admin.newsitem import NewsItemAdmin
from rss.management.admin.newsitem_metric import NewsItemMetricAdmin
from rss.management.admin.corpus import CorpusAdmin
from rss.management.admin.corpus_metric import CorpusMetricAdmin

admin.site.register(Source, SourceAdmin)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(NewsItemMetric, NewsItemMetricAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(CorpusMetric, CorpusMetricAdmin)
