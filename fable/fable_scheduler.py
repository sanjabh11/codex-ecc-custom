#!/usr/bin/env python3
"""
fable_scheduler.py — Background scheduler for Fable 5 workflows.

Supports:
  - Cron-like recurring execution from fable/fable_schedule.json
  - launchd plist generation for macOS
  - Per-workflow cadence: hourly, daily, weekly, or integer seconds
  - --dry-run and --run-once for safe testing

Usage:
  python3 fable/fable_scheduler.py --list
  python3 fable/fable_scheduler.py --add high-agency-inbox-triage hourly
  python3 fable/fable_scheduler.py --run
  python3 fable/fable_scheduler.py --install --apply
"""
import argparse
import json
import os
import plistlib
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, UTC
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).parent / "fable_schedule.json"
PROJECT_ROOT = Path(__file__).parent.parent
LAUNCHD_LABEL = "com.fable.scheduler"


class ScheduleConfig:
    """Loads and persists the fable_schedule.json manifest."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"jobs": []}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, default=str))

    def jobs(self) -> list:
        return self.data.get("jobs", [])

    def find(self, workflow: str) -> dict:
        for job in self.jobs():
            if job.get("workflow") == workflow:
                return job
        return None

    def add(self, workflow: str, cadence: str, params: list = None) -> dict:
        existing = self.find(workflow)
        if existing:
            existing["cadence"] = cadence
            existing["enabled"] = True
            existing["params"] = params or existing.get("params", [])
            return existing
        job = {
            "workflow": workflow,
            "cadence": cadence,
            "enabled": True,
            "last_run": None,
            "params": params or ["--mock", "--iterations", "1"],
        }
        self.data["jobs"].append(job)
        return job

    def toggle(self, workflow: str, enabled: bool) -> bool:
        job = self.find(workflow)
        if job:
            job["enabled"] = enabled
            return True
        return False


class FableScheduler:
    """Runs Fable workflows on a recurring schedule."""

    CADENCE_SECONDS = {
        "minutely": 60,
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
    }

    def __init__(self, config: ScheduleConfig, dry_run: bool = False, max_workers: int = 4):
        self.config = config
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.running = False
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.log_path = PROJECT_ROOT / "fable" / "scheduler.log"
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        self.running = False
        self._log(f"Received signal {signum}; shutting down...")

    def _log(self, message: str) -> None:
        line = f"[{datetime.now(UTC).isoformat()}] {message}"
        print(line)
        with open(self.log_path, "a") as f:
            f.write(line + "\n")

    def _interval_seconds(self, cadence) -> int:
        if isinstance(cadence, int):
            return cadence
        if isinstance(cadence, str) and cadence.isdigit():
            return int(cadence)
        return self.CADENCE_SECONDS.get(cadence.lower(), 86400)

    def _is_due(self, job: dict) -> bool:
        if not job.get("enabled", True):
            return False
        last_run = job.get("last_run")
        if not last_run:
            return True
        try:
            last_dt = datetime.fromisoformat(last_run)
        except ValueError:
            return True
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=UTC)
        interval = self._interval_seconds(job.get("cadence", "daily"))
        return (datetime.now(UTC) - last_dt).total_seconds() >= interval

    def _execute_job(self, job: dict) -> None:
        workflow = job["workflow"]
        params = job.get("params", ["--mock", "--iterations", "1"])
        args = ["python3", "fable/fable_runner.py", "--loop", workflow, *params]

        if self.dry_run:
            self._log(f"[DRY] Would run: {' '.join(args)}")
            job["last_run"] = datetime.now(UTC).isoformat()
            return

        self._log(f"[RUN] {workflow}")
        start = datetime.now(UTC)
        proc = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        elapsed = (datetime.now(UTC) - start).total_seconds()
        self._log(f"[DONE] {workflow} exit={proc.returncode} elapsed={elapsed:.2f}s")

        if proc.stdout:
            for line in proc.stdout.strip().splitlines()[:20]:
                self._log(f"  > {line[:120]}")
        if proc.returncode != 0 and proc.stderr:
            for line in proc.stderr.strip().splitlines()[:10]:
                self._log(f"  ! {line[:120]}")

        job["last_run"] = datetime.now(UTC).isoformat()

    def tick(self) -> None:
        """Check all jobs and execute due ones once."""
        due_jobs = [job for job in self.config.jobs() if self._is_due(job)]
        if due_jobs:
            self._log(f"Tick: {len(due_jobs)} job(s) due")
        for job in due_jobs:
            self._executor.submit(self._execute_job, job)
        self.config.save()

    def run(self) -> None:
        """Run scheduler loop, waking every minute."""
        self.running = True
        self._log(f"Scheduler started. Loaded {len(self.config.jobs())} jobs.")
        try:
            while self.running:
                self.tick()
                # Sleep in short slices so SIGINT/SIGTERM are responsive
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
        finally:
            self._executor.shutdown(wait=True)
            self._log("Scheduler stopped.")

    def install_launchd(self, apply: bool = False) -> Path:
        """Create a launchd plist for macOS to start scheduler at login."""
        launch_agents = Path.home() / "Library" / "LaunchAgents"
        launch_agents.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents / f"{LAUNCHD_LABEL}.plist"

        scheduler_script = (PROJECT_ROOT / "fable" / "fable_scheduler.py").resolve()
        log_dir = (PROJECT_ROOT / "fable").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)

        plist = {
            "Label": LAUNCHD_LABEL,
            "ProgramArguments": [
                sys.executable,
                str(scheduler_script),
                "--run",
            ],
            "WorkingDirectory": str(PROJECT_ROOT),
            "RunAtLoad": True,
            "KeepAlive": True,
            "StandardOutPath": str(log_dir / "scheduler_daemon.log"),
            "StandardErrorPath": str(log_dir / "scheduler_daemon.log"),
            "EnvironmentVariables": {"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
        }
        plist_path.write_bytes(plistlib.dumps(plist))
        self._log(f"Created launchd plist: {plist_path}")

        if apply:
            self._launchctl("bootout", plist_path)
            self._launchctl("bootstrap", plist_path)
        return plist_path

    def uninstall_launchd(self) -> None:
        """Unload and remove the launchd plist."""
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        if plist_path.exists():
            self._launchctl("bootout", plist_path)
            plist_path.unlink()
            self._log(f"Removed launchd plist: {plist_path}")
        else:
            self._log("No launchd plist found.")

    def _launchctl(self, action: str, plist_path: Path) -> None:
        """Run launchctl bootstrap/bootout safely."""
        uid = os.getuid()
        domain = f"gui/{uid}"
        cmd = ["launchctl", action, domain, str(plist_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                self._log(f"launchctl {action} succeeded")
            else:
                self._log(f"launchctl {action} exit={result.returncode}: {result.stderr.strip()}")
        except FileNotFoundError:
            self._log("launchctl not found; skipping launchd operation")

    def status(self) -> None:
        """Print scheduler status."""
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        self._log(f"Config file: {self.config.path}")
        self._log(f"Total jobs: {len(self.config.jobs())}")
        for job in self.config.jobs():
            due = "DUE" if self._is_due(job) else "ok"
            enabled = "enabled" if job.get("enabled", True) else "disabled"
            self._log(f"  - {job['workflow']}: {job.get('cadence')} ({enabled}, {due})")
        self._log(f"launchd plist: {'exists' if plist_path.exists() else 'not installed'}")


def main():
    parser = argparse.ArgumentParser(
        description="Fable 5 Workflow Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List scheduled jobs:
    python3 fable/fable_scheduler.py --list

  Add a job and start the scheduler in the foreground:
    python3 fable/fable_scheduler.py --add daily-runbook-execution daily
    python3 fable/fable_scheduler.py --run

  Test one scheduling tick without executing workflows:
    python3 fable/fable_scheduler.py --run-once --dry-run

  Install macOS background daemon:
    python3 fable/fable_scheduler.py --install --apply
        """,
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to schedule JSON")
    parser.add_argument("--run", action="store_true", help="Run scheduler in foreground")
    parser.add_argument("--run-once", action="store_true", help="Run one tick and exit")
    parser.add_argument("--dry-run", action="store_true", help="Do not execute workflows")
    parser.add_argument("--add", nargs=2, metavar=("WORKFLOW", "CADENCE"), help="Add or update a job")
    parser.add_argument("--enable", type=str, help="Enable a job by workflow name")
    parser.add_argument("--disable", type=str, help="Disable a job by workflow name")
    parser.add_argument("--list", action="store_true", help="List scheduled jobs")
    parser.add_argument("--install", action="store_true", help="Create launchd plist")
    parser.add_argument("--apply", action="store_true", help="Load launchd plist (macOS only)")
    parser.add_argument("--uninstall", action="store_true", help="Unload and remove launchd plist")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")

    args = parser.parse_args()
    config = ScheduleConfig(args.config)
    scheduler = FableScheduler(config, dry_run=args.dry_run)

    if args.add:
        config.add(args.add[0], args.add[1])
        config.save()
        print(f"Added/updated job: {args.add[0]} -> {args.add[1]}")
    elif args.enable:
        if config.toggle(args.enable, True):
            config.save()
            print(f"Enabled {args.enable}")
        else:
            print(f"Job not found: {args.enable}")
    elif args.disable:
        if config.toggle(args.disable, False):
            config.save()
            print(f"Disabled {args.disable}")
        else:
            print(f"Job not found: {args.disable}")
    elif args.list:
        scheduler.status()
    elif args.install:
        path = scheduler.install_launchd(apply=args.apply)
        if not args.apply:
            print(f"\nCreated {path}")
            print(f"To activate, run: launchctl bootstrap gui/$(id -u) {path}")
    elif args.uninstall:
        scheduler.uninstall_launchd()
    elif args.status:
        scheduler.status()
    elif args.run or args.run_once:
        scheduler.tick()
        if args.run:
            scheduler.run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
