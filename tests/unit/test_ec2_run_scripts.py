"""Exercise shutdown/failure behavior with stubbed commands, never a live EC2."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "infra" / "ec2"
SYMBOLS = "NVDA WMT XOM META GOOGL MSFT JPM JNJ AMZN SPCX".split()


@pytest.fixture
def shell_job(tmp_path):
    # Avoid selecting the Windows WSL launcher as a Bash interpreter.
    if os.name == "nt":
        bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
    else:
        bash = Path(shutil.which("bash") or "/nonexistent")
    if not bash.is_file():
        pytest.skip("Bash is required for the EC2 script tests")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("daily-run.sh", "scheduled-run.sh"):
        target = tmp_path / name
        target.write_bytes((SCRIPTS / name).read_bytes())
        target.chmod(0o700)
    (tmp_path / ".env").write_text(
        "PIPEGUARD_API_URL=https://example.invalid\nPIPEGUARD_API_KEY=test-only\n",
        encoding="utf-8",
    )
    stubs = {
        "flock": 'exit "${STUB_LOCK_STATUS:-0}"',
        "docker": 'if [[ "$*" == *"stop"* ]]; then exit "${STUB_STOP_STATUS:-0}"; fi',
        "curl": 'exit "${STUB_CURL_STATUS:-0}"',
        "sleep": "exit 0",
        "make": '[[ "$*" != *"SYMBOL=${STUB_FAIL_SYMBOL:-NONE}"* ]]',
        "timeout": 'shift 2; if [[ -n "${STUB_RUN_STATUS:-}" ]]; then exit "$STUB_RUN_STATUS"; fi; "$@"',
        "sudo": 'exit "${STUB_SHUTDOWN_STATUS:-0}"',
    }
    for name, body in stubs.items():
        executable = bin_dir / name
        executable.write_text(
            '#!/usr/bin/env bash\nprintf "%s\\n" "' + name + ' $*" >> "$TEST_CALLS"\n' + body + "\n",
            encoding="utf-8",
            newline="\n",
        )
        executable.chmod(0o700)

    def run(script, **overrides):
        env = os.environ.copy()
        # Git Bash inherits PATH; include its tools for date, tee and mkdir.
        extra = [str(bin_dir), str(bash.parent)]
        if os.name == "nt":
            extra.append(str(bash.parent.parent / "usr/bin"))
        env.update(
            PATH=os.pathsep.join(extra + [env.get("PATH", "")]),
            LAKEHOUSE_PROJECT_DIR=tmp_path.as_posix(),
            TEST_CALLS=(tmp_path / "calls.txt").as_posix(),
            **overrides,
        )
        result = subprocess.run(
            [str(bash), "-c", 'export PATH="$PWD/bin:$PATH"; exec bash "$1"', "test", script],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
        )
        calls = (tmp_path / "calls.txt").read_text().splitlines()
        return result, calls, tmp_path

    return run


def test_daily_continues_after_symbol_failure_and_returns_failure(shell_job):
    result, calls, _ = shell_job("daily-run.sh", STUB_FAIL_SYMBOL="WMT")
    assert result.returncode == 1, result.stderr
    assert [c for c in calls if c.startswith("make ")] == [
        f"make orchestrate SYMBOL={symbol}" for symbol in SYMBOLS
    ]


def test_pipeguard_warmup_failure_does_not_block_ingestion(shell_job):
    result, calls, _ = shell_job("daily-run.sh", STUB_CURL_STATUS="28")
    assert result.returncode == 0, result.stderr
    assert len([c for c in calls if c.startswith("make ")]) == 10
    assert "PipeGuard warm-up failed" in result.stdout


@pytest.mark.parametrize("status", ["0", "1", "124", "137"])
def test_wrapper_stops_database_and_schedules_shutdown_after_job(shell_job, status):
    result, calls, root = shell_job("scheduled-run.sh", STUB_RUN_STATUS=status)
    assert result.returncode == int(status), result.stderr
    assert calls[-2:] == ["docker compose stop -t 60 db", "sudo shutdown -h +1"]
    assert f"exit_code={status}" in (root / "logs/scheduled-status.log").read_text()


def test_wrapper_busy_job_does_not_stop_database_or_shutdown(shell_job):
    result, calls, _ = shell_job("scheduled-run.sh", STUB_RUN_STATUS="75")
    assert result.returncode == 75, result.stderr
    assert not any(c.startswith(("docker ", "sudo ")) for c in calls)


def test_wrapper_shutdown_is_attempted_even_if_database_stop_fails(shell_job):
    result, calls, _ = shell_job("scheduled-run.sh", STUB_RUN_STATUS="0", STUB_STOP_STATUS="1")
    assert result.returncode == 0, result.stderr
    assert calls[-1] == "sudo shutdown -h +1"


def test_shutdown_failure_is_not_reported_as_success(shell_job):
    result, _, _ = shell_job("scheduled-run.sh", STUB_RUN_STATUS="0", STUB_SHUTDOWN_STATUS="1")
    assert result.returncode == 1, result.stderr
    assert "could not schedule shutdown" in result.stdout
