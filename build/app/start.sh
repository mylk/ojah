#!/bin/sh

./build/wait-for-rabbitmq.sh
./build/wait-for-mariadb.sh

# fail2ban
sudo rm -f /var/run/fail2ban/* && \
sudo fail2ban-server

# cron
# share the env variables with root (runs the cron job)
export | sudo tee -a /etc/profile
sudo crond start

# ojah
make init
./manage.py runserver 0.0.0.0:8000
