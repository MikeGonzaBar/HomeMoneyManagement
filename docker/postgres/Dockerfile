FROM golang:1.26.3-alpine3.23 AS gosu-builder

ARG GOSU_VERSION=1.19

RUN apk add --no-cache git
RUN git clone --depth 1 --branch "${GOSU_VERSION}" https://github.com/tianon/gosu.git /src/gosu
WORKDIR /src/gosu
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /usr/local/bin/gosu .

FROM postgres:15.18-alpine3.23

COPY --from=gosu-builder /usr/local/bin/gosu /usr/local/bin/gosu
RUN chmod +x /usr/local/bin/gosu
