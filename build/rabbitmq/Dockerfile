FROM rabbitmq:3-management

ARG HOST_USER_NAME
ARG HOST_USER_ID
ARG HOST_GROUP_ID

RUN apt update && \
    apt install -y sudo && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g ${HOST_GROUP_ID} ${HOST_USER_NAME} && \
    useradd -m -u ${HOST_USER_ID} -g ${HOST_GROUP_ID} -G sudo -s /bin/bash ${HOST_USER_NAME} && \
    echo "${HOST_USER_NAME} ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers && \
    touch /var/lib/rabbitmq/.erlang.cookie

# config
COPY build/rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

USER ${HOST_USER_NAME}

CMD ["sudo", "/usr/lib/rabbitmq/bin/rabbitmq-server"]
