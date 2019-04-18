"""ojah URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import re_path, include
    2. Add a URL to urlpatterns: re_path(r'^blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.views.generic.base import RedirectView
from django.urls import include, path, re_path

from web.views import web

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^rss/', include('web.urls')),
    re_path(r'^web/', web.news),
    re_path(r'^news/', RedirectView.as_view(url='/web/')),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
