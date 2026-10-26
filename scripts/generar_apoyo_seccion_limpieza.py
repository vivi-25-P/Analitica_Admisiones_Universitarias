"""Genera una figura y una sección breve para el informe administrativo en Drive."""
from pathlib import Path
import csv
import hashlib
import json
import os
import shutil
from collections import Counter

os.environ.setdefault('MPLCONFIGDIR','/tmp/admisiones-matplotlib')
Path(os.environ['MPLCONFIGDIR']).mkdir(parents=True,exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/apoyo_informe_drive'
OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'reports/limpieza/ultima_entrega.json'
summary=json.loads(source.read_text())
assert summary['filas_salida']==5500 and summary['columnas']==18
assert summary['oracle_conservados']==500 and summary['aportes_crm_integrados']==100
assert 5640-38-2-summary['aportes_crm_integrados']==summary['filas_salida']

sequence=[
    {'etapa':'Entrada integrada','registros':5640,'tratamiento':'Fuentes principal, CRM y Oracle'},
    {'etapa':'Repeticiones exactas','registros':5602,'tratamiento':'38 repeticiones exactas consolidadas'},
    {'etapa':'Registros parciales','registros':5600,'tratamiento':'Dos parciales complementados y consolidados'},
    {'etapa':'Conciliación CRM','registros':5500,'tratamiento':'100 aportes incorporados a solicitudes existentes'}]
with (OUT/'conciliacion_registros.csv').open('w',encoding='utf-8-sig',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(sequence[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(sequence)

plt.rcParams.update({'font.family':'DejaVu Sans','figure.dpi':160})
fig,ax=plt.subplots(figsize=(8,4.2))
fig.patch.set_facecolor('white');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ax.text(.5,.96,'Conciliación de registros durante la limpieza',ha='center',va='top',fontsize=14,weight='bold',color='#173F58')
ax.text(.5,.83,'Entrada: 5.040 principal + 100 CRM + 500 Oracle',ha='center',fontsize=10.5,color='#52636E')
centers=[.125,.375,.625,.875]
labels=['Entrada\nintegrada','Repeticiones\nexactas','Registros\nparciales','BaseUnificada\nEntregable']
notes=['Versión de partida\ncon 18 columnas','38 repeticiones\nconsolidadas','2 parciales\nconsolidados','100 aportes CRM\nincorporados']
for j,(x,item) in enumerate(zip(centers,sequence)):
    color='#226C95' if j<3 else '#287F79'
    box=FancyBboxPatch((x-.105,.39),.21,.29,boxstyle='round,pad=0.012,rounding_size=0.025',
                       facecolor=color,edgecolor='none')
    ax.add_patch(box)
    ax.text(x,.735,labels[j],ha='center',va='center',fontsize=11,color='#173F58')
    ax.text(x,.565,f"{item['registros']:,}".replace(',','.'),ha='center',va='center',fontsize=25,weight='bold',color='white')
    ax.text(x,.455,'registros',ha='center',va='center',fontsize=11,color='white')
    ax.text(x,.28,notes[j],ha='center',va='center',fontsize=11,color='#344B58')
    if j<3:
        ax.add_patch(FancyArrowPatch((x+.116,.535),(centers[j+1]-.116,.535),arrowstyle='-|>',mutation_scale=15,linewidth=1.6,color='#8296A2'))
ax.text(.5,.12,'500 registros Oracle incluidos. Se conservan 18 columnas.',
        ha='center',fontsize=11,color='#287F79',weight='bold')
ax.text(.5,.035,'La figura cuenta registros, no personas únicas.',ha='center',fontsize=9,color='#52636E')
fig.subplots_adjust(left=.015,right=.985,top=.98,bottom=.02)
for ext in ['png','pdf']:fig.savefig(OUT/f'conciliacion_registros.{ext}',bbox_inches='tight',facecolor='white')
plt.close(fig)

public=ROOT/summary['datos_salida']/'entregable'
with (public/'Control_Calidad.csv').open(encoding='utf-8-sig',newline='') as handle:
    quality=list(csv.DictReader(handle))
assert len(quality)==5500
received=Counter(r['estado_recibido'] for r in quality)
analytical=Counter(r['estado_analitico'] for r in quality)
states=['Nuevo','Admitido','Matriculado','Inscrito','Documentación pendiente','No admitido','Retirado']
fig,ax=plt.subplots(figsize=(9,4.8))
y=list(range(len(states)))
ax.barh([v-.2 for v in y],[received[s] for s in states],height=.38,color='#91AEBE',label='Estado recibido')
bars=ax.barh([v+.2 for v in y],[analytical[s] for s in states],height=.38,color='#226C95',label='Estado homologado')
ax.bar_label(bars,padding=3)
ax.set_yticks(y,states);ax.invert_yaxis()
ax.set_xlabel('Registros integrados, mismo conjunto de 5.500 filas')
ax.set_title('Homologación de estados sin modificar la cantidad de registros')
ax.legend(loc='lower right');ax.spines[['top','right']].set_visible(False)
fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(OUT/f'homologacion_estados.{ext}',bbox_inches='tight',facecolor='white')
plt.close(fig)
for ext in ['png','pdf']:
    shutil.copy2(ROOT/summary['figuras']/f'05_cobertura_temporal.{ext}',OUT/f'cobertura_temporal.{ext}')
(OUT/'ubicacion_graficos.md').write_text('''# Ubicación de los gráficos en el informe

| Figura | Ubicación recomendada | Qué demuestra |
| :--- | :--- | :--- |
| Conciliación de registros | Limpieza y transformación | Cómo se pasa de 5.640 a 5.500 filas, conservando Oracle. |
| Homologación de estados | Limpieza y transformación, si se desea mostrar el efecto de la regla | Nuevo se agrupa con Admitido sobre el mismo conjunto de 5.500 filas. No son nuevas admisiones. |
| Cobertura temporal | Revisión de fechas dentro de limpieza, o al inicio del análisis temporal | Diferencias de cobertura entre fuentes y observaciones de fecha. |
| Distribución actual de estados | Análisis descriptivo de la base integrada | Cómo se distribuyen los registros entre los estados resultantes. |
| Programas, modalidades, canales, ciudades e importes | Análisis descriptivo de la base integrada | Patrones administrativos de los registros disponibles. |

Para una sección breve, conservar la tabla de tratamientos y la figura de conciliación. Si las fechas son un punto central, añadir cobertura temporal con su explicación. La homologación de estados sirve como evidencia adicional y puede ir en un anexo. No es necesario repetir todas las figuras del análisis descriptivo dentro de limpieza.
''',encoding='utf8')

text='# Limpieza y transformación de la base unificada\n\n## Verificación y preparación\n\nLa limpieza se realizó sobre los 5.640 registros y 18 columnas obtenidos después de integrar las fuentes y complementar el catálogo de programas. Se verificó su procedencia y se conservaron los archivos originales como respaldo. Los cambios quedaron registrados para identificar qué información se modificó y cuál fue su origen.\n\nSe uniformaron las categorías y los tipos de información. Las fechas se representaron en formato de año, mes y día. Los valores económicos se conservaron en pesos colombianos y los periodos se homologaron como códigos de semestre de ingreso. Los valores no disponibles se mantuvieron como ausencias, sin sustituirlos por cero, promedios o categorías supuestas.\n\n## Tratamientos aplicados\n\n**Tabla 5. Síntesis de la limpieza y transformación**\n\n| Aspecto | Tratamiento realizado | Resultado |\n| :--- | :--- | :--- |\n| Categorías y estados | Se unificaron variantes de escritura y Nuevo se agrupó analíticamente con Admitido. Matriculado permaneció separado y se conservó el estado recibido. | Categorías comparables, con el criterio de agrupación documentado. |\n| Ausencias | Se homologaron los vacíos y marcadores de información no disponible. Pendiente en documentación y Sin asignar en asesor conservaron su significado. | Ausencias identificadas sin inventar valores. |\n| Registros repetidos y parciales | Se consolidaron 38 repeticiones exactas y dos registros complementarios, recuperando cinco valores desde sus otras filas. | Se conservaron los vínculos con las entradas originales. |\n| Información CRM | Se incorporaron 100 aportes a las solicitudes correspondientes. Se conservaron 87 importes principales y se recuperaron 13 desde matrícula base CRM. Los derechos administrativos quedaron separados. | Se evitó repetir las solicitudes y se recuperó información económica disponible. |\n| Información Oracle | Se conservaron sus 500 registros. Las coincidencias con la principal se identificaron como candidatas, sin eliminarlas por semejanza. | Oracle permanece dentro de la base y del análisis integrado. |\n| Fechas y periodos | Se conservaron los periodos como semestres de ingreso. Las fechas ambiguas y diferencias temporales se señalaron, sin recalcular automáticamente el periodo. | Cada indicador puede identificar qué registros cumplen sus reglas temporales. |\n\n## Conciliación y comprobación del resultado\n\nLa Figura 5 muestra cómo cambió la cantidad de registros. La incorporación del CRM reúne información de solicitudes ya existentes. No representa la pérdida de 100 solicitudes diferentes. Los 500 registros Oracle permanecieron incluidos.\n\n**Figura 5. Conciliación de registros durante la limpieza**\n\n![Conciliación de registros durante la limpieza](conciliacion_registros.png)\n\n*Nota. Elaboración a partir del control de registros. Las cantidades corresponden a filas y no a personas únicas. La reducción reúne 38 repeticiones exactas, dos registros parciales y 100 aportes CRM incorporados a solicitudes existentes.*\n\nLa verificación final aprobó 23 controles, incluidos la conciliación de cantidades, la conservación de las fuentes y la lectura de los archivos exportados. Se obtuvo **BaseUnificada Entregable, con 5.500 registros y 18 columnas**, acompañada de diccionario, procedencia, metodología y controles de calidad.\n\nPermanecen 26 registros sin programa, 90 sin identificador de aspirante, 246 sin puntaje y 920 sin importe. Estas ausencias no se completaron por suposición. También se conservaron las observaciones temporales y las correspondencias entre sistemas no confirmadas. Para el análisis se distingue el conteo de registros del conteo de identificadores de aspirante, evitando presentar varias solicitudes de una persona como personas nuevas.\n'
(OUT/'seccion_limpieza_transformacion.md').write_text(text,encoding='utf8')
caption='''Figura 5. Conciliación de registros durante la limpieza

Nota. Elaboración a partir del control de registros. Las cantidades corresponden a filas y no a personas únicas. La reducción reúne 38 repeticiones exactas, dos registros parciales y 100 aportes CRM incorporados a solicitudes existentes. Los 500 registros Oracle permanecen incluidos.
'''
(OUT/'titulo_y_nota_figura.txt').write_text(caption,encoding='utf8')
metadata={'resumen_fuente':'reports/limpieza/ultima_entrega.json',
          'id_ejecucion_fuente':summary['id_ejecucion'],
          'sha256_resumen_fuente':hashlib.sha256(source.read_bytes()).hexdigest(),
          'secuencia_registros':[r['registros'] for r in sequence],
          'columnas_finales':18,'oracle_conservados':500,
          'uso':'Apoyo a la sección de limpieza del informe administrativo. No modifica los datos ni reemplaza el informe en Drive.'}
(OUT/'metadatos_apoyo.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Sección redactada:',OUT/'seccion_limpieza_transformacion.md')
print('Figura para insertar:',OUT/'conciliacion_registros.png')
