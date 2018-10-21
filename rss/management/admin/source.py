from django.contrib import admin


class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_crawl')
    ordering = ['-last_crawl']
