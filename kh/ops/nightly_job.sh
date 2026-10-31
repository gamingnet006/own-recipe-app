#!/bin/sh
# KH: nightly host jobs of the ops scripts (auto_update.sh, backup_copy.sh): schedules
# "<script> run --scheduled" with launchd on macOS and cron elsewhere, and logs and reports results.
# The loading script also loads update.sh (setting) and backup/backup.sh (push), then sets JOB_SCRIPT,
# JOB_LABEL, JOB_MARK, JOB_HOUR, JOB_MINUTE, JOB_PUSH_SETTING and LOG.

JOB_SHELL=/bin/sh  # program launchd starts the script with
SCHEDULED=0  # 1 for the nightly run, whose whole output already goes to the log

# Prints the crontab line for the nightly run.
cron_line() {  # ops_dir (absolute)
  echo "$JOB_MINUTE $JOB_HOUR * * * '$1/$JOB_SCRIPT' run --scheduled >> '$1/$LOG' 2>&1 $JOB_MARK"
}

# Prints a crontab without our line, then LINE: other jobs stay, ours exists exactly once.
crontab_with() {  # current line
  crontab_without "$1"
  echo "$2"
}

# Prints a crontab without our line.
crontab_without() {  # current
  [ -z "$1" ] || printf '%s\n' "$1" | grep -vF "$JOB_MARK" || true
}

# macOS lets crontab write only with Full Disk Access, which SSH sessions lack: Macs schedule the
# nightly run with a launchd agent instead.
on_mac() {
  [ "$(uname -s)" = Darwin ]
}

# Path of the launchd agent in the user's LaunchAgents folder; launchd also loads it at login.
agent_file() {
  echo "$HOME/Library/LaunchAgents/$JOB_LABEL.plist"
}

# Prints the launchd agent for the nightly run, the same job as cron_line; & < > in the path are
# escaped for XML.
agent_plist() {  # ops_dir (absolute)
  agent_ops=$(printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')
  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$JOB_LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$JOB_SHELL</string><string>$agent_ops/$JOB_SCRIPT</string><string>run</string><string>--scheduled</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$JOB_HOUR</integer><key>Minute</key><integer>$JOB_MINUTE</integer></dict>
  <key>StandardOutPath</key><string>$agent_ops/$LOG</string>
  <key>StandardErrorPath</key><string>$agent_ops/$LOG</string>
</dict>
</plist>
EOF
}

# Enters the nightly job: on macOS the launchd agent, loaded now and at every login; elsewhere
# our crontab line.
schedule_job() {  # ops_dir (absolute)
  if on_mac; then
    mkdir -p "$(dirname "$(agent_file)")" && agent_plist "$1" > "$(agent_file)" || return 1
    # bootout first: launchctl refuses to bootstrap an agent that is still loaded
    launchctl bootout "gui/$(id -u)/$JOB_LABEL" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$(agent_file)"
    return
  fi
  # Read before the pipe: a crontab that empties itself on writing would lose the other jobs.
  current=$(crontab -l 2>/dev/null || true)
  crontab_with "$current" "$(cron_line "$1")" | crontab -
}

# Removes the nightly job; other cron jobs stay.
unschedule_job() {
  if on_mac; then
    launchctl bootout "gui/$(id -u)/$JOB_LABEL" 2>/dev/null || true
    rm -f "$(agent_file)"
    return
  fi
  current=$(crontab -l 2>/dev/null || true)
  crontab_without "$current" | crontab -
}

# True while the nightly job is entered.
job_scheduled() {
  if on_mac; then
    launchctl print "gui/$(id -u)/$JOB_LABEL" >/dev/null 2>&1
  else
    crontab -l 2>/dev/null | grep -qF "$JOB_MARK"
  fi
}

# Prints a timestamped line; a manual run also appends it to the log.
note() {  # message
  line="$(date '+%Y-%m-%d %H:%M') $1"
  echo "$line"
  [ "$SCHEDULED" = 1 ] || echo "$line" >> "$LOG"
}

# Notes the result and sends it to Uptime Kuma when the setting JOB_PUSH_SETTING holds a push URL
# (backup.sh's push). A URL written for the backup container names host.docker.internal; seen from
# this machine that is localhost.
report() {  # up|down message
  note "$2"
  (KH_BACKUP_PUSH_URL=$(setting "$JOB_PUSH_SETTING" "" | sed 's/host\.docker\.internal/localhost/'); push "$1" "$2")
}
