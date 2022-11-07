FROM ubuntu:latest

WORKDIR /usr/code/spotify
ENV DEBIAN_FRONTEND noninteractive

ENV PYTHONIOENCODING="UTF-8"
ENV LANG C.UTF-8

COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y python3 python3-pip postgresql postgresql-contrib git libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install -r requirements.txt
RUN apt-get -y install locales
COPY . .