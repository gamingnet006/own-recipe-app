#!/bin/sh
# KH: on a Mac a double-click opens this in Terminal and changes where the nightly copies of the
# backups go (backup_copy.sh on, PLAN.md D32). A link to it, e.g. on the desktop, works too.

# The folder of this file, also when it was opened through a link
self=$0
if [ -L "$self" ]; then
  target=$(readlink "$self")
  case "$target" in /*) self=$target ;; *) self=$(dirname "$self")/$target ;; esac
fi
"$(dirname "$self")/backup_copy.sh" on
printf "Zum Schließen Enter drücken. "
read -r _ || true
