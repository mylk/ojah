FROM python:3-alpine

ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

ADD . /ojah
WORKDIR /ojah

RUN apk add make curl gcc libc-dev linux-headers && \
    addgroup -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    adduser -u ${HOST_USER_ID} -G ${HOST_USER_NAME} -s /bin/sh -D ${HOST_USER_NAME} && \
    make deps_dev && \
    make deps_app && \
    make deps_worker_classify

USER ${HOST_USER_NAME}

RUN make deps_corpora

CMD ["/ojah/build/test/start.sh"]
