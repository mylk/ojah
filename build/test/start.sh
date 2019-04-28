#!/bin/sh

make init
./build/wait-for-rabbitmq.sh
./build/wait-for-mariadb.sh
./manage.py test cli.tests core.tests web.tests
