#!/usr/bin/env bash
# Install this file as daily-run.sh in the EC2 project directory.
set -euo pipefail

cd "${LAKEHOUSE_PROJECT_DIR:-/home/ec2-user/de-lakehouse-pipeline}"

exec 9>.daily-run.lock
# Exit 75 means busy; the shutdown wrapper must leave the active job alone.
flock -n 9 || exit 75

set -a
source .env
set +a

mkdir -p logs
exec > >(tee -a "logs/daily-$(date -u +%F).log") 2>&1

docker compose up -d --wait db

# Reporting is best effort. Wake a sleeping Render service before the first run.
if [[ -n "${PIPEGUARD_API_URL:-}" && -n "${PIPEGUARD_API_KEY:-}" ]]; then
  if ! curl -fsSL --max-time 120 -o /dev/null "${PIPEGUARD_API_URL%/}/"; then
    echo "WARNING: PipeGuard warm-up failed; continuing ingestion."
  fi
fi

failed=0
for symbol in NVDA WMT XOM META GOOGL MSFT JPM JNJ AMZN SPCX; do
  echo "===== Daily run: $symbol ====="
  if make orchestrate SYMBOL="$symbol"; then
    echo "SUCCESS: $symbol"
  else
    echo "FAILED: $symbol"
    failed=1
  fi
  sleep 15
done

exit "$failed"
