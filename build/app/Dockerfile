FROM python:3-alpine

ARG DEBUG
ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

ADD . /ojah
WORKDIR /ojah

RUN apk add make curl sudo gcc libc-dev linux-headers fail2ban mariadb-dev mariadb-client && \
    addgroup -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    adduser -u ${HOST_USER_ID} -G ${HOST_USER_NAME} -s /bin/sh -D ${HOST_USER_NAME} && \
    addgroup sudo && \
    addgroup mylk sudo && \
    echo "${HOST_USER_NAME} ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers && \
    make deps_app && \
    if [ "${DEBUG}" = "1" ]; then \
        make deps_dev; \
    fi && \
    touch /ojah/logs/admin-auth.log

# fail2ban
COPY build/app/fail2ban/filter.d/ojah.conf /etc/fail2ban/filter.d/ojah.conf
COPY build/app/fail2ban/jail.local /etc/fail2ban/jail.local

# cron
COPY build/app/crontab /var/spool/cron/crontabs/root

USER ${HOST_USER_NAME}

CMD ["/ojah/build/app/start.sh"]
