#!/bin/sh
# KH: container entrypoint. Schedules backup.sh with cron (KH_BACKUP_CRON) and keeps
# cron in the foreground so `docker logs` shows every backup result.
set -eu

echo "${KH_BACKUP_CRON:-30 3 * * *} /usr/local/bin/backup.sh > /proc/1/fd/1 2> /proc/1/fd/2" > /etc/crontabs/root
echo "Backup geplant: ${KH_BACKUP_CRON:-30 3 * * *} (Zeitzone ${TZ:-UTC})"
exec crond -f -l 8
