"""Gráficos descriptivos exportables sin modificar el archivo original."""

from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/admisiones-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .profiling import ROOT, read_original

BLUE = '#245578'
TEAL = '#187f80'
ORANGE = '#c97228'


def thousands(value):
    return f'{value:,.0f}'.replace(',', '.')


def bars(ax, rows, column, title, color=BLUE):
    counts = Counter(row[column] for row in rows)
    items = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    labels = ['Solo un espacio' if value == ' ' else value for value, _ in items]
    values = [count for _, count in items]
    ax.barh(labels, values, color=color, height=.66)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.43)
    ax.set_xlabel('Número de registros')
    ax.set_title(title, loc='left', fontweight='bold', pad=14)
    for i, count in enumerate(values):
        pct = f'{100 * count / len(rows):.2f}'.replace('.', ',')
        ax.text(count + max(values) * .018, i, f'{thousands(count)}  ({pct} %)', va='center', fontsize=9)
    ax.grid(axis='x', alpha=.15)
    ax.set_axisbelow(True)


def main():
    meta = json.loads((ROOT / 'docker/origen.json').read_text())
    source = ROOT / meta['archivo']
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != meta['sha256']:
        raise ValueError('El CSV no coincide con el original registrado.')
    headers, values = read_original(source)
    rows = [dict(zip(headers, row, strict=True)) for row in values]
    out = ROOT / 'reports/figuras'
    out.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': '#344454', 'text.color': '#243746',
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    paths = []

    def save(fig, name, note):
        fig.text(.02, .018, note, fontsize=9, color='#485768', va='bottom')
        for ext in ['png', 'pdf']:
            fig.savefig(out / f'{name}.{ext}', dpi=180, bbox_inches='tight')
        paths.append(name)
        plt.close(fig)

    for name, cols, titles in [
        ('01_programas_modalidades', ['programa', 'modalidad'], ['Registros por programa', 'Registros por modalidad']),
        ('02_canales_estados', ['canal_captacion', 'estado_proceso'], ['Registros por canal de captación', 'Registros por estado del proceso']),
    ]:
        fig, axes = plt.subplots(1, 2, figsize=(15, 6.8))
        for ax, col, title, color in zip(axes, cols, titles, [BLUE, TEAL], strict=True):
            bars(ax, rows, col, title, color)
        fig.tight_layout(rect=(0, .12, 1, 1), w_pad=3)
        save(fig, name, 'Fuente: CSV original. Base: 5.040 registros, incluidos duplicados. Porcentajes sobre el total.\n'
             'Se conservan las categorías y variantes originales. "Solo un espacio" describe el valor sin programa legible.')

    stats = {}
    for col in ['puntaje_admision', 'valor_matricula_cop']:
        nums = []
        for row in rows:
            try:
                value = float(row[col])
            except ValueError:
                continue
            if np.isfinite(value):
                nums.append(value)
        arr = np.array(nums)
        q1, q3 = np.quantile(arr, [.25, .75], method='linear')
        lower, upper = q1 - 1.5 * (q3-q1), q3 + 1.5 * (q3-q1)
        stats[col] = {'n': len(arr), 'minimo': float(arr.min()), 'maximo': float(arr.max()),
                      'promedio': float(arr.mean()), 'mediana': float(np.median(arr)),
                      'q1': float(q1), 'q3': float(q3), 'limite_inferior': float(lower),
                      'limite_superior': float(upper),
                      'atipicos_segun_criterio': int(((arr < lower) | (arr > upper)).sum())}
        fig, axes = plt.subplots(2, 1, figsize=(10, 6.6), height_ratios=[4, 1], sharex=True)
        top, bottom = axes
        if col == 'puntaje_admision':
            top.hist(arr, bins=np.arange(39.5, 101, 1), color=BLUE, edgecolor='white')
            top.set_title('Distribución de los puntajes de admisión', loc='left', fontweight='bold')
            xlabel = 'Puntaje registrado'
            excluded = '4.811 valores numéricos. Fuera del cálculo: 179 vacíos y 50 registros con "Pendiente".'
            name = '03_distribucion_puntajes'
        else:
            counts = Counter(nums)
            positions = sorted(counts)
            top.bar(positions, [counts[v] for v in positions], width=160000, color=TEAL)
            for value in positions:
                top.text(value, counts[value] + 8, thousands(counts[value]), ha='center', fontsize=10)
            top.set_xticks(positions, [f'{v / 1000000:.1f}'.replace('.', ',') for v in positions])
            top.set_title('Distribución de los valores de matrícula', loc='left', fontweight='bold')
            xlabel = 'Valor registrado en millones de pesos colombianos'
            excluded = '4.179 valores numéricos. Fuera del cálculo: 826 vacíos y 35 registros con "por definir".'
            name = '04_distribucion_matricula'
        average, med = arr.mean(), np.median(arr)
        avg_label = f'Promedio: {average:.2f}'.replace('.', ',') if col == 'puntaje_admision' else f'Promedio: ${thousands(average)}'
        med_label = f'Mediana: {med:.0f}' if col == 'puntaje_admision' else f'Mediana: ${thousands(med)}'
        top.axvline(average, color=ORANGE, linewidth=2, label=avg_label)
        top.axvline(med, color='#593e78', linewidth=1.8, linestyle=':', label=med_label)
        top.set_ylabel('Número de registros')
        top.set_ylim(0, top.get_ylim()[1] * 1.22)
        top.legend(loc='upper right', fontsize=9, framealpha=.95)
        bottom.boxplot(arr, orientation='horizontal', widths=.5, patch_artist=True,
                       boxprops={'facecolor': '#d6e8eb'}, medianprops={'color': '#593e78'})
        bottom.set_yticks([])
        bottom.set_ylabel('Caja', rotation=0, labelpad=20)
        bottom.set_xlabel(xlabel)
        fig.tight_layout(rect=(0, .16, 1, 1))
        save(fig, name, excluded + '\nSe conservan duplicados. Caja: cuartiles y mediana; atípicos según 1,5 veces el rango intercuartílico.\n'
             'No se detectaron atípicos con este criterio. Esto no acredita exactitud ni validez institucional.')

    fmts = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m-%d-%Y', '%d-%b-%Y']
    months = Counter()
    for row in rows:
        for fmt in fmts:
            try:
                date = datetime.strptime(row['fecha_solicitud'], fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError('Fecha sin interpretación documentada.')
        months[(date.year, date.month)] += 1
    keys = sorted(months)
    names = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.bar(range(len(keys)), [months[k] for k in keys], color=[ORANGE if k == (2026,9) else BLUE for k in keys])
    ax.set_xticks(range(len(keys)), [f'{names[m-1]}\n{y}' for y,m in keys], fontsize=8)
    ax.set_ylabel('Número de registros')
    ax.set_title('Registros según el mes de solicitud', loc='left', fontweight='bold')
    ax.text(len(keys)-1, months[keys[-1]]+8, '75\nHasta el día 12', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .15, 1, 1))
    save(fig, '05_cobertura_temporal', 'Fuente: 5.040 registros originales. Fechas interpretadas en memoria mediante cinco formatos explícitos.\n'
         'Septiembre de 2026 tiene cobertura hasta el día 12. La menor cantidad no demuestra una caída de la demanda.')

    empty = [(h, sum(row[h] == '' for row in rows), sum(row[h] != '' and row[h].strip() == '' for row in rows)) for h in headers]
    empty = sorted([x for x in empty if x[1] or x[2]], key=lambda x: -(x[1]+x[2]))
    fig, ax = plt.subplots(figsize=(10, 5.4))
    labels = [x[0] for x in empty]
    ax.barh(labels, [x[1] for x in empty], color=BLUE, label='Vacío exacto')
    ax.barh(labels, [x[2] for x in empty], left=[x[1] for x in empty], color=ORANGE, label='Solo espacios')
    ax.invert_yaxis()
    for i, (_, a, b) in enumerate(empty):
        pct=f'{100*(a+b)/len(rows):.2f}'.replace('.', ',')
        ax.text(a+b+30, i, f'{thousands(a+b)} ({pct} %)', va='center')
    ax.set_xlim(0, max(x[1]+x[2] for x in empty)*1.3)
    ax.set_xlabel('Número de registros')
    ax.set_title('Valores vacíos o con solo espacios por columna', loc='left', fontweight='bold')
    ax.legend(loc='lower right')
    fig.tight_layout(rect=(0, .15, 1, 1))
    save(fig, '06_completitud', 'Fuente: 5.040 registros originales. No incluye "No aplica", "Pendiente" ni "por definir" como vacíos.\n'
         'Un dato ausente no equivale automáticamente a un error; su obligatoriedad depende del estado y de las reglas institucionales.')

    (out / 'estadisticas_graficos.json').write_text(json.dumps({'sha256_original': before, 'base': len(rows), 'numericas': stats, 'figuras': paths}, ensure_ascii=False, indent=2)+'\n')
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('El archivo original cambió durante la generación.')
    print(f'{len(paths)} figuras generadas en PNG y PDF. Original intacto. Destino: {out}')


if __name__ == '__main__':
    main()
