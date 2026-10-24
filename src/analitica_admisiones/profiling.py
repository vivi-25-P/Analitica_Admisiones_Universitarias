"""Perfil estructural reproducible: lee el CSV sin limpiar sus valores."""

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]


def read_original(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        rows = list(reader)
    if any(len(row) != len(headers) for row in rows):
        raise ValueError('Hay filas con un número de columnas diferente al encabezado.')
    return headers, rows


def summarize(headers, rows):
    total = len(rows)
    result = {
        'filas': total,
        'columnas': len(headers),
        'duplicados_exactos_adicionales': total - len(set(map(tuple, rows))),
        'campos': [],
    }
    for i, name in enumerate(headers):
        values = [row[i] for row in rows]
        empty = sum(value == '' for value in values)
        whitespace = sum(value != '' and value.strip() == '' for value in values)
        result['campos'].append({
            'campo': name,
            'vacios_exactos': empty,
            'solo_espacios': whitespace,
            'porcentaje_vacios_exactos': round(100 * empty / total, 2) if total else 0,
            'valores_distintos_no_vacios': len({value for value in values if value != ''}),
        })
    ids = [row[headers.index('registro_id')] for row in rows]
    result['registro_id_distintos'] = len(set(ids))
    result['repeticiones_adicionales_registro_id'] = len(ids) - len(set(ids))
    return result


def numeric_summary(values):
    numbers, invalid = [], Counter()
    for value in values:
        if value == '':
            continue
        try:
            number = Decimal(value)
            if not number.is_finite():
                raise InvalidOperation
        except InvalidOperation:
            invalid[value] += 1
            continue
        numbers.append(number)
    return {
        'vacios': sum(value == '' for value in values),
        'interpretables': len(numbers),
        'no_interpretables': dict(invalid),
        'minimo': str(min(numbers)) if numbers else None,
        'maximo': str(max(numbers)) if numbers else None,
        'promedio': str(sum(numbers) / len(numbers)) if numbers else None,
        'mediana': str(median(numbers)) if numbers else None,
        'nota': 'Estadísticas de valores finitos interpretables, sin excluir atípicos ni validar su exactitud.',
    }


def main():
    meta = json.loads((ROOT / 'docker/origen.json').read_text(encoding='utf-8'))
    source = ROOT / meta['archivo']
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != meta['sha256']:
        raise ValueError('El CSV difiere del original registrado; revisar antes de perfilar.')
    headers, rows = read_original(source)
    if headers != meta['columnas'] or len(rows) != meta['filas']:
        raise ValueError('La estructura del CSV difiere del manifiesto.')
    result = summarize(headers, rows)
    result['sha256_origen'] = digest
    result['numericas'] = {
        name: numeric_summary([row[headers.index(name)] for row in rows])
        for name in ['puntaje_admision', 'valor_matricula_cop']
    }
    out = ROOT / 'reports/exploracion'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'perfil_inicial.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    with (out / 'completitud.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result['campos'][0]))
        writer.writeheader()
        writer.writerows(result['campos'])
    categorical = ['programa', 'modalidad', 'canal_captacion', 'estado_proceso',
                   'documentos_completos', 'ciudad_residencia', 'asesor', 'periodo_academico']
    with (out / 'frecuencias_originales.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['campo', 'valor_original', 'valor_visible_json', 'cantidad', 'porcentaje_filas'])
        for name in categorical:
            counts = Counter(row[headers.index(name)] for row in rows)
            for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
                writer.writerow([name, value, json.dumps(value, ensure_ascii=False), count,
                                 round(100 * count / len(rows), 2)])
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('El archivo original cambió durante el perfilamiento.')
    print(f'Perfil generado: {len(rows)} filas, {len(headers)} columnas. CSV original intacto.')
    print(f'Resultados: {out}')


if __name__ == '__main__':
    main()
