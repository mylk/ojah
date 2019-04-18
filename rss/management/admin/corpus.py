from django.contrib import admin


class CorpusAdmin(admin.ModelAdmin):

    @staticmethod
    def get_news_item_title(obj):
        return obj.news_item.title

    list_display = ['get_news_item_title', 'positive', 'added_at']
    list_filter = ['positive']
    ordering = ['-added_at']
