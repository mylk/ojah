from django.urls import path
from .views import rssfeed

app_name = 'rss'
urlpatterns = [
    path('', rssfeed.RssFeed(), name='feed')
]
