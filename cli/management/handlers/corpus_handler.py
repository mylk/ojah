from core.models.corpus import Corpus


class CorpusHandler:

    def run(self, queue_item, classification):
        if classification == 'pos':
            corpus = Corpus()
            corpus.news_item = queue_item
            corpus.positive = True
            corpus.active = False
            corpus.save()
