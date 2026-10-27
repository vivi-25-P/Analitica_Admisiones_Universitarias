"""Carga la entrega validada en PostgreSQL sin modificar las tablas anteriores."""

from datetime import date, datetime
from decimal import Decimal
import csv
import hashlib
import json
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def sha(content):
    return hashlib.sha256(content).hexdigest()


def normalized(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def prepare(root=ROOT):
    from openpyxl import load_workbook
    summary = json.loads((root / 'reports/limpieza/ultima_entrega.json').read_text())
    public = root / summary['datos_salida'] / 'entregable'
    excel = root / summary['entregable']
    csv_path = public / 'BaseUnificada_Entregable.csv'
    if sha(excel.read_bytes()) != summary['archivos_entregables'][summary['entregable']]:
        raise ValueError('El Excel cambió respecto a la entrega validada')
    rows = []
    columns = list(read_csv(csv_path)[0])
    for line in (public / 'BaseUnificada_Entregable.jsonl').read_text().splitlines():
        r = json.loads(line, parse_float=Decimal)
        for c in ['fecha_solicitud', 'fecha_matricula']:
            if r[c] is not None:
                r[c] = date.fromisoformat(r[c])
        rows.append(r)
    expected_csv = [{c: '' if r[c] is None else str(normalized(r[c])) for c in columns} for r in rows]
    if expected_csv != read_csv(csv_path):
        raise ValueError('CSV y JSONL finales no coinciden')
    book = load_workbook(excel, read_only=True, data_only=True)
    main = list(book['BaseUnificada'].values)
    if list(main[0]) != columns:
        raise ValueError('Las columnas del Excel no coinciden con la base final')
    if [[normalized(v) for v in row] for row in main[1:]] != [
        [normalized(float(r[c])) if isinstance(r[c], Decimal) else normalized(r[c]) for c in columns] for r in rows
    ]:
        raise ValueError('Excel y JSONL no coinciden en todos sus valores')
    sheets = {}
    for sheet in book:
        if sheet.title == 'BaseUnificada':
            continue
        values = iter(sheet.values)
        headers = next(values)
        sheets[sheet.title] = [{c: normalized(v) for c, v in zip(headers, row)} for row in values]
    book.close()
    audit = root / summary['auditoria']
    ledger = read_csv(audit / 'disposicion_5640_entradas.csv')
    prepared = root / 'data/prepared/taller_2/BaseUnificada.csv'
    originals = [
        root / 'data/raw/Caso2_Admisiones_Universitarias.csv',
        root / 'data/raw/taller_2/Caso2 CRM Admisiones.csv',
        root / 'data/raw/taller_2/Caso2 Programas.csv',
        root / 'data/exports/taller_2/Caso2_Oracle_Admisiones.csv', prepared,
    ]
    for manifest_name in ['docs/referencias/integridad.json', 'docs/referencias/taller_2/integridad.json']:
        for name, info in json.loads((root / manifest_name).read_text()).items():
            expected = info['sha256'] if isinstance(info, dict) else info
            if sha((root / name).read_bytes()) != expected:
                raise ValueError('Una fuente de referencia cambió: ' + name)
    frozen_meta = json.loads((root / 'data/prepared/taller_2/BaseUnificada.metadata.json').read_text())
    for name, info in frozen_meta['archivos'].items():
        if sha((prepared.parent / name).read_bytes()) != info['sha256']:
            raise ValueError('La entrada congelada cambió')
    if sha((root / frozen_meta['libro_origen']).read_bytes()) != frozen_meta['sha256_libro_origen']:
        raise ValueError('El libro de integración congelado cambió')
    oracle_meta = root / 'data/exports/taller_2/Caso2_Oracle_Admisiones.metadata.json'
    oracle = json.loads(oracle_meta.read_text())
    if sha((root / oracle['archivo']).read_bytes()) != oracle['sha256']:
        raise ValueError('La exportación Oracle cambió respecto a su captura')
    artifacts = set(originals + [excel, csv_path, public / 'BaseUnificada_Entregable.jsonl',
                               root / 'data/BaseUnificada_Manejo.xlsx',
                               root / 'sql/fuentes/taller_2/caso2.sql',
                               root / 'data/prepared/taller_2/BaseUnificada.metadata.json'])
    # Conservar los controles por celda de las etapas vigentes como archivos íntegros.
    for pointer in sorted((root / 'reports/limpieza').glob('ultima*.json')):
        payload = json.loads(pointer.read_text())
        artifacts.add(pointer)
        if payload.get('auditoria'):
            artifacts.update(p for p in (root / payload['auditoria']).iterdir() if p.is_file())
    for folder in [root / 'config/limpieza', audit]:
        artifacts.update(p for p in folder.iterdir() if p.is_file())
    artifacts.add(root / 'scripts/cargar_base_unificada.py')
    artifacts.add(oracle_meta)
    artifacts.add(root / 'sql/migrations/002_base_unificada_analitica.sql')
    blobs = {str(p.relative_to(root)): p.read_bytes() for p in sorted(artifacts)}
    manifest = {name: sha(content) for name, content in blobs.items()}
    load_id = sha(json.dumps(manifest, sort_keys=True).encode())
    if len(rows) != 5500 or len(ledger) != 5640 or len(columns) != 18:
        raise ValueError('Cantidades inesperadas en la entrega')
    if len({r['registro_id'] for r in rows}) != len(rows):
        raise ValueError('Códigos de registro repetidos en la salida')
    return dict(summary=summary, public=public, excel=excel, csv_path=csv_path, rows=rows,
                columns=columns, sheets=sheets, ledger=ledger, prepared=prepared,
                originals=originals, blobs=blobs, manifest=manifest, load_id=load_id)


def legacy_fingerprint(cursor):
    result = {}
    for name in ['admisiones_original', 'admisiones_tipadas']:
        cursor.execute(sql.SQL('SELECT count(*), md5(string_agg(to_jsonb(t)::text, E\'\\n\' ORDER BY to_jsonb(t)::text)) FROM public.{} t').format(sql.Identifier(name)))
        result[name] = cursor.fetchone()
    return result


def verify(cursor, data):
    load = data['load_id']
    checks = {}
    cursor.execute('SELECT carga_id FROM trazabilidad.publicacion_actual')
    checks['publicacion_correcta'] = cursor.fetchone() == (load,)
    cursor.execute('SELECT * FROM analitica.base_unificada ORDER BY registro_id')
    checks['18_columnas_en_orden'] = [c.name for c in cursor.description] == data['columns']
    expected = sorted([tuple(r[c] for c in data['columns']) for r in data['rows']], key=lambda r: r[0])
    checks['5500_filas_todos_los_valores_iguales'] = cursor.fetchall() == expected
    cursor.execute('SELECT id_fila_entrada, registro_id_salida, fuente, detalle FROM trazabilidad.destinos WHERE carga_id=%s ORDER BY id_fila_entrada', (load,))
    checks['5640_destinos_iguales'] = cursor.fetchall() == sorted([
        (r['id_fila_entrada'], r['registro_id_salida'], r['fuente'], r) for r in data['ledger']])
    cursor.execute('SELECT hoja,posicion,valores FROM trazabilidad.hojas WHERE carga_id=%s ORDER BY hoja,posicion', (load,))
    expected_sheets = sorted((name, pos, row) for name, rows in data['sheets'].items() for pos, row in enumerate(rows, 2))
    checks['9_hojas_auxiliares_iguales'] = cursor.fetchall() == expected_sheets
    cursor.execute('SELECT ruta, archivo_sha256, contenido FROM trazabilidad.archivos_ejecucion JOIN fuentes.archivos ON sha256=archivo_sha256 WHERE carga_id=%s', (load,))
    actual = cursor.fetchall()
    checks['archivos_completos_y_huellas'] = len(actual) == len(data['blobs']) and all(
        bytes(content) == data['blobs'][path] and sha(bytes(content)) == digest for path, digest, content in actual)
    for path in data['originals']:
        digest = data['manifest'][str(path.relative_to(ROOT))]
        cursor.execute('SELECT valores_originales FROM fuentes.filas WHERE archivo_sha256=%s ORDER BY numero_fila', (digest,))
        checks['fuente_' + path.name] = [r[0] for r in cursor.fetchall()] == read_csv(path)
    cursor.execute('SELECT count(*), count(*) FILTER (WHERE importe_recuperado_crm), count(*) FILTER (WHERE fuente_origen=\'Oracle\') FROM analitica.origen_registros')
    checks['origen_recuperacion_y_oracle'] = cursor.fetchone() == (5500, 13, 500)
    cursor.execute('SELECT count(*), count(*) FILTER (WHERE intervalo_dias_apto_reglas_aplicadas), count(*) FILTER (WHERE fecha_solicitud_apta_reglas_aplicadas) FROM analitica.control_calidad')
    checks['controles_temporales'] = cursor.fetchone() == (5500, 1035, 5320)
    cursor.execute('SELECT count(*) FROM analitica.control_economico e JOIN analitica.base_unificada b USING(registro_id) WHERE e."importe_final_COP"=b.valor_matricula_cop')
    checks['100_importes_crm_conciliados'] = cursor.fetchone() == (100,)
    if not all(checks.values()):
        raise ValueError('No pasaron los controles de carga: ' + ', '.join(k for k,v in checks.items() if not v))
    return checks


def cargar(root=ROOT, connection=None, guardar_reporte=True):
    data = prepare(root)
    env = dotenv_values(root / '.env')
    owned = connection is None
    conn = connection or psycopg.connect(host='127.0.0.1', port=int(env.get('POSTGRES_PORT',5433)),
                                        dbname='admisiones', user='analista',
                                        password=env['POSTGRES_PASSWORD'], connect_timeout=10)
    try:
        with conn.transaction(), conn.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(1740041)')
            before = legacy_fingerprint(cursor)
            cursor.execute('SELECT manifiesto FROM trazabilidad.ejecuciones WHERE carga_id=%s', (data['load_id'],))
            existing = cursor.fetchone()
            if existing:
                if existing[0] != data['manifest']:
                    raise ValueError('Una carga existente tiene otro manifiesto')
                action = 'Carga existente verificada, sin duplicar registros'
            else:
                for path, content in data['blobs'].items():
                    cursor.execute('INSERT INTO fuentes.archivos VALUES (%s,%s) ON CONFLICT DO NOTHING',
                                   (data['manifest'][path], content))
                for path in data['originals']:
                    digest = data['manifest'][str(path.relative_to(root))]
                    cursor.executemany('INSERT INTO fuentes.filas VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                        [(digest, n, Jsonb(row)) for n,row in enumerate(read_csv(path),2)])
                cursor.execute('INSERT INTO trazabilidad.ejecuciones(carga_id,ejecucion_limpieza,excel_sha256,csv_sha256,manifiesto) VALUES (%s,%s,%s,%s,%s)',
                    (data['load_id'], data['summary']['id_ejecucion'],
                     data['manifest'][str(data['excel'].relative_to(root))],
                     data['manifest'][str(data['csv_path'].relative_to(root))], Jsonb(data['manifest'])))
                cursor.executemany('INSERT INTO trazabilidad.archivos_ejecucion VALUES (%s,%s,%s)',
                    [(data['load_id'], path, digest) for path,digest in data['manifest'].items()])
                with cursor.copy(sql.SQL('COPY analitica.registros ({}) FROM STDIN').format(
                    sql.SQL(',').join(map(sql.Identifier,['carga_id',*data['columns']])))) as copy:
                    for row in data['rows']:
                        copy.write_row([data['load_id'],*[row[c] for c in data['columns']]])
                with cursor.copy('COPY trazabilidad.hojas FROM STDIN') as copy:
                    for name, rows in data['sheets'].items():
                        for pos,row in enumerate(rows,2):
                            copy.write_row((data['load_id'],name,pos,Jsonb(row)))
                prepared_sha = data['manifest'][str(data['prepared'].relative_to(root))]
                cursor.executemany('INSERT INTO trazabilidad.destinos VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    [(data['load_id'],r['id_fila_entrada'],prepared_sha,int(r['id_fila_entrada'][2:])+1,
                      r['registro_id_salida'],r['fuente'],Jsonb(r)) for r in data['ledger']])
                action = 'Nueva carga publicada con trazabilidad'
            cursor.execute('INSERT INTO trazabilidad.publicacion_actual VALUES (true,%s) ON CONFLICT(unico) DO UPDATE SET carga_id=EXCLUDED.carga_id', (data['load_id'],))
            checks = verify(cursor,data)
            checks['tablas_anteriores_intactas'] = before == legacy_fingerprint(cursor)
            if not checks['tablas_anteriores_intactas']:
                raise ValueError('Las tablas anteriores cambiaron. Se revierte la carga')
        report = {'carga_id':data['load_id'],'accion':action,'registros':5500,'columnas':18,
                  'destinos_entrada':5640,'archivos_conservados':len(data['blobs']),
                  'controles':checks,'tablas_anteriores':{k:{'filas':v[0],'huella_sql':v[1]} for k,v in before.items()},
                  'excel':str(data['excel'].relative_to(root)),
                  'sha256_excel':data['manifest'][str(data['excel'].relative_to(root))],
                  'vista_powerbi':'analitica.base_unificada'}
        if guardar_reporte:
            (root/'reports/limpieza/carga_postgresql.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(action)
        print('PostgreSQL y Excel: 5.500 registros y 18 columnas iguales. Destinos: 5.640.')
        print('Controles correctos:',len(checks))
        return report
    finally:
        if owned:
            conn.close()


if __name__ == '__main__':
    cargar()
