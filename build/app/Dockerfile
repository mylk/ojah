FROM python:3
ARG DEBUG

ADD . /ojah
WORKDIR /ojah

COPY build/app/crontab /var/spool/cron/crontabs/root

RUN apt-get update && \
    apt-get -y install cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    make deps && \
    if [ "$DEBUG" = "1" ]; \
        then make deps_dev; \
    fi && \
    make init

CMD ["/ojah/build/app/start.sh"]
