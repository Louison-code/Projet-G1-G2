#!/usr/bin/env python3
"""Point d'entrée de l'application — lance le backend API + frontend Streamlit."""
import subprocess, time, sys

def main():
    print("Démarrage de l'application...")

    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ])

    frontend = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", "8501"
    ])

    time.sleep(3)

    print("Application prête !")
    print("Interface : http://localhost:8501")
    print("API : http://localhost:8000")
    print("Docs API : http://localhost:8000/docs")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("Arrêt...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    main()
