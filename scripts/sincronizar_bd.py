"""Levanta y sincroniza la base local con las migraciones SQL del repositorio."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))


@dataclass(frozen=True)
class Migration:
    name: str
    version: int
    digest: str
    sql: str


def discover(folder):
    migrations = []
    versions = set()
    for path in sorted(folder.glob('*.sql')):
        match = re.fullmatch(r'(\d{3})_[a-z0-9_]+\.sql', path.name)
        if not match:
            raise ValueError(f'Nombre de migración inválido: {path.name}')
        version = int(match[1])
        if version in versions:
            raise ValueError(f'Versión repetida: {version}')
        versions.add(version)
        content = path.read_bytes()
        migrations.append(Migration(path.name, version, hashlib.sha256(content).hexdigest(), content.decode('utf-8')))
    if not migrations:
        raise ValueError('No hay migraciones SQL en el repositorio.')
    return migrations


def plan(migrations, applied):
    local = {m.name: m for m in migrations}
    for name, digest in applied.items():
        if name not in local:
            raise ValueError(f'La base tiene una migración ausente del repositorio: {name}. Actualiza Git antes de continuar.')
        if local[name].digest != digest:
            raise ValueError(f'La migración aplicada {name} fue modificada. Se debe crear una versión nueva.')
    last = max((local[name].version for name in applied), default=0)
    pending = [m for m in migrations if m.name not in applied]
    if any(m.version < last for m in pending):
        raise ValueError('Se encontró una migración nueva anterior a la última aplicada; revisar el orden.')
    return pending


def literal(text):
    return "'" + text.replace("'", "''") + "'"


def psql(sql):
    result = subprocess.run(
        ['docker','compose','exec','-T','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1',
         '-U','analista','-d','admisiones'], cwd=ROOT,
        input=sql.encode('utf-8'), stdout=subprocess.PIPE, check=True,
    )
    return result.stdout.decode('utf-8')


def ensure_environment():
    if not shutil.which('docker'):
        raise RuntimeError('Instala Docker con Compose y comprueba que el motor esté en ejecución.')
    path = ROOT / '.env'
    if not path.exists():
        try:
            with path.open('x', encoding='utf-8') as handle:
                handle.write('POSTGRES_PASSWORD='+secrets.token_urlsafe(30)+'\nPOSTGRES_PORT=5433\n')
            print('Se creó .env con una contraseña local. No se muestra ni se comparte por Git.', flush=True)
        except FileExistsError:
            pass
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('POSTGRES_PASSWORD=') and line.split('=',1)[1] == 'CAMBIAR_POR_UNA_CLAVE_LOCAL':
            if not os.environ.get('POSTGRES_PASSWORD'):
                raise ValueError('Reemplaza la contraseña de ejemplo en .env antes de iniciar.')


def registry():
    psql('''
CREATE TABLE IF NOT EXISTS public.migraciones_proyecto (
    archivo TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    aplicado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
''')
    data = psql('''
COPY (SELECT COALESCE(jsonb_object_agg(archivo, sha256), '{}'::jsonb)
      FROM public.migraciones_proyecto) TO STDOUT;
''')
    return json.loads(data.strip())


def apply_migration(migration):
    name, digest, body = map(literal, [migration.name, migration.digest, migration.sql])
    tag = '$migracion_' + migration.digest + '$'
    # El SQL se ejecuta dentro de DO y de una transacción externa. Una migración
    # no puede confirmar su propia transacción ni dejar una aplicación parcial.
    return psql(f'''
BEGIN;
SET LOCAL standard_conforming_strings = on;
SELECT pg_advisory_xact_lock(1740041);
CREATE TEMP TABLE fuente_antes ON COMMIT DROP AS
    SELECT to_jsonb(a) AS fila FROM public.admisiones_original a;
CREATE TEMP TABLE tipado_antes ON COMMIT DROP AS
    SELECT to_jsonb(a) AS fila FROM public.admisiones_tipadas a;
DO {tag}
DECLARE anterior TEXT;
BEGIN
    SELECT sha256 INTO anterior FROM public.migraciones_proyecto WHERE archivo={name};
    IF anterior IS NULL THEN
        EXECUTE {body};
        INSERT INTO public.migraciones_proyecto(archivo,sha256) VALUES ({name},{digest});
    ELSIF anterior <> {digest} THEN
        RAISE EXCEPTION 'La migración ya aplicada tiene otro contenido';
    END IF;
END {tag};
DO $control_origen$
BEGIN
    IF EXISTS (
        (SELECT fila FROM fuente_antes EXCEPT ALL SELECT to_jsonb(a) FROM public.admisiones_original a)
        UNION ALL
        (SELECT to_jsonb(a) FROM public.admisiones_original a EXCEPT ALL SELECT fila FROM fuente_antes)
    ) THEN RAISE EXCEPTION 'La migración alteró la tabla original. Se revierte.'; END IF;
    IF EXISTS (
        (SELECT fila FROM tipado_antes EXCEPT ALL SELECT to_jsonb(a) FROM public.admisiones_tipadas a)
        UNION ALL
        (SELECT to_jsonb(a) FROM public.admisiones_tipadas a EXCEPT ALL SELECT fila FROM tipado_antes)
    ) THEN RAISE EXCEPTION 'La migración alteró la base tipada previa a limpieza. Se revierte.'; END IF;
END $control_origen$;
COMMIT;
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--estado', action='store_true', help='Muestra versiones y pendientes sin aplicar las migraciones SQL.')
    args = parser.parse_args()
    migrations = discover(ROOT / 'sql/migrations')
    ensure_environment()
    from analitica_admisiones.database import main as start_database
    start_database()
    applied = registry()
    pending = plan(migrations, applied)
    print('Migraciones aplicadas:', len(applied), '| Pendientes:', len(pending), flush=True)
    for migration in pending:
        print('Pendiente:', migration.name, flush=True)
    if args.estado:
        print('Consulta finalizada. No se aplicaron las migraciones pendientes.', flush=True)
        return
    from scripts.respaldar_bd import main as backup
    backup()
    from scripts.preparar_tipos import main as prepare_types
    prepare_types()
    for migration in pending:
        print('Aplicando:', migration.name, flush=True)
        apply_migration(migration)
    final = registry()
    if plan(migrations, final):
        raise RuntimeError('Quedaron migraciones sin aplicar.')
    from scripts.cargar_base_unificada import cargar
    cargar()
    print('Base sincronizada con el repositorio, incluida la entrega analítica. Las tablas originales permanecen intactas.', flush=True)


if __name__=='__main__':
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f'No se completó la sincronización: {error}')
