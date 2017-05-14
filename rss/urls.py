from django.conf.urls import url
from .views import rssfeed

urlpatterns = [
    url(r'', rssfeed.RssFeed(), name='feed')
]
