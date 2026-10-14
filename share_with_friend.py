import os
import sys
import time
import pathlib
import subprocess
import webbrowser
from pyngrok import conf, ngrok

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def copy_to_clipboard(text: str):
    try:
        subprocess.run(['clip.exe'], input=text.strip().encode('utf-8'), check=True)
        return True
    except Exception:
        return False

def main():
    print("=" * 70)
    print("🚀 E-SALE MANAGEMENT SYSTEM - NGROK PUBLIC SHARING")
    print("=" * 70)

    base_dir = pathlib.Path(__file__).resolve().parent

    # Configure ngrok config path from user profile if available
    user_ngrok_cfg = pathlib.Path(os.environ.get('LOCALAPPDATA', '')) / 'ngrok' / 'ngrok.yml'
    if user_ngrok_cfg.exists():
        conf.get_default().config_path = str(user_ngrok_cfg)

    # 1. Start FastAPI Backend if not already running on port 8000
    backend_proc = None
    if not is_port_in_use(8000):
        print("[1/3] Starting FastAPI Backend on port 8000...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(base_dir)
        )
        time.sleep(2)
    else:
        print("[1/3] FastAPI Backend is already running on port 8000.")

    # 2. Start Streamlit UI if not already running on port 8501
    frontend_proc = None
    if not is_port_in_use(8501):
        print("[2/3] Starting Streamlit UI on port 8501...")
        frontend_proc = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run", "frontend/app.py",
                "--server.port", "8501",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ],
            cwd=str(base_dir)
        )
        time.sleep(3)
    else:
        print("[2/3] Streamlit UI is already running on port 8501.")

    # 3. Create ngrok public tunnel on port 8501
    print("[3/3] Opening secure ngrok public tunnel...")
    try:
        tunnel = ngrok.connect(8501, "http")
        public_url = tunnel.public_url

        copied = copy_to_clipboard(public_url)
        copied_msg = " (Copied to your clipboard!)" if copied else ""

        print("\n" + "=" * 70)
        print("🎉 SUCCESS! YOUR E-SALE SYSTEM IS LIVE ON THE INTERNET")
        print("=" * 70)
        print(f"\n👉 SHARE THIS LINK WITH YOUR FRIEND:\n   {public_url}{copied_msg}\n")
        print("=" * 70)
        print(f"🏠 Local Streamlit UI: http://localhost:8501")
        print(f"📘 Local Swagger Docs: http://127.0.0.1:8000/docs")
        print("=" * 70)
        print("\nPress Ctrl+C to close the tunnel and stop the servers.\n")

        # Open in default browser
        try:
            webbrowser.open(public_url)
        except Exception:
            pass

        # Keep alive until Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down ngrok tunnel and servers...")
    except Exception as e:
        print(f"\nError creating ngrok tunnel: {e}")
    finally:
        try:
            ngrok.kill()
        except Exception:
            pass
        for proc in [frontend_proc, backend_proc]:
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
        print("Everything cleanly stopped.")

if __name__ == "__main__":
    main()
