FROM python:3.10-alpine3.18
RUN apk update && \
  apk upgrade && \
  apk add bash

COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

COPY . /HomeMoneyManagement