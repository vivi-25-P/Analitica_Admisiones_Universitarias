"""Publica un único Excel y conserva las copias anteriores en el archivo interno."""

import hashlib
import re
import shutil
from pathlib import Path


def huella(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publicar_excel(root, source, expected_sha):
    root, source = Path(root), Path(source)
    if huella(source) != expected_sha:
        raise ValueError('El Excel de origen no coincide con su huella verificada')
    delivery = root / 'deliverables'
    delivery.mkdir(exist_ok=True)
    target = delivery / 'BaseUnificada_Entregable.xlsx'
    archive = root / 'reports/limpieza/archivo_publicaciones'
    names = {'BaseUnificada_Entregable.xlsx', 'BaseUnificada_Entregable.csv',
             'BaseUnificada_Entregable.zip', 'Informe_BaseUnificada_Entregable.pdf',
             'Informe_BaseUnificada_Entregable.md', 'Metadatos_Entrega.json',
             'Guia_Hojas.md', 'ULTIMA_VERSION.md'}
    folders = [p for p in delivery.iterdir() if p.is_dir() and re.fullmatch(r'v\d+(?:[_.]\d+)*', p.name)]
    for folder in folders:
        if any(not p.is_file() or p.name not in names for p in folder.iterdir()):
            raise ValueError(f'La carpeta {folder.name} contiene archivos no reconocidos. Se conserva intacta')
    candidates = [p for p in delivery.iterdir() if p.is_file() and p.name in names]
    candidates += [p for folder in folders for p in folder.iterdir()]
    archived = []
    for path in candidates:
        digest = huella(path)
        backup = archive / digest / path.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        if huella(backup) != digest:
            raise ValueError('La copia interna no coincide con el archivo anterior')
        archived.append({'anterior': str(path.relative_to(root)),
                         'archivo_interno': str(backup.relative_to(root)), 'sha256': digest})
    temp = delivery / '.BaseUnificada_Entregable.tmp'
    shutil.copy2(source, temp)
    try:
        if huella(temp) != expected_sha:
            raise ValueError('La copia temporal no coincide con el origen')
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    for path in candidates:
        if path != target:
            path.unlink()
    for folder in folders:
        folder.rmdir()
    return {'entregable': str(target.relative_to(root)), 'sha256': huella(target),
            'copias_anteriores_archivadas': archived}
