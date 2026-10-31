"""Genera una sustentación administrativa v3. Conserva original y v2.

uv run --no-project --with python-pptx --with pillow python scripts/crear_sustentacion_administrativa_v3.py
"""
from copy import deepcopy
import csv
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'presentacion/Sustentación analítica de admisiones del Instituto Universitario Horizonte_v2.pptx'
DEST = SOURCE.with_name(SOURCE.name.replace('_v2.pptx', '_v3.pptx'))
OUT = ROOT / 'reports/revision_presentacion_v3'
OUT.mkdir(parents=True, exist_ok=True)
BLUE, GOLD, INK, MUTED, PALE = '003B5C', 'A47720', '203C50', '536776', 'EDF4F8'
source_hash = sha256(SOURCE.read_bytes()).hexdigest()
prs = Presentation(SOURCE)
original = list(prs.slides)
with ZipFile(ROOT / 'docs/referencias/Calidad de datos.pptx') as z:
    background = z.read('ppt/media/image4.jpg')


def text(slide, value, x, y, w, h, size=18, ink=INK, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.04)
    tf.margin_top = tf.margin_bottom = Inches(.035)
    for index, line in enumerate(value.split('\n')):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.space_after = Pt(5)
        for run in p.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = RGBColor.from_string(ink)
    return shape


def rect(slide, x, y, w, h, color=PALE):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(color)
    sh.line.fill.background()
    return sh


def note(slide, value):
    slide.notes_slide.notes_text_frame.text = value


def base(title, tag, number):
    slide = prs.slides.add_slide(prs.slide_layouts[-1])
    for sh in list(slide.shapes):
        slide.shapes._spTree.remove(sh._element)
    slide.shapes.add_picture(BytesIO(background), 0, 0, width=prs.slide_width, height=prs.slide_height)
    text(slide, tag.upper(), .94, .88, 11.5, .36, 12, GOLD, True)
    text(slide, title, .94, 1.35, 11.5, .68, 29, BLUE, True)
    rect(slide, .98, 2.10, 11.3, .025, 'D4B36B')
    text(slide, f'{number:02d} / 10', 11.5, 8.1, .86, .28, 10, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def picture(slide, source, x, y, w, h):
    data = source.read_bytes() if isinstance(source, Path) else source
    with Image.open(BytesIO(data)) as image:
        iw, ih = image.size
    scale = min(w / iw, h / ih)
    fw, fh = iw * scale, ih * scale
    slide.shapes.add_picture(BytesIO(data), Inches(x + (w-fw)/2), Inches(y + (h-fh)/2),
                             width=Inches(fw), height=Inches(fh))


def card(slide, x, y, w, value, label, body, color=PALE):
    rect(slide, x, y, w, 2.85, color)
    text(slide, value, x+.16, y+.16, w-.32, .68, 32, BLUE, True)
    text(slide, label, x+.16, y+.94, w-.32, .92, 17, BLUE, True)
    text(slide, body, x+.16, y+1.94, w-.32, .79, 14, MUTED)


def footer(slide, value):
    text(slide, value, .98, 7.55, 11.3, .42, 12, MUTED)


def rows(name):
    with (ROOT / 'reports/analisis_administrativo/tablas' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


# Portada y flujo de conciliación ya revisados visualmente, con notas actualizadas.
cover, flow = original[0], original[5]
note(cover, 'Tiempo: 30 segundos. Presentamos cómo convertir la información de admisiones en prioridades de gestión. '
     'El resultado es una base integrada, una lectura del negocio y un tablero de consulta. '
     'No enumerar herramientas ni leer los nombres del equipo. Dar paso a la necesidad institucional.')
for sh in flow.shapes:
    if sh.has_text_frame:
        if 'Conciliación: de 5.640 a 5.500 registros' in sh.text:
            for p in sh.text_frame.paragraphs:
                for run in p.runs:
                    run.text = run.text.replace('Conciliación: de 5.640 a 5.500 registros', 'Qué base obtuvimos y qué límites conserva')
        for p in sh.text_frame.paragraphs:
            for run in p.runs:
                run.text = run.text.replace('06 / 15', '05 / 10').replace('PARTE 2', 'PREPARACIÓN DE LA INFORMACIÓN')
for shape in flow.shapes:
    if shape.has_text_frame and shape.text.startswith('Las 5.640 entradas conservan trazabilidad'):
        shape.text_frame.clear()
        shape.height = Inches(1.10)
        p = shape.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = ('5.500 registros y 18 columnas, con procedencia documentada.\n'
                    'Permanecen 26 sin programa, 90 sin identificador de aspirante, 246 sin puntaje y 920 sin importe.')
        run.font.name = 'Arial'
        run.font.size = Pt(17)
        run.font.color.rgb = RGBColor.from_string(MUTED)
footer(flow, 'Conciliación de registros. No representa conversión ni confirma aspirantes únicos.')
note(flow, 'Tiempo: 60 segundos. El flujo es conciliación de registros y no un embudo de conversión. '
     'Las 5.640 entradas reúnen principal, CRM y Oracle. Consolidamos 38 repeticiones exactas, dos registros parciales '
     'y los 100 aportes CRM a solicitudes existentes. Quedan 5.500 registros y 18 columnas. Se recuperan cinco valores '
     'parciales y trece matrículas base desde CRM. Se conservan los 500 Oracle. Las ausencias no se sustituyen por '
     'promedios ni ceros. Los 24 controles corresponden al cierre de limpieza, no a todas las interacciones del tablero. '
     'Mensaje administrativo: una base comparable con procedencia y cambios documentados.')

s2 = base('Qué necesitaba conocer la institución', 'Necesidad del negocio', 2)
text(s2, '¿Cómo se distribuyen las solicitudes por programa, modalidad y canal, y qué se observa en los estados del proceso de admisión?',
     1.02, 2.55, 11.1, 1.14, 25, BLUE, True)
for x, heading, body in [
    (1.02, 'Oferta y demanda registrada', 'Reconocer dónde se concentra el interés y revisar la capacidad de atención.'),
    (4.86, 'Captación', 'Identificar combinaciones de programa, modalidad y ciudad para probar campañas.'),
    (8.70, 'Seguimiento', 'Detectar registros que requieren revisión documental o asignación de responsable.')]:
    rect(s2, x, 4.20, 3.53, 2.8)
    text(s2, heading, x+.14, 4.39, 3.25, .74, 19, BLUE, True)
    text(s2, body, x+.14, 5.28, 3.25, 1.5, 18, MUTED)
footer(s2, 'Tres ejes: programas y periodos, diferencias entre canales y estados según documentación y asesor.')
note(s2, 'Tiempo: 60 segundos. Hablar desde la necesidad de la institución. Antes de recomendar inversión, '
     'necesitábamos conocer el interés registrado, cómo llegan las solicitudes y qué aspectos del seguimiento '
     'requieren revisión. Las tres preguntas específicas del informe desarrollan programas, canales y estados. '
     'No prometer resultados comerciales ni reducción de costos que no hemos medido.')

s3 = base('Qué impedía una lectura confiable', 'Retos de la información', 3)
for x, value, label, body in [
    (1.02, '3 fuentes', 'Solicitudes e información CRM', 'Principal: 5.040. CRM: 100 aportes. Oracle: 500 registros.'),
    (4.86, '1 catálogo', 'Oferta académica', 'Atributos complementarios para siete programas de referencia.'),
    (8.70, '3 retos', 'Comparabilidad y seguimiento', 'Variantes de escritura, repeticiones y datos sin diligenciar.')]:
    card(s3, x, 2.67, 3.53, value, label, body)
text(s3, 'Construimos criterios comunes para comparar la información y conservar su procedencia.',
     1.10, 6.03, 11.0, 1.08, 25, BLUE, True)
footer(s3, 'Un registro de solicitud no equivale automáticamente a un aspirante único.')
note(s3, 'Tiempo: 60 segundos. Explicar que había tres fuentes de solicitudes o aportes y un catálogo, '
     'cuatro insumos en total. El CRM complementaba solicitudes existentes. Las categorías y fechas no eran '
     'comparables de entrada. Se documentaron criterios de catálogo, estado Nuevo y periodos de ingreso. '
     'No afirmar que las coincidencias Oracle confirman duplicados ni que el catálogo fue validado oficialmente.')

s4 = base('Cómo integramos y transformamos los datos', 'Preparación de la información', 4)
for x, y, heading, body in [
    (1.02, 2.61, 'Integrar con una estructura común',
     'Principal, CRM y Oracle con 15 columnas comunes. El catálogo añade facultad, duración y nivel.'),
    (6.83, 2.61, 'Unificar categorías con reglas',
     'Derecho y DERECHO se presentan como Derecho. Nuevo se agrupa con Admitido para el análisis.'),
    (1.02, 4.88, 'Interpretar fechas y valores',
     'Fechas en año, mes y día. Importes en pesos colombianos. Periodo como semestre de ingreso.'),
    (6.83, 4.88, 'Conciliar y conservar evidencia',
     'Consolidar repeticiones y aportes CRM. Mantener la procedencia, los valores recibidos y las ausencias.')]:
    rect(s4, x, y, 5.40, 1.99)
    text(s4, heading, x+.17, y+.14, 5.04, .63, 19, BLUE, True)
    text(s4, body, x+.17, y+.87, 5.04, 1.0, 17, MUTED)
footer(s4, 'Las transformaciones tienen reglas y respaldo. No se completaron datos por suposición.')
note(s4, 'Tiempo: 90 segundos. Esta lámina explica qué hicimos antes de mostrar cuánto cambió la base. '
     'Se anexaron tres fuentes con nombres y estructura comparables, se separaron identificadores CRM y se '
     'complementó el catálogo. La suma inicial de matrícula base y derechos CRM no quedó como criterio final: '
     'en la conciliación económica se conservó la matrícula base y se separaron los derechos administrativos. '
     'Se unificaron tildes, espacios y categorías con reglas; Nuevo se agrupó analíticamente con Admitido y se '
     'conservó el estado recibido. Las fechas se interpretaron y se señalaron ambigüedades sin deducir el periodo '
     'desde el mes. Se trataron repeticiones exactas, dos parciales y aportes CRM con trazabilidad. Las coincidencias '
     'Oracle no se eliminaron por similitud. Mensaje: hacer comparables los datos y dejar evidencia de cada cambio.')

s5 = base('Dónde se concentra el interés registrado', 'Programas y modalidades: pregunta general y H1', 6)
programs = rows('programa.csv')
assert sum(int(r['registros']) for r in programs) == 5500
short = {'Especialización en Data Analytics': 'Esp. Data Analytics', 'Especialización en Gerencia': 'Esp. Gerencia',
         'Administración de Empresas': 'Administración de Empresas'}
text(s5, 'Registros por programa', 1.03, 2.46, 6.5, .42, 18, BLUE, True)
for i, row in enumerate(programs):
    y = 3.06 + i*.43
    text(s5, short.get(row['programa'], row['programa']), 1.03, y, 3.05, .36, 14, MUTED)
    rect(s5, 4.12, y+.055, 2.58*int(row['registros'])/1233, .22, BLUE if i<2 else '7A9DB3')
    text(s5, f"{int(row['registros']):,}".replace(',', '.'), 6.82, y-.015, .7, .37, 14, BLUE, True)
rect(s5, 8.04, 2.55, 4.18, 1.53)
text(s5, '44,53 %', 8.23, 2.69, 3.8, .68, 34, BLUE, True)
text(s5, 'Derecho y Data Analytics', 8.23, 3.41, 3.8, .49, 18, BLUE)
text(s5, 'Modalidades', 8.10, 4.45, 3.95, .45, 19, BLUE, True)
for i, row in enumerate(rows('modalidad.csv')):
    value=float(row['participacion_registros_pct'])
    text(s5, row['modalidad']+f'   {value:.2f} %'.replace('.',','), 8.10, 5.03+i*.47, 4.0, .4, 19, MUTED)
text(s5, 'Admitido: 1.822 (33,13 %). Matriculado: 1.179 (21,44 %).', 1.03, 6.92, 11.0, .43, 18, BLUE, True)
footer(s5, 'H1: la concentración ya existía. Gestión: revisar capacidad y seguimiento por programa y periodo.')
note(s5, 'Tiempo: 90 segundos. Esta lámina responde la distribución general y el componente descriptivo de H1. '
     'Derecho y Data Analytics reúnen 2.449 registros y el 44,53 %. Presencial y Virtual están cerca del 40 % cada una. '
     'La concentración ya existía antes de limpiar. No se explica simplemente por las variantes de escritura. '
     'La fuente Oracle cambia el orden final y esto no prueba crecimiento. Hay 26 registros sin programa. '
     'La matrícula registrada es 21,44 % y la conversión definitiva requiere confirmar solicitudes independientes, '
     'matrícula efectiva y una ventana comparable. Propuesta: revisar capacidad y seguimiento donde se concentra el volumen.')

s6 = base('Qué requiere revisión administrativa', 'Estados y seguimiento: pregunta general y H3', 8)
card(s6, 1.02, 2.59, 3.53, '514 de 1.179', 'Matriculado con documentos No o Pendiente', '43,60 % de los registros Matriculado.')
card(s6, 4.86, 2.59, 3.53, '393 de 638', 'Documentación pendiente con documentos Sí', '61,60 % de ese estado.')
card(s6, 8.70, 2.59, 3.53, '1.101', 'Registros Sin asignar', '20,02 % del total de solicitudes registradas.')
text(s6, 'La prioridad es comprobar reglas, actualización y responsables antes de atribuir fallas operativas.',
     1.08, 5.72, 11.02, .9, 25, BLUE, True)
text(s6, 'En grupos equivalentes no aparece el patrón documental esperado. La diferencia según asignación es pequeña.',
     1.08, 6.78, 11.02, .65, 18, MUTED)
footer(s6, 'H3: sin patrón documental general. Revisar los casos antes de evaluar la gestión del asesor.')
note(s6, 'Tiempo: 90 segundos. Presentar los numeradores y denominadores. Estos casos son situaciones por revisar, '
     'no incumplimientos confirmados. H3 estudia la distribución de los seis estados según documentación y asesor '
     'dentro de programa, modalidad y periodo. Como síntesis, Documentación pendiente o Retirado con composición común '
     'representan 21,92 % con documentos No o Pendiente y 23,45 % con Sí. No aparece el patrón general esperado. '
     'Sin asesor es 23,36 % frente a 22,68 % con asesor, diferencia de 0,68 puntos. No interpretar causalmente ni '
     'descartar asociaciones más específicas. Falta historial de estados y asignación para explicar recorridos. '
     'Acción: revisión coordinada de los 514, 393 y 1.101 registros, con explicación o actualización respaldada.')

s7 = base('Qué canales y oportunidades conviene explorar', 'Captación: pregunta general y H2', 7)
picture(s7, ROOT/'reports/analisis_administrativo/figuras/02_canales_comparables.png', 1.0, 2.42, 11.28, 2.75)
for x, heading, value, body in [
    (1.02, 'Canales comparables', '4,03 a 3,20 puntos', 'Las diferencias se reducen, pero permanecen.'),
    (4.86, 'Administración virtual en Cali', '19 de 44 · 43,18 %', 'Evaluar un piloto sujeto a capacidad y seguimiento.'),
    (8.70, 'Administración virtual en Bogotá', '22 de 66 · 33,33 %', 'Evaluar un piloto con oferta e inversión registradas.')]:
    rect(s7, x, 5.39, 3.53, 1.76)
    text(s7, heading, x+.13, 5.51, 3.25, .61, 16, BLUE, True)
    text(s7, value, x+.13, 6.17, 3.25, .38, 17, BLUE, True)
    text(s7, body, x+.13, 6.61, 3.25, .53, 13, MUTED)
footer(s7, 'H2: comparar grupos equivalentes. Gestión: probar pilotos antes de mover presupuesto. No es rentabilidad.')
note(s7, 'Tiempo: 120 segundos. Respuesta H2 y oportunidades exploratorias. Los canales aportan entre 888 y '
     '941 registros. Instagram presenta 23,86 % Matriculado y Referido 19,67 % en sus totales. La amplitud de '
     '4,03 a 3,20 puntos corresponde solo a los 5.474 registros de los 63 grupos comunes por programa, modalidad '
     'y periodo. La composición explica parte de la diferencia descriptiva, no una causa ni rentabilidad. '
     'Administración virtual en Cali tiene 19 de 44 Matriculado, 43,18 %, y en Bogotá 22 de 66, 33,33 %. '
     'Son oportunidades para probar con capacidad validada, oferta comparable, inversión y resultados registrados. '
     'Los tamaños son limitados y no confirman nichos rentables. Como revisión de seguimiento, Derecho virtual '
     'en Bogotá reúne 21 Matriculado de 133 y Derecho presencial en Popayán 13 de 101. Revisar estados, periodo '
     'y fuente antes de ampliar inversión. No interpretar solicitudes abiertas como perdidas.')

s9 = base('Cómo consultar y seguir los resultados', 'Tablero Power BI', 9)
pics=[sh for sh in original[12].shapes if sh.shape_type==MSO_SHAPE_TYPE.PICTURE and sh.name!='Plantilla institucional de la presentación de teoría']
preview=max(pics,key=lambda sh:sh.width*sh.height)
picture(s9, preview.image.blob, 1.0, 2.52, 7.52, 4.60)
text(s9, 'Una consulta con propósito', 8.82, 2.57, 3.44, .73, 20, BLUE, True)
text(s9, '1. Definir el periodo.\n2. Seleccionar programa y modalidad.\n3. Revisar volumen, estados y documentación.',
     8.82, 3.54, 3.44, 1.96, 18, MUTED)
text(s9, 'Inicio y seis páginas de análisis', 8.82, 5.91, 3.44, .77, 19, BLUE, True)
footer(s9, 'Cuatro páginas de análisis con filtros. Las dos de resultados globales mantienen la base completa.')
note(s9, 'Tiempo: 90 segundos, incluida una demostración de máximo 45 segundos. La captura de apoyo procede '
     'de la v2 y conserva las cifras del análisis. En el proyecto actual también existe la portada Inicio. '
     'Preparar antes la selección de un periodo y Administración de Empresas virtual. No recorrer todas las páginas. '
     'Panorama, Captación, Seguimiento y Cobertura tienen filtros. Comparaciones y Respuestas son globales. '
     'El proyecto utiliza el Excel y seis CSV. PostgreSQL conserva la base equivalente como alternativa. '
     'Se verificaron 22 referencias basales, 28 grupos, 395 segmentos y contextos de los porcentajes corregidos. '
     'Faltan algunos indicadores dinámicos explícitos y la revisión completa de interacciones. No afirmar validación '
     'total. Si no se dispone de la aplicación preparada, utilizar la captura y no improvisar conexiones.')

s10 = base('Qué proponemos acordar', 'Recomendaciones para la gestión', 10)
for i,(title,body,owner,tracking) in enumerate([
    ('Revisión documental','Revisar los 514 y 393 casos señalados.','Admisiones y gestión documental','Explicación y actualización respaldadas. K04 y K05.'),
    ('Asignación','Comprobar la asignación de 1.101 registros.','Coordinación de admisiones','Responsable, contacto y siguiente acción. K02.'),
    ('Pilotos de captación','Evaluar Administración virtual en Cali y Bogotá.','Mercadeo y coordinación académica','Capacidad, inversión y resultados comparables. K01.')]):
    y=2.57+i*1.38
    rect(s10,1.02,y,11.2,1.17)
    text(s10,title,1.18,y+.12,3.06,.44,19,BLUE,True)
    text(s10,body,1.18,y+.54,3.06,.62,15,MUTED)
    text(s10,owner,4.55,y+.13,3.17,.79,17,BLUE,True)
    text(s10,tracking,8.0,y+.13,3.96,.79,17,MUTED)
text(s10, 'Acordar responsables, plazos y metas de seguimiento.',
     1.08, 6.99, 11.0, .67, 21, BLUE, True)
footer(s10, 'Son propuestas para discusión. El análisis no demuestra rentabilidad ni conversión definitiva.')
note(s10, 'Tiempo: 90 segundos. No cerrar repitiendo todos los resultados. Proponer tres acuerdos concretos: '
     'revisión documental, verificación de responsables y diseño de dos pilotos. Los responsables son propuestos, '
     'no asignados oficialmente. Los indicadores K04 y K05 tienen referencias de 43,60 % y 61,60 %. K02 es '
     '79,98 % de asignación registrada. K01 describe Matriculado y no conversión definitiva. Las metas y plazos '
     'deben acordarse con la institución. Distinguir una corrección del dato de una mejora real de la operación. '
     'Cierre: ahora contamos con una base comparable y evidencia para priorizar acciones comprobables. '
     'Reservar hasta dos minutos para preguntas. Los anexos ocultos son respaldo y no forman parte de los trece minutos.')

# Anexos ocultos para preguntas. Se conservan contenidos técnicos y notas de la v2.
annexes = [original[4], original[6], original[9], original[11]]
for i, slide in enumerate(annexes,1):
    slide._element.set('show','0')
    for shape in slide.shapes:
        if shape.has_text_frame:
            for par in shape.text_frame.paragraphs:
                for run in par.runs:
                    run.text=re.sub(r'\d{2} / 15',f'Anexo {i}',run.text)
    if i==4:
        for shape in slide.shapes:
            if shape.has_text_frame and 'Modelo preparado. Falta cerrar' in shape.text:
                shape.text='Medidas generales y contextos revisados. Pendiente completar indicadores e interacciones.'
                shape.height=Inches(.94)
                for par in shape.text_frame.paragraphs:
                    for run in par.runs:
                        run.font.name='Arial';run.font.size=Pt(14);run.font.color.rgb=RGBColor.from_string(MUTED)
        note(slide,'Respaldo técnico. Una fila por registro, nueve dimensiones, 22 medidas. Relación de solicitud '
             'activa y matrícula inactiva. Se comprobaron valores generales y contextos específicos de porcentajes. '
             'La auditoría no certifica todas las interacciones ni completa los indicadores dinámicos pendientes.')
    else:
        note(slide,'Anexo oculto para preguntas. No exponer dentro de los trece minutos.\n'+slide.notes_slide.notes_text_frame.text)

main=[cover,s2,s3,s4,flow,s5,s7,s6,s9,s10]
keep=main+annexes
id_by_part={prs.part.related_slide(entry.rId).part:entry for entry in list(prs.slides._sldIdLst)}
keep_parts={slide.part for slide in keep}
for entry in list(prs.slides._sldIdLst):
    part=prs.part.related_slide(entry.rId).part
    prs.slides._sldIdLst.remove(entry)
    if part not in keep_parts:
        prs.part.drop_rel(entry.rId)
for slide in keep:
    prs.slides._sldIdLst.append(id_by_part[slide.part])
for slide in main:
    slide._element.attrib.pop('show',None)
prs.save(DEST)
assert sha256(SOURCE.read_bytes()).hexdigest()==source_hash
check=Presentation(DEST)
assert len(check.slides)==14
assert sum(s._element.get('show')=='0' for s in check.slides)==4
for slide in check.slides:
    assert slide.notes_slide.notes_text_frame.text.strip()
    for shape in slide.shapes:
        if shape.has_text_frame:
            assert not any(c in shape.text for c in ['«','»'])
metadata={'fecha':'2026-10-30','entrada':str(SOURCE.relative_to(ROOT)),'salida':str(DEST.relative_to(ROOT)),
          'sha256_v2':source_hash,'sha256_v3':sha256(DEST.read_bytes()).hexdigest(),
          'principales':10,'anexos_ocultos':4,'minutos_estimados':13,'minutos_preguntas':2,
          'minutos_por_diapositiva':[.5,1,1,1.5,1,1.5,2,1.5,1.5,1.5],
          'original_y_v2_conservadas':True,'notas_en_todas':True,'renderizado_powerpoint':False,
          'datos_modelo_o_drive_modificados':False,'commit_o_push':False}
(OUT/'verificacion.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
times=metadata['minutos_por_diapositiva']
assert sum(times)==13
lines=['# Guion de la sustentación administrativa v3', '',
       'Diez diapositivas principales para trece minutos estimados y hasta dos minutos de preguntas. '
       'Ensayar con transiciones y demostración. Los cuatro anexos están ocultos.', '',
       'Recorrido: necesidad institucional, fuentes y retos, transformaciones, base obtenida, '
       'programas y modalidades, canales y oportunidades, seguimiento, tablero y acciones.', '']
for i,slide in enumerate(check.slides,1):
    lines += [f'## Diapositiva {i}' + (' · anexo oculto' if i>10 else f' · {times[i-1]} minutos'), '',
              slide.notes_slide.notes_text_frame.text, '']
lines += ['## Preparación de la demostración', '',
          'Abrir previamente el PBIP actual. Mostrar una consulta de periodo, programa y modalidad. '
          'La imagen de Panorama es una captura de apoyo anterior a los últimos ajustes visuales. '
          'No recorrer todas las páginas. Usar los anexos solo para preguntas.', '']
(OUT/'guion_exposicion.md').write_text('\n'.join(lines),encoding='utf-8')
print(DEST)
