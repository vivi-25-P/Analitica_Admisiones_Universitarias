"""Exploración de admisiones conservando los datos de origen."""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['perfilar', 'graficar', 'bd'])
    args = parser.parse_args()
    if args.accion == 'perfilar':
        from .profiling import main as run
    elif args.accion == 'graficar':
        from .visualizations import main as run
    else:
        from .database import main as run
    try:
        run()
    except subprocess.CalledProcessError as exc:
        sys.exit(f'Falló el comando externo (código {exc.returncode}).')
