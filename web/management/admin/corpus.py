from django.contrib import admin


def corpus_activate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = True
        corpus.save()


corpus_activate.short_description = 'Activate'


def corpus_deactivate(model_admin, request, query_set):
    for corpus in query_set:
        corpus.active = False
        corpus.save()


corpus_deactivate.short_description = 'Deactivate'


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
