"""Construye el notebook de análisis administrativo sin ejecutar sus celdas."""

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
# Análisis administrativo de BaseUnificada

Responde una pregunta general, tres específicas y una línea adicional de segmentos.
Usa la entrega validada y los criterios de elegibilidad del notebook 03.
El proceso de limpieza permanece en el notebook 02. No se modifica el Excel,
PostgreSQL ni Drive. El dashboard se construirá después con las mismas definiciones.

Los porcentajes describen registros, no personas independientes confirmadas.
No se fuerza una conclusión favorable a un canal o segmento. No se aplican pruebas
de significación de manera automática y no se identifica no significación con equivalencia.
La marca de menos de 30 registros es prudencia visual, no una garantía de precisión.
''')
code('''
from pathlib import Path
import sys
import pandas as pd
from IPython.display import display, Markdown, Image

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'pyproject.toml').exists())
sys.path.insert(0, str(ROOT / 'src'))
from analitica_admisiones.analisis_administrativo import AnalisisAdministrativo

analisis = AnalisisAdministrativo(ROOT)
display(pd.DataFrame([{'Registros':len(analisis.base), 'Columnas':len(analisis.base.columns),
    'Unidad':'Registro de solicitud de origen', 'SHA256 del Excel':analisis.input_sha}]))
''')
md('''
## 1. Pregunta general y demanda por programa

¿Cómo se distribuyen las solicitudes por programa, modalidad y canal, y qué se observa
en los estados del proceso? Las cantidades usan los 5.500 registros. Sin información
es una etiqueta para presentar programas ausentes y no una imputación del dato maestro.
Los periodos representan semestres de ingreso. No se deducen desde la fecha de solicitud.
''')
code('''
display(analisis.volumen())
for nombre in ['programa','modalidad','canal_captacion','estado_proceso','programa_periodo_academico']:
    display(Markdown('### ' + nombre.replace('_',' ')))
    display(analisis.tables[nombre])
''')
md('''
## 2. Canales comparables

Se muestran las proporciones brutas y una estandarización descriptiva con pesos comunes
de programa, modalidad y periodo. Solo se incluyen estratos donde están los seis canales.
La tabla informa su cobertura y las celdas pequeñas. No es una comparación causal ni
una tasa definitiva de conversión. La igualdad de composición no resuelve la dependencia
entre solicitudes del mismo aspirante o los candidatos Oracle.
''')
code('''
display(analisis.canales_comparables())
display(analisis.tables['pesos_estratos_comunes'].head(10))
''')
md('''
## 3. Documentación, asesor, puntajes, tiempos y recurrencia

La tercera pregunta específica del informe se responde con distribución de estados
según documentación y asesor, incluidos sus cruces por programa, modalidad y periodo.
El intervalo entre solicitud y matrícula es un complemento, no tiempo por etapa.
Las franjas de puntaje son descriptivas y no representan reglas institucionales de aprobación.
Los códigos se cuentan por origen. La recurrencia no se declara duplicado automáticamente.
''')
code('''
display(analisis.seguimiento())
for nombre in ['documentos_completos','documentacion_estado','asesor',
               'franja_puntaje_estados_porcentajes','intervalos_por_documentacion',
               'recurrencia_codigos','importes_por_programa']:
    display(Markdown('### ' + nombre.replace('_',' ')))
    display(analisis.tables[nombre])
''')
md('''
## 4. Segmentos de interés y sensibilidad

Las combinaciones de ciudad, programa y modalidad se ordenan por volumen, sin afirmar
que sean nichos de mercado confirmados. Los cruces finos por canal y periodo se guardan
completos con marca de grupos pequeños. Se comprueba un escenario hipotético de contar
una vez los 49 pares compatibles. Las 500 filas Oracle permanecen en la entrega.
No se resuelve con ese escenario la identidad de los otros 451 pares.
''')
code('''
display(analisis.segmentos())
display(analisis.tables['segmentos_completos'].describe(include='all'))
''')
md('''
## 5. Qué cambió después de limpiar y de incorporar fuentes

Primero se alinean categorías sobre las mismas 5.040 filas originales. Después se
compara esa fuente con sus 5.000 registros conciliados. Finalmente se incorporan los
500 registros Oracle. El aumento de fuente no se presenta como efecto de limpieza
o crecimiento institucional. Los archivos originales se mantienen intactos.
''')
code('''
display(analisis.antes_despues())
display(analisis.tables['evolucion_cantidades'])
display(analisis.tables['antes_despues_ambitos_separados'])
''')
md('''
## 6. Visualizaciones

Cada figura responde a una pregunta y conserva la unidad y cobertura. La guía separa
las tres figuras principales del material de apoyo. Los importes no se usan para
deducir tarifas o recaudo y los estados no se dibujan como transiciones de un embudo.
''')
code('''
for figura in analisis.graficar():
    display(Image(filename=str(analisis.fig / figura['archivo'])))
''')
md('''
## 7. Interpretación y acciones propuestas

Cada hallazgo distingue hecho, acción y límite. Los responsables son propuestas
funcionales y no asignaciones realizadas. Las metas se definirán después de revisar
capacidad, costos y una línea de referencia. El informe en Drive no se edita automáticamente.
''')
code('''
display(analisis.redactar())
display(analisis.tables['acciones_propuestas'])
display(Markdown((analisis.out / 'seccion_informe_drive.md').read_text()))
''')
md('''
## 8. Controles y archivos

Se verifica que las tablas reconcilien, que los pesos y ámbitos sean válidos y que la
entrega y las entradas no cambien. Las figuras, tablas, redacción administrativa,
guía de inserción y metadatos están en reports/analisis_administrativo.
El notebook respalda el análisis y prepara la fase de Power BI. No crea un PBIX.
''')
code('''
display(analisis.cerrar(ROOT / 'notebooks/04_analisis_administrativo.ipynb'))
print('Sección para el informe:', analisis.out / 'seccion_informe_drive.md')
print('Guía de figuras:', analisis.out / 'guia_insercion_y_figuras.md')
print('Respaldo completo:', analisis.out / 'reporte_analisis_administrativo.md')
''')

notebook = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {
    'display_name':'Python del proyecto uv','language':'python','name':'python3'}})
path = ROOT / 'notebooks/04_analisis_administrativo.ipynb'
nbf.write(notebook,path)
print(path)
