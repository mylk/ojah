from django.apps import AppConfig


class RssConfig(AppConfig):
    name = 'rss'

    def ready(self):
        import rss.receivers.admin.login
