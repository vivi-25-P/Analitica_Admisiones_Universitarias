"""Crea una proyección tipada y reversible, conservando todos los valores de origen."""
import collections
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORMATS = [
    (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d'),
    (r'\d{4}/\d{2}/\d{2}', '%Y/%m/%d'),
    (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),
    (r'\d{2}-\d{2}-\d{4}', '%m-%d-%Y'),
    (r'\d{2}-[A-Za-z]{3}-\d{4}', '%d-%b-%Y'),
]
NUMERIC = {'puntaje_admision', 'valor_matricula_cop'}
DATES = {'fecha_solicitud', 'fecha_matricula'}


def represent(column, value):
    if column not in NUMERIC | DATES:
        return value, None
    if value == '':
        return None, {'columna': column, 'valor': value, 'motivo': 'vacio_original'}
    if column in NUMERIC:
        try:
            parsed = Decimal(value)
            if parsed.is_finite():
                return str(parsed), None
        except InvalidOperation:
            pass
        return None, {'columna': column, 'valor': value, 'motivo': 'texto_sin_representacion_numerica'}
    if value == 'No aplica':
        return None, {'columna': column, 'valor': value, 'motivo': 'no_aplica_original'}
    for pattern, fmt in FORMATS:
        if re.fullmatch(pattern, value):
            try:
                return datetime.strptime(value, fmt).date().isoformat(), None
            except ValueError:
                break
    return None, {'columna': column, 'valor': value, 'motivo': 'fecha_sin_interpretacion'}


def execute(sql):
    result = subprocess.run(
        ['docker','compose','exec','-T','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1',
         '-U','analista','-d','admisiones'],
        cwd=ROOT, input=sql.encode('utf-8'), stdout=subprocess.PIPE, check=True,
    )
    return result.stdout.decode('utf-8')


def verify_source(headers, rows, digest):
    # La proyección se construye desde el CSV para mantener su posición reproducible.
    # Primero se prueba que la tabla original representa exactamente esas mismas filas.
    content = execute("COPY public.admisiones_original TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8');")
    original = list(csv.reader(io.StringIO(content, newline='')))
    if original[0] != headers or collections.Counter(map(tuple, original[1:])) != collections.Counter(map(tuple, rows)):
        raise ValueError('La tabla original no coincide con el CSV. No se aplicarán cambios.')
    assert hashlib.sha256((ROOT / json.loads((ROOT/'docker/origen.json').read_text())['archivo']).read_bytes()).hexdigest()==digest


def main():
    meta = json.loads((ROOT/'docker/origen.json').read_text())
    path = ROOT/meta['archivo']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != meta['sha256']:
        raise ValueError('El archivo original cambió; no se aplicará el tipado.')
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle);headers=next(reader);rows=list(reader)
    assert headers==meta['columnas'] and len(rows)==meta['filas']
    assert all(len(row)==len(headers) for row in rows)
    verify_source(headers, rows, digest)
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\n')
    counts = collections.Counter()
    for position, values in enumerate(rows, 2):
        original = dict(zip(headers, values, strict=True))
        typed, notes = [], []
        for col, value in original.items():
            parsed, note = represent(col, value)
            typed.append(parsed)
            if parsed is not None: counts[col]+=1
            if note: notes.append(note)
        writer.writerow([position,digest,*typed,json.dumps(original,ensure_ascii=False),json.dumps(notes,ensure_ascii=False)])
    text_columns = ', '.join(col for col in headers if col not in NUMERIC | DATES)
    migration = (ROOT/'sql/migrations/001_admisiones_tipadas.sql').read_text()
    sql = 'BEGIN;\nSELECT pg_advisory_xact_lock(1740040);\n' + migration
    sql += '\nCREATE TEMP TABLE entrada_tipado (LIKE public.admisiones_tipadas INCLUDING DEFAULTS) ON COMMIT DROP;\n'
    sql += f'COPY entrada_tipado FROM STDIN WITH (FORMAT CSV, FORCE_NOT_NULL ({text_columns}));\n'
    sql += buffer.getvalue() + chr(92) + ".\n"
    sql += '''
INSERT INTO public.admisiones_tipadas
SELECT * FROM entrada_tipado WHERE NOT EXISTS (SELECT 1 FROM public.admisiones_tipadas);
DO $$ BEGIN
    IF EXISTS (
        (SELECT * FROM entrada_tipado EXCEPT ALL SELECT * FROM public.admisiones_tipadas)
        UNION ALL
        (SELECT * FROM public.admisiones_tipadas EXCEPT ALL SELECT * FROM entrada_tipado)
    ) THEN RAISE EXCEPTION 'La proyección existente no coincide con la entrada. Se revierte la transacción.';
    END IF;
END $$;
COMMIT;
'''
    execute(sql)
    # Reconstrucción de cada una de las 15 columnas a partir de sus valores originales.
    literals = ', '.join("datos_originales ->> '"+col+"'" for col in headers)
    reconstructed = execute(f'COPY (SELECT {literals} FROM public.admisiones_tipadas ORDER BY fila_origen_csv) TO STDOUT WITH (FORMAT CSV);')
    restored = list(csv.reader(io.StringIO(reconstructed,newline='')))
    if restored != rows:
        raise ValueError('La reconstrucción del origen difiere del CSV.')
    verify_source(headers, rows, digest)
    report = {
        'tabla': 'public.admisiones_tipadas', 'filas': len(rows), 'columnas_fuente': len(headers),
        'origen_sha256':digest, 'original_reconstruido_por_fila':True,
        'tabla_original_verificada':True,
        'valores_representados_por_columna':dict(counts),
        'reglas_fecha': ['AAAA-MM-DD','AAAA/MM/DD','DD/MM/AAAA','MM-DD-AAAA','DD-Mmm-AAAA (mes en inglés)'],
        'alcance':'Solo representación de tipos. No elimina filas, unifica categorías, imputa ni corrige valores.',
        'valores_no_representables':'NULL en la proyección; valor íntegro en datos_originales y motivo en observaciones_tipado.',
    }
    output = ROOT/'reports/estructura';output.mkdir(parents=True,exist_ok=True)
    (output/'verificacion_tipado.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
