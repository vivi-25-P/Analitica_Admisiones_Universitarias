"""Figuras de lectura administrativa con equivalencias explícitas del Anexo A."""

from collections import Counter
import hashlib
import json

from .visualizations import ROOT, BLUE, TEAL, bars, plt, read_original


def main():
    meta = json.loads((ROOT / 'docker/origen.json').read_text())
    source = ROOT / meta['archivo']
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != meta['sha256']:
        raise ValueError('El archivo difiere del original registrado.')
    headers, values = read_original(source)
    originals = [dict(zip(headers, row, strict=True)) for row in values]
    rules = {
        'programa': {'DERECHO': 'Derecho', 'Especializacion en Data Analytics': 'Especialización en Data Analytics', ' ': 'Sin programa registrado'},
        'modalidad': {'VIRTUAL': 'Virtual', 'presencial': 'Presencial'},
        'estado_proceso': {'ADMITIDO': 'Admitido', 'matriculado': 'Matriculado'},
    }
    display = [{k: rules.get(k, {}).get(v, v) for k,v in row.items()} for row in originals]
    out = ROOT / 'reports/figuras'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'text.color': '#243746', 'figure.facecolor': 'white'})
    for name, columns, titles in [
        ('07_programas_modalidades_lectura', ['programa','modalidad'], ['Registros por programa', 'Registros por modalidad']),
        ('08_canales_estados_lectura', ['canal_captacion','estado_proceso'], ['Registros por canal de captación', 'Registros por estado del proceso']),
    ]:
        fig, axes = plt.subplots(2,1,figsize=(10,9.5))
        for ax,col,title,color in zip(axes,columns,titles,[BLUE,TEAL],strict=True):
            bars(ax, display, col, title, color)
        fig.tight_layout(rect=(0,.1,1,1),h_pad=3)
        fig.text(.02,.018,'Fuente: 5.040 registros originales, incluidos duplicados. Porcentajes sobre el total.\n'
                 'Variantes agrupadas únicamente para presentación según Anexo A. El CSV no se modifica.\n'
                 '"Sin programa registrado" identifica 25 valores con solo un espacio; no es un programa imputado.',fontsize=8)
        for ext in ['png','pdf']:
            fig.savefig(out/f'{name}.{ext}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    result={'filas':len(display),'sha256_original':digest,'equivalencias_presentacion':rules,'conteos':{col:dict(Counter(row[col] for row in display)) for col in rules}}
    (out/'equivalencias_figuras_informe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    assert len(originals)==len(display)==5040
    print(json.dumps(result['conteos'],ensure_ascii=False))
    print('Dos figuras de lectura generadas en PNG y PDF. Filas y CSV originales conservados.')


if __name__=='__main__':
    main()
