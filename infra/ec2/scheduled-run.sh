#!/usr/bin/env bash
# This entry point schedules an OS shutdown, including when ingestion fails.
set -uo pipefail

cd "${LAKEHOUSE_PROJECT_DIR:-/home/ec2-user/de-lakehouse-pipeline}" || {
  echo "ERROR: project directory unavailable; scheduling shutdown."
  sudo shutdown -h +1
  exit 1
}

exec 8>.scheduled-run.lock
flock -n 8 || exit 75

run_status=0
timeout --kill-after=30s 600 ./daily-run.sh || run_status=$?

# A concurrent daily run owns the database: do not stop it.
if [[ "$run_status" -eq 75 ]]; then
  echo "Daily run is already active; skipping shutdown."
  exit 75
fi

mkdir -p logs
printf '%s exit_code=%s\n' "$(date -u --iso-8601=seconds)" "$run_status" \
  >> logs/scheduled-status.log

docker compose stop -t 60 db
# Leave time for SSM to return the command's result before the instance stops.
sudo shutdown -h +1
shutdown_status=$?
if [[ "$shutdown_status" -ne 0 ]]; then
  echo "ERROR: could not schedule shutdown; check EC2 and the fallback schedule."
  exit "$shutdown_status"
fi
exit "$run_status"
