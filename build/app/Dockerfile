FROM python:3

ARG DEBUG
ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

ADD . /ojah
WORKDIR /ojah

COPY build/app/crontab /var/spool/cron/crontabs/root

RUN apt-get update && \
    apt-get -y install cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    useradd -m -u ${HOST_USER_ID} -g ${HOST_GROUP_ID} -s /bin/bash ${HOST_USER_NAME} && \
    make deps && \
    if [ "${DEBUG}" = "1" ]; \
        then make deps_dev; \
    fi && \
    make init

USER ${HOST_USER_NAME}

CMD ["/ojah/build/app/start.sh"]
