#!/bin/sh

./build/wait-for-rabbitmq.sh

# cron
sudo crond start
tail -f /dev/null
