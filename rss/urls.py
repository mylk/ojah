from django.urls import path
from rss.views import rssfeed

app_name = 'rss'
urlpatterns = [
    path('', rssfeed.RssFeed(), name='feed')
]
