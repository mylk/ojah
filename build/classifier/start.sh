#!/bin/sh

./build/wait-for-rabbitmq.sh
./build/wait-for-mariadb.sh
./manage.py classify
