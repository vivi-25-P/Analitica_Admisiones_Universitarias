"""Configura la carpeta del proyecto sin regenerar el modelo ni el informe Power BI."""

import argparse
from pathlib import Path, PureWindowsPath
import re

ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / 'powerbi/DashboardAdmisiones/DashboardAdmisiones.SemanticModel/definition'
PARAMETER = re.compile(r'(?m)^(expression RutaProyecto =\s*)"(?:[^"\n]|"")*"')


def ruta_windows(path):
    resolved = str(path.resolve())
    mounted = re.fullmatch(r'/mnt/([a-zA-Z])/(.*)', resolved)
    if mounted:
        drive, relative = mounted.groups()
        return str(PureWindowsPath(f'{drive.upper()}:/') / relative)
    return resolved


def texto_m(value):
    return '"' + value.replace('"', '""') + '"'


def expresiones_rutas(root, excel):
    try:
        excel_expression = 'ArchivoProyecto(' + texto_m(excel.relative_to(root).as_posix()) + ')'
    except ValueError:
        excel_expression = texto_m(ruta_windows(excel))
    return (
        f'expression RutaProyecto = {texto_m(ruta_windows(root))} meta '
        '[IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\n'
        'expression ArchivoProyecto =\n'
        '\t\t(relativa as text) as text =>\n'
        '\t\t    Text.TrimEnd(RutaProyecto, {"/", "\\"}) & "\\" & '
        'Text.Replace(Text.TrimStart(relativa, {"/", "\\"}), "/", "\\")\n\n'
        f'expression RutaLibroBase = {excel_expression}\n\n'
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comprobar', action='store_true', help='Comprueba los archivos sin escribir.')
    args = parser.parse_args()
    expression_file = DEFINITION / 'expressions.tmdl'
    text = expression_file.read_text(encoding='utf-8')
    if len(PARAMETER.findall(text)) != 1:
        raise SystemExit('No se encontró un único parámetro RutaProyecto. Revisa la versión del modelo.')
    relative_files = set()
    for path in [expression_file, *DEFINITION.glob('tables/Ref*.tmdl')]:
        relative_files.update(re.findall(r'ArchivoProyecto\("([^"\n]+)"\)', path.read_text(encoding='utf-8')))
    if len(relative_files) != 7:
        raise SystemExit('Se esperaban el Excel entregable y seis CSV relativos. Revisa las fuentes.')
    missing = [name for name in sorted(relative_files) if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit('Faltan fuentes: ' + ', '.join(missing))
    root = ruta_windows(ROOT)
    if not re.match(r'^(?:[A-Za-z]:[\\/]|\\\\)', root):
        raise SystemExit('Ejecuta este comando en Windows o desde un repositorio en /mnt/<unidad>/ de WSL.')
    updated = PARAMETER.sub(lambda match: match[1] + texto_m(root), text, count=1)
    if not args.comprobar and updated != text:
        expression_file.write_text(updated, encoding='utf-8', newline='\n')
    print('Fuentes disponibles: 1 Excel y 6 CSV.')
    print(('Ruta detectada: ' if args.comprobar else 'Ruta configurada: ') + root)
    if args.comprobar:
        print('El parámetro coincide con este equipo.' if updated == text else 'Ejecuta sin --comprobar para configurar la ruta.')
    else:
        print('Abre el PBIP y pulsa Actualizar. Se conservaron medidas, diseño y caché.')


if __name__ == '__main__':
    main()
