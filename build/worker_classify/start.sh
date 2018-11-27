#!/bin/sh

/ojah/build/worker_classify/wait-for-rabbitmq.sh
/ojah/manage.py classify
