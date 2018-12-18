#!/bin/sh

# cron
sudo crond start

# fail2ban
sudo rm -f /var/run/fail2ban/* && \
sudo fail2ban-server

# ojah
./manage.py runserver 0.0.0.0:8000
