#!/bin/sh

make init
./build/wait-for-rabbitmq.sh
./manage.py test core.tests rss.tests
