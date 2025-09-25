FROM python:3.10-alpine3.19

# Install system dependencies for PostgreSQL
RUN apk update && \
  apk upgrade && \
  apk add bash postgresql-dev gcc musl-dev

COPY requirements.txt /
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /requirements.txt

COPY . /HomeMoneyManagement

# Set working directory
WORKDIR /HomeMoneyManagement