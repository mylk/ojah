from django.urls import path
from web.views import rssfeed

app_name = 'web'
urlpatterns = [
    path('', rssfeed.RssFeed(), name='feed')
]
