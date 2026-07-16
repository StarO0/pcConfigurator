from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import BinaryIO


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "pc-builder-backend"
FRONTEND = ROOT / "front"
RUN_DIR = ROOT / ".run"
LOG_DIR = ROOT / "logs"
API_HEALTH = "http://127.0.0.1:8000/api/v1/health"
FRONTEND_URL = "http://127.0.0.1:3000"
PROXY_HEALTH = f"{FRONTEND_URL}/api-backend/health"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def reachable(url: str) -> bool:
    try:
        with OPENER.open(url, timeout=2) as response:
            return 200 <= response.status < 400
    except (OSError, urllib.error.URLError):
        return False


def catalog_is_ready() -> bool:
    try:
        with OPENER.open(
            f"{FRONTEND_URL}/api-backend/products?limit=1&in_stock=true", timeout=5
        ) as response:
            payload = json.load(response)
        items = payload.get("items", [])
        return payload.get("total", 0) > 0 and bool(items and items[0].get("offers"))
    except (OSError, ValueError, urllib.error.URLError):
        return False


def stack_is_ready() -> bool:
    return (
        reachable(API_HEALTH)
        and reachable(FRONTEND_URL)
        and reachable(PROXY_HEALTH)
        and catalog_is_ready()
    )


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)


def spawn(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    log: BinaryIO | None = None,
    detached: bool = False,
) -> subprocess.Popen[bytes]:
    kwargs: dict[str, object] = {"cwd": cwd, "env": env}
    if log is not None:
        kwargs.update(
            {"stdout": log, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
        )
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP
        if detached:
            flags |= subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        kwargs["creationflags"] = flags
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(command, **kwargs)  # type: ignore[arg-type]


def wait_until_ready(processes: list[subprocess.Popen[bytes]], timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for process, name in zip(processes, ("API", "Frontend"), strict=True):
            code = process.poll()
            if code is not None:
                raise RuntimeError(f"{name} завершился раньше времени (код {code})")
        if stack_is_ready():
            return
        time.sleep(0.5)
    raise TimeoutError(f"Сервисы не успели запуститься за {timeout} секунд")


def print_log_tail(path: Path, lines: int = 30) -> None:
    if not path.exists():
        return
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    print(f"\nПоследние строки {path.relative_to(ROOT)}:", file=sys.stderr)
    for line in content[-lines:]:
        print(f"  {line}", file=sys.stderr)


def write_pid(name: str, process: subprocess.Popen[bytes]) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / f"{name}.pid").write_text(str(process.pid), encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description="Advanced local run against PostgreSQL")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--check-and-exit",
        action="store_true",
        help="проверить API, frontend и frontend-to-API proxy, затем остановить их",
    )
    parser.add_argument(
        "--detach",
        action="store_true",
        help="оставить сервисы работать в фоне после завершения launcher",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    if stack_is_ready() and not args.check_and_exit:
        print("PC Configurator уже запущен и отвечает на запросы.")
        if not args.no_browser:
            webbrowser.open(FRONTEND_URL)
        return 0

    occupied = [port for port in (8000, 3000) if not port_is_free(port)]
    if occupied:
        print(
            f"Ошибка: порты уже заняты: {', '.join(map(str, occupied))}",
            file=sys.stderr,
        )
        print("Запустите stop-windows.bat и повторите запуск.", file=sys.stderr)
        return 2

    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        print(
            "Ошибка: npm не найден. Установите Node.js 20 LTS или новее.",
            file=sys.stderr,
        )
        return 2

    common = os.environ.copy()
    common.update(
        {
            "PYTHONUTF8": "1",
            "DATABASE_URL": os.environ.get(
                "DATABASE_URL",
                "postgresql+asyncpg://pcbuilder:pcbuilder-local-change-in-production@127.0.0.1:5432/pcbuilder",
            ),
            "AUTO_CREATE_TABLES": "false",
            "SEED_DEMO_DATA": "false",
            "STARTER_SNAPSHOT_ENABLED": "true",
            "PUBLIC_COLLECTORS_ENABLED": "false",
            "HARVESTER_SCHEDULER_ENABLED": "true",
            "ADMIN_BOOTSTRAP_EMAIL": "admin@pcbuilder.app",
            "ADMIN_BOOTSTRAP_PASSWORD": "Local-admin-123",
            "NEXT_PUBLIC_API_URL": "/api-backend",
            "BACKEND_INTERNAL_URL": "http://127.0.0.1:8000/api/v1",
            "FRONTEND_URL": FRONTEND_URL,
        }
    )

    detached = args.detach and not args.check_and_exit
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_paths = [LOG_DIR / "backend.log", LOG_DIR / "frontend.log"]
    log_handles: list[BinaryIO] = []
    processes: list[subprocess.Popen[bytes]] = []
    keep_running = False
    try:
        if detached:
            for path in log_paths:
                log_handles.append(path.open("wb"))

        print("Запускаю API на http://127.0.0.1:8000 ...")
        processes.append(
            spawn(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                BACKEND,
                common,
                log_handles[0] if detached else None,
                detached,
            )
        )
        print("Запускаю интерфейс на http://127.0.0.1:3000 ...")
        processes.append(
            spawn(
                [npm, "run", "dev", "--", "--hostname", "127.0.0.1"],
                FRONTEND,
                common,
                log_handles[1] if detached else None,
                detached,
            )
        )
        wait_until_ready(processes, args.timeout)
        print("\nПроект готов и API доступен через интерфейс:")
        print(f"  Интерфейс: {FRONTEND_URL}")
        print("  API docs:  http://127.0.0.1:8000/docs")
        print(f"  Логи:      {LOG_DIR}")
        if args.check_and_exit:
            print("Проверка полного пути frontend -> API пройдена.")
            return 0
        if not args.no_browser:
            webbrowser.open(FRONTEND_URL)
        if detached:
            write_pid("api", processes[0])
            write_pid("frontend", processes[1])
            keep_running = True
            print("Сервисы работают в фоне. Это окно можно закрыть.")
            print("Для остановки запустите stop-windows.bat.")
            return 0

        print("Для остановки нажмите Ctrl+C.")
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        failed = next(process for process in processes if process.poll() is not None)
        return failed.returncode or 1
    except KeyboardInterrupt:
        print("\nОстанавливаю проект...")
        return 0
    except (RuntimeError, TimeoutError) as exc:
        print(f"Ошибка запуска: {exc}", file=sys.stderr)
        for path in log_paths:
            print_log_tail(path)
        return 1
    finally:
        for handle in log_handles:
            handle.close()
        if not keep_running:
            for process in reversed(processes):
                stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
