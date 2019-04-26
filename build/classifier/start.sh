#!/bin/sh

./build/wait-for-rabbitmq.sh
./manage.py classify
