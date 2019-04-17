from django.contrib import admin
from core.models.source import Source
from core.models.newsitem import NewsItem
from core.models.newsitem_metric import NewsItemMetric
from core.models.corpus import Corpus
from core.models.corpus_metric import CorpusMetric
from web.management.admin.source import SourceAdmin
from web.management.admin.newsitem import NewsItemAdmin
from web.management.admin.newsitem_metric import NewsItemMetricAdmin
from web.management.admin.corpus import CorpusAdmin
from web.management.admin.corpus_metric import CorpusMetricAdmin

admin.site.register(Source, SourceAdmin)
admin.site.register(NewsItem, NewsItemAdmin)
admin.site.register(NewsItemMetric, NewsItemMetricAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(CorpusMetric, CorpusMetricAdmin)
