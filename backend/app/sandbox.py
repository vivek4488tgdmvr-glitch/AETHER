import shutil
import subprocess
import tempfile
from pathlib import Path
from . import config

def docker_available() -> bool:
    return shutil.which("docker") is not None

def run_tests(root: Path, command: str = "auto") -> dict:
    if not docker_available():
        return {
            "status": "unavailable",
            "message": "Docker CLI was not found. Install and start Docker Desktop, then retry.",
            "stdout": "",
            "stderr": "",
            "exit_code": None,
        }
    try:
        version = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=10,
        )
        if version.returncode != 0:
            return {
                "status": "unavailable",
                "message": "Docker is installed but the Docker daemon is not running.",
                "stdout": version.stdout[-4000:],
                "stderr": version.stderr[-4000:],
                "exit_code": version.returncode,
            }
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "unavailable", "message": f"Docker check failed: {exc}", "stdout": "", "stderr": "", "exit_code": None}

    with tempfile.TemporaryDirectory(prefix="aethercode-test-") as tmp:
        copied = Path(tmp) / "workspace"
        shutil.copytree(root, copied, symlinks=False, ignore=shutil.ignore_patterns(
            ".env", ".env.*", ".git", ".venv", "venv", "node_modules",
            "__pycache__", ".pytest_cache", "data"
        ))
        if command == "pytest":
            test_cmd = "python -m pytest -q"
        elif command == "unittest":
            test_cmd = "python -m unittest discover -v"
        else:
            test_cmd = (
                "if python -c 'import pytest' >/dev/null 2>&1; then "
                "python -m pytest -q; else python -m unittest discover -v; fi"
            )
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "384m",
            "--cpus", "1",
            "--pids-limit", "64",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--user", "65534:65534",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "PYTHONUNBUFFERED=1",
            "-v", f"{copied.as_posix()}:/workspace:ro",
            "-w", "/workspace",
            config.SANDBOX_IMAGE,
            "sh", "-lc", test_cmd,
        ]
        try:
            result = subprocess.run(
                docker_cmd, capture_output=True, text=True, timeout=90,
            )
            status = "passed" if result.returncode == 0 else "failed"
            return {
                "status": status,
                "message": "Test command completed in Docker with network disabled.",
                "stdout": result.stdout[-12000:],
                "stderr": result.stderr[-12000:],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "timeout",
                "message": "Test run exceeded 90 seconds and was stopped.",
                "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
                "exit_code": None,
            }
        except OSError as exc:
            return {"status": "error", "message": str(exc), "stdout": "", "stderr": "", "exit_code": None}
