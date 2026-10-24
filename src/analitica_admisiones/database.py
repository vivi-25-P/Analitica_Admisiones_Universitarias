"""Arranca PostgreSQL y compara cada fila con el CSV original sin modificarlo."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def main():
    if not shutil.which("docker"):
        sys.exit("Docker no está disponible. Instala/inicia Docker y habilita su integración con este WSL.")
    meta = json.loads((ROOT / "docker/origen.json").read_text(encoding="utf-8"))
    source = ROOT / meta["archivo"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != meta["sha256"]:
        sys.exit("El CSV cambió respecto a la preparación inicial. Revisa el origen antes de cargarlo.")
    subprocess.run(["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "180"], cwd=ROOT, check=True)
    query = "COPY public.admisiones_original TO STDOUT WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');"
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-X", "-q", "-v", "ON_ERROR_STOP=1",
         "-U", "analista", "-d", "admisiones", "-c", query],
        cwd=ROOT, check=True, stdout=subprocess.PIPE,
    )
    loaded = list(csv.reader(io.StringIO(result.stdout.decode("utf-8"), newline="")))
    with source.open(encoding="utf-8-sig", newline="") as handle:
        original = list(csv.reader(handle))
    if loaded[0] != original[0]:
        sys.exit("ERROR: las columnas no coinciden con el CSV.")
    if collections.Counter(map(tuple, loaded[1:])) != collections.Counter(map(tuple, original[1:])):
        sys.exit("ERROR: los datos cargados no coinciden con el CSV, incluidos sus duplicados.")
    if hashlib.sha256(source.read_bytes()).hexdigest() != meta["sha256"]:
        sys.exit("ERROR: el archivo de origen cambió durante la verificación.")
    print(f"Carga verificada: {len(loaded)-1} filas y {len(loaded[0])} columnas idénticas al CSV.")
    print("Tabla: admisiones.public.admisiones_original. Usuario: analista. Puerto: el indicado en .env (5433 por defecto).")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Falló Docker/PostgreSQL (código {exc.returncode}). Revisa: docker compose logs postgres")
