FROM python:3-alpine

ARG DEBUG
ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

ADD . /ojah
WORKDIR /ojah

RUN apk add make curl gcc libc-dev linux-headers mariadb-dev mariadb-client && \
    addgroup -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    adduser -u ${HOST_USER_ID} -G ${HOST_USER_NAME} -s /bin/sh -D ${HOST_USER_NAME} && \
    make deps_classifier && \
    if [ "${DEBUG}" = "1" ]; then \
        make deps_dev; \
    fi

USER ${HOST_USER_NAME}

RUN make deps_corpora

CMD ["/ojah/build/classifier/start.sh"]
