#!/bin/sh
set -e

until curl -sL "http://rabbitmq:15672" -o /dev/null
do
    echo "Waiting for RabbitMQ..."
    sleep 1
done

echo "RabbitMQ is ready!"
