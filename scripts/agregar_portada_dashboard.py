"""Crea una portada académica con navegación, sin modificar las páginas del análisis."""

from copy import deepcopy
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = 'LogoFUPPortada20261030.png'
PAGE_NAME = 'ReportSectionPortadaAdmisiones'
BLUE, MUTED, WHITE = '#1D4A66', '#5F6B73', '#FFFFFF'


def literal(value):
    return {'expr': {'Literal': {'Value': value}}}


def color(value):
    return {'solid': {'color': literal("'" + value + "'")}}


def props(**values):
    return [{'properties': values}]


def agregar_portada(report_folder):
    path = report_folder / 'report.json'
    report = json.loads(path.read_text(encoding='utf-8'))
    pages = [p for p in report['sections'] if p['name'] != PAGE_NAME]
    targets = [(p['name'], p['displayName']) for p in pages]
    if len(targets) != 6:
        raise ValueError('La portada espera las seis páginas actuales del análisis.')
    visuals = []

    def add(name, kind, x, y, width, height, objects, container):
        position = dict(x=x, y=y, z=len(visuals), width=width, height=height)
        config = {'name': name, 'layouts': [{'id': 0, 'position': deepcopy(position)}],
                  'singleVisual': {'visualType': kind, 'drillFilterOtherVisuals': True,
                                   'objects': objects, 'vcObjects': container}}
        visuals.append({**position, 'config': json.dumps(config, ensure_ascii=False), 'filters': '[]'})

    def text(name, value, x, y, width, height, points=12, ink=BLUE, bold=False, fill=None):
        style = {'fontSize': f'{points}pt', 'fontFamily': 'Segoe UI', 'color': ink}
        if bold:
            style['fontWeight'] = 'bold'
        add(name, 'textbox', x, y, width, height,
            {'general': props(paragraphs=[{'textRuns': [{'value': value, 'textStyle': style}]}])},
            {'visualHeader': props(show=literal('false')),
             'background': props(show=literal('true' if fill else 'false'),
                                 color=color(fill or WHITE), transparency=literal('0D'))})

    text('PortadaIdentificacion', 'ANALÍTICA DE ADMISIONES', 44, 36, 740, 46, 17, bold=True)
    text('PortadaTitulo', 'Instituto Universitario\nHorizonte', 44, 100, 770, 122, 32, bold=True)
    text('PortadaProposito', 'Información para apoyar la captación y el seguimiento de las solicitudes.',
         44, 235, 760, 64, 17, MUTED)
    text('PortadaPregunta', '¿Cómo se distribuyen las solicitudes por programa, modalidad y canal, '
         'y qué se observa en los estados del proceso de admisión?', 44, 305, 760, 70, 13, MUTED)

    for index, (target, label) in enumerate(targets):
        x, y = 48 + (index % 2) * 382, 404 + (index // 2) * 70
        add('PortadaAcceso' + str(index), 'actionButton', x, y, 360, 54,
            {'text': props(show=literal('true'), text=literal("'" + label + "'"),
                           fontColor=color(WHITE), fontSize=literal('12D'),
                           fontFamily=literal("'Segoe UI'"), horizontalAlignment=literal("'center'"),
                           verticalAlignment=literal("'middle'")),
             'fill': props(show=literal('true'), fillColor=color(BLUE), transparency=literal('0D')),
             'outline': props(show=literal('false')),
             'icon': props(show=literal('false'))},
            {'visualHeader': props(show=literal('false')),
             'visualLink': props(show=literal('true'), type=literal("'PageNavigation'"),
                                 navigationSection=literal("'" + target + "'"),
                                 tooltip=literal("'Abrir " + label + "'"))})

    text('PortadaSeparador', '', 856, 60, 2, 546, fill='#C5A45D')
    add('PortadaLogoFUP', 'image', 918, 96, 264, 264,
        {'general': props(imageUrl={'expr': {'ResourcePackageItem': {
            'PackageName': 'RegisteredResources', 'PackageType': 1, 'ItemName': RESOURCE}}})},
        {'visualHeader': props(show=literal('false')),
         'background': props(show=literal('false'))})
    text('PortadaUniversidad', 'Fundación Universitaria\nde Popayán', 898, 374, 330, 84, 19, bold=True)
    text('PortadaContexto', 'Presentación académica de BI\n\nInstituto Universitario Horizonte es la institución del caso analizado.',
         898, 480, 330, 118, 12, MUTED)
    text('PortadaAlcance', 'Unidad de análisis: registros de solicitud. Las proporciones observadas no equivalen '
         'a conversión definitiva ni permiten atribuir efectos causales a los canales.',
         44, 648, 1176, 56, 11, MUTED)

    page = {'name': PAGE_NAME, 'displayName': 'Inicio', 'displayOption': 1, 'filters': '[]',
            'height': 720, 'width': 1280, 'visualContainers': visuals,
            'config': json.dumps({'objects': {'background': props(color=color(WHITE), transparency=literal('0D')),
                                            'outspace': props(color=color('#F3F5F7'))}})}
    report['sections'] = [page, *pages]
    config = json.loads(report['config'])
    config['activeSectionIndex'] = 0
    report['config'] = json.dumps(config, ensure_ascii=False)
    packages = report.setdefault('resourcePackages', [])
    package = next((p['resourcePackage'] for p in packages
                    if p.get('resourcePackage', {}).get('name') == 'RegisteredResources'), None)
    if package is None:
        package = {'name': 'RegisteredResources', 'type': 1, 'items': []}
        packages.append({'resourcePackage': package})
    if not any(i['name'] == RESOURCE for i in package['items']):
        package['items'].append({'name': RESOURCE, 'path': RESOURCE, 'type': 100})
    destination = report_folder / 'StaticResources/RegisteredResources' / RESOURCE
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'Logo FUP 2018 Isotipo-02.png', destination)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    agregar_portada(ROOT / 'powerbi/DashboardAdmisiones/DashboardAdmisiones.Report')
    print('Portada Inicio creada con logo FUP y seis accesos al análisis.')
