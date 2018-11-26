FROM python:3

ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

ADD . /ojah
WORKDIR /ojah

RUN groupadd -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    useradd -m -u ${HOST_USER_ID} -g ${HOST_GROUP_ID} -s /bin/bash ${HOST_USER_NAME} && \
    make deps_worker_classify && \
    make init

USER ${HOST_USER_NAME}

CMD ["/ojah/build/worker_classify/start.sh"]
