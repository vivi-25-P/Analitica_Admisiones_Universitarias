"""Adapta la sustentación a la identidad de las presentaciones de teoría.

Ejecutar con uv run --no-project --with python-pptx --with pillow python
scripts/actualizar_sustentacion_v2.py. Conserva la presentación original.
"""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'presentacion/Sustentación analítica de admisiones del Instituto Universitario Horizonte.pptx'
TEMPLATE = ROOT / 'docs/referencias/Calidad de datos.pptx'
DEST = SOURCE.with_name(SOURCE.stem + '_v2.pptx')
REPORT = ROOT / 'reports/revision_presentacion_v2'
BLUE, GOLD, INK, MUTED = '003B5C', 'A47720', '203C50', '536776'
PALETTE = {
    '14304A': BLUE, 'F6F4EF': 'FFFFFF', '4D6173': MUTED, 'DFE0DF': 'DDE5EB',
    '2A7F7A': '005A86', '8FD3CB': 'DDEBF3', 'C2410C': GOLD,
    '1F6662': '005A86', '4A5A6A': MUTED, 'C9D6E2': 'DDE5EB',
}


def textbox(slide, text, x, y, w, h, size=16, color=INK, bold=False,
            align=PP_ALIGN.LEFT, fill=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.06)
    tf.margin_top = tf.margin_bottom = Inches(.04)
    for index, line in enumerate(text.split('\n')):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.space_after = Pt(5)
        for run in p.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = RGBColor.from_string(color)
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    return shape


def rectangle(slide, x, y, w, h, fill, line=None, rounded=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                  Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line:
        shape.line.color.rgb = RGBColor.from_string(line)
    else:
        shape.line.fill.background()
    return shape


def put_background(slide, blob, width, height):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
    pic = slide.shapes.add_picture(BytesIO(blob), 0, 0, width=width, height=height)
    tree = slide.shapes._spTree
    tree.remove(pic._element)
    tree.insert(2, pic._element)
    pic.name = 'Plantilla institucional de la presentación de teoría'


def replace_text(slide, old, new, height=None, size=None):
    found = 0
    for shape in slide.shapes:
        if not shape.has_text_frame or old not in shape.text:
            continue
        tf = shape.text_frame
        p = tf.paragraphs[0]
        seed = deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
        value = shape.text.replace(old, new)
        tf.clear()
        for index, line in enumerate(value.split('\n')):
            p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = line
            if seed is not None:
                run._r.insert(0, deepcopy(seed))
            run.font.name = 'Arial'
            if size:
                run.font.size = Pt(size)
        tf.word_wrap = True
        if height:
            shape.height = Inches(height)
        found += 1
    if not found:
        raise ValueError(f'Texto no encontrado: {old}')


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def star_diagram(slide):
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    put_background(slide, backgrounds['content'], prs.slide_width, prs.slide_height)
    textbox(slide, 'PARTE 3 · MODELO ANALÍTICO', .89, .92, 11.7, .32, 13, GOLD, True)
    textbox(slide, 'Un modelo estrella detrás del dashboard', .89, 1.35, 11.7, .65, 31, BLUE, True)
    rectangle(slide, .95, 2.10, 11.3, .025, 'D4B36B')
    cards = [
        ('DimPrograma', 1.0, 2.75), ('DimCanal', 3.15, 2.75),
        ('DimPeriodo', 5.3, 2.75), ('DimCiudad', 1.0, 4.6),
        ('DimFuente', 5.3, 4.6), ('DimEstado', 1.0, 6.45),
        ('DimModalidad', 3.15, 6.45), ('DimAsesor', 5.3, 6.45),
        ('DimFecha', 3.15, 7.35),
    ]
    cx, cy = 4.10, 5.0
    for name, x, y in cards:
        sx, sy = x + .95, y + .34
        if name == 'DimFecha':
            # Rodear DimModalidad para no sugerir una relación entre dimensiones.
            for color, points, dashed in [
                ('7A9DB3', [(3.02, 5.65), (3.02, 7.69), (3.15, 7.69)], False),
                (GOLD, [(3.08, 5.65), (3.08, 7.82), (3.15, 7.82)], True),
            ]:
                for (x1, y1), (x2, y2) in zip(points, points[1:]):
                    route = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                        Inches(x1), Inches(y1), Inches(x2), Inches(y2))
                    route.line.color.rgb = RGBColor.from_string(color)
                    route.line.width = Pt(1.4)
                    if dashed:
                        dash = OxmlElement('a:prstDash')
                        dash.set('val', 'dash')
                        route._element.spPr.get_or_add_ln().append(dash)
            continue
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(cx), Inches(cy),
                                          Inches(sx), Inches(sy))
        line.line.color.rgb = RGBColor.from_string('7A9DB3')
        line.line.width = Pt(1.4)
        # La dimensión filtra hacia los registros, según las relaciones del modelo.
        head = OxmlElement('a:headEnd')
        head.set('type', 'triangle')
        line._element.spPr.get_or_add_ln().append(head)
    for name, x, y in cards:
        rectangle(slide, x, y, 1.9, .68, 'EDF4F8', '9DB7C8', True)
        textbox(slide, name, x + .04, y + .14, 1.82, .35, 14, BLUE, True, PP_ALIGN.CENTER)
    rectangle(slide, 2.95, 4.43, 2.3, 1.22, BLUE, rounded=True)
    textbox(slide, 'FactRegistros', 3.02, 4.60, 2.16, .4, 20, 'FFFFFF', True, PP_ALIGN.CENTER)
    textbox(slide, '5.500 filas · 22 medidas', 3.0, 5.08, 2.2, .3, 12, 'FFFFFF', align=PP_ALIGN.CENTER)
    items = [
        ('Tabla de hechos', 'Una fila por registro de solicitud de origen.'),
        ('Nueve dimensiones', 'Relaciones de uno a varios. El filtro va de la dimensión a los registros.'),
        ('Dos usos de la fecha', 'Solicitud activa y matrícula inactiva. La segunda requiere una medida específica.'),
        ('Estado de revisión', 'Modelo preparado. Falta cerrar la validación de medidas e interacciones en este equipo.'),
    ]
    for i, (heading, body) in enumerate(items):
        y = 2.75 + i * 1.24
        textbox(slide, heading, 8.0, y, 4.35, .4, 17, BLUE, True)
        textbox(slide, body, 8.0, y + .43, 4.35, .73, 15, MUTED)
    set_notes(slide, 'En el centro está FactRegistros con 5.500 registros de solicitudes y 22 medidas definidas. '
              'Las nueve dimensiones permiten analizar por programa, canal, periodo, ciudad, fuente, fecha, estado, modalidad y asesor. '
              'Las relaciones filtran de la dimensión hacia la tabla de registros. La relación con fecha de solicitud está activa '
              'y la de matrícula permanece inactiva. No afirmar que una medida usa esta última hasta comprobar su implementación. '
              'Los resultados del notebook son la referencia. La validación final de medidas, selecciones e interacciones del dashboard '
              'en este equipo continúa pendiente. No se afirma que existan 5.500 personas únicas.')


def matricula_observada(slide):
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    put_background(slide, backgrounds['content'], prs.slide_width, prs.slide_height)
    textbox(slide, 'PARTE 2 · RESULTADO REGISTRADO', .89, .92, 11.7, .32, 13, GOLD, True)
    textbox(slide, 'Matrícula registrada en la base integrada', .89, 1.35, 11.7, .65, 31, BLUE, True)
    rectangle(slide, .95, 2.10, 11.3, .025, 'D4B36B')
    textbox(slide, '21,4 %', 1.1, 2.65, 11.1, 1.80, 100, BLUE, True, PP_ALIGN.CENTER)
    textbox(slide, '1.179 de 5.500 registros tienen estado Matriculado', 1.1, 4.55, 11.1, .65,
            25, BLUE, align=PP_ALIGN.CENTER)
    textbox(slide, 'Por programa va de 19,3 % a 23,9 % y por canal de 19,7 % a 23,9 %: '
            'diferencias de pocos puntos, que se leen junto con el tamaño de cada grupo.',
            1.1, 5.65, 11.1, 1.1, 21, MUTED, align=PP_ALIGN.CENTER)
    rectangle(slide, 1.1, 7.20, 11.1, .55, 'EDF4F8', rounded=True)
    textbox(slide, 'Proporción observada de registros. No representa conversión definitiva de personas.',
            1.22, 7.29, 10.85, .4, 14, BLUE, align=PP_ALIGN.CENTER)
    textbox(slide, '08 / 15', 11.50, 8.10, .85, .25, 10, MUTED, align=PP_ALIGN.RIGHT)


REPORT.mkdir(parents=True, exist_ok=True)
original_sha = sha256(SOURCE.read_bytes()).hexdigest()
prs = Presentation(SOURCE)
template = Presentation(TEMPLATE)
with ZipFile(TEMPLATE) as archive:
    backgrounds = {name: archive.read('ppt/media/' + image)
                   for name, image in [('cover', 'image2.jpg'), ('agenda', 'image3.jpg'),
                                       ('content', 'image4.jpg'), ('closing', 'image5.jpg')]}
    theme = archive.read('ppt/theme/theme1.xml')
prs.slide_width, prs.slide_height = template.slide_width, template.slide_height
original_notes = [s.notes_slide.notes_text_frame.text for s in prs.slides]
original_pictures = {i + 1: [sha256(sh.image.blob).hexdigest() for sh in slide.shapes
                             if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
                     for i, slide in enumerate(prs.slides)}

for number, slide in enumerate(prs.slides, 1):
    for shape in list(slide.shapes):
        # El borde decorativo anterior no forma parte del contenido.
        if shape.left == 0 and shape.width < Inches(.25) and shape.height >= Inches(7.0):
            shape._element.getparent().remove(shape._element)
            continue
        shape.top = int(shape.top * 1.10)
        shape.height = int(shape.height * 1.10)
        if shape.left + shape.width > Inches(12.65):
            shape.width = max(Inches(.2), Inches(12.65) - shape.left)
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            # Centrar la imagen sin deformar sus proporciones.
            frame_h, frame_w = shape.height, shape.width
            iw, ih = shape.image.size
            ratio = min(frame_w / iw, frame_h / ih)
            width, height = int(iw * ratio), int(ih * ratio)
            shape.left += (frame_w - width) // 2
            shape.top += (frame_h - height) // 2
            shape.width, shape.height = width, height
        for node in shape._element.iter():
            local = node.tag.rsplit('}', 1)[-1]
            if local == 't' and node.text:
                node.text = node.text.replace('«', '').replace('»', '')
            if local == 'srgbClr' and node.get('val', '').upper() in PALETTE:
                node.set('val', PALETTE[node.get('val').upper()])
            if local in ('latin', 'cs', 'ea'):
                node.set('typeface', 'Arial')
            if local in ('rPr', 'defRPr', 'endParaRPr') and node.get('sz'):
                old = int(node.get('sz'))
                node.set('sz', str(round(max(1250, old * 1.04) if old < 2400 else old)))
        if shape.has_text_frame:
            shape.text_frame.word_wrap = True
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    if '«' in run.text or '»' in run.text:
                        run.text = run.text.replace('«', '').replace('»', '')
    bg = 'cover' if number == 1 else 'agenda' if number == 2 else 'closing' if number == 15 else 'content'
    put_background(slide, backgrounds[bg], prs.slide_width, prs.slide_height)
    if 3 <= number <= 14:
        rectangle(slide, .95, 2.10 if number != 13 else 2.53, 11.3, .025, 'D4B36B')
    if number not in (1, 15):
        textbox(slide, f'{number:02d} / 15', 11.50, 8.10, .85, .25, 10, MUTED, align=PP_ALIGN.RIGHT)

# Portada institucional con todos los datos del equipo.
cover = prs.slides[0]
positions = {
    'CASO 2': (.89, 2.50, 11.4, .34, 15),
    'Analítica para': (.89, 3.00, 11.4, 1.40, 39),
    'Instituto Universitario': (.89, 4.65, 11.4, .50, 23),
    'PRESENTAN': (.89, 5.50, 5.5, .30, 13),
    'Jose David': (.89, 5.95, 5.8, .43, 19),
    'Yaneth Viviana': (.89, 6.45, 6.0, .43, 19),
    'Darlyn Kamila': (.89, 6.95, 5.9, .43, 19),
    'Especialización en': (7.45, 5.95, 4.85, .8, 15),
    'Fundación Universitaria': (7.45, 6.90, 4.85, .65, 15),
    'Docente:': (7.45, 7.65, 4.85, .63, 14),
}
for shape in cover.shapes:
    if not shape.has_text_frame:
        continue
    for prefix, (x, y, w, h, size) in positions.items():
        if shape.text.startswith(prefix):
            shape.left, shape.top, shape.width, shape.height = map(Inches, (x, y, w, h))
            for p in shape.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
            for node in shape._element.iter():
                if node.tag.rsplit('}', 1)[-1] in ('rPr', 'defRPr', 'endParaRPr'):
                    node.set('sz', str(int(size * 100)))
            for p in shape.text_frame.paragraphs:
                for run in p.runs:
                    run.font.color.rgb = RGBColor.from_string('E5C67A' if prefix in ('CASO 2', 'PRESENTAN') else 'FFFFFF')
                    run.font.name = 'Arial'
            break

# La agenda utiliza la banda azul de la plantilla de apertura de tema.
for shape in prs.slides[1].shapes:
    if shape.has_text_frame and shape.text.startswith(('Base original', 'Limpieza en', 'Respuestas, hallazgos')):
        shape.height = Inches(2.2)
    if shape.has_text_frame and shape.top < Inches(2.7):
        for p in shape.text_frame.paragraphs:
            for run in p.runs:
                run.font.color.rgb = RGBColor.from_string('FFFFFF')
                if shape.text.startswith('Tres partes'):
                    run.font.size = Pt(32)

replace_text(prs.slides[5], 'De 5.640 filas a 5.500 registros',
             'Conciliación: de 5.640 a 5.500 registros', size=32)
replace_text(prs.slides[5], 'Ninguna fila se perdió: cada una de las 5.640 entradas tiene un destino registrado, conservada o consolidada.',
             'Las 5.640 entradas conservan trazabilidad, tanto las mantenidas como las consolidadas.', height=.65, size=15)
set_notes(prs.slides[5], 'Este flujo representa conciliación de registros, no un embudo de conversión de aspirantes. '
          'Partimos de 5.640 entradas. Consolidar 38 repeticiones exactas deja 5.602. Conciliar dos registros parciales '
          'deja 5.600 y recupera cinco valores documentados. Incorporar 100 aportes CRM a solicitudes existentes deja '
          '5.500 y permite recuperar 13 matrículas base. Los derechos administrativos quedan separados. Los 500 Oracle '
          'se conservan. Las 49 correspondencias más compatibles no se eliminan por similitud. Todas las entradas tienen '
          'un destino documentado. Permanecen 26 registros sin programa, 90 sin identificador de aspirante, 246 sin puntaje '
          'y 920 sin importe. No se imputaron valores por promedio ni se inventaron datos. Los 24 controles corresponden '
          'al cierre de limpieza y entrega, no a una validación del dashboard.')
replace_text(prs.slides[9], 'No aparece el patrón esperado',
             'Documentos sin patrón general\nAsesor: diferencia de 0,68 puntos', height=.82, size=12.5)
set_notes(prs.slides[9], 'Primera pregunta: la concentración en Derecho y Data Analytics ya existía. La conciliación cambia '
          'muy poco sus participaciones en la misma fuente y Oracle cambia el orden final. Segunda pregunta: en grupos '
          'comunes, la amplitud entre canales baja de 4,03 a 3,20 puntos con pesos comunes. Las diferencias permanecen, '
          'sin demostrar causas o rentabilidad. Tercera pregunta: Pendiente o Retirado con pesos comunes es 21,92 % con '
          'documentos No o Pendiente y 23,45 % con Sí. No aparece el patrón general esperado para documentación. '
          'Sin asesor es 23,36 % frente a 22,68 % con asesor: existe una diferencia descriptiva pequeña de 0,68 puntos, '
          'sin atribuirla al asesor ni concluir ausencia de asociación. La identidad única, matrícula efectiva y '
          'actualización de estados conservan condiciones pendientes.')
set_notes(prs.slides[3], original_notes[3] + '\nLa cifra de 498 correspondencias describe la revisión inicial. '
          'Después de estandarizar las ausencias se identificaron candidatos para los 500 Oracle, sin confirmar duplicados.')
set_notes(prs.slides[8], 'Se compararon 63 grupos comunes de programa, modalidad y periodo, con 5.474 registros. '
          'La amplitud entre canales baja de 4,03 a 3,20 puntos al aplicar los mismos pesos. Es una comparación descriptiva '
          'y no prueba una explicación causal, rentabilidad o independencia de las solicitudes. Los grupos con menos '
          'de 30 registros se identifican como pequeños, pero 30 no garantiza precisión ni demuestra un mercado atractivo.')
matricula_observada(prs.slides[7])
star_diagram(prs.slides[11])
textbox(prs.slides[11], '12 / 15', 11.50, 8.10, .85, .25, 10, MUTED, align=PP_ALIGN.RIGHT)
replace_text(prs.slides[12], 'Un dashboard en Power BI con las mismas cifras',
             'Dashboard de admisiones en Power BI', size=32)
set_notes(prs.slides[12], 'El proyecto contiene seis páginas: panorama de admisiones, captación y segmentos, seguimiento '
          'del proceso, cobertura y condiciones, comparaciones controladas y respuestas y decisiones. Las cuatro primeras '
          'tienen filtros por periodo, programa, modalidad, canal, ciudad y fuente. Las dos últimas muestran resultados '
          'calculados en el notebook sobre toda la base y no cambian con los filtros. Actualmente lee Excel y seis CSV '
          'de apoyo. PostgreSQL está disponible como alternativa, pero este proyecto todavía no está conectado a esa fuente. '
          'El notebook valida las cifras de referencia, incluidos 5.500 registros y 1.179 Matriculado. Falta cerrar en este '
          'equipo la prueba completa de carga, visuales, denominadores y filtros, completar indicadores dinámicos y '
          'guardar un PBIX con los datos cargados para consulta. No afirmar que todas las medidas e interacciones '
          'ya están verificadas. Los diez indicadores y seis propuestas aparecen también en tablas de referencia.')
textbox(prs.slides[12], 'Carga y validación final de medidas e interacciones pendientes.',
        .89, 7.95, 10.4, .30, 12.5, GOLD, True)
for shape in prs.slides[12].shapes:
    if shape.has_text_frame and shape.text.startswith('6 páginas.'):
        shape.top, shape.height = Inches(7.30), Inches(.60)
    elif shape.has_text_frame and shape.text.startswith('Comparaciones controladas y respuestas'):
        shape.top, shape.height = Inches(7.05), Inches(.65)
    elif shape.has_text_frame and shape.text == '13 / 15':
        shape.top = Inches(8.32)

# La plantilla de cierre ya incorpora la palabra Gracias y la identidad institucional.
closing = prs.slides[14]
for shape in list(closing.shapes):
    if shape.has_text_frame and shape.text.strip() == 'Gracias':
        shape._element.getparent().remove(shape._element)
    elif shape.has_text_frame:
        shape.left, shape.width = Inches(.89), Inches(11.4)
        shape.top = Inches(6.25 if 'Preguntas' in shape.text else .70)
        for p in shape.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER if 'Preguntas' in shape.text else PP_ALIGN.LEFT
            for run in p.runs:
                run.font.color.rgb = RGBColor.from_string('FFFFFF' if 'Preguntas' in shape.text else 'E5C67A')
                run.font.size = Pt(24 if 'Preguntas' in shape.text else 14)

prs.core_properties.title = 'Sustentación analítica de admisiones del Instituto Universitario Horizonte'
prs.core_properties.subject = 'Versión 2. Plantilla institucional de teoría y revisión del contenido'
prs.save(DEST)

# Aplicar también el tema de Office de la teoría, además de sus fondos auténticos.
with ZipFile(DEST) as z:
    members = {i.filename: z.read(i.filename) for i in z.infolist()}
members['ppt/theme/theme1.xml'] = theme
with ZipFile(DEST, 'w', ZIP_DEFLATED) as z:
    for name, content in members.items():
        z.writestr(name, content)

result = Presentation(DEST)
checks = {
    'original_intacto': sha256(SOURCE.read_bytes()).hexdigest() == original_sha,
    '15_diapositivas': len(result.slides) == 15,
    'notas_en_15_diapositivas': all(s.notes_slide.notes_text_frame.text.strip() for s in result.slides),
    'formato_de_la_teoria': result.slide_width == template.slide_width and result.slide_height == template.slide_height,
    'graficas_y_capturas_conservadas': all(
        Counter(original_pictures[i]).items() <= Counter(sha256(sh.image.blob).hexdigest()
          for sh in result.slides[i-1].shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE).items()
        for i in (3, 9, 13)),
    'sin_afirmacion_validacion_completa': 'Verificamos todas las medidas y filtros' not in '\n'.join(
        s.notes_slide.notes_text_frame.text for s in result.slides),
}
if not all(checks.values()):
    raise ValueError(checks)
metadata = {
    'fecha': '2026-10-30', 'original': str(SOURCE.relative_to(ROOT)),
    'salida': str(DEST.relative_to(ROOT)), 'plantilla': str(TEMPLATE.relative_to(ROOT)),
    'sha256_original': original_sha, 'sha256_v2': sha256(DEST.read_bytes()).hexdigest(),
    'comprobaciones': checks, 'modelo_y_notebook_modificados': False,
    'subido_a_git': False, 'renderizado_powerpoint': False,
}
(REPORT / 'verificacion.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False, indent=2))
