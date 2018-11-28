#!/bin/bash

./build/worker_classify/wait-for-rabbitmq.sh
./manage.py classify
