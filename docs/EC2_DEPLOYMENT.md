# Scheduled EC2 deployment

Run the market pipeline on an Amazon Linux 2023 x86_64 EC2 instance in
`us-west-2`. PostgreSQL 16 runs in Docker on EBS; PipeGuard remains a separate
service on Render. This is a small, intermittently running project deployment,
not a highly available database service. There is no automatic local/cloud DB
synchronization.

## What has been verified

User-operated validation on October 10, 2026 (America/Los_Angeles):

- The migrated database contained 98,292 rows across 13 symbols before backfill.
- Alpha Vantage backfill brought the ten configured symbols to the October 9
  trading date: AMZN 115 rows, GOOGL 180, JNJ 115, JPM 115, META 115,
  MSFT 191, NVDA 115, SPCX 83, WMT 115, XOM 115 (Alpha Vantage rows only).
- A manually submitted SSM command successfully ran the original shutdown
  wrapper, and the instance subsequently reached `Stopped`.
- Three Scheduler schedules were created and reported enabled by the operator.

These scripts reconstruct the manually installed configuration, adding a
PipeGuard warm-up and busy-run handling. These additions are locally tested,
but are **not yet installed or verified on EC2**. The first scheduled execution
of the ten-symbol job and delivery of all ten PipeGuard reports remain
unverified. A successful SSM command alone does not prove every report arrived.

## Instance and credentials

- Instance: `t3.small`, Amazon Linux 2023 x86_64, 10 GiB gp3 root volume.
- Attach an EC2-trusted IAM role with `AmazonSSMManagedInstanceCore`.
- Use Session Manager for administrative access. SSM Agent must be running,
  with outbound connectivity to the regional SSM endpoints. No inbound SSH
  rule is required for Session Manager. If using SSH, restrict port 22 to the
  operator's IP. Do not expose PostgreSQL port 5432 publicly.
- Set **instance-initiated shutdown behavior to Stop**, not Terminate. The
  wrapper invokes OS shutdown; this setting determines the resulting EC2 state.
- Use termination protection to reduce accidental deletion. Stop protection
  must be disabled so the fallback stop schedule can work.
- Do not copy local IAM access keys onto EC2. The EC2 role and Scheduler
  execution roles serve different purposes.

Install the base packages and enable Docker:

```bash
sudo dnf install -y git make docker python3.11 python3.11-pip
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
```

Log in again to apply Docker group membership. Install the official Docker
Compose plugin for Linux x86_64; this deployment requires Compose 2.24.4+ for
the port override. Verify `docker compose version` and `docker ps` as ec2-user.

Clone the repository into `/home/ec2-user/de-lakehouse-pipeline`. From a Session
Manager shell, run `sudo -iu ec2-user`, then change to that directory:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pip install -e .
cp -n .env.example .env
chmod 600 .env
nano .env
```

Set `ALPHA_VANTAGE_API_KEY`, and optionally both `PIPEGUARD_API_URL` and
`PIPEGUARD_API_KEY`. Set `PIPEGUARD_TIMEOUT_SECONDS=60` for a sleeping service.
Keep credentials out of screenshots, Git, Scheduler inputs and logs. This
deployment uses the existing local Compose database credentials; change the
actual database password and matching application configuration together if
hardening the deployment. Changing an environment variable does not reset a
password in an existing PostgreSQL volume.

Also add this Linux-only Compose configuration to `.env`:

```bash
COMPOSE_FILE=docker-compose.yml:infra/ec2/compose.ec2.yml
```

Load `.env` with `set -a; source .env; set +a`, then run
`docker compose config` and confirm the only published DB address is
`127.0.0.1:5432`. The `!override` tag replaces the base port list instead of
adding a second binding. Use the same Compose files and project directory for
all database commands to preserve the existing named volume.

## Database migration and backfill

Create a custom-format `pg_dump` of the source database and transfer it over
SSH/SCP. Restore into an empty target database with `pg_restore --no-owner
--no-privileges --exit-on-error --single-transaction`. Verify row counts,
symbols and latest dates before using the target as the primary database.
Do not commit the dump; do not use `docker compose down -v` on this database.

For a fresh database instead of migration, run the project migrations using
`make db-migrate`. Do not seed demo data into an imported production dataset.

Run manual backfill as ec2-user in the project directory with `.env` loaded:

```bash
docker compose up -d --wait db
make backfill START=YYYY-MM-DD END=YYYY-MM-DD SYMBOL=NVDA
make run-marts
```

Alpha Vantage backfill accepts one symbol per invocation, skips dates completed
in PostgreSQL, and fetches one shared daily payload per symbol. It only fills
dates present in the returned payload. The default endpoint supplies the most
recent 100 trading days; it cannot guarantee arbitrary historical coverage.
Weekend/holiday dates without bars are not marked complete. `make backfill`
does not report to PipeGuard; `make orchestrate` does. Respect the key's daily
request allowance, including retries and other uses of the same key.

## Install and operate the scripts

Disable the run/start schedules during installation. Preserve any manually
installed scripts before replacing them:

```bash
cp -p daily-run.sh daily-run.sh.previous
cp -p scheduled-run.sh scheduled-run.sh.previous
install -m 700 infra/ec2/daily-run.sh daily-run.sh
install -m 700 infra/ec2/scheduled-run.sh scheduled-run.sh
bash -n daily-run.sh
bash -n scheduled-run.sh
```

On a fresh installation, omit the two backup commands if the files do not yet
exist. Both entry points default to the project path above;
`LAKEHOUSE_PROJECT_DIR` can override it for testing. Run as ec2-user, whose
sudo policy must permit the shutdown command without an interactive password.

`daily-run.sh` holds an advisory lock, starts the database, attempts one
120-second PipeGuard warm-up, then runs these symbols sequentially:

`NVDA WMT XOM META GOOGL MSFT JPM JNJ AMZN SPCX`

AAPL is intentionally absent from this ten-symbol list. Each `make orchestrate`
ingests and loads data, checks quality, builds marts on success and attempts a
PipeGuard report. Marts rebuild per symbol, not just once after the loop. A
failed symbol does not prevent the remaining symbols from running; the overall
exit code records whether any failed. Reporting remains best effort and can
fail without failing ingestion. All symbols currently share the same PipeGuard
pipeline name, so its historical comparison is not a separate baseline per
symbol.

`scheduled-run.sh` limits the daily job to 600 seconds, with a 30-second kill
grace, stops the DB with a 60-second grace and schedules shutdown one minute
later. It also stops after job failure or timeout. Exit 75 means another run is
busy: it leaves that run and its database alone. Locks only protect these
entry points; a direct manual `make orchestrate` does not take their locks.

Logs are in `logs/daily-YYYY-MM-DD.log` and `logs/scheduled-status.log`.
Monitor `df -h /`; no automatic retention or S3/database backup is installed by
this change. EBS persists across Stop/Start but is not itself a separate backup.

## EventBridge Scheduler

Create all schedules in **Oregon / us-west-2**, group `default`, timezone
`America/New_York`, recurring cron, flexible window **Off**, retry **Off**,
DLQ **None**, completion action **NONE**. Leave start/end dates blank.
Initially keep schedules **Disabled**.

| Schedule | Cron | Universal target ARN | Input template |
| --- | --- | --- | --- |
| de-lakehouse-start | `cron(0 20 * * ? *)` | `arn:aws:scheduler:::aws-sdk:ec2:startInstances` | `infra/ec2/scheduler-start-input.json` |
| de-lakehouse-run | `cron(5 20 * * ? *)` | `arn:aws:scheduler:::aws-sdk:ssm:sendCommand` | `infra/ec2/scheduler-run-input.json` |
| de-lakehouse-stop | `cron(20 20 * * ? *)` | `arn:aws:scheduler:::aws-sdk:ec2:stopInstances` | `infra/ec2/scheduler-stop-input.json` |

Replace `<ACCOUNT_ID>` and `<INSTANCE_ID>` before using any JSON templates.
Create Scheduler-trusted execution roles with `scheduler-trust-policy.json`.
Use `scheduler-power-policy.json` for the start/stop role and
`scheduler-run-policy.json` for the run role. Permissions are limited to the
selected instance and AWS-RunShellScript document; the run role still permits
arbitrary shell commands on that instance, not just this script. Do not choose
the EC2 instance's SSM role as the Scheduler execution role.

The run input gives a command 300 seconds to start and a 720-second execution
timeout. Start/stop and SendCommand success are delivery results, not proof of
a healthy pipeline. Scheduler is not an exactly-once job orchestrator. The
fallback stop is independent of SSM and may interrupt a manually started job
or demo at 20:20 New York time. Pause the schedules during maintenance.

## Validation and recovery

1. Start EC2, wait for SSM online, and submit AWS-RunShellScript manually with
   `sudo -iu ec2-user /home/ec2-user/de-lakehouse-pipeline/scheduled-run.sh`
   and execution timeout 720. This actually runs the job and stops the server.
2. Check SSM command output, quality results, PipeGuard delivery, and EC2
   `Stopped`. Do not resubmit a still-running command.
3. Enable fallback stop first, then run, then start. At the first daily cycle,
   check Run Command history, logs, individual symbol latest dates and
   PipeGuard records. Confirm the instance is stopped afterward.
4. If reporting fails, check the redacted logs and URL/key configuration;
   Render Free services can take about a minute to wake. A 60-second report
   timeout and warm-up improve delivery but do not guarantee it.
5. If SSM did not accept the command, check the instance role, agent,
   connectivity, Scheduler execution policy and schedule region. Verify the
   20:20 fallback stopped the instance, or stop it manually.

There is no automatic alert if a daily run never arrives in PipeGuard. A missing
run requires checking Scheduler/SSM history; do not equate absence with success.
For rollback, disable schedules, restore the previous scripts, check Bash
syntax, and revalidate before enabling. Leave EC2 stopped while unused. Storage
continues to incur costs; budgets are alerts, not a spending cap.

## References

- [AWS Scheduler universal targets](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html)
- [AWS Scheduler timezone and cron behavior](https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html)
- [SSM SendCommand parameters](https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_SendCommand.html)
- [Docker Compose merge and override behavior](https://docs.docker.com/reference/compose-file/merge/)
- [Alpha Vantage API documentation](https://www.alphavantage.co/documentation/)
- [Render Free service limitations](https://render.com/docs/free)
