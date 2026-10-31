"""Genera el proyecto Power BI (PBIP) del dashboard de admisiones, con un modelo en estrella."""

from pathlib import Path
import argparse
import json
import re
import shutil

from configurar_powerbi_windows import expresiones_rutas, texto_m

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--excel', type=Path, default=ROOT / 'deliverables/BaseUnificada_Entregable.xlsx')
parser.add_argument('--destino', type=Path, default=ROOT / 'powerbi/DashboardAdmisiones')
args = parser.parse_args()
EXCEL = args.excel.resolve()
DEST = args.destino
NAME = 'DashboardAdmisiones'
SM = DEST / f'{NAME}.SemanticModel'
RP = DEST / f'{NAME}.Report'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def indent(text, tabs):
    return ''.join('\t' * tabs + line + '\n' for line in text.strip().splitlines())


# Modelo semántico en estrella: FactRegistros y sus dimensiones, desde la consulta de la plantilla.
template = (ROOT / 'powerbi/BaseUnificada.pq').read_text(encoding='utf-8')
assert template.count('Origen = "PostgreSQL",') == 1
base_query = template.replace('Origen = "PostgreSQL",', 'Origen = "Excel",', 1)
base_query = re.sub(r'RutaExcel = "[^"]*"', lambda _: 'RutaExcel = RutaLibroBase', base_query)
base_query = '\n'.join(l for l in base_query.splitlines() if not l.strip().startswith('//'))
control_query = f'''
let
    RutaExcel = RutaLibroBase,
    Hoja = Excel.Workbook(File.Contents(RutaExcel), null, true){{[Item="Control_Calidad", Kind="Sheet"]}}[Data],
    Encabezados = Table.PromoteHeaders(Hoja, [PromoteAllScalars=true]),
    Tipos = {{
        {{"registro_id", type text}}, {{"fuente_origen", type text}},
        {{"intervalo_dias_apto_reglas_aplicadas", type logical}}, {{"dias_solicitud_matricula", Int64.Type}},
        {{"fecha_solicitud_apta_reglas_aplicadas", type logical}}
    }},
    Columnas = Table.SelectColumns(Encabezados, List.Transform(Tipos, each _{{0}})),
    Resultado = Table.TransformColumnTypes(Columnas, Tipos)
in
    Resultado
'''
# El programa ausente se presenta como Sin información para relacionarlo con su dimensión; el dato maestro no cambia.
SIN_PROGRAMA = '{"programa", each if _ = null or _ = "" then "Sin información" else _, type text}'
fact_query = f'''
let
    Unida = Table.NestedJoin(BaseUnificadaOrigen, {{"registro_id"}}, ControlOrigen, {{"registro_id"}}, "control", JoinKind.LeftOuter),
    Control = Table.ExpandTableColumn(Unida, "control",
        {{"fuente_origen", "intervalo_dias_apto_reglas_aplicadas", "dias_solicitud_matricula", "fecha_solicitud_apta_reglas_aplicadas"}},
        {{"fuente_origen", "intervalo_apto", "dias_solicitud_matricula", "fecha_solicitud_apta"}}),
    Programa = Table.TransformColumns(Control, {{{SIN_PROGRAMA}}}),
    Codigo = Table.AddColumn(Programa, "codigo_origen",
        each if [aspirante_id] = null or [aspirante_id] = "" then null else [fuente_origen] & "|" & [aspirante_id], type text),
    Conteo = Table.Group(Table.SelectRows(Codigo, each [codigo_origen] <> null), {{"codigo_origen"}},
        {{{{"solicitudes_codigo", each Table.RowCount(_), Int64.Type}}}}),
    ConConteo = Table.NestedJoin(Codigo, {{"codigo_origen"}}, Conteo, {{"codigo_origen"}}, "conteo", JoinKind.LeftOuter),
    Recurrencia = Table.ExpandTableColumn(ConConteo, "conteo", {{"solicitudes_codigo"}}),
    Resultado = Table.RemoveColumns(Recurrencia, {{"facultad", "duracion_semestres", "nivel_formacion"}})
in
    Resultado
'''


def dim_query(column, label, source='BaseUnificadaOrigen'):
    return f'''
let
    Valores = Table.Distinct(Table.SelectColumns({source}, {{"{column}"}})),
    Nombrada = Table.RenameColumns(Valores, {{{{"{column}", "{label}"}}}}),
    Resultado = Table.Sort(Nombrada, {{{{"{label}", Order.Ascending}}}})
in
    Resultado
'''


programa_query = f'''
let
    Base = Table.TransformColumns(BaseUnificadaOrigen, {{{SIN_PROGRAMA}}}),
    Columnas = Table.Distinct(Table.SelectColumns(Base, {{"programa", "facultad", "duracion_semestres", "nivel_formacion"}})),
    Unicos = Table.Distinct(Columnas, {{"programa"}}),
    Resultado = Table.RenameColumns(Unicos, {{{{"programa", "Programa"}}, {{"facultad", "Facultad"}},
        {{"duracion_semestres", "Duración en semestres"}}, {{"nivel_formacion", "Nivel de formación"}}}})
in
    Resultado
'''
fecha_query = '''
let
    Fechas = List.RemoveNulls(BaseUnificadaOrigen[fecha_solicitud] & BaseUnificadaOrigen[fecha_matricula]),
    Inicio = #date(Date.Year(List.Min(Fechas)), 1, 1),
    Fin = #date(Date.Year(List.Max(Fechas)), 12, 31),
    Dias = List.Dates(Inicio, Duration.Days(Fin - Inicio) + 1, #duration(1, 0, 0, 0)),
    Tabla = Table.FromList(Dias, Splitter.SplitByNothing(), type table [Fecha = date]),
    Anio = Table.AddColumn(Tabla, "Año", each Date.Year([Fecha]), Int64.Type),
    NumeroMes = Table.AddColumn(Anio, "Número de mes", each Date.Month([Fecha]), Int64.Type),
    Mes = Table.AddColumn(NumeroMes, "Mes", each Date.ToText([Fecha], "yyyy-MM"), type text)
in
    Mes
'''

FACT = 'FactRegistros'
F = FACT + '.'
fact_types = dict(registro_id='string', aspirante_id='string', fecha_solicitud='dateTime', programa='string',
    modalidad='string', canal_captacion='string', estado_proceso='string', puntaje_admision='double',
    documentos_completos='string', valor_matricula_cop='decimal', ciudad_residencia='string', asesor='string',
    fecha_matricula='dateTime', correo='string', periodo_academico='int64', fuente_origen='string',
    intervalo_apto='boolean', dias_solicitud_matricula='int64', fecha_solicitud_apta='boolean',
    codigo_origen='string', solicitudes_codigo='int64')
# Claves hacia las dimensiones: quedan ocultas para que los filtros usen las columnas de cada dimensión.
dimensions = {
    'DimPrograma': (programa_query, dict(Programa='string', Facultad='string',
                    **{'Duración en semestres': 'int64', 'Nivel de formación': 'string'}), 'programa', 'Programa'),
    'DimModalidad': (dim_query('modalidad', 'Modalidad'), dict(Modalidad='string'), 'modalidad', 'Modalidad'),
    'DimCanal': (dim_query('canal_captacion', 'Canal'), dict(Canal='string'), 'canal_captacion', 'Canal'),
    'DimEstado': (dim_query('estado_proceso', 'Estado'), dict(Estado='string'), 'estado_proceso', 'Estado'),
    'DimCiudad': (dim_query('ciudad_residencia', 'Ciudad'), dict(Ciudad='string'), 'ciudad_residencia', 'Ciudad'),
    'DimAsesor': (dim_query('asesor', 'Asesor'), dict(Asesor='string'), 'asesor', 'Asesor'),
    'DimPeriodo': (dim_query('periodo_academico', 'Periodo'), dict(Periodo='int64'), 'periodo_academico', 'Periodo'),
    'DimFuente': (dim_query('fuente_origen', 'Fuente', 'ControlOrigen'), dict(Fuente='string'), 'fuente_origen', 'Fuente'),
    'DimFecha': (fecha_query, {'Fecha': 'dateTime', 'Año': 'int64', 'Número de mes': 'int64', 'Mes': 'string'},
                 'fecha_solicitud', 'Fecha'),
}
hidden = {key for _, _, key, _ in dimensions.values()} | {'fecha_matricula', 'codigo_origen', 'intervalo_apto',
                                                         'fecha_solicitud_apta', 'dias_solicitud_matricula'}

# Tablas de respaldo del notebook 04: comparaciones con pesos comunes, escenario de 49 pares, respuestas,
# indicadores y decisiones. Se calculan sobre la base completa, sin relación con los filtros del informe.
TABLAS = ROOT / 'reports/analisis_administrativo/tablas'
M_TYPE = {'text': 'type text', 'int': 'Int64.Type', 'num': 'type number', 'pct': 'type number',
          'bool': 'type logical'}
TMDL_TYPE = {'text': 'string', 'int': 'int64', 'num': 'double', 'pct': 'double'}
FORMAT = {'int': '#,0', 'num': '+0.00;-0.00;0.00', 'pct': '0.00%'}


def csv_query(file, columns, typed=(), steps=''):
    """columns: (origen, nombre, tipo) visibles; typed: tipos de columnas auxiliares usadas en steps."""
    created = set(re.findall(r'AddColumn\(\w+, "(\w+)"', steps))
    types = ', '.join(f'{{"{c}", {M_TYPE[k]}}}' for c, k in dict([*typed, *((c, k) for c, _, k in columns)]).items()
                      if c not in created)
    pcts = ', '.join(f'{{"{c}", each _ / 100, type number}}' for c, _, k in columns if k == 'pct')
    names = ', '.join(f'{{"{c}", "{n}"}}' for c, n, _ in columns)
    return f'''
let
    Origen = Csv.Document(File.Contents(ArchivoProyecto({texto_m("reports/analisis_administrativo/tablas/" + file)})), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Encabezados, {{{types}}}, "en-US"),
    {steps or 'Listo = Tipos,'}
    Porcentajes = Table.TransformColumns(Listo, {{{pcts}}}),
    Columnas = Table.SelectColumns(Porcentajes, {{{', '.join(f'"{c}"' for c, _, _ in columns)}}}),
    Resultado = Table.RenameColumns(Columnas, {{{names}}})
in
    Resultado
'''


SENSIBILIDAD_PASOS = '''Grandes = Table.SelectRows(Tipos, each not [grupo_pequeno_base]),
    Categoria = Table.AddColumn(Grandes, "categoria", each Text.Combine(List.Select({[ciudad_residencia], [programa],
        [modalidad], [canal_captacion], [estado_proceso]}, each _ <> null and _ <> ""), " · "), type text),
    Ambito = Table.AddColumn(Categoria, "ambito", each if Text.Contains([dimension], ",") then "Ciudad, programa y modalidad"
        else if [dimension] = "canal_captacion" then "Canal" else if [dimension] = "estado_proceso" then "Estado"
        else Text.Proper([dimension]), type text),
    Listo = Table.AddColumn(Ambito, "cambio_abs", each Number.Abs([diferencia_matriculado_pp]), type number),'''
references = {
    'RefCanalesComparables': ('canales_comparables.csv', [
        ('canal_captacion', 'Canal', 'text'), ('registros_totales', 'Registros', 'int'),
        ('registros_soporte_comun', 'Registros en estratos comunes', 'int'),
        ('proporcion_bruta_soporte_pct', '% bruto en estratos comunes', 'pct'),
        ('proporcion_estandarizada_descriptiva_pct', '% con pesos comunes', 'pct'),
        ('celdas_menores_30', 'Celdas con menos de 30', 'int')], (), ''),
    'RefH3Condicionada': ('H3_comparacion_hipotesis_condicionada.csv', [
        ('variable', 'Variable', 'text'), ('grupo', 'Grupo', 'text'),
        ('registros_grupo_comun', 'Registros del grupo', 'int'),
        ('pendiente_o_retirado_bruto_soporte_pct', '% Pendiente o Retirado bruto', 'pct'),
        ('pendiente_o_retirado_ponderado_pct', '% Pendiente o Retirado con pesos comunes', 'pct')], (),
        'Listo = Table.TransformColumns(Tipos, {"variable", each if _ = "situacion_documental" then "Documentos" '
        'else "Asesor", type text}),'),
    'RefSensibilidad49': ('sensibilidad_49_pares.csv', [
        ('ambito', 'Ámbito', 'text'), ('categoria', 'Categoría', 'text'), ('registros_base', 'Registros', 'int'),
        ('proporcion_matriculado_pct_base', '% Matriculado base', 'pct'),
        ('proporcion_matriculado_pct_escenario', '% Matriculado con 49 pares', 'pct'),
        ('diferencia_matriculado_pp', 'Cambio en puntos', 'num'), ('cambio_abs', 'Cambio absoluto', 'num')],
        [('grupo_pequeno_base', 'bool'), ('dimension', 'text'), ('ciudad_residencia', 'text'), ('programa', 'text'),
         ('modalidad', 'text'), ('canal_captacion', 'text'), ('estado_proceso', 'text')], SENSIBILIDAD_PASOS),
    'RefRespuestas': ('respuestas_preguntas_hipotesis.csv', [
        ('referencia', 'Referencia', 'text'), ('pregunta_o_hipotesis', 'Pregunta o hipótesis', 'text'),
        ('estado_de_respuesta', 'Estado de la respuesta', 'text'),
        ('conocimiento_obtenido', 'Conocimiento obtenido', 'text')], (), ''),
    'RefIndicadores': ('cuadro_indicadores_negocio.csv', [
        ('codigo', 'Código', 'text'), ('indicador', 'Indicador', 'text'), ('numerador', 'Numerador', 'int'),
        ('denominador', 'Denominador', 'int'), ('valor', 'Valor', 'pct'), ('lectura', 'Lectura', 'text')], (), ''),
    'RefDecisiones': ('decisiones_negocio.csv', [
        ('codigo', 'Código', 'text'), ('decision_propuesta', 'Decisión propuesta', 'text'),
        ('evidencia', 'Evidencia', 'text'), ('indicador_de_evaluacion', 'Indicador de evaluación', 'text')], (), ''),
}
measures = {
    'Registros': (f'COUNTROWS({FACT})', '#,0'),
    'Matriculado': ('CALCULATE([Registros], DimEstado[Estado] = "Matriculado")', '#,0'),
    '% Matriculado': ('DIVIDE(CALCULATE([Registros], REMOVEFILTERS(DimEstado), REMOVEFILTERS(FactRegistros[estado_proceso]), DimEstado[Estado] = "Matriculado"), CALCULATE([Registros], REMOVEFILTERS(DimEstado), REMOVEFILTERS(FactRegistros[estado_proceso])))', '0.0%'),
    '% del total': ('DIVIDE([Registros], CALCULATE([Registros], ALLSELECTED()))', '0.0%'),
    'Códigos por origen': (f'DISTINCTCOUNTNOBLANK({FACT}[codigo_origen])', '#,0'),
    'Sin código de aspirante': (f'CALCULATE([Registros], LEN({FACT}[aspirante_id]) = 0)', '#,0'),
    'Puntajes informados': (f'COUNT({FACT}[puntaje_admision])', '#,0'),
    'Puntaje mediano': (f'MEDIAN({FACT}[puntaje_admision])', '0.0'),
    'Puntaje promedio': (f'AVERAGE({FACT}[puntaje_admision])', '0.0'),
    'Importes informados': (f'COUNT({FACT}[valor_matricula_cop])', '#,0'),
    'Importe mediano': (f'MEDIAN({FACT}[valor_matricula_cop])', '$ #,0'),
    'Matriculado sin documentos completos': (
        f'CALCULATE([Matriculado], {FACT}[documentos_completos] <> "Sí")', '#,0'),
    '% sin asesor asignado': (
        'DIVIDE(COALESCE(CALCULATE([Registros], KEEPFILTERS(DimAsesor[Asesor] = "Sin asignar")), 0), [Registros])', '0.0%'),
    'Registros con fecha apta': (f'CALCULATE([Registros], {FACT}[fecha_solicitud_apta] = TRUE())', '#,0'),
    'Intervalos aptos': (f'CALCULATE([Registros], {FACT}[intervalo_apto] = TRUE())', '#,0'),
    'Días medianos a matrícula': (
        f'CALCULATE(MEDIAN({FACT}[dias_solicitud_matricula]), {FACT}[intervalo_apto] = TRUE())', '0'),
    # Sobre las tablas de respaldo del notebook 04; no cambian con los filtros.
    'Proporción bruta': ("SUM(RefCanalesComparables[% bruto en estratos comunes])", '0.00%'),
    'Proporción con pesos comunes': ("SUM(RefCanalesComparables[% con pesos comunes])", '0.00%'),
    'Brecha bruta entre canales': (
        "100 * (MAX(RefCanalesComparables[% bruto en estratos comunes]) "
        "- MIN(RefCanalesComparables[% bruto en estratos comunes]))", '0.00 "pts"'),
    'Brecha con pesos comunes': (
        "100 * (MAX(RefCanalesComparables[% con pesos comunes]) - MIN(RefCanalesComparables[% con pesos comunes]))",
        '0.00 "pts"'),
    'Registros comparables': ("SUM(RefCanalesComparables[Registros en estratos comunes])", '#,0'),
    'Cambio máximo con 49 pares': ("MAX(RefSensibilidad49[Cambio absoluto])", '0.00 "pts"'),
}


def name(text):
    return text if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', text) else f"'{text}'"


def columns_tmdl(types, hide=(), key=None, formats=None):
    formats = formats or {}
    return ''.join(f'\tcolumn {name(c)}\n\t\tdataType: {t}\n'
                   + (f'\t\tformatString: {formats[c]}\n' if c in formats else '')
                   + ('\t\tisKey\n' if c == key else '') + ('\t\tisHidden\n' if c in hide else '')
                   + f'\t\tsummarizeBy: none\n\t\tsourceColumn: {c}\n\n' for c, t in types.items())


def table_tmdl(table, types, query, hide=(), key=None, extra='', formats=None):
    return (f'table {table}\n{extra}\n' + columns_tmdl(types, hide, key, formats)
            + f'\tpartition {table} = m\n\t\tmode: import\n\t\tsource =\n{indent(query, 4)}\n')


fact_tmdl = f'table {FACT}\n\n' + ''.join(
    f'\tmeasure {name(m)} = {expr}\n\t\tformatString: {fmt}\n\n' for m, (expr, fmt) in measures.items())
fact_tmdl += columns_tmdl(fact_types, hidden) + \
    f'\tpartition {FACT} = m\n\t\tmode: import\n\t\tsource =\n{indent(fact_query, 4)}\n'
relationships = ''.join(
    f'relationship {dim}_{key}\n\tfromColumn: {F}{key}\n\ttoColumn: {dim}.{name(dim_key)}\n\n'
    for dim, (_, _, key, dim_key) in dimensions.items())
# La fecha de matrícula usa la misma dimensión mediante una relación inactiva (USERELATIONSHIP).
relationships += f'relationship DimFecha_fecha_matricula\n\tisActive: false\n\tfromColumn: {F}fecha_matricula\n' \
                 '\ttoColumn: DimFecha.Fecha\n'

write(DEST / f'{NAME}.pbip', json.dumps({'version': '1.0', 'artifacts': [{'report': {'path': f'{NAME}.Report'}}],
                                         'settings': {'enableAutoRecovery': True}}, indent=2))
write(SM / 'definition.pbism', json.dumps({'version': '4.0', 'settings': {}}, indent=2))
write(SM / 'definition/database.tmdl', 'database\n\tcompatibilityLevel: 1567\n')
write(SM / 'definition/model.tmdl', 'model Model\n\tculture: es-CO\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n'
      '\tsourceQueryCulture: es-CO\n\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n\n'
      + ''.join(f'ref table {t}\n' for t in [FACT, *dimensions, *references]))
write(SM / 'definition/expressions.tmdl',
      expresiones_rutas(ROOT, EXCEL) + f'expression BaseUnificadaOrigen =\n{indent(base_query, 2)}\n'
      f'expression ControlOrigen =\n{indent(control_query, 2)}')
write(SM / 'definition/relationships.tmdl', relationships)
# Lo que Power BI Desktop guarda al editar (formato PBIR, metadatos lingüísticos, caché) describe el modelo
# anterior; se retira para que el proyecto se abra desde lo generado aquí.
shutil.rmtree(SM / 'definition/tables', ignore_errors=True)
shutil.rmtree(SM / 'definition/cultures', ignore_errors=True)
shutil.rmtree(RP / 'definition', ignore_errors=True)
(SM / '.pbi/cache.abf').unlink(missing_ok=True)
write(SM / f'definition/tables/{FACT}.tmdl', fact_tmdl)
for dim, (query, types, _, dim_key) in dimensions.items():
    extra = '\tdataCategory: Time\n' if dim == 'DimFecha' else ''
    write(SM / f'definition/tables/{dim}.tmdl', table_tmdl(dim, types, query, key=dim_key, extra=extra))
for table, (file, columns, typed, steps) in references.items():
    write(SM / f'definition/tables/{table}.tmdl', table_tmdl(
        table, {n: TMDL_TYPE[k] for _, n, k in columns}, csv_query(file, columns, typed, steps),
        hide={'Cambio absoluto'}, formats={n: FORMAT[k] for _, n, k in columns if k in FORMAT}))

# Informe: formato report.json con contenedores de objetos visuales sobre las dimensiones.
ALIAS = {FACT: 'f', **{dim: f'd{i}' for i, dim in enumerate(dimensions)},
         **{table: f'r{i}' for i, table in enumerate(references)}}
MEASURES = set(measures)
DISPLAY = {'documentos_completos': 'Documentos completos', 'Mes': 'Mes de solicitud',
           'solicitudes_codigo': 'Solicitudes por código'}
PRIMARY, DARK, INK, MUTED, LINE, PAGE = '#27678C', '#1D4A66', '#22313F', '#5F6B73', '#DDE3E8', '#F3F5F7'
WIDTH, HEIGHT, GAP = 1280, 720, 10


def ref(field):
    table, prop = field.split('.', 1)
    kind = 'Measure' if table == FACT and prop in MEASURES else 'Column'
    return {kind: {'Expression': {'SourceRef': {'Source': ALIAS[table]}}, 'Property': prop}}


def literal(value):
    return {'expr': {'Literal': {'Value': value}}}


def color(hex_code):
    return {'solid': {'color': literal(f"'{hex_code}'")}}


def size(points):
    return literal(f'{points}D')


def props(**values):
    return [{'properties': values}]


TRUE, FALSE = literal('true'), literal('false')
FRAME = {'background': props(show=TRUE, color=color('#FFFFFF'), transparency=size(0)),
         'border': props(show=TRUE, color=color(LINE), radius=size(8)),
         'dropShadow': props(show=FALSE),
         'visualHeader': props(show=FALSE)}
BAR = {'dataPoint': props(fill=color(PRIMARY)),
       'labels': props(show=TRUE, color=color(INK), fontSize=size(10), labelDisplayUnits=size(1)),
       'categoryAxis': props(show=TRUE, fontSize=size(10), labelColor=color(INK), showAxisTitle=FALSE,
                             maxMarginFactor=size(45)),
       'valueAxis': props(show=FALSE, showAxisTitle=FALSE, gridlineShow=FALSE)}
GRID = {'columnHeaders': props(fontColor=color('#FFFFFF'), backColor=color(DARK), fontSize=size(10),
                               wordWrap=TRUE),
        'rowHeaders': props(fontColor=color(INK), fontSize=size(10)),
        'values': props(fontColor=color(INK), fontSize=size(10), backColorSecondary=color('#F7F9FA'),
                        wordWrap=TRUE),
        'total': props(fontColor=color(INK), fontSize=size(10)),
        'grid': props(gridHorizontalColor=color(LINE), gridVerticalColor=color(LINE))}
STYLE = {'clusteredBarChart': BAR, 'clusteredColumnChart': BAR, 'tableEx': GRID, 'pivotTable': GRID,
         'card': {'labels': props(color=color(DARK), fontSize=size(26)),
                  'categoryLabels': props(show=TRUE, color=color(MUTED), fontSize=size(10))},
         'slicer': {'data': props(mode=literal("'Dropdown'")),
                    'header': props(show=TRUE, fontColor=color(MUTED), fontSize=size(10)),
                    'items': props(fontColor=color(INK), fontSize=size(10))}}


class Page:
    def __init__(self, title, subtitle):
        self.title, self.visuals = title, []
        self.has_slicers = False
        self.text(title, 0, 0, WIDTH, 52, 18, '#FFFFFF', DARK, bold=True)
        self.text(subtitle, GAP, 54, WIDTH - 2 * GAP, 28, 10, MUTED)

    def add(self, vtype, x, y, w, h, single):
        # Reservar altura suficiente para el título y la selección de los filtros.
        if self.has_slicers and vtype != 'slicer' and y >= 146:
            scale = (HEIGHT - 178) / (HEIGHT - 146)
            y = round(178 + (y - 146) * scale, 2)
            h = round(h * scale, 2)
        z = len(self.visuals)
        config = {'name': re.sub(r'\W', '', self.title)[:14] + f'{z:02d}',
                  'layouts': [{'id': 0, 'position': {'x': x, 'y': y, 'z': z, 'width': w, 'height': h}}],
                  'singleVisual': {'visualType': vtype, **single}}
        self.visuals.append({'x': x, 'y': y, 'z': z, 'width': w, 'height': h,
                             'config': json.dumps(config, ensure_ascii=False), 'filters': '[]'})

    def text(self, value, x, y, w, h, points, ink, fill=None, bold=False):
        style = {'fontSize': f'{points}pt', 'color': ink, **({'fontWeight': 'bold'} if bold else {})}
        frame = {'background': props(show=TRUE, color=color(fill), transparency=size(0))} if fill else {
            'background': props(show=FALSE)}
        self.add('textbox', x, y, w, h, {'drillFilterOtherVisuals': True,
            'objects': {'general': props(paragraphs=[{'textRuns': [{'value': value, 'textStyle': style}]}])},
            'vcObjects': {**frame, 'visualHeader': props(show=FALSE)}})

    def chart(self, vtype, x, y, w, h, title, roles, sort=None, objects=None, widths=None):
        fields = list(dict.fromkeys(f for fs in roles.values() for f in fs))
        query = {'Version': 2,
                 'From': [{'Name': ALIAS[t], 'Entity': t, 'Type': 0}
                          for t in dict.fromkeys(f.split('.')[0] for f in fields)],
                 'Select': [{**ref(f), 'Name': f} for f in fields]}
        if sort:
            query['OrderBy'] = [{'Direction': 2 if sort[1] == 'desc' else 1, 'Expression': ref(sort[0])}]
        heading = props(show=TRUE, text=literal(f"'{title}'"), fontColor=color(INK), fontSize=size(11)) \
            if title else props(show=FALSE)
        self.add(vtype, x, y, w, h, {
            'projections': {role: [{'queryRef': f} for f in fs] for role, fs in roles.items()},
            'prototypeQuery': query, 'drillFilterOtherVisuals': True,
            'columnProperties': {f: {'displayName': DISPLAY[f.split('.', 1)[1]]}
                                 for f in fields if f.split('.', 1)[1] in DISPLAY},
            'objects': {**STYLE.get(vtype, {}), **(objects or {}), **({
                'columnHeaders': [{'properties': {**GRID['columnHeaders'][0]['properties'],
                                                  'autoSizeColumnWidth': FALSE}}],
                'columnWidth': [{'properties': {'value': size(px)}, 'selector': {'metadata': f}}
                                for f, px in widths.items()]} if widths else {})},
            'vcObjects': {**FRAME, 'title': heading}})

    def slicers(self):
        self.has_slicers = True
        fields = ['DimPeriodo.Periodo', 'DimPrograma.Programa', 'DimModalidad.Modalidad', 'DimCanal.Canal',
                  'DimCiudad.Ciudad', 'DimFuente.Fuente']
        width = (WIDTH - GAP) // len(fields)
        for i, field in enumerate(fields):
            self.chart('slicer', GAP + i * width, 90, width - GAP, 76, None, {'Values': [field]})

    def cards(self, names, y=146):
        width = (WIDTH - GAP) // len(names)
        for i, m in enumerate(names):
            self.chart('card', GAP + i * width, y, width - GAP, 86, None, {'Values': [B + m]})

    def section(self, index):
        config = {'objects': {'background': props(color=color(PAGE), transparency=size(0)),
                              'outspace': props(color=color(PAGE))}}
        return {'config': json.dumps(config), 'displayName': self.title, 'displayOption': 1, 'filters': '[]',
                'height': HEIGHT, 'width': WIDTH, 'name': f'ReportSection{index}', 'visualContainers': self.visuals}


UNIT = ('Unidad: registro de solicitud de origen, no persona única. '
        '% Matriculado es una proporción observada, no una tasa definitiva de conversión.')
B = F
HALF = (WIDTH - 3 * GAP) // 2
LEFT, RIGHT = GAP, 2 * GAP + HALF
ROW1, ROW2, ROW_H = 240, 480, 230
pages = []


def bar(page, x, y, w, h, title, category, measure, vtype='clusteredBarChart', sort=None):
    page.chart(vtype, x, y, w, h, title, {'Category': [category], 'Y': [B + measure]},
               sort or (B + measure, 'desc'))


p = Page('Panorama de admisiones', UNIT)
p.slicers()
p.cards(['Registros', 'Matriculado', '% Matriculado', 'Códigos por origen'])
bar(p, LEFT, ROW1, HALF, ROW_H, 'Registros por programa', 'DimPrograma.Programa', 'Registros')
bar(p, RIGHT, ROW1, HALF, ROW_H, 'Registros por canal de captación', 'DimCanal.Canal', 'Registros')
bar(p, LEFT, ROW2, HALF, ROW_H, 'Registros por estado del proceso', 'DimEstado.Estado', 'Registros')
bar(p, RIGHT, ROW2, HALF, ROW_H, 'Registros por modalidad', 'DimModalidad.Modalidad', 'Registros')
pages.append(p)

p = Page('Captación y segmentos', 'Segmentos con interés registrado para campañas piloto. '
         'Interpretar solo segmentos con al menos 30 registros. ' + UNIT.split('. ')[0] + '.')
p.slicers()
p.chart('pivotTable', LEFT, 146, 780, 282, 'Registros por programa y ciudad',
        {'Rows': ['DimPrograma.Programa'], 'Columns': ['DimCiudad.Ciudad'], 'Values': [B + 'Registros']})
bar(p, 800, 146, WIDTH - 800 - GAP, 282, '% Matriculado por canal', 'DimCanal.Canal', '% Matriculado')
p.chart('tableEx', LEFT, 438, 780, 272, 'Segmentos de ciudad, programa y modalidad',
        {'Values': ['DimCiudad.Ciudad', 'DimPrograma.Programa', 'DimModalidad.Modalidad', B + 'Registros',
                    B + 'Matriculado', B + '% Matriculado']}, (B + 'Registros', 'desc'))
bar(p, 800, 438, WIDTH - 800 - GAP, 272, 'Registros por ciudad', 'DimCiudad.Ciudad', 'Registros')
pages.append(p)

p = Page('Seguimiento del proceso', 'Estados observados en un corte, sin historial de transiciones. '
         'No es un embudo ni mide productividad de asesores. La recurrencia cuenta solicitudes por código en la base completa.')
p.slicers()
p.cards(['Matriculado sin documentos completos', '% sin asesor asignado', 'Días medianos a matrícula',
         'Intervalos aptos'])
COL2, COL3 = 540, 850
p.chart('pivotTable', LEFT, ROW1, 520, ROW_H, 'Registros por estado y documentación',
        {'Rows': ['DimEstado.Estado'], 'Columns': [B + 'documentos_completos'], 'Values': [B + 'Registros']})
bar(p, COL2, ROW1, 300, ROW_H, '% Matriculado por documentación', B + 'documentos_completos', '% Matriculado')
p.chart('tableEx', COL3, ROW1, WIDTH - COL3 - GAP, ROW_H, 'Puntaje de admisión por estado',
        {'Values': ['DimEstado.Estado', B + 'Puntajes informados', B + 'Puntaje promedio', B + 'Puntaje mediano']},
        ('DimEstado.Estado', 'asc'), widths={'DimEstado.Estado': 170, B + 'Puntajes informados': 85,
                                             B + 'Puntaje promedio': 70, B + 'Puntaje mediano': 70})
p.chart('pivotTable', LEFT, ROW2, 520, ROW_H, 'Registros por estado y asesor',
        {'Rows': ['DimEstado.Estado'], 'Columns': ['DimAsesor.Asesor'], 'Values': [B + 'Registros']})
bar(p, COL2, ROW2, 300, ROW_H, '% Matriculado por asesor', 'DimAsesor.Asesor', '% Matriculado')
p.chart('pivotTable', COL3, ROW2, WIDTH - COL3 - GAP, ROW_H, 'Códigos según solicitudes por código',
        {'Rows': [B + 'solicitudes_codigo'], 'Columns': ['DimFuente.Fuente'], 'Values': [B + 'Códigos por origen']})
pages.append(p)

p = Page('Cobertura y condiciones', 'Faltantes, origen y fechas. La serie usa fechas de solicitud aptas; '
         'septiembre y octubre de 2026 tienen cobertura incompleta.')
p.slicers()
p.cards(['Puntajes informados', 'Importes informados', 'Sin código de aspirante', 'Registros con fecha apta'])
bar(p, LEFT, ROW1, WIDTH - 2 * GAP, ROW_H, 'Registros con fecha apta por mes de solicitud',
    'DimFecha.Mes', 'Registros con fecha apta', 'clusteredColumnChart', ('DimFecha.Mes', 'asc'))
bar(p, LEFT, ROW2, 400, ROW_H, 'Registros por fuente', 'DimFuente.Fuente', 'Registros')
p.chart('tableEx', 420, ROW2, WIDTH - 420 - GAP, ROW_H, 'Cobertura por programa',
        {'Values': ['DimPrograma.Programa', B + 'Registros', B + 'Puntajes informados', B + 'Puntaje mediano',
                    B + 'Importes informados', B + 'Importe mediano']}, (B + 'Registros', 'desc'))
pages.append(p)

CANALES, H3, SENS = 'RefCanalesComparables.', 'RefH3Condicionada.', 'RefSensibilidad49.'
p = Page('Comparaciones controladas', 'Tablas de respaldo del notebook 04, calculadas sobre la base completa: no cambian '
         'con los filtros. Estratos comunes: programa, modalidad y periodo con presencia de todos los grupos.')
p.cards(['Brecha bruta entre canales', 'Brecha con pesos comunes', 'Registros comparables',
         'Cambio máximo con 49 pares'], y=88)
series = [B + 'Proporción bruta', B + 'Proporción con pesos comunes']
p.chart('clusteredBarChart', LEFT, 184, 620, 270, '% Matriculado por canal en 63 estratos comunes',
        {'Category': [CANALES + 'Canal'], 'Y': series}, (series[1], 'desc'), objects={
            'dataPoint': [{'properties': {'fill': color(c)}, 'selector': {'metadata': f}}
                          for f, c in zip(series, ('#9FB7C7', PRIMARY))],
            'labels': props(show=TRUE, color=color(INK), fontSize=size(8)),
            'legend': props(show=TRUE, position=literal("'Top'"), fontSize=size(10))})
p.chart('tableEx', 640, 184, WIDTH - 640 - GAP, 270, 'H3: Pendiente o Retirado por documentos y asesor',
        {'Values': [H3 + 'Variable', H3 + 'Grupo', H3 + 'Registros del grupo', H3 + '% Pendiente o Retirado bruto',
                    H3 + '% Pendiente o Retirado con pesos comunes']},
        widths={H3 + 'Variable': 90, H3 + 'Grupo': 150, H3 + 'Registros del grupo': 80,
                H3 + '% Pendiente o Retirado bruto': 120, H3 + '% Pendiente o Retirado con pesos comunes': 130})
p.chart('tableEx', LEFT, 464, WIDTH - 2 * GAP, 246,
        'Escenario de 49 pares Oracle: grupos con al menos 30 registros, de mayor a menor cambio',
        {'Values': [SENS + 'Ámbito', SENS + 'Categoría', SENS + 'Registros', SENS + '% Matriculado base',
                    SENS + '% Matriculado con 49 pares', SENS + 'Cambio en puntos']},
        (SENS + 'Cambio en puntos', 'desc'), widths={
            SENS + 'Ámbito': 220, SENS + 'Categoría': 420, SENS + 'Registros': 90, SENS + '% Matriculado base': 140,
            SENS + '% Matriculado con 49 pares': 160, SENS + 'Cambio en puntos': 120})
pages.append(p)

RESP, IND, DEC = 'RefRespuestas.', 'RefIndicadores.', 'RefDecisiones.'
p = Page('Respuestas y decisiones', 'Lectura ejecutiva del notebook 04 sobre la base completa. Las metas y responsables '
         'son propuestas por acordar con la institución, no decisiones adoptadas.')
p.chart('tableEx', LEFT, 88, WIDTH - 2 * GAP, 284, 'Respuestas a la pregunta general y las hipótesis',
        {'Values': [RESP + f for f in ('Referencia', 'Pregunta o hipótesis', 'Estado de la respuesta',
                                       'Conocimiento obtenido')]}, (RESP + 'Referencia', 'asc'),
        widths={RESP + 'Referencia': 80, RESP + 'Pregunta o hipótesis': 290, RESP + 'Estado de la respuesta': 220,
                RESP + 'Conocimiento obtenido': 630})
p.chart('tableEx', LEFT, 382, 620, 328, 'Indicadores de seguimiento',
        {'Values': [IND + f for f in ('Código', 'Indicador', 'Numerador', 'Denominador', 'Valor')]},
        (IND + 'Código', 'asc'), widths={IND + 'Código': 60, IND + 'Indicador': 280, IND + 'Numerador': 80,
                                         IND + 'Denominador': 100, IND + 'Valor': 60})
p.chart('tableEx', 640, 382, WIDTH - 640 - GAP, 328, 'Decisiones propuestas',
        {'Values': [DEC + f for f in ('Código', 'Decisión propuesta', 'Evidencia', 'Indicador de evaluación')]},
        (DEC + 'Código', 'asc'), widths={DEC + 'Código': 60, DEC + 'Decisión propuesta': 190, DEC + 'Evidencia': 230,
                                         DEC + 'Indicador de evaluación': 90})
pages.append(p)

write(RP / 'definition.pbir', json.dumps({'version': '4.0', 'datasetReference': {
    'byPath': {'path': f'../{NAME}.SemanticModel'}}}, indent=2))
write(RP / 'report.json', json.dumps({'config': json.dumps({'version': '5.37', 'themeCollection': {}}),
    'layoutOptimization': 0, 'resourcePackages': [],
    'sections': [p.section(i) for i, p in enumerate(pages)]}, ensure_ascii=False, indent=2))
print(DEST / f'{NAME}.pbip')
