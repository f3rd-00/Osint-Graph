import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
BACKEND_SCRIPT = BACKEND_DIR / "app.py"
FRONTEND_FILE = BASE_DIR / "outrasec.html"
BACKEND_URL = "http://localhost:5000/api/health"


def iniciar_backend():
    print("Subindo o backend em http://localhost:5000 ...")
    return subprocess.Popen([sys.executable, str(BACKEND_SCRIPT)], cwd=str(BACKEND_DIR))


def esperar_backend_subir(tentativas=20):
    import urllib.request

    for _ in range(tentativas):
        try:
            urllib.request.urlopen(BACKEND_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def abrir_frontend():
    print("Abrindo o OutraSec no navegador...")
    webbrowser.open(FRONTEND_FILE.as_uri())


def main():
    if not FRONTEND_FILE.exists():
        print(f"Não encontrei {FRONTEND_FILE.name}. Rode este script na pasta do projeto.")
        return

    processo_backend = iniciar_backend()

    if esperar_backend_subir():
        print("Backend no ar.")
    else:
        print("O backend demorou pra responder, mas vou abrir a página assim mesmo.")

    abrir_frontend()

    print("\nOutraSec rodando. Feche esta janela ou aperte Ctrl+C para encerrar o backend.\n")
    try:
        processo_backend.wait()
    except KeyboardInterrupt:
        print("\nEncerrando...")
        processo_backend.terminate()


if __name__ == "__main__":
    main()
