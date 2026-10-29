# KH: small backup container (D21): cron, curl for Mealie's API, unzip to verify archives.
FROM alpine:3.22

RUN apk add --no-cache curl unzip tzdata

COPY backup.sh restore.sh run.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/restore.sh /usr/local/bin/run.sh

CMD ["/usr/local/bin/run.sh"]
