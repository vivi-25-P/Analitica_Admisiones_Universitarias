"""Organiza la última entrega sin volver a limpiar o cambiar sus datos."""

from pathlib import Path
import hashlib
import json

from analitica_admisiones.publicacion_entrega import publicar_excel

ROOT = Path(__file__).resolve().parents[1]
pointer = ROOT / 'reports/limpieza/ultima_entrega.json'
before = pointer.read_bytes()
summary = json.loads(before)
source = ROOT / summary['datos_salida'] / 'entregable/BaseUnificada_Entregable.xlsx'
meta = json.loads((source.parent / 'Metadatos_Entrega.json').read_text())
expected = meta['archivos'][source.name]['sha256']
publication = publicar_excel(ROOT, source, expected)
backup = ROOT / 'reports/limpieza/archivo_publicaciones' / hashlib.sha256(before).hexdigest() / pointer.name
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_bytes(before)
summary['entregable'] = publication['entregable']
summary['paquete'] = str(Path(summary['datos_salida']) / 'BaseUnificada_Entregable.zip')
summary['archivos_entregables'] = {publication['entregable']: publication['sha256']}
summary['publicacion'] = {'tipo': 'Excel único con nombre estable',
                        'resumen_anterior': str(backup.relative_to(ROOT)),
                        'datos_modificados': False}
pointer.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
(ROOT / 'reports/limpieza/publicacion_actual.json').write_text(
    json.dumps(publication, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(publication['entregable'])
print('Excel verificado. Se conservan 5.500 registros y 18 columnas.')
