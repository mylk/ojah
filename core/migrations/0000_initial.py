# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import User


def create_superuser(apps, schema_editor):
    User.objects.create_superuser(username='ojah', password='ojah', email='milonas.ko@gmail.com')


class Migration(migrations.Migration):
    operations = [migrations.RunPython(create_superuser)]
