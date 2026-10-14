import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("=" * 60)
    print("⚡ Starting E-Sale Management System (FastAPI + Streamlit)")
    print("=" * 60)

    base_dir = Path(__file__).resolve().parent

    # 1. Start FastAPI backend
    print("[1/2] Launching FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1", "--port", "8000"
        ],
        cwd=str(base_dir)
    )

    # Wait for backend to be ready
    time.sleep(2)

    # 2. Start Streamlit UI with headless flags
    print("[2/2] Launching Streamlit Web UI on http://localhost:8501...")
    frontend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ],
        cwd=str(base_dir)
    )

    time.sleep(2)
    print("\n✅ Both servers are online!")
    print("👉 Streamlit Web UI:     http://localhost:8501")
    print("👉 FastAPI Swagger Docs: http://127.0.0.1:8000/docs")
    print("\nPress Ctrl+C to terminate both servers.\n")

    # Automatically open browser
    try:
        webbrowser.open("http://localhost:8501")
    except Exception:
        pass

    try:
        while True:
            # Check if any process terminated unexpectedly
            b_code = backend_proc.poll()
            f_code = frontend_proc.poll()
            if b_code is not None:
                print(f"\nBackend process exited with code {b_code}.")
                break
            if f_code is not None:
                print(f"\nFrontend process exited with code {f_code}.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        for proc in [backend_proc, frontend_proc]:
            try:
                proc.terminate()
            except Exception:
                pass
        print("Servers successfully stopped.")

if __name__ == "__main__":
    main()
