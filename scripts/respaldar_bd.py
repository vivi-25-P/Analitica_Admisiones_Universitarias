"""Crea un respaldo local de PostgreSQL y verifica que su índice sea legible."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def main():
    stamp = datetime.now(ZoneInfo('America/Bogota')).strftime('%Y%m%d_%H%M%S_%f')
    folder = ROOT / 'data/backups'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'admisiones_{stamp}.dump'
    command = ['docker', 'compose', 'exec', '-T', 'postgres']
    # El modo exclusivo evita sobrescribir un respaldo anterior.
    with path.open('xb') as output:
        try:
            subprocess.run(command + ['pg_dump', '-U', 'analista', '-d', 'admisiones',
                                      '--format=custom'], cwd=ROOT, stdout=output, check=True)
        except subprocess.CalledProcessError:
            print(f'Respaldo incompleto, no usar: {path}')
            raise
    data = path.read_bytes()
    if not data.startswith(b'PGDMP'):
        raise ValueError('El respaldo no tiene la cabecera del formato personalizado de PostgreSQL.')
    listing = subprocess.run(command + ['pg_restore', '--list'], input=data,
                             stdout=subprocess.PIPE, cwd=ROOT, check=True)
    toc = listing.stdout.decode('utf-8')
    if 'TABLE DATA public admisiones_original' not in toc:
        raise ValueError('No se encontró la tabla original en el índice del respaldo.')
    info = {
        'creado_bogota': datetime.now(ZoneInfo('America/Bogota')).isoformat(),
        'archivo': path.name,
        'formato': 'PostgreSQL custom',
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'verificacion': 'Cabecera PGDMP e índice leído correctamente con pg_restore --list.',
        'limite': 'Esta comprobación no sustituye una prueba de restauración completa.',
    }
    path.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    path.with_suffix('.toc.txt').write_text(toc, encoding='utf-8')
    print('Respaldo creado:', path.relative_to(ROOT))
    print('Índice verificado; incluye datos de public.admisiones_original.')
    print('Tamaño:', len(data), 'bytes. SHA256:', info['sha256'])


if __name__ == '__main__':
    main()
