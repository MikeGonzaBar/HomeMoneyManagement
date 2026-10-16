# Alpine minor is not patch-pinned. python:3.12.13-alpine3.23 is a frozen tag:
# it resolved to Alpine 3.23.5 and could never pick up the 3.23.6 fixes for
# libssl3/libcrypto3 (CVE-2026-14456) and libuuid (CVE-2026-53612 et al).
# python:3.12-alpine3.23 tracks the current 3.23 patch instead. The Python 3.12
# minor itself is still pinned.
FROM python:3.12-alpine3.23 AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt /tmp/requirements.txt
RUN python -m venv "${VIRTUAL_ENV}" \
  && pip install --no-cache-dir --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r /tmp/requirements.txt

FROM python:3.12-alpine3.23

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache bash postgresql-libs

COPY --from=builder /opt/venv /opt/venv
COPY . /HomeMoneyManagement

WORKDIR /HomeMoneyManagement
