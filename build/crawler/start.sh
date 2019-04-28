#!/bin/sh

./build/wait-for-rabbitmq.sh
./build/wait-for-mariadb.sh

# cron
# share the env variables with root (runs the cron job)
export | sudo tee -a /etc/profile
sudo crond start
tail -f /dev/null
