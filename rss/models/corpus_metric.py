from .corpus import Corpus


class CorpusMetric(Corpus):

    class Meta:
        proxy = True
        verbose_name = 'corpus metric'
        verbose_name_plural = 'corpus metrics'
