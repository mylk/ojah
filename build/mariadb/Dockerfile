FROM mariadb:latest

ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

RUN groupadd -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    useradd -m -u ${HOST_USER_ID} -g ${HOST_GROUP_ID} -G sudo -s /bin/bash ${HOST_USER_NAME} && \
    echo "${HOST_USER_NAME} ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers

# config
COPY build/mariadb/my.cnf /etc/mysql/my.cnf

USER ${HOST_USER_NAME}

CMD ["mysqld"]
