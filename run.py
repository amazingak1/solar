"""
Solar Vest - Unified Service Runner
===================================
Launches the ML Microservice (port 8001), Backend API (port 8000),
and Frontend static server (port 3000) concurrently from Python code.

Usage:
    .\.venv\Scripts\python.exe run.py
"""

import os
import sys
import subprocess
import signal
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable


def main():
    print("=" * 60)
    print("  Solar Vest - Starting Platform Services")
    print(f"  Python: {PYTHON_EXE}")
    print("=" * 60)

    # 1. Start ML Microservice
    ml_cmd = [
        PYTHON_EXE, "-m", "uvicorn", "app:app",
        "--app-dir", os.path.join(ROOT_DIR, "ml"),
        "--host", "0.0.0.0",
        "--port", "8001",
    ]
    print("\n[1/3] Starting ML Microservice on http://localhost:8001 ...")
    ml_proc = subprocess.Popen(ml_cmd, cwd=ROOT_DIR)

    # Allow ML service to initialize (model loading takes a moment)
    time.sleep(2)

    # 2. Start Backend API
    backend_cmd = [
        PYTHON_EXE, "-m", "uvicorn", "app.main:app",
        "--app-dir", os.path.join(ROOT_DIR, "backend"),
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    print("[2/3] Starting Backend API on http://localhost:8000 ...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=ROOT_DIR)

    # 3. Serve frontend via Python's built-in HTTP server (avoids file:// CORS issues)
    frontend_cmd = [
        PYTHON_EXE, "-m", "http.server", "3000",
        "--directory", os.path.join(ROOT_DIR, "frontend"),
    ]
    print("[3/3] Starting Frontend server on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)
    print("\n" + "=" * 60)
    print("  All services are running!")
    print()
    print("  >> Open in browser: http://localhost:3000")
    print()
    print("  Backend API Docs : http://localhost:8000/docs")
    print("  ML Service Docs  : http://localhost:8001/docs")
    print()
    print("  Login credentials:")
    print("    owner@solarvest.com    / password123  (Panel Owner)")
    print("    investor@solarvest.com / password123  (Investor)")
    print("    admin@solarvest.com    / password123  (Admin)")
    print("=" * 60)
    print("  Press CTRL+C to stop all services.\n")

    procs = [ml_proc, backend_proc, frontend_proc]
    proc_names = ["ML service", "Backend API", "Frontend server"]

    def handle_exit(signum, frame):
        print("\nStopping Solar Vest services...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
            except Exception:
                pass
        print("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit)

    try:
        while True:
            for p, name in zip(procs, proc_names):
                if p.poll() is not None:
                    print(f"WARNING: {name} terminated unexpectedly. Recheck logs.")
            time.sleep(2)
    except KeyboardInterrupt:
        handle_exit(None, None)


if __name__ == "__main__":
    main()
