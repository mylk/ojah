#!/bin/sh

./build/wait-for-rabbitmq.sh

# fail2ban
sudo rm -f /var/run/fail2ban/* && \
sudo fail2ban-server

# ojah
make init
./manage.py runserver 0.0.0.0:8000
