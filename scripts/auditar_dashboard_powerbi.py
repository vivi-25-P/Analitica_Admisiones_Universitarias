"""Auditoría de solo lectura del modelo abierto mediante el MCP local de Power BI."""

import csv
import json
import math
from pathlib import Path
import queue
import re
import statistics
import subprocess
import threading
import time
import tomllib

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/revision_dashboard_powerbi'
OUT.mkdir(parents=True, exist_ok=True)
config = tomllib.loads((ROOT / '.codex/config.toml').read_text())['mcp_servers']['powerbi_modeling']
if '--read-only' not in config['args']:
    raise ValueError('La auditoría requiere MCP en modo de solo lectura')


class Client:
    def __init__(self):
        self.process = subprocess.Popen([config['command'], *config['args']], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
            errors='replace', bufsize=1)
        self.messages, self.errors, self.next_id = queue.Queue(), [], 0
        def stdout():
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    pass
        def stderr():
            for line in self.process.stderr:
                self.errors.append(line.strip())
        threading.Thread(target=stdout, daemon=True).start()
        threading.Thread(target=stderr, daemon=True).start()
        self.request('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
            'clientInfo': {'name': 'auditoria-admisiones-solo-lectura', 'version': '1.0'}})
        self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + '\n')
        self.process.stdin.flush()

    def request(self, method, params):
        self.next_id += 1
        id = self.next_id
        self.send({'jsonrpc': '2.0', 'id': id, 'method': method, 'params': params})
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                msg = self.messages.get(timeout=1)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError('Servidor MCP finalizado')
                continue
            if msg.get('id') == id:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg['result']
        raise TimeoutError(method)

    def call(self, name, request):
        result = self.request('tools/call', {'name': name, 'arguments': {'request': request}})
        values = [json.loads(c['text']) for c in result.get('content', []) if c.get('type') == 'text']
        if result.get('isError'):
            raise RuntimeError(values)
        return values[0]

    def dax(self, query):
        result = self.call('dax_query_operations', {'operation': 'Execute', 'query': query,
            'resultMode': 'Inline', 'maxRows': 5000, 'timeoutSeconds': 30})
        data = result['data']
        if data.get('isTruncated'):
            raise ValueError('Consulta truncada')
        return [{re.sub(r'^.*\[([^]]+)\]$', r'\1', k): v for k, v in row.items()}
                for row in data['rows']]

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()


def csv_rows(name):
    with (ROOT / 'reports/analisis_administrativo/tablas' / name).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


book = load_workbook(ROOT / 'deliverables/BaseUnificada_Entregable.xlsx', read_only=True, data_only=True)
values = iter(book['BaseUnificada'].values)
headers = next(values)
rows = [dict(zip(headers, r)) for r in values]
values = iter(book['Control_Calidad'].values)
headers = next(values)
controls = [dict(zip(headers, r)) for r in values]
values = iter(book['Origen_Registros'].values)
headers = next(values)
origins = [dict(zip(headers, r)) for r in values]
book.close()
origin_by_id = {r['registro_id']: r['fuente_origen'] for r in origins}
channels = csv_rows('canales_comparables.csv')
sens = csv_rows('sensibilidad_49_pares.csv')
scores = [r['puntaje_admision'] for r in rows if r['puntaje_admision'] is not None]
amounts = [r['valor_matricula_cop'] for r in rows if r['valor_matricula_cop'] is not None]
eligible = [r['dias_solicitud_matricula'] for r in controls if r['intervalo_dias_apto_reglas_aplicadas']]
matriculado = sum(r['estado_proceso'] == 'Matriculado' for r in rows)
measures = {
    'Registros': len(rows), 'Matriculado': matriculado, '% Matriculado': matriculado / len(rows),
    '% del total': 1,
    'Códigos por origen': len({(origin_by_id[r['registro_id']], r['aspirante_id']) for r in rows if r['aspirante_id']}),
    'Sin código de aspirante': sum(not r['aspirante_id'] for r in rows),
    'Puntajes informados': len(scores), 'Puntaje mediano': statistics.median(scores),
    'Puntaje promedio': statistics.mean(scores), 'Importes informados': len(amounts),
    'Importe mediano': statistics.median(amounts),
    'Matriculado sin documentos completos': sum(r['estado_proceso'] == 'Matriculado' and r['documentos_completos'] != 'Sí' for r in rows),
    '% sin asesor asignado': sum(r['asesor'] == 'Sin asignar' for r in rows) / len(rows),
    'Registros con fecha apta': sum(bool(r['fecha_solicitud_apta_reglas_aplicadas']) for r in controls),
    'Intervalos aptos': len(eligible), 'Días medianos a matrícula': statistics.median(eligible),
    'Proporción bruta': sum(float(r['proporcion_bruta_soporte_pct']) for r in channels) / 100,
    'Proporción con pesos comunes': sum(float(r['proporcion_estandarizada_descriptiva_pct']) for r in channels) / 100,
    'Brecha bruta entre canales': max(float(r['proporcion_bruta_soporte_pct']) for r in channels) - min(float(r['proporcion_bruta_soporte_pct']) for r in channels),
    'Brecha con pesos comunes': max(float(r['proporcion_estandarizada_descriptiva_pct']) for r in channels) - min(float(r['proporcion_estandarizada_descriptiva_pct']) for r in channels),
    'Registros comparables': sum(int(r['registros_soporte_comun']) for r in channels),
    'Cambio máximo con 49 pares': max(abs(float(r['diferencia_matriculado_pp'])) for r in sens
        if r['grupo_pequeno_base'].lower() == 'false'),
}
report = {'fecha': '2026-10-30', 'solo_lectura': True, 'medidas': [], 'grupos': [], 'pruebas_filtros': []}
client = Client()
try:
    instances = client.call('connection_operations', {'operation': 'ListLocalInstances'})['data']
    matches = [r for r in instances if r['parentWindowTitle'] == 'DashboardAdmisiones']
    if len(matches) != 1:
        raise ValueError('Se requiere una instancia única abierta de DashboardAdmisiones')
    client.call('connection_operations', {'operation': 'Connect', 'connectionString': matches[0]['connectionString']})
    query = 'EVALUATE ROW(' + ', '.join(f'"{name}", [{name}]' for name in measures) + ')'
    actual = client.dax(query)[0]
    for name, expected in measures.items():
        value = actual.get(name)
        report['medidas'].append({'medida': name, 'valor': value, 'esperado': expected,
            'coincide': value is not None and math.isclose(value, expected, rel_tol=1e-7, abs_tol=1e-5)})
    for dimension, label, field in [
        ('DimPrograma', 'Programa', 'programa'), ('DimCanal', 'Canal', 'canal_captacion'),
        ('DimCiudad', 'Ciudad', 'ciudad_residencia'), ('DimPeriodo', 'Periodo', 'periodo_academico'),
        ('DimModalidad', 'Modalidad', 'modalidad'), ('DimFuente', 'Fuente', 'fuente_origen')]:
        actual = client.dax(f'EVALUATE SUMMARIZECOLUMNS({dimension}[{label}], "Registros", [Registros], "Matriculado", [Matriculado])')
        expected = {}
        for r in rows:
            key = origin_by_id[r['registro_id']] if field == 'fuente_origen' else r[field]
            key = key or 'Sin información'
            count = expected.setdefault(str(key), [0, 0])
            count[0] += 1
            count[1] += r['estado_proceso'] == 'Matriculado'
        for r in actual:
            e = expected[str(r[label])]
            report['grupos'].append({'dimension': dimension, 'categoria': r[label],
                'registros': r['Registros'], 'matriculado': r.get('Matriculado') or 0,
                'coincide': [r['Registros'], r.get('Matriculado') or 0] == e})
    for state in ['Matriculado', 'Admitido', 'Documentación pendiente']:
        query = f'EVALUATE CALCULATETABLE(ROW("Registros", [Registros], "Matriculado", [Matriculado], "Porcentaje", [% Matriculado]), DimEstado[Estado] = "{state}")'
        a = client.dax(query)[0]
        report['pruebas_filtros'].append({'filtro': 'Estado: ' + state, 'actual': a,
            'porcentaje_esperado_segun_plan': matriculado / len(rows),
            'requiere_ajuste': not math.isclose(a['Porcentaje'], matriculado / len(rows))})
    for advisor in sorted({r['asesor'] for r in rows if r['asesor']}):
        query = f'EVALUATE CALCULATETABLE(ROW("Registros", [Registros], "SinAsesor", [% sin asesor asignado]), DimAsesor[Asesor] = "{advisor}")'
        a = client.dax(query)[0]
        expected = 1 if advisor == 'Sin asignar' else 0
        report['pruebas_filtros'].append({'filtro': 'Asesor: ' + advisor, 'actual': a,
            'porcentaje_esperado_dentro_grupo': expected,
            'requiere_ajuste': not math.isclose(a['SinAsesor'] or 0, expected)})
    actual = client.dax('EVALUATE SUMMARIZECOLUMNS(DimCiudad[Ciudad], DimPrograma[Programa], '
        'DimModalidad[Modalidad], DimPeriodo[Periodo], "Registros", [Registros], "Matriculado", [Matriculado])')
    expected = {}
    for r in rows:
        key = (r['ciudad_residencia'], r['programa'] or 'Sin información', r['modalidad'], r['periodo_academico'])
        count = expected.setdefault(key, [0, 0])
        count[0] += 1
        count[1] += r['estado_proceso'] == 'Matriculado'
    report['segmentos'] = []
    for r in actual:
        key = (r['Ciudad'], r['Programa'], r['Modalidad'], r['Periodo'])
        report['segmentos'].append({**r, 'coincide': [r['Registros'], r.get('Matriculado') or 0] == expected[key]})
    definitions = [
        ('DimPrograma', 'Programa', 'programa'), ('DimCanal', 'Canal', 'canal_captacion'),
        ('DimCiudad', 'Ciudad', 'ciudad_residencia'), ('DimPeriodo', 'Periodo', 'periodo_academico'),
        ('DimModalidad', 'Modalidad', 'modalidad'), ('DimFuente', 'Fuente', 'fuente_origen'),
        ('DimEstado', 'Estado', 'estado_proceso'), ('DimAsesor', 'Asesor', 'asesor'),
        ('DimFecha', 'Fecha', 'fecha_solicitud'),
    ]
    report['dimensiones'] = client.dax('EVALUATE UNION(' + ', '.join(
        f'ROW("Dimension", "{dim}", "Filas", COUNTROWS({dim}), '
        f'"Claves", DISTINCTCOUNTNOBLANK({dim}[{label}]), '
        f'"SinCorrespondencia", COUNTROWS(EXCEPT(FILTER(VALUES(FactRegistros[{field}]), '
        f'NOT ISBLANK(FactRegistros[{field}])), VALUES({dim}[{label}]))))'
        for dim, label, field in definitions) + ')')
    for r in report['dimensiones']:
        # COUNTROWS devuelve BLANK cuando EXCEPT no encuentra correspondencias ausentes.
        r['SinCorrespondencia'] = r['SinCorrespondencia'] or 0
        r['correcta'] = r['Filas'] == r['Claves'] and r['SinCorrespondencia'] == 0
    proposed_mat = ('DIVIDE(CALCULATE([Registros], REMOVEFILTERS(DimEstado), '
        'REMOVEFILTERS(FactRegistros[estado_proceso]), DimEstado[Estado] = "Matriculado"), '
        'CALCULATE([Registros], REMOVEFILTERS(DimEstado), REMOVEFILTERS(FactRegistros[estado_proceso])))')
    proposed_advisor = ('DIVIDE(COALESCE(CALCULATE([Registros], '
        'KEEPFILTERS(DimAsesor[Asesor] = "Sin asignar")), 0), [Registros])')
    report['propuestas_no_aplicadas'] = {'matriculado': proposed_mat, 'sin_asesor': proposed_advisor}
    states = client.dax('DEFINE MEASURE FactRegistros[PropuestaMat] = ' + proposed_mat
        + ' EVALUATE SUMMARIZECOLUMNS(DimEstado[Estado], "Valor", [PropuestaMat])')
    advisors = client.dax('DEFINE MEASURE FactRegistros[PropuestaAsesor] = ' + proposed_advisor
        + ' EVALUATE SUMMARIZECOLUMNS(DimAsesor[Asesor], "Valor", [PropuestaAsesor])')
    report['validacion_propuestas'] = {
        'estados': states, 'asesores': advisors,
        'matriculado_correcto': all(math.isclose(r['Valor'], matriculado/len(rows)) for r in states),
        'asesor_correcto': all(math.isclose(r['Valor'], 1 if r['Asesor'] == 'Sin asignar' else 0) for r in advisors),
    }
    for name in ['MEASURES', 'RELATIONSHIPS', 'TABLES']:
        try:
            metadata = client.dax('EVALUATE INFO.VIEW.' + name + '()')
            (OUT / ('modelo_' + name.lower() + '.json')).write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        except Exception as exc:
            report.setdefault('metadatos_no_disponibles', {})[name] = str(exc)
    report['resumen'] = {
        'medidas_comprobadas': len(report['medidas']),
        'medidas_basales_correctas': sum(r['coincide'] for r in report['medidas']),
        'grupos_comprobados': len(report['grupos']),
        'grupos_correctos': sum(r['coincide'] for r in report['grupos']),
        'filtros_con_ajustes': sum(r['requiere_ajuste'] for r in report['pruebas_filtros']),
        'segmentos_comprobados': len(report['segmentos']),
        'segmentos_correctos': sum(r['coincide'] for r in report['segmentos']),
        'dimensiones_correctas': sum(r['correcta'] for r in report['dimensiones']),
        'propuestas_validadas_sin_modificar_modelo': all(report['validacion_propuestas'][k]
            for k in ['matriculado_correcto', 'asesor_correcto']),
    }
finally:
    client.close()
(OUT / 'auditoria_modelo.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report['resumen'], ensure_ascii=False, indent=2))
print(json.dumps(report['pruebas_filtros'], ensure_ascii=False, indent=2))
