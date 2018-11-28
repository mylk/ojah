#!/bin/bash

sudo /etc/init.d/cron start
./manage.py runserver 0.0.0.0:8000
