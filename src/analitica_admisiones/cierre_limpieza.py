"""Etapas L05 a L09: revisión, consolidación exacta y cierre con pendientes explícitos."""
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
from statistics import median, quantiles
import unicodedata
from zoneinfo import ZoneInfo

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(value):
    text = re.sub(r'\s+', ' ', str(value or '').strip()).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def serial(value):
    if value is None:
        return ''
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return format(value, 'f') if isinstance(value, Decimal) else str(value)


def json_literal(value):
    if isinstance(value, Decimal):
        assert value.is_finite()
        return format(value, 'f')
    if isinstance(value, date):
        return json.dumps(value.isoformat())
    return json.dumps(value, ensure_ascii=False)


class CierreLimpieza:
    def __init__(self, root, frame, original, ids, origen, l04_alerts, l04_summary, code_sha):
        self.root = Path(root)
        self.headers = list(frame.columns)
        self.original = original.to_dict('records')
        self.rows = frame.to_dict('records')
        self.ids = list(ids)
        self.by_id = dict(zip(self.ids, self.rows))
        self.raw_by_id = dict(zip(self.ids, self.original))
        self.origin = {r['id_fila_entrada']: r for r in origen.to_dict('records')}
        self.rules_path = self.root / 'config/limpieza/cierre_v1.json'
        self.rules = json.loads(self.rules_path.read_text())
        self.module_sha = sha(__file__)
        self.rule_sha = sha(self.rules_path)
        self.code_sha = code_sha
        self.l04_summary = l04_summary
        self.l04_alerts = l04_alerts.to_dict('records')
        self.run_id = f"{self.rules['version']}_{l04_summary['archivos_datos']['BaseUnificada_Tipada.jsonl'][:10]}_{self.rule_sha[:8]}_{self.module_sha[:8]}_{code_sha[:8]}"
        self.audit = self.root / 'reports/limpieza/ejecuciones' / self.run_id
        self.audit.mkdir(parents=True, exist_ok=True)
        self.mapping = {i: i for i in self.ids}
        self.kept = list(self.ids)
        self.steps = []
        self.metrics = {}
        self.issues = []
        self.decisions = []
        self._issue_keys = set()
        self.reference = date.fromisoformat(self.rules['fecha_referencia_revision'])

    def write(self, filename, rows, headers=None):
        rows = list(rows)
        headers = headers or (list(rows[0]) if rows else ['sin_casos'])
        with (self.audit / filename).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)

    def step(self, stage, before, after, action, changed=0, consolidated=0):
        self.steps.append({'id_ejecucion': self.run_id, 'paso': stage, 'accion': action,
                           'filas_antes': before, 'filas_despues': after,
                           'celdas_modificadas': changed, 'repeticiones_consolidadas': consolidated,
                           'filas_excluidas': 0, 'filas_generadas': 0})
        self.write('registro_pasos.csv', self.steps)

    def issue(self, ident, column, kind, detail, decision):
        item_key = (ident, column, kind, detail)
        if item_key in self._issue_keys:
            return
        self._issue_keys.add(item_key)
        self.issues.append({'id_incidencia': f'INC{len(self.issues)+1:06d}',
                           'id_fila_entrada': ident, 'id_registro_salida': self.mapping[ident],
                           'registro_id': self.by_id[ident]['registro_id'],
                           'fuente': self.origin[ident]['origen_sistema'], 'columna': column,
                           'tipo': kind, 'detalle': detail, 'decision': decision, 'estado': 'pendiente'})

    def l05(self, manejo_path, integration_code):
        book = load_workbook(manejo_path, read_only=True, data_only=True)
        values = list(book[self.rules['catalogo_hoja']].values)
        book.close()
        catalog = [dict(zip(values[0], row)) for row in values[1:]]
        index = {}
        for row in catalog:
            k = key(row['programa'])
            assert k and k not in index, 'Catálogo no único'
            index[k] = row
        assert len(index) == 7
        self.catalog = catalog
        evidence = []
        mismatch = []
        for ident, row, raw in zip(self.ids, self.rows, self.original):
            candidate = index.get(key(row['programa']))
            attrs = ['facultad', 'duracion_semestres', 'nivel_formacion']
            correct = all(row[c] == candidate[c] for c in attrs) if candidate else all(row[c] is None for c in attrs)
            modality_diff = bool(candidate and key(candidate['modalidad']) != key(row['modalidad']))
            evidence.append({'id_fila_entrada': ident, 'programa_entrada': raw['programa'],
                             'programa_estandarizado': row['programa'],
                             'programa_catalogo_reconstruido': candidate['programa'] if candidate else '',
                             'regla': 'clave normalizada única, sin nueva coincidencia difusa',
                             'atributos_coinciden': correct, 'modalidad_solicitud': row['modalidad'],
                             'modalidad_catalogo': candidate['modalidad'] if candidate else '',
                             'modalidades_diferentes': modality_diff,
                             'nombre_fuzzy_original_recuperado': False,
                             'estado': 'reproducción compatible' if candidate and correct else 'sin programa identificado' if not candidate and correct else 'revisar atributos'})
            if not candidate:
                self.issue(ident, 'programa', 'programa_sin_identificar', 'Sin correspondencia útil con catálogo de trabajo', 'D01')
            if not correct:
                mismatch.append(ident)
                self.issue(ident, 'facultad,duracion_semestres,nivel_formacion', 'atributos_catalogo_discrepantes', 'Salida distinta de catálogo de trabajo', 'D02')
        self.write('L05_correspondencias_programas.csv', evidence)
        self.write('L05_catalogo_trabajo.csv', catalog)
        (self.audit / 'L05_integracion_powerquery.m').write_text(integration_code, encoding='utf8')
        self.metrics['L05'] = {'filas_revisadas': len(evidence), 'programas_catalogo': len(catalog),
                               'con_correspondencia_reproducida': sum(bool(r['programa_catalogo_reconstruido']) for r in evidence),
                               'sin_correspondencia': sum(not r['programa_catalogo_reconstruido'] for r in evidence),
                               'atributos_discrepantes': len(mismatch),
                               'modalidades_diferentes_catalogo': sum(r['modalidades_diferentes'] for r in evidence),
                               'nombre_fuzzy_historico_disponible': False}
        self.step('L05', len(self.ids), len(self.ids), 'Reproducir catálogo de trabajo y comprobar atributos; conservar modalidad de solicitud')
        return self.metrics['L05']

    def l06(self):
        groups = defaultdict(list)
        for ident in self.ids:
            # La igualdad tipada sola no borra diferencias de formato o motivo original.
            sig = (self.origin[ident]['origen_sistema'],
                   tuple(self.raw_by_id[ident][c] for c in self.headers),
                   tuple(self.by_id[ident][c] for c in self.headers))
            groups[sig].append(ident)
        consolidated = []
        for members in groups.values():
            representative = min(members)
            for ident in members:
                self.mapping[ident] = representative
                if len(members) > 1:
                    consolidated.append({'id_grupo': representative, 'id_fila_entrada': ident,
                                         'id_registro_salida': representative, 'fuente': self.origin[ident]['origen_sistema'],
                                         'accion': 'representante' if ident == representative else 'consolidada',
                                         'regla': '18 columnas originales y tipadas iguales, misma fuente; menor BU técnico'})
        self.kept = [i for i in self.ids if self.mapping[i] == i]
        self.write('L06_grupos_exactos.csv', consolidated,
                   ['id_grupo', 'id_fila_entrada', 'id_registro_salida', 'fuente', 'accion', 'regla'])
        # Los incidentes L05 siguen ligados a sus entradas incluso después de consolidar.
        for issue in self.issues:
            issue['id_registro_salida'] = self.mapping[issue['id_fila_entrada']]
        self.metrics['L06'] = {'grupos_exactos': len({r['id_grupo'] for r in consolidated}),
                               'filas_en_grupos': len(consolidated),
                               'repeticiones_consolidadas': len(self.ids)-len(self.kept),
                               'filas_salida': len(self.kept), 'regla_representante': 'menor índice BU, sin precedencia administrativa'}
        self.step('L06', len(self.ids), len(self.kept), 'Consolidar exactos preservando cada entrada en su representante', consolidated=len(self.ids)-len(self.kept))
        return self.metrics['L06']

    def l07(self):
        groups = defaultdict(list)
        sources = defaultdict(list)
        for ident in self.kept:
            row = self.by_id[ident]
            sources[self.origin[ident]['origen_sistema']].append(ident)
            if row['registro_id']:
                groups[row['registro_id']].append(ident)
        repeated = []
        pairs = []
        for reg, members in groups.items():
            if len(members) < 2:
                continue
            for ident in members:
                repeated.append({'registro_id': reg, 'id_fila_entrada': ident, 'fuente': self.origin[ident]['origen_sistema'], 'filas_grupo': len(members)})
                self.issue(ident, 'registro_id', 'identificador_compartido_con_diferencias', f'{reg}: {len(members)} filas conservadas', 'D03')
            for a, b in itertools.combinations(members, 2):
                cols = [c for c in self.headers if self.by_id[a][c] != self.by_id[b][c]]
                pairs.append({'registro_id': reg, 'fila_a': a, 'fuente_a': self.origin[a]['origen_sistema'],
                              'fila_b': b, 'fuente_b': self.origin[b]['origen_sistema'],
                              'columnas_distintas': ', '.join(cols), 'diferencias': json.dumps({c: [serial(self.by_id[a][c]), serial(self.by_id[b][c])] for c in cols}, ensure_ascii=False)})
        self.write('L07_identificadores_repetidos.csv', repeated, ['registro_id', 'id_fila_entrada', 'fuente', 'filas_grupo'])
        self.write('L07_diferencias_por_par.csv', pairs, ['registro_id','fila_a','fuente_a','fila_b','fuente_b','columnas_distintas','diferencias'])
        principal = defaultdict(list)
        for ident in sources['Principal']:
            principal[self.by_id[ident]['registro_id']].append(ident)
        crm = []
        for ident in sources['CRM']:
            row = self.by_id[ident]
            matches = principal.get(row['registro_id'], [])
            core = [c for c in self.headers[:15] if c not in {'registro_id','aspirante_id','valor_matricula_cop'}]
            for other in matches:
                base = self.by_id[other]
                crm.append({'fila_crm': ident, 'fila_principal': other, 'registro_id': row['registro_id'],
                            'coinciden_12_atributos_no_ids_ni_importe': all(row[c] == base[c] for c in core),
                            'aspirante_id_igual': row['aspirante_id'] == base['aspirante_id'],
                            'importe_crm_base_mas_derechos': serial(row['valor_matricula_cop']),
                            'importe_principal_reportado': serial(base['valor_matricula_cop']),
                            'importe_principal_ausente': base['valor_matricula_cop'] is None,
                            'accion': 'conservar ambos; confirmar precedencia por atributo y concepto económico'})
        self.write('L07_crm_principal.csv', crm, ['fila_crm','fila_principal','registro_id','coinciden_12_atributos_no_ids_ni_importe','aspirante_id_igual','importe_crm_base_mas_derechos','importe_principal_reportado','importe_principal_ausente','accion'])
        cols13 = [c for c in self.headers[:15] if c not in {'registro_id','aspirante_id'}]
        cols11 = [c for c in cols13 if not c.startswith('fecha_')]
        index11 = defaultdict(list)
        index13 = defaultdict(list)
        for ident in sources['Principal']:
            index11[tuple(self.by_id[ident][c] for c in cols11)].append(ident)
            index13[tuple(self.by_id[ident][c] for c in cols13)].append(ident)
        oracle, oracle_pairs = [], []
        for ident in sources['Oracle']:
            row = self.by_id[ident]
            candidates = index11.get(tuple(row[c] for c in cols11), [])
            full = index13.get(tuple(row[c] for c in cols13), [])
            oracle.append({'fila_oracle': ident, 'registro_id_oracle': row['registro_id'],
                           'candidatos_11_atributos': len(candidates), 'candidatos_13_atributos': len(full),
                           'ids_candidatos_distintos': len({self.by_id[i]['registro_id'] for i in candidates}),
                           'atributos_informados_de_11': sum(row[c] is not None and row[c] != '' for c in cols11),
                           'candidatos': ', '.join(candidates), 'accion': 'no fusionar; igualdad de atributos no confirma solicitud'})
            for other in candidates:
                base = self.by_id[other]
                a, b = base['fecha_solicitud'], row['fecha_solicitud']
                swapped = a != b and a.year == b.year and a.day == b.month and a.month == b.day
                oracle_pairs.append({'fila_oracle': ident, 'fila_principal': other,
                                     'fecha_solicitud_principal': serial(a), 'fecha_solicitud_oracle': serial(b),
                                     'solicitud_igual': a == b, 'compatible_intercambio_dia_mes': swapped,
                                     'fecha_matricula_principal': serial(base['fecha_matricula']),
                                     'fecha_matricula_oracle': serial(row['fecha_matricula']),
                                     'coinciden_13_atributos': all(row[c] == base[c] for c in cols13)})
            if candidates:
                self.issue(ident, 'registro_id,fecha_solicitud,fecha_matricula', 'oracle_candidato_solapamiento', f'{len(candidates)} candidatos principales por 11 atributos, incluidas ausencias iguales', 'D04')
        self.write('L07_oracle_candidatos.csv', oracle)
        self.write('L07_oracle_fechas_por_par.csv', oracle_pairs)
        self.sources = sources
        self.metrics['L07'] = {'grupos_registro_id_repetido': len({r['registro_id'] for r in repeated}),
                               'filas_en_grupos_repetidos': len(repeated),
                               'crm_con_codigo_en_principal': len({r['fila_crm'] for r in crm}),
                               'crm_con_importe_principal_ausente': len({r['fila_crm'] for r in crm if r['importe_principal_ausente']}),
                               'oracle_candidatos_11': sum(r['candidatos_11_atributos'] > 0 for r in oracle),
                               'oracle_candidatos_13': sum(r['candidatos_13_atributos'] > 0 for r in oracle),
                               'oracle_compatibles_intercambio_fecha': len({r['fila_oracle'] for r in oracle_pairs if r['compatible_intercambio_dia_mes']}),
                               'filas_conciliadas_automaticamente': 0}
        self.step('L07', len(self.kept), len(self.kept), 'Cruzar fuentes e identificar conflictos por atributo; conservar parciales y códigos')
        return self.metrics['L07']

    def l08(self):
        # Conservar la evidencia L04 con su fecha histórica; recalcular alertas de negocio
        # en las filas representativas con la referencia explícita de esta revisión.
        for issue in self.l04_alerts:
            if issue['alerta'] == 'formato_dia_mes_ambiguo':
                self.issue(issue['id_fila_entrada'], issue['columna'], 'formato_dia_mes_ambiguo', issue['detalle'], 'D05')
        counts = Counter()
        emails = []
        cat_rules = json.loads((self.root / 'config/limpieza/estandarizacion_v1.json').read_text())['categorias']
        for ident in self.kept:
            row = self.by_id[ident]
            def add(col, kind, detail, decision):
                self.issue(ident, col, kind, detail, decision)
                counts[kind] += 1
            for col in ['fecha_solicitud','fecha_matricula']:
                if row[col] and row[col] > self.reference:
                    add(col, 'fecha_posterior_a_referencia', f"{serial(row[col])} posterior a {self.reference}; referencia de revisión, no corte institucional", 'D05')
            if row['fecha_matricula'] and row['fecha_matricula'] < row['fecha_solicitud']:
                add('fecha_matricula','matricula_anterior_a_solicitud','Orden temporal por validar', 'D05')
            if row['fecha_solicitud'].year > row['periodo_academico']//10:
                add('periodo_academico','solicitud_posterior_al_anio_del_periodo','No se infiere el periodo desde la fecha', 'D06')
            if row['estado_proceso'] == 'Matriculado' and row['documentos_completos'] != 'Sí':
                add('documentos_completos','matriculado_con_documentacion_no_completa','Confirmar excepciones documentales institucionales', 'D07')
            if row['estado_proceso'] == 'Matriculado' and row['fecha_matricula'] is None:
                add('fecha_matricula','matriculado_sin_fecha','Estado y ausencia de fecha requieren validación', 'D07')
            if row['estado_proceso'] != 'Matriculado' and row['fecha_matricula'] is not None:
                add('fecha_matricula','fecha_en_otro_estado','Fecha informada no prueba matrícula efectiva o estado vigente', 'D07')
            for col in ['aspirante_id','registro_id']:
                if not row[col] or row[col].casefold() == 'nan':
                    add(col, 'identificador_ausente_o_marcador', 'Valor conservado; no se infiere identidad por correo', 'D08')
            for col, allowed in cat_rules.items():
                if row[col] is not None and row[col] not in allowed:
                    add(col, 'categoria_fuera_catalogo', serial(row[col]), 'D02')
            correo = row['correo']
            valid = bool(correo and re.fullmatch(r'[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+', correo))
            status = 'sin información' if correo is None else 'estructura compatible' if valid else 'revisar estructura'
            emails.append({'id_fila_entrada': ident, 'correo': correo, 'estado': status, 'entregabilidad_verificada': False})
            if correo is not None and not valid:
                add('correo','correo_estructura_dudosa','No se corrige por aproximación', 'D08')
        numeric = []
        for col in ['puntaje_admision','valor_matricula_cop','duracion_semestres']:
            partitions = self.sources.items() if col == 'valor_matricula_cop' else [('Todas', self.kept)]
            for source, ids in partitions:
                values = sorted(Decimal(self.by_id[i][col]) for i in ids if self.by_id[i][col] is not None)
                q1, _, q3 = quantiles(values, n=4, method='inclusive')
                low, high = q1-Decimal('1.5')*(q3-q1), q3+Decimal('1.5')*(q3-q1)
                numeric.append({'columna': col, 'fuente': source, 'concepto': 'base más derechos administrativos' if col == 'valor_matricula_cop' and source == 'CRM' else 'importe reportado; concepto pendiente' if col == 'valor_matricula_cop' else 'valor registrado',
                                'filas_denominador': len(ids), 'informados': len(values), 'ausentes': len(ids)-len(values),
                                'minimo': serial(min(values)), 'maximo': serial(max(values)),
                                'promedio': serial(sum(values)/len(values)), 'mediana': serial(median(values)),
                                'q1': serial(q1), 'q3': serial(q3), 'limite_inferior_RIC': serial(low), 'limite_superior_RIC': serial(high),
                                'negativos': sum(v<0 for v in values), 'atipicos_RIC': sum(v<low or v>high for v in values)})
                for ident in ids:
                    value = self.by_id[ident][col]
                    if value is not None and (value<0 or value<low or value>high):
                        self.issue(ident,col,'valor_negativo_o_inusual',f'{serial(value)}; RIC descriptivo de {source}, no regla de exclusión','D09')
        self.write('L08_correos.csv', emails)
        self.write('L08_estadisticas_numericas.csv', numeric)
        self.metrics['L08'] = {'referencia_revision': self.reference.isoformat(), 'alertas_negocio_en_representantes': dict(counts),
                               'correos_por_estado': dict(Counter(r['estado'] for r in emails)),
                               'negativos_numericos': sum(r['negativos'] for r in numeric),
                               'atipicos_RIC': sum(r['atipicos_RIC'] for r in numeric)}
        self.step('L08', len(self.kept), len(self.kept), 'Evaluar coherencia, correos y valores inusuales; registrar incidencias sin imputar')
        return self.metrics['L08']

    def l09(self, preserve_empty_text):
        from .tipado_limpieza import interpretar_decimal, interpretar_cop, interpretar_entero
        out = self.root / 'data/processed/taller_2' / self.run_id
        out.mkdir(parents=True, exist_ok=True)
        rows = [self.by_id[i] for i in self.kept]
        stem = 'BaseUnificada_Revision'
        csv_path, xlsx_path, json_path = [out / f'{stem}.{ext}' for ext in ['csv','xlsx','jsonl']]
        with csv_path.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.writer(handle, lineterminator='\n')
            writer.writerow(self.headers)
            writer.writerows([[serial(row[c]) for c in self.headers] for row in rows])
        with json_path.open('w', encoding='utf8') as handle:
            for row in rows:
                handle.write('{' + ', '.join(json.dumps(c)+': '+json_literal(row[c]) for c in self.headers) + '}\n')
        wb = Workbook()
        ws = wb.active
        ws.title = stem
        ws.append(self.headers)
        for row in rows:
            ws.append([row[c] for c in self.headers])
        for j, col in enumerate(self.headers, 1):
            fmt = 'yyyy-mm-dd' if col.startswith('fecha_') else '"COP" #,##0.00' if col == 'valor_matricula_cop' else '0.00' if col == 'puntaje_admision' else '0' if col in ['periodo_academico','duracion_semestres'] else '@'
            for i in range(2,len(rows)+2):
                ws.cell(i,j).number_format = fmt
            ws.column_dimensions[get_column_letter(j)].width = 42 if col == 'programa' else 24
        table = Table(displayName=stem, ref=f'A1:R{len(rows)+1}')
        table.tableStyleInfo = TableStyleInfo(name='TableStyleMedium9', showRowStripes=True)
        ws.add_table(table)
        ws.freeze_panes = 'A2'
        readme = wb.create_sheet('Alcance')
        for values in [
            ['Aspecto','Criterio'], ['Estado','Preparación técnica terminada; conciliación administrativa pendiente'],
            ['Unidad','Registro conservado; no equivale a solicitud o aspirante único'],
            ['Entrada',len(self.ids)], ['Salida',len(rows)],
            ['Consolidaciones exactas',len(self.ids)-len(rows)],
            ['Importes','COP; CRM incluye derechos. No promediar conjuntamente sin definición común'],
            ['Identificadores','Originales conservados. No usar registro_id como clave única'],
            ['Fechas','ISO; convenciones ambiguas y fechas de negocio pendientes'],
            ['Auditoría',str(self.audit.relative_to(self.root))], ['Ejecución',self.run_id]]:
            readme.append(values)
        wb.save(xlsx_path)
        wb.close()
        preserve_empty_text(xlsx_path, [tuple(row[c] for c in self.headers) for row in rows])

        def restored(value, col):
            if value is None: return None
            if col.startswith('fecha_'):
                return value.date() if isinstance(value,datetime) else value if isinstance(value,date) else date.fromisoformat(value)
            if col == 'valor_matricula_cop': return interpretar_cop(str(value))
            if col == 'puntaje_admision': return interpretar_decimal(str(value))
            if col in ['duracion_semestres','periodo_academico']: return interpretar_entero(str(value))
            return value

        with json_path.open() as handle:
            json_read = [json.loads(line,parse_float=Decimal) for line in handle]
        json_ok = [{c:restored(row[c],c) for c in self.headers} for row in json_read] == rows
        checked = load_workbook(xlsx_path, read_only=True, data_only=True)
        excel_read = list(checked[stem].values)
        excel_ok = list(excel_read[0]) == self.headers and [{c:restored(v,c) for c,v in zip(self.headers,row)} for row in excel_read[1:]] == rows
        checked.close()
        with csv_path.open(encoding='utf-8-sig',newline='') as handle:
            csv_read = list(csv.reader(handle))
        csv_ok = csv_read == [self.headers, *[[serial(row[c]) for c in self.headers] for row in rows]]
        positions = {ident:n for n,ident in enumerate(self.kept,2)}
        output_sha = sha(csv_path)
        dispositions = [{'id_ejecucion':self.run_id,'id_fila_entrada':ident,
                         'id_registro_salida':self.mapping[ident],'fila_salida_csv':positions[self.mapping[ident]],
                         'fuente':self.origin[ident]['origen_sistema'],
                         'registro_id':self.by_id[ident]['registro_id'],
                         'estado_destino':'conservada' if ident == self.mapping[ident] else 'consolidada_exacta',
                         'sha256_csv_salida':output_sha} for ident in self.ids]
        self.write('L09_disposicion_filas.csv',dispositions)
        self.write('L09_incidencias_pendientes.csv',self.issues)
        # Los motivos de ausencia L03 se consultan por entrada; todas las entradas se
        # vinculan con salida. No se pierden al retirar una repetición.
        self._decisions()
        self.write('L09_decisiones_pendientes.csv',self.decisions)
        flags = defaultdict(set)
        for issue in self.issues:
            flags[issue['id_registro_salida']].add(issue['tipo'])
        self.write('L09_estado_revision_por_fila.csv',[
            {'id_registro_salida':ident,'fuente':self.origin[ident]['origen_sistema'],
             'alertas_distintas':len(flags[ident]),'alertas':', '.join(sorted(flags[ident])),
             'alcance':'registro para descripción provisional; no solicitud única validada'} for ident in self.kept])
        completeness = []
        for c in self.headers:
            before, after = [r[c] for r in self.rows], [r[c] for r in rows]
            completeness.append({'columna':c,'tipo_logico':self.l04_summary['tipos_logicos'][c],
                                 'filas_antes':len(before),'ausentes_L04':sum(v is None for v in before),
                                 'filas_despues':len(after),'ausentes_salida':sum(v is None for v in after),
                                 'texto_vacio_salida':sum(isinstance(v,str) and v=='' for v in after),
                                 'literal_nan_salida':sum(isinstance(v,str) and v.casefold()=='nan' for v in after)})
        self.write('L09_completitud_y_diccionario.csv',completeness)
        frequencies = []
        categories = ['programa','modalidad','canal_captacion','estado_proceso','documentos_completos','ciudad_residencia','asesor','periodo_academico','facultad','nivel_formacion']
        for stage,source_rows in [('entrada_preparada',self.original),('salida_revision',rows)]:
            for c in categories:
                for value,count in Counter(r[c] for r in source_rows).most_common():
                    frequencies.append({'etapa':stage,'columna':c,'valor':serial(value),
                                        'cantidad':count,'denominador_registros':len(source_rows),
                                        'porcentaje':round(count*100/len(source_rows),4)})
        self.write('L09_frecuencias_antes_despues.csv',frequencies)
        for col in ['programa','modalidad','canal_captacion','estado_proceso']:
            self.write(f'L09_frecuencias_{col}_por_fuente.csv',[
                {'fuente':source,'valor':serial(value),'cantidad':count,'denominador':len(ids),
                 'porcentaje':round(count*100/len(ids),4)}
                for source,ids in self.sources.items()
                for value,count in Counter(self.by_id[i][col] for i in ids).most_common()])
        input_meta = json.loads((self.root/'data/prepared/taller_2/BaseUnificada.metadata.json').read_text())
        originals_ok = True
        for manifest in ['docs/referencias/integridad.json','docs/referencias/taller_2/integridad.json']:
            for path,item in json.loads((self.root/manifest).read_text()).items():
                originals_ok &= sha(self.root/path) == (item if isinstance(item,str) else item['sha256'])
        prepared_ok = all(sha(self.root/'data/prepared/taller_2'/name)==v['sha256'] for name,v in input_meta['archivos'].items())
        safe_groups = all(self.origin[i]['origen_sistema']==self.origin[self.mapping[i]]['origen_sistema'] and self.raw_by_id[i]==self.raw_by_id[self.mapping[i]] and self.by_id[i]==self.by_id[self.mapping[i]] for i in self.ids)
        exact_after = len(rows)-len({tuple(r[c] for c in self.headers) for r in rows})
        checks = [
            ('Fuentes originales intactas',originals_ok),('Entrada preparada intacta',prepared_ok),
            ('Todas las entradas tienen un destino',len(dispositions)==len(self.ids) and len({r['id_fila_entrada'] for r in dispositions})==len(self.ids)),
            ('Destinos existentes',set(self.mapping.values())==set(self.kept)),
            ('Conciliación de filas',len(rows)==len(self.ids)-self.metrics['L06']['repeticiones_consolidadas']),
            ('Consolidación solo de exactos con misma fuente y originales',safe_groups),
            ('Valores de representantes e identificadores conservados',all(row==self.by_id[ident] for row,ident in zip(rows,self.kept))),
            ('18 columnas de negocio',len(self.headers)==18 and all(list(r)==self.headers for r in rows)),
            ('Lectura completa JSONL exacta',json_ok),('Lectura completa Excel exacta',excel_ok),('Lectura completa CSV exacta',csv_ok),
            ('Incidencias con destino válido',all(i['id_registro_salida'] in self.kept for i in self.issues)),
            ('Referencias de decisión existentes',{i['decision'] for i in self.issues} <= {d['id_decision'] for d in self.decisions}),
            ('Reproducibilidad de representantes',all(self.mapping[self.mapping[i]]==self.mapping[i] for i in self.ids)),
            ('Sin cambios durante L05 a L09',all(r==self.by_id[i] for r,i in zip(self.rows,self.ids))),
            ('Sin repeticiones exactas adicionales en salida',exact_after==0)]
        self.write('L09_controles.csv',[{'control':k,'correcto':bool(v)} for k,v in checks])
        assert all(v for _,v in checks), [k for k,v in checks if not v]
        self.step('L09',len(self.kept),len(self.kept),'Conciliar entradas, exportar base de revisión y controles, comparar antes y después')
        self.metrics['L09'] = {'controles_correctos':len(checks),'filas_entrada':len(self.ids),'filas_salida':len(rows),
                               'columnas':len(self.headers),'incidencias':len(self.issues),
                               'filas_salida_con_incidencias':sum(bool(v) for v in flags.values()),'decisiones_pendientes':len(self.decisions),
                               'repeticiones_exactas_adicionales_salida':exact_after,
                               'filas_por_fuente':{s:len(ids) for s,ids in self.sources.items()}}
        summary = {'id_ejecucion':self.run_id,'ejecutado_en':datetime.now(ZoneInfo('America/Bogota')).isoformat(),
                   'estado':'preparación técnica ejecutada, conciliación administrativa pendiente',
                   'etapas_ejecutadas':['L05','L06','L07','L08','L09'],
                   'etapas_sin_decision_institucional_cerrada':['L05 catálogo institucional','L07 conciliación','L08 incidencias administrativas'],
                   'entrada_l04':self.l04_summary['id_ejecucion'],'sha256_codigo_notebook':self.code_sha,
                   'sha256_modulo':self.module_sha,'sha256_reglas':self.rule_sha,
                   'filas_entrada':len(self.ids),'filas_salida':len(rows),'columnas':len(self.headers),
                   'repeticiones_consolidadas':len(self.ids)-len(rows),'filas_excluidas':0,
                   'celdas_modificadas_L05_L09':0,'valores_imputados':0,'solicitudes_unicas_validadas':False,
                   'metricas':self.metrics,'auditoria':str(self.audit.relative_to(self.root)),
                   'datos_salida':str(out.relative_to(self.root)),
                   'archivos_datos':{p.name:sha(p) for p in [csv_path,xlsx_path,json_path]},
                   'apta_para':'Descripción provisional de registros con procedencia y alertas',
                   'pendiente_para':'Solicitudes o aspirantes únicos, conversión definitiva y comparación monetaria entre fuentes'}
        (self.audit/'resumen_ejecucion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (self.root/'reports/limpieza/ultimo_cierre.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (out/'README.md').write_text(f'# Base unificada en revisión\n\n{len(rows):,} registros y 18 columnas después de consolidar {len(self.ids)-len(rows)} repeticiones exactas.\n\nPreparación técnica ejecutada; las decisiones administrativas siguen pendientes. No equivale a solicitudes únicas.\n\nLa hoja Alcance de Excel explica las limitaciones. Los controles y destinos de las {len(self.ids)} entradas se conservan en {self.audit.relative_to(self.root)}. JSONL distingue null de texto vacío; CSV requiere la auditoría.\n\nSe conserva la referencia histórica L04 de 24 de octubre. L08 usa 26 de octubre para revisar fechas posteriores; ninguna referencia representa un corte institucional confirmado.\n',encoding='utf8')
        self._report(summary)
        return summary

    def _decisions(self):
        repeated_ids = {i['id_registro_salida'] for i in self.issues if i['decision']=='D03'}
        scopes = {
            'D01':{i for i in self.kept if self.by_id[i]['programa'] is None},
            'D02':{i for i in self.kept if self.by_id[i]['programa'] is not None},
            'D03':repeated_ids,
            'D04':{i['id_registro_salida'] for i in self.issues if i['decision']=='D04'},
            'D05':{i['id_registro_salida'] for i in self.issues if i['decision']=='D05'},
            'D06':{i['id_registro_salida'] for i in self.issues if i['decision']=='D06'},
            'D07':{i['id_registro_salida'] for i in self.issues if i['decision']=='D07'},
            'D08':{i['id_registro_salida'] for i in self.issues if i['decision']=='D08'},
            'D09':set(self.kept), 'D10':{i for i in self.kept if any(v is None for v in self.by_id[i].values())}}
        descriptions = [
            ('D01','Programas no identificados','Recuperar el programa desde la solicitud original o conservarlo ausente','Permite asignar facultad, duración y nivel; evita inventar el programa'),
            ('D02','Catálogo institucional y modalidad','Confirmar los siete programas, sus atributos y la selección de Data Analytics Ingeniería; revisar diferencias de modalidad sin reemplazar la solicitud','Valida análisis por facultad y nivel. La reproducción de nombres no demuestra que el fuzzy histórico asignó el nombre correcto'),
            ('D03','CRM y registros parciales','Definir la unidad solicitud y la precedencia por atributo para los 100 CRM; resolver REG003600 y REG004804 con evidencia','Determina qué filas consolidar y evita contar una misma solicitud dos veces'),
            ('D04','Solapamiento Oracle','Confirmar si cada candidato es la misma solicitud o un evento distinto; conservar códigos propios y documentar equivalencias si se aprueban','Determina el volumen real; no fusionar por parecido de atributos'),
            ('D05','Fechas y referencia temporal','Confirmar las convenciones de día y mes, fechas contradictorias y el corte institucional; definir si hay fechas programadas','Valida tendencias temporales y duraciones; no intercambiar fechas por conveniencia'),
            ('D06','Periodos académicos','Validar solicitudes de 2026 asociadas a 20252 sin deducir la corrección del año','Valida comparaciones entre periodos; el código entero ya está aprobado'),
            ('D07','Estados, documentación y matrícula','Confirmar excepciones documentales y significado de fecha de matrícula en cada estado; acordar qué acredita matrícula efectiva','Permite medir avance y después conversión con denominador definido'),
            ('D08','Identidad y datos de contacto','Recuperar los ID vacíos y nan con fuente autorizada; validar correos sin asumir que correo equivale a persona','Permite contar aspirantes; conservar códigos Oracle. Un correo válido en estructura no acredita entregabilidad'),
            ('D09','Importes y reglas numéricas','Acordar si el indicador económico es matrícula base o base más derechos y reconstruir una medida comparable; confirmar escala oficial de puntajes y tarifas si se quieren validar','Evita promediar conceptos diferentes y confundir matrícula con pago. Los extremos estadísticos no se eliminan automáticamente'),
            ('D10','Ausencias y versión final','Definir qué vacíos son admisibles por estado, qué recuperar y quién valida cada excepción; aprobar la versión y el denominador final','Conserva motivos de ausencia; no imputar ceros o promedios para completar')]
        self.decisions = [{'id_decision':d,'tema':topic,'filas_salida_en_alcance':len(scopes[d]),
                           'que_decidir':what,'efecto_y_beneficio':effect,'tratamiento_actual':'Conservar y documentar; pendiente de validación',
                           'responsable_sugerido':'Admisiones y custodio de la fuente','estado':'pendiente'} for d,topic,what,effect in descriptions]

    def _report(self, summary):
        n = len(self.kept)
        f = lambda v: f'{v:,}'.replace(',','.')
        m = self.metrics
        lines = ['# Reporte de limpieza y decisiones pendientes',
                 '', 'Fecha de revisión: 26 de octubre de 2026.', '',
                 f"Se ejecutaron las etapas L05 a L09 sobre las 5.640 filas ya estandarizadas y tipadas. La salida conserva **{f(n)} registros y 18 columnas**, después de consolidar {m['L06']['repeticiones_consolidadas']} repeticiones exactas de la misma fuente. Cada entrada mantiene su destino en la auditoría. No se completaron datos por suposición ni se fusionaron registros con diferencias.",
                 '', '| Etapa | Resultado |', '| :--- | :--- |',
                 f"| L05, catálogo | {f(m['L05']['con_correspondencia_reproducida'])} correspondencias reproducibles y {m['L05']['sin_correspondencia']} sin programa identificado; {m['L05']['atributos_discrepantes']} discrepancias en los atributos de trabajo. |",
                 f"| L06, exactos | {m['L06']['grupos_exactos']} grupos; {m['L06']['repeticiones_consolidadas']} filas adicionales consolidadas. Representante por índice BU, sin atribuirle mayor actualidad. |",
                 f"| L07, fuentes | {m['L07']['crm_con_codigo_en_principal']} filas CRM con código en principal y {m['L07']['grupos_registro_id_repetido']} grupos de código repetido conservados. Oracle tiene {m['L07']['oracle_candidatos_11']} filas con candidatos por 11 atributos y {m['L07']['oracle_candidatos_13']} por 13; son sondas, no identidades confirmadas. |",
                 '| L08, coherencia | Se revisaron fechas, periodos, documentación, estados, identificadores, correos y valores numéricos; los casos pendientes se conservan. |',
                 f"| L09, cierre técnico | {m['L09']['controles_correctos']} controles correctos; CSV, Excel y JSONL verificados íntegramente; frecuencias y completitud recalculadas. |",
                 '', 'Las fechas usan año, mes y día. Los importes conservan precisión exacta en COP; la presentación colombiana se aplica en las tablas y según la configuración regional en Excel. Los periodos mantienen 20252, 20261 y 20262 como códigos. Los identificadores originales se conservan.',
                 '', '## Qué queda disponible para análisis', '',
                 f"La base permite describir los {f(n)} registros conservados por programa, modalidad, canal y estado, citando el denominador. Todavía no permite afirmar solicitudes o aspirantes únicos, ni tasas definitivas de conversión. Los importes se resumen por fuente porque CRM incluye derechos administrativos y el concepto de las otras fuentes está por confirmar.",
                 '', f"L09 registra {f(m['L09']['incidencias'])} incidencias en {f(m['L09']['filas_salida_con_incidencias'])} filas de salida distintas. Los alcances se superponen y no deben sumarse como personas. La ausencia de alertas particulares tampoco acredita validación institucional.",
                 '', '## Hallazgos de revisión', '',
                 f"Las modalidades de solicitud difieren de la modalidad única del catálogo en {f(m['L05']['modalidades_diferentes_catalogo'])} entradas anteriores a la consolidación. Se conserva la modalidad de solicitud. Los tres atributos del catálogo coinciden con la reproducción por una clave normalizada única. El nombre asignado originalmente por fuzzy fue retirado del libro final: la reproducción actual no recupera esa evidencia histórica.",
                 '', f"En CRM hay {m['L07']['crm_con_importe_principal_ausente']} filas con importe informado cuyo candidato principal no tiene importe. No se utiliza el total CRM para rellenarlas sin acordar antes el concepto y la precedencia. REG003600 conserva una diferencia de importe y REG004804 una diferencia de programa y atributos asociados.",
                 '', f"Oracle presenta {m['L07']['oracle_compatibles_intercambio_fecha']} filas candidatas compatibles con intercambio de día y mes en alguna fecha de solicitud principal. Esa compatibilidad no demuestra cuál fecha es correcta y no se aplica una corrección automática. Las sondas incluyen ausencias iguales; el detalle indica cuántos de los 11 atributos están informados.",
                 '', '| Alerta administrativa en representantes | Casos |', '| :--- | ---: |']
        for kind,count in m['L08']['alertas_negocio_en_representantes'].items():
            lines.append(f'| {kind.replace("_"," ")} | {f(count)} |')
        lines += ['', 'La referencia L08 es el 26 de octubre de 2026, fecha de revisión. L04 conserva su referencia histórica del día 24. Ninguna equivale a un corte institucional confirmado; los conteos de fechas posteriores no deben compararse sin indicar la referencia.',
                  '', f"El control de correos registra {m['L08']['correos_por_estado']}. Se revisó estructura, sin comprobar existencia o entregabilidad. La evaluación numérica detectó {m['L08']['negativos_numericos']} negativos y {m['L08']['atipicos_RIC']} valores fuera del criterio intercuartílico aplicado por variable y por fuente en los importes. Esto no acredita que todos los valores sean exactos.",
                  '', '## Decisiones necesarias para aprobar la versión final', '',
                  '| Decisión | Alcance en filas de salida | Qué resolver | Efecto |', '| :--- | ---: | :--- | :--- |']
        for d in self.decisions:
            lines.append(f"| {d['id_decision']}: {d['tema']} | {f(d['filas_salida_en_alcance'])} | {d['que_decidir']} | {d['efecto_y_beneficio']} |")
        lines += ['', 'Los alcances indican filas que podrían verse afectadas por una decisión, no errores confirmados. Por ejemplo, validar el catálogo alcanza a todas sus asignaciones y acordar el concepto monetario afecta al diseño de indicadores de toda la base.',
                  '', 'Las decisiones se aplicarán mediante reglas versionadas y un registro por celda o consolidación. Luego se recalcularán los destinos, controles y denominadores. La versión se denomina BaseUnificada_Revision para identificar que su preparación técnica está terminada y su conciliación administrativa sigue pendiente.',
                  '', '## Archivos y trazabilidad', '',
                  f"Datos: `{summary['datos_salida']}`.", '', f"Auditoría: `{summary['auditoria']}`.", '',
                  'El archivo reports/limpieza/ultimo_cierre.json identifica esta ejecución y los hashes de las tres salidas. L09_disposicion_filas.csv enlaza las 5.640 entradas con su salida. L09_incidencias_pendientes.csv conserva los casos individuales y L09_decisiones_pendientes.csv resume las reglas por resolver. Los motivos de ausencia se mantienen en L03 y se recuperan mediante esa relación de entradas.',
                  '', 'Los archivos originales y preparados permanecen intactos. Esta ejecución no carga ni reemplaza las tablas de Docker. El notebook 01 conserva la evidencia de la exploración inicial; el notebook 02 respalda la base consolidada y las etapas de limpieza.']
        report = self.root/'reports/limpieza/reporte_cierre_limpieza.md'
        report.write_text('\n'.join(lines)+'\n',encoding='utf8')
