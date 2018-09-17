FROM python:3

ADD . /ojah
WORKDIR /ojah

COPY build/app/crontab /var/spool/cron/crontabs/root

RUN apt-get update && \
    apt-get -y install cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    make deps && \
    make init

CMD ["/ojah/build/app/start.sh"]
