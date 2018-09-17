FROM python:3

ADD . /ojah
WORKDIR /ojah

RUN make deps && \
    make init

CMD ["/ojah/build/worker_classify/start.sh"]
