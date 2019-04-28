#!/bin/sh
set -e

until mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} -hmariadb -e "show databases;" &> /dev/null
do
    echo "Waiting for MariaDB..."
    sleep 1
done

echo "MariaDB is ready!"

