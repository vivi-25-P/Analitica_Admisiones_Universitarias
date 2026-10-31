"""Amplía los filtros sin regenerar ni modificar el modelo semántico."""

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'powerbi/DashboardAdmisiones/DashboardAdmisiones.Report/report.json'
OUT = ROOT / 'reports/revision_dashboard_powerbi'
OUT.mkdir(exist_ok=True, parents=True)
before = TARGET.read_bytes()
report = json.loads(before)
pages, slicers = [], 0
scale = (720 - 178) / (720 - 146)
for section in report['sections']:
    visuals = section['visualContainers']
    filters = [v for v in visuals if json.loads(v['config']).get('singleVisual', {}).get('visualType') == 'slicer']
    if not filters:
        continue
    if all(v['height'] == 76 and v['y'] == 90 for v in filters):
        continue
    if len(filters) != 6 or any(v['height'] != 58 or v['y'] != 82 for v in filters):
        raise ValueError('El diseño cambió. Revisar manualmente: ' + section['displayName'])
    for visual in visuals:
        config = json.loads(visual['config'])
        kind = config.get('singleVisual', {}).get('visualType')
        if kind == 'slicer':
            y, height = 90, 76
            slicers += 1
        elif visual['y'] >= 146:
            y = round(178 + (visual['y'] - 146) * scale, 2)
            height = round(visual['height'] * scale, 2)
        else:
            continue
        visual['y'], visual['height'] = y, height
        for layout in config.get('layouts', []):
            if layout.get('id') == 0:
                layout['position']['y'] = y
                layout['position']['height'] = height
        visual['config'] = json.dumps(config, ensure_ascii=False)
    pages.append(section['displayName'])

if pages:
    backup = OUT / 'respaldo_diseno_anterior.json'
    if backup.exists():
        raise ValueError('Existe un respaldo anterior. No se sobrescribe.')
    backup.write_bytes(before)
    if TARGET.read_bytes() != before:
        raise ValueError('El informe cambió durante la revisión')
    TARGET.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

checks = {}
for section in report['sections']:
    for visual in section['visualContainers']:
        config = json.loads(visual['config'])
        pos = config['layouts'][0]['position']
        if any(abs(pos[k] - visual[k]) > .02 for k in ['x', 'y', 'width', 'height']):
            raise ValueError('Posiciones inconsistentes')
        if visual['y'] < 0 or visual['y'] + visual['height'] > section['height'] + .02:
            raise ValueError('Objeto fuera del lienzo')
    if section['displayName'] in pages:
        filters = [v for v in section['visualContainers'] if json.loads(v['config']).get('singleVisual', {}).get('visualType') == 'slicer']
        content = [v for v in section['visualContainers'] if v['y'] >= 178]
        checks[section['displayName']] = max(v['y'] + v['height'] for v in filters) < min(v['y'] for v in content)

metadata = {'fecha': '2026-10-30', 'paginas_ajustadas': pages, 'filtros_ajustados': slicers,
    'altura_anterior': 58, 'altura_nueva': 76, 'comprobaciones_espaciado': checks,
    'sha256_antes': sha256(before).hexdigest(), 'sha256_despues': sha256(TARGET.read_bytes()).hexdigest(),
    'modelo_modificado': False, 'verificado_en_pantalla_despues': False}
if pages:
    (OUT / 'ajuste_visual.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
print(json.dumps(metadata, ensure_ascii=False, indent=2))
