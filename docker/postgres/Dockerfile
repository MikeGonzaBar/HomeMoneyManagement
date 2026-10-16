# Build-only stage: gosu is compiled here and copied into the final image, so
# nothing from this base ships. It is on 3.24 to match the runtime base below.
# 1.26.6 is the current 1.26 patch on 3.24; 1.26.3 has no 3.24 variant.
FROM golang:1.26.6-alpine3.24 AS gosu-builder

ARG GOSU_VERSION=1.19

RUN apk add --no-cache git
RUN git clone --depth 1 --branch "${GOSU_VERSION}" https://github.com/tianon/gosu.git /src/gosu
WORKDIR /src/gosu
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /usr/local/bin/gosu .

# alpine3.24, not 3.23: postgres:15 on 3.23 scans to 11 OS HIGH/CRIT; on 3.24
# it is 0.
#
# The Alpine minor is deliberately NOT patch-pinned here (postgres:15-alpine3.24,
# not 15.18-alpine3.24). Pinning the PG patch also pins the Alpine layer:
# 15.18-alpine3.24 froze at Alpine 3.24.1 and still carried libssl3/libuuid
# HIGH CVEs, while the floating tag tracks 3.24.2 where they are fixed.
FROM postgres:15-alpine3.24

COPY --from=gosu-builder /usr/local/bin/gosu /usr/local/bin/gosu
RUN chmod +x /usr/local/bin/gosu
