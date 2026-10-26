"""Construye el cuaderno de limpieza por etapas; no lo ejecuta."""

from pathlib import Path
from textwrap import dedent

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(value):
    cells.append(nbf.v4.new_markdown_cell(dedent(value).strip()))


def code(value):
    cells.append(nbf.v4.new_code_cell(dedent(value).strip()))


md('''
# Limpieza y transformación de BaseUnificada

Este cuaderno sigue el orden del plan en `docs/plan_limpieza_datos.md`.
La integración previa se conserva en el libro de manejo y la entrada congelada.

**Este cuaderno ejecuta L00 a L09:** identificación de la entrada,
reconstrucción comprobada de la procedencia y estandarización textual mediante
catálogos explícitos. L01 deja documentadas las decisiones económicas, temporales
y de catálogo que siguen pendientes; no las da por resueltas. L03 representa las
ausencias de las demás variables y conserva sus motivos en controles separados.
L04 interpreta tipos con reglas explícitas, presenta fechas como AAAA-MM-DD y
mantiene importes decimales exactos en COP; las alertas no se corrigen automáticamente.

L06 consolida únicamente repeticiones exactas de la misma fuente y conserva todos
sus orígenes. Las filas con diferencias se mantienen pendientes de conciliación.
No se imputan valores, se altera el valor numérico de importes ni se corrigen fechas
por aproximación. El resultado es una base preparada para revisión y análisis
descriptivo provisional, con decisiones administrativas pendientes. L02 conserva los marcadores recibidos;
L03 aplica las reglas de ausencia documentadas sin completar datos por suposición.
Los vacíos y nan de identificadores seguirán sin modificarse hasta los cruces.

Ejecutar desde el principio con el Python del proyecto y los grupos `notebooks`
y `excel` de uv. Guardar el notebook antes de ejecutarlo para registrar su versión.
''')
code('''
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import base64
import csv
import hashlib
import io
import json
import re
import struct
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd
from IPython.display import display, Markdown
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'pyproject.toml').exists())
sys.path.insert(0, str(ROOT / 'scripts'))
from exportar_base_unificada import preserve_empty_text
from analizar_relaciones_taller_2 import profile

SOURCE = ROOT / 'data/prepared/taller_2/BaseUnificada.csv'
META = json.loads(SOURCE.with_suffix('.metadata.json').read_text(encoding='utf8'))
RULE_PATH = ROOT / 'config/limpieza/estandarizacion_v1.json'
RULES = json.loads(RULE_PATH.read_text(encoding='utf8'))
INPUT_SHA = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert INPUT_SHA == META['archivos'][SOURCE.name]['sha256'], 'La entrada cambió de versión'
RULE_SHA = hashlib.sha256(RULE_PATH.read_bytes()).hexdigest()
NOTEBOOK = ROOT / 'notebooks/02_limpieza_base_unificada.ipynb'
saved_notebook = json.loads(NOTEBOOK.read_text(encoding='utf8'))
saved_code = '\\n'.join(''.join(c['source']) if isinstance(c['source'], list) else c['source']
                       for c in saved_notebook['cells'] if c['cell_type'] == 'code')
CODE_SHA = hashlib.sha256(saved_code.encode()).hexdigest()
RUN_ID = f"{RULES['version']}_{INPUT_SHA[:10]}_{RULE_SHA[:8]}_{CODE_SHA[:8]}"
''')
md('''
## L00. Entrada congelada e identificación de las filas

Se leen las 18 columnas como texto para que pandas no interprete periodos como fechas,
ni convierta nan o ausencias a valores faltantes por su cuenta. La conversión de tipos
de negocio corresponde a L04. El índice BU identifica filas de esta versión, no personas.
''')
code('''
df_entrada = pd.read_csv(SOURCE, dtype=str, keep_default_na=False, na_filter=False,
                        encoding='utf-8-sig')
original = df_entrada.copy(deep=True)
N = len(original)
HEADERS = list(original.columns)
assert N == META['filas_sin_encabezado'] == 5640
assert HEADERS == META['encabezados'] and len(HEADERS) == 18
ids_fila = pd.Series([f'BU{i:06d}' for i in range(1, N + 1)], index=original.index)
inventario = pd.read_csv(ROOT / 'reports/limpieza/inventario_entrada.csv',
                         dtype=str, keep_default_na=False, encoding='utf-8-sig')
assert inventario['id_fila_entrada'].tolist() == ids_fila.tolist()
assert set(inventario['sha256_archivo_entrada']) == {INPUT_SHA}
diagnostico_inicial = profile(original.to_dict('records'))
display(pd.DataFrame([
    ['Filas', N], ['Columnas de negocio', len(HEADERS)],
    ['registro_id distintos', original['registro_id'].nunique()],
    ['Repeticiones exactas adicionales', int(original.duplicated().sum())],
    ['Filas con facultad sin asignar', int(original['facultad'].eq('').sum())]
], columns=['Control', 'Resultado']))
''')
md('''
## L01. Procedencia y decisiones pendientes

Se utiliza el libro de manejo que produjo la exportación. Se exige que su hash coincida
con los metadatos y se comprueba el orden de Table.Combine. Cada bloque se contrasta
con las 15 columnas de su hoja fuente, admitiendo solo las operaciones textuales
ya documentadas en la integración. No se asigna origen solo porque una fila ocupe
una posición o tenga un identificador REG.

Esto valida la procedencia dentro del libro congelado. No convierte el identificador
Oracle en identificador institucional de persona ni resuelve cuál fuente tiene razón.
''')
code('''
def serializar(valor):
    return '' if valor is None else str(valor)

def limpiar_externo(valor):
    return ''.join(c for c in unicodedata.normalize('NFC', valor)
                   if unicodedata.category(c) != 'Cc').strip()

MANEJO = ROOT / META['libro_origen']
manejo_bytes = MANEJO.read_bytes()
assert hashlib.sha256(manejo_bytes).hexdigest() == META['sha256_libro_origen']
with zipfile.ZipFile(BytesIO(manejo_bytes)) as archive:
    mashup = base64.b64decode(ET.fromstring(archive.read('customXml/item1.xml')).text)
    package_size = struct.unpack_from('<I', mashup, 4)[0]
    with zipfile.ZipFile(BytesIO(mashup[8:8 + package_size])) as package:
        codigo_integracion = package.read('Formulas/Section1.m').decode('utf-8-sig')
assert re.search(r'Table\\.Combine\\(\\{Caso2_Admisiones_Universitarias_Principal,\\s*'
                 r'Caso2_CRM_Admisiones,\\s*Caso2_Oracle_Admisiones\\}\\)', codigo_integracion)

origenes = [('Principal', 'Caso2_Admisiones_Universitarias', 5040),
            ('CRM', 'Caso2_CRM_Admisiones', 100),
            ('Oracle', 'Caso2_Oracle_Admisiones', 500)]
columnas_presentacion = {'programa', 'modalidad', 'canal_captacion',
                        'estado_proceso', 'ciudad_residencia', 'asesor'}
def comparable_integracion(valor, columna):
    valor = serializar(valor)
    if columna in columnas_presentacion:
        return limpiar_externo(valor).casefold()
    if columna in {'registro_id', 'aspirante_id'}:
        return limpiar_externo(valor)
    return valor

procedencia = []
offset = 0
book = load_workbook(BytesIO(manejo_bytes), read_only=True, data_only=True)
for sistema, hoja, cantidad in origenes:
    cache = list(book[hoja].iter_rows(values_only=True))
    columnas = list(cache[0])
    filas = [dict(zip(columnas, fila)) for fila in cache[1:]]
    assert len(filas) == cantidad
    assert columnas == HEADERS[:15]
    bloque = original.iloc[offset:offset + cantidad].to_dict('records')
    for posicion, (recibida, consolidada) in enumerate(zip(filas, bloque), 2):
        assert all(comparable_integracion(recibida[c], c) ==
                   comparable_integracion(consolidada[c], c) for c in HEADERS[:15]), (sistema, posicion)
        indice = offset + posicion - 2
        procedencia.append({'id_fila_entrada': ids_fila.iloc[indice],
                           'origen_sistema': sistema, 'hoja_evidencia': hoja,
                           'fila_hoja_evidencia': posicion,
                           'registro_id': consolidada['registro_id'],
                           'sha256_libro_evidencia': META['sha256_libro_origen']})
    offset += cantidad
book.close()
assert offset == N
origen_df = pd.DataFrame(procedencia)
assert origen_df['id_fila_entrada'].is_unique
display(origen_df.groupby('origen_sistema').size().rename('Filas verificadas').to_frame())
''')
code('''
decisiones_pendientes = pd.DataFrame([
    ['Identidad de solicitud', 'Conservar repeticiones; no definir personas o solicitudes únicas por registro_id solamente.'],
    ['Importes CRM', 'El valor integra base y derechos. Mantenerlo hasta acordar una medida comparable entre fuentes.'],
    ['Fechas Oracle', 'Conservar y señalar diferencias; no intercambiar día y mes ni sustituir fechas en esta etapa.'],
    ['Catálogo', 'La selección de Data Analytics y otros ajustes quedan como decisiones documentadas pendientes de validación.'],
    ['Asignaciones fuzzy', 'Revisar las denominaciones asignadas desde la evidencia de integración; no validar facultades solo por coincidencia.']
], columns=['Decisión', 'Tratamiento durante L02'])
display(decisiones_pendientes)
''')
md('''
### Alcance acordado sobre identificadores

La revisión de identificadores entre fuentes se pospone hasta los cruces. Los códigos
Oracle y los de las demás fuentes se conservan; no necesitan coincidir para continuar
la estandarización. No se fusionan personas o solicitudes, no se cambia nan del
identificador ni se eliminan filas por este motivo en las primeras etapas. Los conteos
son diagnóstico y el índice BU sirve para auditar filas, no para reemplazar códigos.
''')
md('''
## L02. Estandarización de textos y categorías

La regla usa espacios y acentos solo para buscar en un catálogo explícito. Se guarda
la denominación acordada, con sus tildes. No realiza coincidencia difusa ni asigna
valores desconocidos a la opción más cercana. Los desconocidos quedan intactos y señalados.

Se homologan los periodos como texto. La conversión a códigos enteros 20252, 20261 y
20262 permanece para L04. Fechas, puntajes, importes y duración se mantienen exactamente
como fueron recibidos. nan no se trata todavía como ausencia: corresponde a L03.
''')
code('''
def clave_catalogo(valor):
    texto = re.sub(r'\\s+', ' ', limpiar_externo(valor)).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')

catalogos = {}
for columna, valores in RULES['categorias'].items():
    mapping = {clave_catalogo(v): v for v in valores}
    assert len(mapping) == len(valores), f'Catálogo ambiguo: {columna}'
    catalogos[columna] = mapping
periodos = {clave_catalogo(k): v for k, v in RULES['periodos'].items()}
assert (set(catalogos) | {'periodo_academico', 'correo'} |
        set(RULES['identificadores']) | set(RULES['sin_transformacion_en_esta_etapa'])) == set(HEADERS)

def estandarizar(valor, columna):
    if columna in catalogos:
        return catalogos[columna].get(clave_catalogo(valor), valor)
    if columna == 'periodo_academico':
        return periodos.get(clave_catalogo(valor), valor)
    if columna in RULES['identificadores']:
        return limpiar_externo(valor)
    if columna == 'correo':
        correo = valor.strip()
        if correo.count('@') == 1:
            local, dominio = correo.split('@')
            return local + '@' + dominio.lower()
        return correo
    return valor

display(pd.DataFrame([
    {'columna': c, 'tratamiento': 'Catálogo explícito' if c in catalogos else
     'Equivalencias de periodo, aún como texto' if c == 'periodo_academico' else
     'Identificador: espacios externos y controles' if c in RULES['identificadores'] else
     'Espacios externos y dominio del correo' if c == 'correo' else
     'Sin cambios en esta etapa'} for c in HEADERS
]))
''')
code('''
df_estandarizada = original.copy(deep=True)
cambios = []
pasos = []
incidencias = []
for numero, columna in enumerate(HEADERS, 1):
    regla = f'E{numero:02d}'
    antes = df_estandarizada[columna].copy()
    despues = antes.map(lambda v: estandarizar(v, columna))
    modificadas = antes.ne(despues)
    for indice in antes.index[modificadas]:
        cambios.append({'id_ejecucion': RUN_ID, 'paso': 'L02', 'regla': regla,
                        'id_fila_entrada': ids_fila.loc[indice],
                        'registro_id': original.loc[indice, 'registro_id'],
                        'columna': columna, 'valor_anterior': antes.loc[indice],
                        'valor_posterior': despues.loc[indice],
                        'tipo_anterior': 'texto de entrada', 'tipo_posterior': 'texto',
                        'motivo': 'Estandarización explícita; no cambia identidad ni elimina filas'})
    df_estandarizada[columna] = despues
    pasos.append({'id_ejecucion': RUN_ID, 'paso': 'L02', 'regla': regla,
                  'columna': columna, 'version_reglas': RULES['version'],
                  'filas_antes': N, 'filas_despues': len(df_estandarizada),
                  'filas_modificadas_unicas': int(modificadas.sum()),
                  'celdas_valor_modificado': int(modificadas.sum()),
                  'celdas_tipo_modificado': 0, 'filas_excluidas': 0,
                  'repeticiones_consolidadas': 0, 'filas_generadas': 0})
    if columna in catalogos or columna == 'periodo_academico':
        aceptados = catalogos[columna] if columna in catalogos else periodos
        for indice, valor in antes.items():
            if valor and clave_catalogo(valor) not in aceptados:
                incidencias.append({'id_ejecucion': RUN_ID, 'id_fila_entrada': ids_fila.loc[indice],
                                    'columna': columna, 'valor': valor,
                                    'motivo': 'Categoría sin equivalencia; valor conservado'})

pasos_df = pd.DataFrame(pasos)
cambios_df = pd.DataFrame(cambios, columns=['id_ejecucion', 'paso', 'regla', 'id_fila_entrada',
    'registro_id', 'columna', 'valor_anterior', 'valor_posterior', 'tipo_anterior', 'tipo_posterior', 'motivo'])
incidencias_df = pd.DataFrame(incidencias, columns=['id_ejecucion', 'id_fila_entrada', 'columna', 'valor', 'motivo'])
display(pasos_df[['regla', 'columna', 'filas_antes', 'filas_despues', 'celdas_valor_modificado', 'filas_excluidas']])
''')
md('''
### Antes y después de las equivalencias

Cada fila de esta tabla describe una transformación de valor y cuántas celdas afecta.
La suma de cambios de varias columnas no equivale a filas eliminadas ni a personas.
''')
code('''
equivalencias = (cambios_df.groupby(['columna', 'valor_anterior', 'valor_posterior'], dropna=False)
                 .size().reset_index(name='celdas_modificadas'))
display(equivalencias)
display(Markdown(f"**Filas con algún cambio:** {cambios_df['id_fila_entrada'].nunique():,}. "
                 f"**Celdas modificadas:** {len(cambios_df):,}. **Filas eliminadas: 0.**"))
''')
code('''
comparacion_frecuencias = []
for columna in [*catalogos, 'periodo_academico']:
    antes = original[columna].value_counts(dropna=False)
    despues = df_estandarizada[columna].value_counts(dropna=False)
    for valor in sorted(set(antes.index) | set(despues.index)):
        comparacion_frecuencias.append({'columna': columna, 'valor': valor,
            'antes': int(antes.get(valor, 0)), 'despues': int(despues.get(valor, 0))})
frecuencias_df = pd.DataFrame(comparacion_frecuencias)
display(frecuencias_df[frecuencias_df['columna'].isin(['programa', 'documentos_completos',
                                                      'ciudad_residencia', 'periodo_academico'])])
''')
md('''
## Controles y casos que siguen pendientes

Unificar una tilde no resuelve un duplicado ni valida la facultad asignada. Se preservan
las ausencias y marcadores recibidos. El importe CRM continúa con el concepto calculado
en la integración; no se compara como si ese concepto estuviera confirmado para todas
las fuentes. Las columnas pendientes se conservaron sin modificar.
''')
code('''
sin_cambios = RULES['sin_transformacion_en_esta_etapa']
controles = pd.DataFrame([
    ['Filas conservadas', len(df_estandarizada) == N],
    ['18 columnas y orden original', list(df_estandarizada.columns) == HEADERS],
    ['Entrada en memoria intacta', df_entrada.equals(original)],
    ['Identificadores de negocio intactos', df_estandarizada[['registro_id', 'aspirante_id']].equals(original[['registro_id', 'aspirante_id']])],
    ['Fechas, puntajes, importes y duración intactos', df_estandarizada[sin_cambios].equals(original[sin_cambios])],
    ['Índice de filas completo y en el mismo orden', df_estandarizada.index.equals(original.index)],
    ['Todas las procedencias verificadas', len(origen_df) == N],
    ['Categorías desconocidas conservadas', all(df_estandarizada.loc[int(i[2:]) - 1, c] == v
        for i, c, v in incidencias_df[['id_fila_entrada', 'columna', 'valor']].itertuples(index=False, name=None))],
    ['Segunda aplicación no cambia valores', all(df_estandarizada[c].map(lambda v: estandarizar(v, c)).equals(df_estandarizada[c]) for c in HEADERS)],
    ['CSV de entrada intacto', hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA]
], columns=['Control', 'Correcto'])
assert controles['Correcto'].all()
display(controles)
display(pd.DataFrame([
    ['Repeticiones exactas adicionales', int(original.duplicated().sum()), int(df_estandarizada.duplicated().sum())],
    ['Aspirantes vacíos', int(original['aspirante_id'].eq('').sum()), int(df_estandarizada['aspirante_id'].eq('').sum())],
    ['Aspirantes nan', int(original['aspirante_id'].eq('nan').sum()), int(df_estandarizada['aspirante_id'].eq('nan').sum())],
    ['Programas vacíos', int(original['programa'].eq('').sum()), int(df_estandarizada['programa'].eq('').sum())],
    ['Programas sin especificar', int(original['programa'].eq('Sin Especificar').sum()), int(df_estandarizada['programa'].eq('Sin especificar').sum())],
    ['Facultades sin asignar', int(original['facultad'].eq('').sum()), int(df_estandarizada['facultad'].eq('').sum())]
], columns=['Situación', 'Antes', 'Después']))
''')
md('''
## Guardado del estado intermedio y de la auditoría

La carpeta de ejecución se identifica mediante versión de reglas y hashes de entrada,
reglas y código. Repetir la misma versión reconstruye el mismo estado de datos, sin
acumular nuevas filas. Los datos de partida no se sobrescriben.

Se exportan las 18 columnas de negocio, la procedencia comprobada, cambios por celda,
resumen por regla, equivalencias, controles y disposición de todas las filas. En esta
etapa cada entrada se conserva como salida individual.
''')
code('''
DATA_OUT = ROOT / 'data/interim/taller_2' / RUN_ID
AUDIT_OUT = ROOT / 'reports/limpieza/ejecuciones' / RUN_ID
DATA_OUT.mkdir(parents=True, exist_ok=True)
AUDIT_OUT.mkdir(parents=True, exist_ok=True)
csv_path = DATA_OUT / 'BaseUnificada_Estandarizada.csv'
xlsx_path = DATA_OUT / 'BaseUnificada_Estandarizada.xlsx'
df_estandarizada.to_csv(csv_path, index=False, encoding='utf-8-sig', lineterminator='\\n')
book = Workbook()
sheet = book.active
sheet.title = 'BaseUnificada_Estandarizada'
sheet.append(HEADERS)
output_rows = list(df_estandarizada.itertuples(index=False, name=None))
for fila in output_rows:
    sheet.append(fila)
table = Table(displayName='BaseUnificada_Estandarizada', ref=f'A1:{get_column_letter(len(HEADERS))}{N + 1}')
table.tableStyleInfo = TableStyleInfo(name='TableStyleMedium9', showRowStripes=True)
sheet.add_table(table)
sheet.freeze_panes = 'A2'
book.save(xlsx_path)
book.close()
preserve_empty_text(xlsx_path, output_rows)
assert pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_filter=False,
                   encoding='utf-8-sig').equals(df_estandarizada)
verify_book = load_workbook(xlsx_path, read_only=True, data_only=True)
verify_rows = list(verify_book['BaseUnificada_Estandarizada'].iter_rows(values_only=True))
assert list(verify_rows[0]) == HEADERS and verify_rows[1:] == output_rows
verify_book.close()
OUTPUT_SHA = hashlib.sha256(csv_path.read_bytes()).hexdigest()

disposicion_df = pd.DataFrame({'id_ejecucion': RUN_ID, 'id_fila_entrada': ids_fila,
    'registro_id_original': original['registro_id'], 'estado_destino': 'conservada',
    'id_registro_salida': ids_fila, 'fila_csv_salida': range(2, N + 2),
    'sha256_archivo_salida': OUTPUT_SHA, 'motivo': 'L02 no elimina ni consolida filas'})
for nombre, frame in {
    'L01_procedencia.csv': origen_df, 'L01_decisiones_pendientes.csv': decisiones_pendientes,
    'L02_registro_pasos.csv': pasos_df, 'L02_cambios_por_celda.csv': cambios_df,
    'L02_equivalencias_observadas.csv': equivalencias, 'L02_frecuencias_antes_despues.csv': frecuencias_df,
    'L02_categorias_desconocidas.csv': incidencias_df, 'L02_controles.csv': controles,
    'L02_disposicion_filas.csv': disposicion_df
}.items():
    frame.to_csv(AUDIT_OUT / nombre, index=False, encoding='utf-8-sig', lineterminator='\\n')

resumen = {'id_ejecucion': RUN_ID, 'ejecutado_en': datetime.now(ZoneInfo('America/Bogota')).isoformat(),
    'version_reglas': RULES['version'], 'sha256_entrada': INPUT_SHA, 'sha256_reglas': RULE_SHA,
    'sha256_codigo_notebook': CODE_SHA, 'filas_entrada': N, 'filas_salida': len(df_estandarizada),
    'columnas_negocio': len(HEADERS), 'filas_con_cambios': int(cambios_df['id_fila_entrada'].nunique()),
    'celdas_modificadas': len(cambios_df), 'filas_eliminadas': 0, 'filas_consolidadas': 0,
    'categorias_desconocidas': len(incidencias_df), 'controles_correctos': bool(controles['Correcto'].all()),
    'origenes_verificados': origen_df['origen_sistema'].value_counts().to_dict(),
    'repeticiones_exactas_antes': int(original.duplicated().sum()),
    'repeticiones_exactas_despues': int(df_estandarizada.duplicated().sum()),
    'archivos_datos': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [csv_path, xlsx_path]},
    'datos_intermedios': str(DATA_OUT.relative_to(ROOT)), 'auditoria': str(AUDIT_OUT.relative_to(ROOT)),
    'etapas': ['L00 entrada identificada', 'L01 procedencia verificada y decisiones documentadas', 'L02 estandarización textual'],
    'pendientes': ['L03 ausencias', 'L04 tipos y validaciones', 'L05 revisión de enriquecimiento',
                   'L06 duplicados exactos', 'L07 conciliación', 'L08 coherencia', 'L09 salida final']}
(AUDIT_OUT / 'resumen_ejecucion.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
latest = ROOT / 'reports/limpieza/ultima_estandarizacion.json'
latest.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
assert disposicion_df['id_fila_entrada'].nunique() == N
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA
display(pd.DataFrame([{'Etapa': 'L02', 'Filas de entrada': N, 'Filas de salida': N,
    'Filas con cambios': resumen['filas_con_cambios'], 'Celdas modificadas': len(cambios_df),
    'Filas eliminadas': 0, 'Controles correctos': resumen['controles_correctos']}]))
print('Datos intermedios:', DATA_OUT.relative_to(ROOT))
print('Auditoría:', AUDIT_OUT.relative_to(ROOT))
''')
md('''
## L03. Tratamiento de ausencias con su motivo

Esta etapa toma el resultado L02 sin descartar registros. Representa como ausentes
los vacíos de columnas distintas de los identificadores y cuatro marcadores explícitos:
Sin especificar en programa, Pendiente en puntaje, por definir en importe y No aplica
en fecha de matrícula. Cada celda mantiene en la auditoría su texto anterior y motivo.

Pendiente en documentos y Sin asignar en asesor siguen siendo categorías. Los vacíos
y nan de los identificadores permanecen intactos. Un vacío se registra como no informado
en la base; no se presume su causa institucional ni se convierte en cero.
''')
code('''
AUS_PATH = ROOT / 'config/limpieza/ausencias_v1.json'
AUS_RULES = json.loads(AUS_PATH.read_text(encoding='utf8'))
AUS_SHA = hashlib.sha256(AUS_PATH.read_bytes()).hexdigest()
L03_ID = f"{AUS_RULES['version']}_{OUTPUT_SHA[:10]}_{AUS_SHA[:8]}_{CODE_SHA[:8]}"
entrada_l03 = df_estandarizada.copy(deep=True)

def motivo_ausencia(valor, columna):
    if columna in AUS_RULES['columnas_excluidas']:
        return None
    if valor is None:
        return 'ya_ausente'
    if valor == '':
        return AUS_RULES['vacio_en_otra_columna']
    return AUS_RULES['marcadores_por_columna'].get(columna, {}).get(valor)

display(pd.DataFrame([
    {'Columna': 'Cualquier columna salvo identificadores', 'Valor recibido': 'Texto vacío',
     'Motivo': AUS_RULES['vacio_en_otra_columna']},
    *[{'Columna': c, 'Valor recibido': v, 'Motivo': motivo}
      for c, valores in AUS_RULES['marcadores_por_columna'].items() for v, motivo in valores.items()]
]))
''')
code('''
df_ausencias = entrada_l03.astype(object).copy(deep=True)
cambios_l03 = []
pasos_l03 = []
for numero, columna in enumerate(HEADERS, 1):
    valores = []
    afectados = 0
    for indice, valor in entrada_l03[columna].items():
        motivo = motivo_ausencia(valor, columna)
        if motivo is not None and motivo != 'ya_ausente':
            valores.append(None)
            afectados += 1
            cambios_l03.append({'id_ejecucion': L03_ID, 'paso': 'L03', 'regla': f'A{numero:02d}',
                'id_fila_entrada': ids_fila.loc[indice],
                'registro_id': original.loc[indice, 'registro_id'], 'columna': columna,
                'valor_anterior': valor, 'valor_posterior': None,
                'tipo_anterior': 'texto vacío' if valor == '' else 'texto',
                'tipo_posterior': 'ausente', 'motivo_ausencia': motivo,
                'imputado': False})
        else:
            valores.append(valor)
    df_ausencias[columna] = pd.Series(valores, index=entrada_l03.index, dtype=object)
    pasos_l03.append({'id_ejecucion': L03_ID, 'paso': 'L03', 'regla': f'A{numero:02d}',
        'columna': columna, 'filas_antes': N, 'filas_despues': len(df_ausencias),
        'celdas_ausencia_normalizada': afectados, 'filas_excluidas': 0,
        'repeticiones_consolidadas': 0, 'filas_imputadas': 0,
        'tratamiento': 'Identificador sin cambios' if columna in AUS_RULES['columnas_excluidas']
                       else 'Aplicación de reglas explícitas de ausencia'})

audit_l03 = pd.DataFrame(cambios_l03)
pasos_l03_df = pd.DataFrame(pasos_l03)
motivos_l03 = (audit_l03.groupby(['columna', 'motivo_ausencia']).size()
               .reset_index(name='celdas'))
columnas_con_ausencias = motivos_l03['columna'].unique()
comparacion_l03 = pd.DataFrame([{'Columna': c,
    'Textos vacíos antes': int(entrada_l03[c].eq('').sum()),
    'Ausencias normalizadas después': int(df_ausencias[c].isna().sum()),
    'Valores con información conservada': int(df_ausencias[c].notna().sum())}
    for c in columnas_con_ausencias])
display(motivos_l03)
display(comparacion_l03)
display(Markdown(f"**Celdas con ausencia normalizada:** {len(audit_l03):,}. "
    f"**Filas afectadas:** {audit_l03['id_fila_entrada'].nunique():,}. "
    "**Filas eliminadas o imputadas: 0.**"))
''')
md('''
### Controles de L03

Una ausencia normalizada no equivale a una corrección de su causa. Se mantiene el
detalle por celda para distinguir los motivos aunque Excel o CSV los presenten vacíos.
La relación de identificadores pospuestos es solo un listado de revisión, sin cambios.
''')
code('''
ids_columns = AUS_RULES['columnas_excluidas']
changed_keys = {(x['id_fila_entrada'], x['columna']) for x in cambios_l03}
sin_cambios_fuera_auditoria = all(
    df_ausencias.loc[i, c] == entrada_l03.loc[i, c]
    for i in entrada_l03.index for c in HEADERS if (ids_fila.loc[i], c) not in changed_keys)
valores_informados_intactos = all(
    valor is None or valor == entrada_l03.loc[i, c]
    for c in HEADERS for i, valor in df_ausencias[c].items())
idempotente_l03 = all(
    (None if motivo_ausencia(v, c) is not None else v) == v
    for c in HEADERS for v in df_ausencias[c])
controles_l03 = pd.DataFrame([
    ['Filas conservadas', len(df_ausencias) == N],
    ['18 columnas y orden original', list(df_ausencias.columns) == HEADERS],
    ['Identificadores intactos', df_ausencias[ids_columns].values.tolist() == entrada_l03[ids_columns].values.tolist()],
    ['Registro por cada celda convertida en ausente', len(audit_l03) == int(df_ausencias.isna().sum().sum())],
    ['Solo cambian las celdas auditadas', sin_cambios_fuera_auditoria],
    ['Valores informados intactos', valores_informados_intactos],
    ['Documentación pendiente conservada', df_ausencias['documentos_completos'].tolist() == entrada_l03['documentos_completos'].tolist()],
    ['Asesores sin asignar conservados', df_ausencias['asesor'].tolist() == entrada_l03['asesor'].tolist()],
    ['Sin cambios al repetir la regla', idempotente_l03],
    ['Entrada L02 intacta', df_estandarizada.equals(entrada_l03)],
    ['Archivo preparado intacto', hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA]
], columns=['Control', 'Correcto'])
assert controles_l03['Correcto'].all()
pospuestos_l03 = pd.DataFrame([{
    'id_fila_entrada': ids_fila.loc[i], 'registro_id': original.loc[i, 'registro_id'],
    'aspirante_id': original.loc[i, 'aspirante_id'],
    'situacion': 'Identificador vacío' if original.loc[i, 'aspirante_id'] == '' else 'Marcador nan',
    'decision': 'Conservado sin cambios hasta los cruces'}
    for i in original.index if original.loc[i, 'aspirante_id'] in {'', 'nan'}])
display(controles_l03)
display(pospuestos_l03.groupby('situacion').size().rename('Filas pospuestas').to_frame())
''')
md('''
### Exportación y motivos conservados

Los datos se guardan en CSV, Excel y JSONL. JSONL conserva explícitamente null y texto
vacío; el CSV representa ambos como celda vacía y requiere la auditoría para distinguirlos.
Cada una de las 5.640 entradas conserva su destino. Se mantienen separados los motivos
de ausencia, el inventario de identificadores pospuestos y el resumen de ejecución.
''')
code('''
L03_DATA = ROOT / 'data/interim/taller_2' / L03_ID
L03_AUDIT = ROOT / 'reports/limpieza/ejecuciones' / L03_ID
L03_DATA.mkdir(parents=True, exist_ok=True)
L03_AUDIT.mkdir(parents=True, exist_ok=True)
csv_l03 = L03_DATA / 'BaseUnificada_Ausencias.csv'
xlsx_l03 = L03_DATA / 'BaseUnificada_Ausencias.xlsx'
jsonl_l03 = L03_DATA / 'BaseUnificada_Ausencias.jsonl'
df_ausencias.to_csv(csv_l03, index=False, encoding='utf-8-sig', lineterminator='\\n', na_rep='')
records_l03 = df_ausencias.to_dict('records')
with jsonl_l03.open('w', encoding='utf8') as handle:
    for record in records_l03:
        handle.write(json.dumps(record, ensure_ascii=False) + '\\n')
book_l03 = Workbook()
sheet_l03 = book_l03.active
sheet_l03.title = 'BaseUnificada_Ausencias'
sheet_l03.append(HEADERS)
rows_l03 = list(df_ausencias.itertuples(index=False, name=None))
for row in rows_l03:
    sheet_l03.append(row)
table_l03 = Table(displayName='BaseUnificada_Ausencias', ref=f'A1:{get_column_letter(len(HEADERS))}{N + 1}')
table_l03.tableStyleInfo = TableStyleInfo(name='TableStyleMedium9', showRowStripes=True)
sheet_l03.add_table(table_l03)
sheet_l03.freeze_panes = 'A2'
book_l03.save(xlsx_l03)
book_l03.close()
preserve_empty_text(xlsx_l03, rows_l03)
verified_l03 = load_workbook(xlsx_l03, read_only=True, data_only=True)
assert list(verified_l03['BaseUnificada_Ausencias'].iter_rows(values_only=True))[1:] == rows_l03
verified_l03.close()
with jsonl_l03.open(encoding='utf8') as handle:
    assert [json.loads(line) for line in handle] == records_l03
with csv_l03.open(encoding='utf-8-sig', newline='') as handle:
    csv_read_l03 = list(csv.reader(handle))
assert csv_read_l03 == [HEADERS, *[['' if v is None else v for v in row] for row in rows_l03]]
L03_OUTPUT_SHA = hashlib.sha256(jsonl_l03.read_bytes()).hexdigest()
destinos_l03 = pd.DataFrame({'id_ejecucion': L03_ID, 'id_fila_entrada': ids_fila,
    'id_registro_salida': ids_fila, 'estado_destino': 'conservada',
    'fila_jsonl_salida': range(1, N + 1), 'sha256_salida_jsonl': L03_OUTPUT_SHA})
for nombre, frame in {
    'L03_cambios_por_celda.csv': audit_l03, 'L03_registro_pasos.csv': pasos_l03_df,
    'L03_motivos_ausencia.csv': motivos_l03, 'L03_completitud_antes_despues.csv': comparacion_l03,
    'L03_controles.csv': controles_l03, 'L03_disposicion_filas.csv': destinos_l03,
    'L03_identificadores_pospuestos.csv': pospuestos_l03
}.items():
    frame.to_csv(L03_AUDIT / nombre, index=False, encoding='utf-8-sig', lineterminator='\\n')
resumen_l03 = {
    'id_ejecucion': L03_ID, 'etapa': 'L03',
    'ejecutado_en': datetime.now(ZoneInfo('America/Bogota')).isoformat(),
    'entrada_l02_id': RUN_ID, 'sha256_entrada_l02_csv': OUTPUT_SHA,
    'sha256_reglas': AUS_SHA, 'sha256_codigo_notebook': CODE_SHA,
    'filas_entrada': N, 'filas_salida': len(df_ausencias), 'columnas': len(HEADERS),
    'celdas_ausencia_normalizada': len(audit_l03),
    'filas_afectadas': int(audit_l03['id_fila_entrada'].nunique()),
    'filas_eliminadas': 0, 'filas_consolidadas': 0, 'valores_imputados': 0,
    'identificadores_sin_cambios': True, 'identificadores_pospuestos': len(pospuestos_l03),
    'controles_correctos': bool(controles_l03['Correcto'].all()),
    'motivos': audit_l03['motivo_ausencia'].value_counts().to_dict(),
    'datos_intermedios': str(L03_DATA.relative_to(ROOT)), 'auditoria': str(L03_AUDIT.relative_to(ROOT)),
    'archivos_datos': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [csv_l03, xlsx_l03, jsonl_l03]},
    'limite': 'Sin tipado numérico o de fechas; motivos registrados y ninguna identidad resuelta.'}
(L03_AUDIT / 'resumen_ejecucion.json').write_text(json.dumps(resumen_l03, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
(ROOT / 'reports/limpieza/ultima_ausencias.json').write_text(json.dumps(resumen_l03, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
assert destinos_l03['id_fila_entrada'].nunique() == N
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA
display(pd.DataFrame([{'Etapa': 'L03', 'Filas de entrada': N, 'Filas de salida': len(df_ausencias),
    'Celdas con ausencia normalizada': len(audit_l03), 'Filas afectadas': resumen_l03['filas_afectadas'],
    'Filas eliminadas': 0, 'Valores imputados': 0}]))
print('Datos L03:', L03_DATA.relative_to(ROOT))
print('Auditoría L03:', L03_AUDIT.relative_to(ROOT))
''')
md('''
## L04. Tipos, fechas AAAA-MM-DD e importes COP

Se convierte cada valor informado mediante una regla explícita y se conserva su
representación anterior en la auditoría. Los nulos de L03 mantienen sus motivos.
Los identificadores permanecen como texto sin cambios.

Las fechas se interpretan con las cinco convenciones ya documentadas y se muestran
como AAAA-MM-DD. Si día y mes admiten dos lecturas, se registra una alerta aun cuando
se aplique la convención correspondiente al formato. Esto no confirma su exactitud
institucional ni resuelve las discrepancias entre Oracle y las otras fuentes.

El dinero se maneja con Decimal y escala de dos decimales, sin float ni redondeo
automático. En tablas se presenta como COP 2.200.000,00. Excel guarda un número con
formato monetario; sus separadores dependen de la configuración regional del equipo.
El CSV guarda 2200000.00, sin símbolo ni separadores de miles, para intercambio.
Los conceptos económicos distintos de las fuentes siguen pendientes de conciliación.
''')
code('''
from datetime import date
from decimal import Decimal
sys.path.insert(0, str(ROOT / 'src'))
from analitica_admisiones.tipado_limpieza import (
    interpretar_fecha, interpretar_decimal, interpretar_cop, interpretar_entero, mostrar_cop)

TYPES_PATH = ROOT / 'config/limpieza/tipos_v1.json'
TYPES = json.loads(TYPES_PATH.read_text(encoding='utf8'))
TYPES_SHA = hashlib.sha256(TYPES_PATH.read_bytes()).hexdigest()
MODULE_PATH = ROOT / 'src/analitica_admisiones/tipado_limpieza.py'
MODULE_SHA = hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest()
L04_ID = f"{TYPES['version']}_{L03_OUTPUT_SHA[:10]}_{TYPES_SHA[:8]}_{MODULE_SHA[:8]}_{CODE_SHA[:8]}"
entrada_l04 = df_ausencias.copy(deep=True)
convertir_columnas = [*TYPES['fechas'], TYPES['puntaje'], TYPES['monetaria'], TYPES['entero'], 'periodo_academico']
tipos_logicos = {c: 'texto' for c in HEADERS}
tipos_logicos.update({c: 'fecha' for c in TYPES['fechas']})
tipos_logicos.update({TYPES['puntaje']: 'decimal', TYPES['monetaria']: 'decimal COP, escala 2',
                     TYPES['entero']: 'entero', 'periodo_academico': 'entero identificador'})

def texto_intercambio(value):
    if value is None:
        return ''
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, 'f')
    return str(value)

def convertir_l04(value, columna):
    if columna in TYPES['fechas']:
        parsed = interpretar_fecha(value)
        return parsed.valor, parsed.formato, parsed.dia_mes_ambiguo
    if columna == TYPES['puntaje']:
        return interpretar_decimal(value), 'decimal_punto', False
    if columna == TYPES['monetaria']:
        return interpretar_cop(value), 'COP_decimal_punto_sin_miles', False
    if columna == TYPES['entero']:
        return interpretar_entero(value), 'entero_exacto', False
    if columna == 'periodo_academico':
        if value not in TYPES['periodo']:
            raise ValueError('Periodo sin equivalencia adoptada')
        return TYPES['periodo'][value], 'codigo_periodo_adoptado', False
    raise ValueError('Columna sin regla de conversión')

display(pd.DataFrame([{'Columna': c, 'Tipo lógico': tipos_logicos[c]} for c in HEADERS]))
''')
code('''
df_tipadas = entrada_l04.astype(object).copy(deep=True)
conversiones_l04 = []
errores_l04 = []
ambiguas_l04 = []
pasos_l04 = []
for numero, columna in enumerate(convertir_columnas, 1):
    values = []
    exitos = 0
    errores_columna = 0
    for indice, anterior in entrada_l04[columna].items():
        if anterior is None:
            values.append(None)
            continue
        try:
            posterior, formato, ambigua = convertir_l04(anterior, columna)
            values.append(posterior)
            exitos += 1
            conversiones_l04.append({'id_ejecucion': L04_ID, 'paso': 'L04', 'regla': f'T{numero:02d}',
                'id_fila_entrada': ids_fila.loc[indice], 'registro_id': original.loc[indice, 'registro_id'],
                'columna': columna, 'valor_anterior': anterior,
                'valor_posterior': texto_intercambio(posterior), 'tipo_anterior': 'texto',
                'tipo_posterior': tipos_logicos[columna], 'formato_origen': formato,
                'cambio_de_tipo': True, 'cambio_de_representacion': anterior != texto_intercambio(posterior)})
            if ambigua:
                ambiguas_l04.append({'id_fila_entrada': ids_fila.loc[indice], 'columna': columna,
                    'valor_original': anterior, 'fecha_interpretada': posterior.isoformat(),
                    'convencion_aplicada': formato, 'estado': 'Revisar convención con la fuente'})
        except (ValueError, ArithmeticError) as exc:
            values.append(None)
            errores_columna += 1
            errores_l04.append({'id_ejecucion': L04_ID, 'id_fila_entrada': ids_fila.loc[indice],
                'registro_id': original.loc[indice, 'registro_id'], 'columna': columna,
                'valor_original': anterior, 'motivo': str(exc), 'tratamiento': 'Ausente tipado con original conservado; sin imputación'})
    df_tipadas[columna] = pd.Series(values, index=entrada_l04.index, dtype=object)
    pasos_l04.append({'id_ejecucion': L04_ID, 'paso': 'L04', 'regla': f'T{numero:02d}',
        'columna': columna, 'filas_antes': N, 'filas_despues': len(df_tipadas),
        'valores_convertidos': exitos, 'ausencias_previas_conservadas': int(entrada_l04[columna].isna().sum()),
        'errores_conversion': errores_columna, 'filas_excluidas': 0, 'valores_imputados': 0})

conversiones_l04_df = pd.DataFrame(conversiones_l04)
errores_l04_df = pd.DataFrame(errores_l04, columns=['id_ejecucion', 'id_fila_entrada', 'registro_id', 'columna', 'valor_original', 'motivo', 'tratamiento'])
ambiguas_l04_df = pd.DataFrame(ambiguas_l04, columns=['id_fila_entrada', 'columna', 'valor_original', 'fecha_interpretada', 'convencion_aplicada', 'estado'])
pasos_l04_df = pd.DataFrame(pasos_l04)
display(pasos_l04_df)
indices_importe = df_tipadas.index[df_tipadas[TYPES['monetaria']].notna()][:5]
display(pd.DataFrame([{'Recibido': entrada_l04.loc[i, TYPES['monetaria']],
    'Valor exacto de intercambio': texto_intercambio(df_tipadas.loc[i, TYPES['monetaria']]),
    'Presentación Colombia': mostrar_cop(df_tipadas.loc[i, TYPES['monetaria']])} for i in indices_importe]))
''')
md('''
### Validaciones y alertas, sin corrección automática

La fecha de referencia es la de revisión, no un corte institucional confirmado.
Las fechas posteriores, periodos dispares, matrícula anterior a solicitud o documentación
pendiente se registran para revisar; no se modifican por esta condición. No se impone
una escala oficial de puntaje ni una tarifa de matrícula a partir del rango observado.
''')
code('''
referencia_l04 = date.fromisoformat(TYPES['fecha_referencia_alertas'])
alertas_l04 = []
origen_por_fila = origen_df.set_index('id_fila_entrada')['origen_sistema'].to_dict()
def alerta_l04(indice, columna, motivo, detalle):
    ident = ids_fila.loc[indice]
    alertas_l04.append({'id_ejecucion': L04_ID, 'id_fila_entrada': ident,
        'registro_id': original.loc[indice, 'registro_id'], 'origen_sistema': origen_por_fila[ident],
        'columna': columna, 'alerta': motivo, 'detalle': detalle, 'accion': 'Conservar y revisar'})

for item in ambiguas_l04:
    indice = int(item['id_fila_entrada'][2:]) - 1
    alerta_l04(indice, item['columna'], 'formato_dia_mes_ambiguo',
        f"{item['valor_original']} interpretado como {item['fecha_interpretada']} mediante {item['convencion_aplicada']}")
for indice, row in df_tipadas.iterrows():
    solicitud, matricula = row['fecha_solicitud'], row['fecha_matricula']
    for columna in TYPES['fechas']:
        value = row[columna]
        if value is not None and value > referencia_l04:
            alerta_l04(indice, columna, 'fecha_posterior_a_referencia', value.isoformat())
    if solicitud is not None and matricula is not None and matricula < solicitud:
        alerta_l04(indice, 'fecha_matricula', 'matricula_anterior_a_solicitud',
                    f'Solicitud {solicitud.isoformat()}; matrícula {matricula.isoformat()}')
    periodo = row['periodo_academico']
    if solicitud is not None and periodo is not None and solicitud.year > periodo // 10:
        alerta_l04(indice, 'periodo_academico', 'solicitud_posterior_al_anio_del_periodo',
                    f'Solicitud {solicitud.isoformat()}; periodo {periodo}')
    for columna in [TYPES['puntaje'], TYPES['monetaria'], TYPES['entero']]:
        value = row[columna]
        if value is not None and value < 0:
            alerta_l04(indice, columna, 'valor_negativo', texto_intercambio(value))
    if row['duracion_semestres'] is not None and row['duracion_semestres'] not in {2, 8, 10}:
        alerta_l04(indice, 'duracion_semestres', 'duracion_fuera_del_catalogo_de_trabajo', str(row['duracion_semestres']))
    if row['estado_proceso'] == 'Matriculado' and row['documentos_completos'] in {'No', 'Pendiente'}:
        alerta_l04(indice, 'documentos_completos', 'matriculado_con_documentacion_no_completa', row['documentos_completos'])

alertas_l04_df = pd.DataFrame(alertas_l04, columns=['id_ejecucion', 'id_fila_entrada', 'registro_id',
    'origen_sistema', 'columna', 'alerta', 'detalle', 'accion'])
display(alertas_l04_df.groupby('alerta').agg(Incidencias=('id_fila_entrada', 'size'),
    Filas_distintas=('id_fila_entrada', 'nunique')).reset_index())
display(ambiguas_l04_df.head(8))
display(errores_l04_df)
display(df_tipadas['periodo_academico'].value_counts(dropna=False).rename('Registros por código de periodo').to_frame())
''')
code('''
def tipo_correcto(value, columna):
    if value is None:
        return True
    if columna in TYPES['fechas']:
        return type(value) is date
    if columna in {TYPES['puntaje'], TYPES['monetaria']}:
        return isinstance(value, Decimal) and value.is_finite()
    if columna in {TYPES['entero'], 'periodo_academico'}:
        return type(value) is int
    return isinstance(value, str)

errores_index = {(r['id_fila_entrada'], r['columna']) for r in errores_l04}
informados_preservados = all(
    (ids_fila.loc[i], c) in errores_index or entrada_l04.loc[i, c] is None or
    (interpretar_decimal(entrada_l04.loc[i, c]) == df_tipadas.loc[i, c])
    for c in [TYPES['puntaje'], TYPES['monetaria'], TYPES['entero']]
    for i in entrada_l04.index)
ausencias_preservadas = all(
    df_tipadas.loc[i, c] is None
    for c in HEADERS for i in entrada_l04.index if entrada_l04.loc[i, c] is None)
columnas_iguales = [c for c in HEADERS if c not in convertir_columnas]
controles_l04 = pd.DataFrame([
    ['Filas y orden conservados', len(df_tipadas) == N and df_tipadas.index.equals(entrada_l04.index)],
    ['18 columnas conservadas', list(df_tipadas.columns) == HEADERS],
    ['Identificadores intactos', df_tipadas[ids_columns].values.tolist() == entrada_l04[ids_columns].values.tolist()],
    ['Columnas fuera del tipado intactas', df_tipadas[columnas_iguales].values.tolist() == entrada_l04[columnas_iguales].values.tolist()],
    ['Tipos lógicos válidos', all(tipo_correcto(v, c) for c in HEADERS for v in df_tipadas[c])],
    ['Ausencias L03 conservadas', ausencias_preservadas],
    ['Números informados sin cambio de valor', informados_preservados],
    ['COP con escala exacta de dos decimales', all(v is None or v.as_tuple().exponent == -2 for v in df_tipadas[TYPES['monetaria']])],
    ['Cada conversión está auditada', len(conversiones_l04_df) == int(pasos_l04_df['valores_convertidos'].sum())],
    ['Cada fallo está auditado', len(errores_l04_df) == int(pasos_l04_df['errores_conversion'].sum())],
    ['Entrada L03 intacta', df_ausencias.equals(entrada_l04)],
    ['Archivo preparado intacto', hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA]
], columns=['Control', 'Correcto'])
assert controles_l04['Correcto'].all()
display(controles_l04)
''')
md('''
### Salida tipada y formatos de intercambio

Excel contiene fechas reales con formato yyyy-mm-dd, periodos y duración enteros,
puntajes numéricos e importes numéricos identificados como COP. Se comprueba el regreso
de cada valor, incluida la precisión de centavos.

JSONL escribe decimales como literales numéricos exactos y las fechas como texto ISO;
al leerlo se debe utilizar Decimal para los números decimales y el esquema registrado
para recuperar fechas. CSV mantiene ISO, punto decimal y coma delimitadora. No se debe
guardar el CSV otra vez desde Excel sin revisar sus separadores y sus tipos.
''')
code('''
L04_DATA = ROOT / 'data/interim/taller_2' / L04_ID
L04_AUDIT = ROOT / 'reports/limpieza/ejecuciones' / L04_ID
L04_DATA.mkdir(parents=True, exist_ok=True)
L04_AUDIT.mkdir(parents=True, exist_ok=True)
csv_l04 = L04_DATA / 'BaseUnificada_Tipada.csv'
xlsx_l04 = L04_DATA / 'BaseUnificada_Tipada.xlsx'
jsonl_l04 = L04_DATA / 'BaseUnificada_Tipada.jsonl'
typed_rows = list(df_tipadas.itertuples(index=False, name=None))
serialized_l04 = [[texto_intercambio(v) for v in row] for row in typed_rows]
with csv_l04.open('w', encoding='utf-8-sig', newline='') as handle:
    writer = csv.writer(handle, lineterminator='\\n')
    writer.writerow(HEADERS)
    writer.writerows(serialized_l04)

def literal_json_l04(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    if isinstance(value, date):
        return json.dumps(value.isoformat())
    return json.dumps(value, ensure_ascii=False)

with jsonl_l04.open('w', encoding='utf8') as handle:
    for row in typed_rows:
        handle.write('{' + ','.join(json.dumps(c) + ':' + literal_json_l04(v)
                                   for c, v in zip(HEADERS, row)) + '}\\n')
book_l04 = Workbook()
sheet_l04 = book_l04.active
sheet_l04.title = 'BaseUnificada_Tipada'
sheet_l04.append(HEADERS)
for row in typed_rows:
    sheet_l04.append(row)
for j, columna in enumerate(HEADERS, 1):
    if columna in TYPES['fechas']:
        fmt = TYPES['formato_excel_fecha']
    elif columna == TYPES['monetaria']:
        fmt = TYPES['formato_excel_moneda']
    elif columna == TYPES['puntaje']:
        fmt = '0.00'
    elif columna in {TYPES['entero'], 'periodo_academico'}:
        fmt = '0'
    else:
        fmt = '@'
    for i in range(2, N + 2):
        sheet_l04.cell(i, j).number_format = fmt
    sheet_l04.column_dimensions[get_column_letter(j)].width = 24 if columna != 'programa' else 42
table_l04 = Table(displayName='BaseUnificada_Tipada', ref=f'A1:{get_column_letter(len(HEADERS))}{N + 1}')
table_l04.tableStyleInfo = TableStyleInfo(name='TableStyleMedium9', showRowStripes=True)
sheet_l04.add_table(table_l04)
sheet_l04.freeze_panes = 'A2'
book_l04.save(xlsx_l04)
book_l04.close()
preserve_empty_text(xlsx_l04, typed_rows)

def reconstruir_celda_l04(value, columna):
    if value is None:
        return None
    if columna in TYPES['fechas']:
        if isinstance(value, datetime):
            assert value.time().isoformat() == '00:00:00'
            return value.date()
        return value if isinstance(value, date) else date.fromisoformat(value)
    if columna == TYPES['monetaria']:
        return interpretar_cop(str(value))
    if columna == TYPES['puntaje']:
        return interpretar_decimal(str(value))
    if columna in {TYPES['entero'], 'periodo_academico'}:
        return interpretar_entero(str(value))
    return value

checked_l04 = load_workbook(xlsx_l04, read_only=True, data_only=True)
xlsx_read = list(checked_l04['BaseUnificada_Tipada'].iter_rows(values_only=True))
assert list(xlsx_read[0]) == HEADERS
assert [tuple(reconstruir_celda_l04(v, c) for c, v in zip(HEADERS, row)) for row in xlsx_read[1:]] == typed_rows
assert checked_l04['BaseUnificada_Tipada']['J2'].number_format == TYPES['formato_excel_moneda']
checked_l04.close()
with jsonl_l04.open(encoding='utf8') as handle:
    json_read_l04 = [json.loads(line, parse_float=Decimal) for line in handle]
assert [tuple(reconstruir_celda_l04(r[c], c) for c in HEADERS) for r in json_read_l04] == typed_rows
with csv_l04.open(encoding='utf-8-sig', newline='') as handle:
    assert list(csv.reader(handle)) == [HEADERS, *serialized_l04]

schema_l04 = pd.DataFrame([{'columna': c, 'tipo_logico': tipos_logicos[c],
    'valores_informados': int(df_tipadas[c].notna().sum()), 'ausentes': int(df_tipadas[c].isna().sum()),
    'representacion_csv': 'AAAA-MM-DD' if c in TYPES['fechas'] else
                         'Punto decimal, sin miles ni símbolo' if c == TYPES['monetaria'] else tipos_logicos[c]}
    for c in HEADERS])
destinos_l04 = pd.DataFrame({'id_ejecucion': L04_ID, 'id_fila_entrada': ids_fila,
    'id_registro_salida': ids_fila, 'estado_destino': 'conservada', 'fila_salida': range(2, N + 2),
    'sha256_csv_salida': hashlib.sha256(csv_l04.read_bytes()).hexdigest()})
for nombre, frame in {
    'L04_conversiones_por_celda.csv': conversiones_l04_df, 'L04_registro_pasos.csv': pasos_l04_df,
    'L04_errores_conversion.csv': errores_l04_df, 'L04_fechas_ambiguas.csv': ambiguas_l04_df,
    'L04_alertas_validacion.csv': alertas_l04_df, 'L04_controles.csv': controles_l04,
    'L04_esquema.csv': schema_l04, 'L04_disposicion_filas.csv': destinos_l04
}.items():
    frame.to_csv(L04_AUDIT / nombre, index=False, encoding='utf-8-sig', lineterminator='\\n')
resumen_l04 = {'id_ejecucion': L04_ID, 'etapa': 'L04',
    'ejecutado_en': datetime.now(ZoneInfo('America/Bogota')).isoformat(),
    'entrada_l03_id': L03_ID, 'sha256_entrada_l03_jsonl': L03_OUTPUT_SHA,
    'sha256_reglas': TYPES_SHA, 'sha256_modulo_tipado': MODULE_SHA, 'sha256_codigo_notebook': CODE_SHA,
    'filas_entrada': N, 'filas_salida': len(df_tipadas), 'columnas': len(HEADERS),
    'celdas_convertidas': len(conversiones_l04_df), 'errores_conversion': len(errores_l04_df),
    'alertas_validacion': len(alertas_l04_df), 'filas_con_alertas': int(alertas_l04_df['id_fila_entrada'].nunique()),
    'alertas_por_tipo': alertas_l04_df['alerta'].value_counts().to_dict(),
    'ausencias_conservadas': int(df_tipadas.isna().sum().sum()), 'identificadores_sin_cambios': True,
    'filas_eliminadas': 0, 'valores_imputados': 0, 'controles_correctos': bool(controles_l04['Correcto'].all()),
    'tipos_logicos': tipos_logicos, 'formato_fecha': 'AAAA-MM-DD', 'moneda': 'COP', 'escala_monetaria': 2,
    'periodos': {str(k): int(v) for k, v in df_tipadas['periodo_academico'].value_counts().items()},
    'datos_intermedios': str(L04_DATA.relative_to(ROOT)), 'auditoria': str(L04_AUDIT.relative_to(ROOT)),
    'archivos_datos': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [csv_l04, xlsx_l04, jsonl_l04]},
    'limites': ['Convenciones ambiguas y fechas de negocio pendientes de validación',
               'Importes de distintas fuentes no acreditan equivalencia de concepto ni pagos',
               'CSV conserva punto decimal; presentación Excel depende de la configuración regional']}
(L04_AUDIT / 'resumen_ejecucion.json').write_text(json.dumps(resumen_l04, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
(ROOT / 'reports/limpieza/ultima_tipificacion.json').write_text(json.dumps(resumen_l04, ensure_ascii=False, indent=2) + '\\n', encoding='utf8')
assert destinos_l04['id_fila_entrada'].nunique() == N
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUT_SHA
display(schema_l04)
display(pd.DataFrame([{'Etapa': 'L04', 'Filas': N, 'Columnas': len(HEADERS),
    'Celdas convertidas': len(conversiones_l04_df), 'Errores de conversión': len(errores_l04_df),
    'Alertas para revisión': len(alertas_l04_df), 'Filas eliminadas': 0}]))
print('Datos L04:', L04_DATA.relative_to(ROOT))
print('Auditoría L04:', L04_AUDIT.relative_to(ROOT))
''')
from celdas_cierre_limpieza import agregar_cierre
agregar_cierre(md, code)

md('''
## Qué falta para aprobar la versión final

L03 ya distingue las ausencias de las demás variables. Los cuatro nan y los vacíos de
aspirante_id se mantienen registrados y sin modificar hasta la revisión de cruces.
L04 ya representa fechas y números y utiliza el código entero del periodo.
Las fechas dudosas y los importes con conceptos diferentes siguen señalados.

L05 revisó el catálogo; L06 consolidó repeticiones exactas con trazabilidad; L07
identificó conflictos entre fuentes. L08 documentó la coherencia administrativa y
L09 exportó la versión de revisión, sus controles y las decisiones pendientes.
Las decisiones del reporte deben validarse y aplicarse mediante reglas versionadas
antes de aprobar solicitudes únicas y los indicadores administrativos definitivos.

El notebook anterior sigue respaldando la exploración inicial de 5.040 filas. Este
cuaderno respalda el trabajo sobre la base consolidada de 5.640 filas.
''')

notebook = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"display_name": "Python del proyecto uv", "language": "python", "name": "python3"}})
path = ROOT / "notebooks/02_limpieza_base_unificada.ipynb"
nbf.write(notebook, path)
print(f"Notebook construido: {path}; {sum(c.cell_type == 'code' for c in cells)} celdas de código")
