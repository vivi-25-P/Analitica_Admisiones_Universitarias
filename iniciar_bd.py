"""Entrada compatible desde la raíz: uv run python iniciar_bd.py."""
from src.analitica_admisiones.database import main
import subprocess
import sys

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Falló Docker/PostgreSQL (código {exc.returncode}). Revisa: docker compose logs postgres")
