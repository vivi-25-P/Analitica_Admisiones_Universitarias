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

**Esta primera ejecución cubre L00, L01 y L02:** identificación de la entrada,
reconstrucción comprobada de la procedencia y estandarización textual mediante
catálogos explícitos. L01 deja documentadas las decisiones económicas, temporales
y de catálogo que siguen pendientes; no las da por resueltas.

**No se elimina ninguna fila.** No se imputan valores, se fusionan solicitudes,
se cambian importes ni se interpretan o corrigen fechas. El resultado es un estado
intermedio, no una base limpia definitiva. Los valores vacíos, nan, Pendiente,
No aplica y por definir se conservan para las etapas posteriores. Los nan de
identificadores seguirán sin modificarse hasta la revisión de cruces.

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
## Cómo continuaremos

L03 distinguirá los motivos de ausencia de las demás variables. Los cuatro nan de
aspirante_id se mantienen registrados y sin modificar hasta la revisión de cruces.
L04 representará fechas y números, revisará excepciones y tratará el código entero del
periodo. Las fechas dudosas y los importes con conceptos diferentes seguirán señalados.

Después se revisará el enriquecimiento del catálogo en L05. Solo en L06 y L07 se
evaluará retirar repeticiones o conciliar filas. Cada entrada mantendrá un destino
documentado y se actualizarán los denominadores. Las reglas que no cuenten con evidencia
no se convertirán en correcciones inventadas.

El notebook anterior sigue respaldando la exploración inicial de 5.040 filas. Este
cuaderno respalda el trabajo sobre la base consolidada de 5.640 filas.
''')

notebook = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"display_name": "Python del proyecto uv", "language": "python", "name": "python3"}})
path = ROOT / "notebooks/02_limpieza_base_unificada.ipynb"
nbf.write(notebook, path)
print(f"Notebook construido: {path}; {sum(c.cell_type == 'code' for c in cells)} celdas de código")
