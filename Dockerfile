
FROM alpine:latest

RUN apk add --no-cache g++ libstdc++

RUN adduser -D player
USER player

WORKDIR /home/player