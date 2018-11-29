#!/bin/sh

sudo crond start &
./manage.py runserver 0.0.0.0:8000
