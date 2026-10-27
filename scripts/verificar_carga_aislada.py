"""Restaura el respaldo anterior y prueba la migración nueva en una base temporal."""

import os
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

from dotenv import dotenv_values
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from preparar_tipos import represent

ROOT = Path(__file__).resolve().parents[1]
env = dotenv_values(ROOT / '.env')
settings = dict(host='127.0.0.1', port=env.get('POSTGRES_PORT','5433'), user='analista',
                password=env['POSTGRES_PASSWORD'])
backups = sorted(p for p in (ROOT / 'data/backups').glob('*.dump')
                 if p.with_suffix('.toc.txt').exists()
                 and 'SCHEMA - analitica' not in p.with_suffix('.toc.txt').read_text())
if not backups:
    raise RuntimeError('Primero cree un respaldo de la base anterior')
backup = backups[-1]
with psycopg.connect(dbname='postgres', autocommit=True, **settings) as admin:
    for scenario in ['respaldo_anterior', 'instalacion_nueva']:
        name = 'admisiones_validacion_' + uuid.uuid4().hex[:10]
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        try:
            if scenario == 'respaldo_anterior':
                with backup.open('rb') as handle:
                    subprocess.run(['docker','compose','exec','-T','postgres','pg_restore',
                                    '-U','analista','-d',name,'--exit-on-error','--no-owner'],
                                   cwd=ROOT, stdin=handle, check=True)
            with psycopg.connect(dbname=name, **settings) as conn:
                if scenario == 'instalacion_nueva':
                    conn.execute((ROOT / 'docker/init/01_cargar.sql').read_text())
                    conn.execute((ROOT / 'sql/migrations/001_admisiones_tipadas.sql').read_text())
                    original = ROOT / 'data/raw/Caso2_Admisiones_Universitarias.csv'
                    digest = hashlib.sha256(original.read_bytes()).hexdigest()
                    with original.open(encoding='utf-8-sig', newline='') as handle:
                        rows = list(csv.DictReader(handle))
                    with conn.cursor().copy('COPY public.admisiones_tipadas FROM STDIN') as copy:
                        for n, row in enumerate(rows,2):
                            converted = [represent(c,v) for c,v in row.items()]
                            copy.write_row((n,digest,*[v[0] for v in converted],Jsonb(row),
                                            Jsonb([v[1] for v in converted if v[1] is not None])))
                conn.execute((ROOT / 'sql/migrations/002_base_unificada_analitica.sql').read_text())
            result = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests',
                                     '-p','test_carga_analitica_docker.py','-v'], cwd=ROOT,
                                    env={**os.environ,'ADMISIONES_TEST_DATABASE':name})
            if result.returncode:
                raise RuntimeError('Falló la prueba de carga aislada: ' + scenario)
            print('Escenario verificado:',scenario,flush=True)
        finally:
            admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
(ROOT / 'reports/limpieza/verificacion_postgresql_aislada.json').write_text(json.dumps({
    'escenarios':['respaldo_anterior','instalacion_nueva'],
    'respaldo_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),
    'controles':['Restauración o inicialización de originales y tipadas',
                 'Migración 002 aplicada', 'Carga dos veces sin duplicar',
                 'Comparación íntegra de datos y trazabilidad',
                 'Alteración detectada', 'Bases temporales retiradas'],
    'resultado':'Correcto'},ensure_ascii=False,indent=2)+'\n')
