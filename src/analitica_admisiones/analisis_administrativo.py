"""Análisis descriptivo reproducible de la entrega, sin modificar sus datos."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(value):
    text = re.sub(r'\s+', ' ', str(value).strip()).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def fmt(value, decimals=0):
    return f'{value:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


class AnalisisAdministrativo:
    def __init__(self, root):
        self.root = Path(root)
        self.out = self.root / 'reports/analisis_administrativo'
        self.tables_dir = self.out / 'tablas'
        self.fig = self.out / 'figuras'
        for folder in [self.tables_dir, self.fig]:
            folder.mkdir(parents=True, exist_ok=True)
        self.rules_path = self.root / 'config/analisis_administrativo.json'
        self.rules = json.loads(self.rules_path.read_text())
        self.summary_path = self.root / 'reports/limpieza/ultima_entrega.json'
        self.summary = json.loads(self.summary_path.read_text())
        self.source = self.root / self.summary['entregable']
        self.input_sha = sha(self.source)
        assert self.input_sha == self.summary['archivos_entregables'][self.summary['entregable']]
        book = load_workbook(self.source, read_only=True, data_only=True)
        self.sheets = {}
        for sheet in book:
            values = iter(sheet.values)
            headers = next(values)
            self.sheets[sheet.title] = pd.DataFrame(values, columns=headers)
        book.close()
        self.base = self.sheets['BaseUnificada']
        self.original = self.base.copy(deep=True)
        assert self.base.shape == (5500, 18) and self.base.registro_id.is_unique
        self.df = self.base.merge(self.sheets['Origen_Registros'][['registro_id', 'fuente_origen']],
                                  on='registro_id', validate='one_to_one')
        q = self.sheets['Control_Calidad']
        quality_columns = [c for c in q if c not in self.df.columns or c == 'registro_id']
        self.df = self.df.merge(q[quality_columns], on='registro_id', validate='one_to_one')
        self.df['programa'] = self.df.programa.fillna('Sin información')
        self.df['matriculado'] = self.df.estado_proceso.eq('Matriculado').astype(int)
        self.tables = {}
        self.figures = []
        self.inputs = {self.source: self.input_sha, self.summary_path: sha(self.summary_path),
                       self.rules_path: sha(self.rules_path)}
        self.n = len(self.df)

    def save(self, name, frame):
        self.tables[name] = frame.copy()
        frame.to_csv(self.tables_dir / f'{name}.csv', index=False, encoding='utf-8-sig',
                     lineterminator='\n', float_format='%.6f')
        return frame

    def group(self, dimensions, frame=None):
        frame = self.df if frame is None else frame
        dimensions = [dimensions] if isinstance(dimensions, str) else dimensions
        result = frame.groupby(dimensions, dropna=False).agg(
            registros=('registro_id', 'size'), matriculados=('matriculado', 'sum'),
            puntajes_informados=('puntaje_admision', 'count'),
            importes_informados=('valor_matricula_cop', 'count')).reset_index()
        result['participacion_registros_pct'] = result.registros / len(frame) * 100
        result['proporcion_matriculado_pct'] = result.matriculados / result.registros * 100
        result['diferencia_pp_frente_total_ambito'] = result.proporcion_matriculado_pct - frame.matriculado.mean() * 100
        result['cobertura_puntaje_pct'] = result.puntajes_informados / result.registros * 100
        result['cobertura_importe_pct'] = result.importes_informados / result.registros * 100
        result['grupo_pequeno'] = result.registros.lt(self.rules['grupos_pequenos_menores_de'])
        result['denominador_ambito'] = len(frame)
        return result

    def volumen(self):
        for dim in ['programa', 'modalidad', 'canal_captacion', 'estado_proceso',
                    'ciudad_residencia', 'periodo_academico', 'fuente_origen']:
            self.save(dim, self.group(dim).sort_values('registros', ascending=False))
        for dims in [['programa', 'modalidad'], ['programa', 'periodo_academico'],
                     ['canal_captacion', 'programa', 'modalidad', 'periodo_academico']]:
            tab = self.group(dims)
            if dims == ['programa','periodo_academico']:
                tab['denominador_periodo'] = tab.groupby('periodo_academico').registros.transform('sum')
                tab['participacion_dentro_periodo_pct'] = tab.registros / tab.denominador_periodo * 100
            if dims == ['programa','modalidad']:
                tab['denominador_programa'] = tab.groupby('programa').registros.transform('sum')
                tab['participacion_modalidad_en_programa_pct'] = tab.registros / tab.denominador_programa * 100
            self.save('_'.join(dims), tab)
        states = pd.crosstab(self.df.canal_captacion, self.df.estado_proceso).reset_index()
        self.save('canal_estado_conteos', states)
        self.save('canal_estado_porcentajes', pd.crosstab(
            self.df.canal_captacion, self.df.estado_proceso, normalize='index').mul(100).reset_index())
        self.save('resumen', pd.DataFrame([{
            'registros': self.n, 'matriculados': int(self.df.matriculado.sum()),
            'proporcion_matriculado_pct': self.df.matriculado.mean() * 100,
            'puntajes_informados': int(self.df.puntaje_admision.notna().sum()),
            'importes_informados': int(self.df.valor_matricula_cop.notna().sum()),
            'programas_identificados': self.base.programa.nunique(),
            'programa_sin_informacion': int(self.base.programa.isna().sum())}]))
        return self.tables['resumen']

    def canales_comparables(self):
        dims = ['programa', 'modalidad', 'periodo_academico']
        known = self.df[self.df.programa.ne('Sin información')]
        counts = known.groupby([*dims, 'canal_captacion']).matriculado.agg(['size', 'sum'])
        presence = counts['size'].unstack('canal_captacion', fill_value=0)
        common = presence.index[presence.gt(0).all(axis=1)]
        mask = pd.MultiIndex.from_frame(known[dims]).isin(common)
        support = known.loc[mask].copy()
        assert len(support) > 0
        weights = support.groupby(dims).size() / len(support)
        rows = []
        for channel, total in self.df.groupby('canal_captacion'):
            subset = support[support.canal_captacion.eq(channel)]
            cells = subset.groupby(dims).matriculado.agg(['size', 'sum'])
            assert set(cells.index) == set(common)
            adjusted = cells['sum'].div(cells['size']).mul(weights).sum() * 100
            rows.append({'canal_captacion': channel, 'registros_totales': len(total),
                'proporcion_bruta_pct': total.matriculado.mean() * 100,
                'registros_soporte_comun': len(subset),
                'proporcion_bruta_soporte_pct': subset.matriculado.mean() * 100,
                'proporcion_estandarizada_descriptiva_pct': adjusted,
                'estratos_comunes': len(common), 'menor_celda': int(cells['size'].min()),
                'celdas_menores_30': int(cells['size'].lt(self.rules['grupos_pequenos_menores_de']).sum()),
                'cobertura_soporte_del_canal_pct': len(subset) / len(total) * 100})
        self.save('pesos_estratos_comunes', weights.rename('peso_comun').reset_index())
        self.save('canales_comparables', pd.DataFrame(rows).sort_values('proporcion_bruta_pct', ascending=False))
        return self.tables['canales_comparables']

    def seguimiento(self):
        for dim in ['documentos_completos', 'asesor']:
            self.save(dim, self.group(dim))
        for dims in [['documentos_completos', 'programa', 'modalidad', 'periodo_academico'],
                     ['asesor', 'programa', 'modalidad', 'periodo_academico']]:
            self.save('_'.join(dims), self.group(dims))
        self.save('documentacion_estado', pd.crosstab(self.df.documentos_completos,
                  self.df.estado_proceso).reset_index())
        self.save('puntajes_por_estado', self.df.groupby('estado_proceso').puntaje_admision.agg(
            informados='count', promedio='mean', mediana='median', minimo='min', maximo='max',
            cuartil_1=lambda s:s.quantile(.25), cuartil_3=lambda s:s.quantile(.75)).reset_index().merge(
                self.group('estado_proceso')[['estado_proceso', 'registros', 'cobertura_puntaje_pct']],
                on='estado_proceso', validate='one_to_one'))
        with_score = self.df[self.df.puntaje_admision.notna()].copy()
        with_score['franja_puntaje'] = pd.cut(with_score.puntaje_admision,
            bins=self.rules['franjas_puntaje'], labels=self.rules['etiquetas_puntaje'], right=False)
        assert with_score.franja_puntaje.notna().all()
        self.save('franja_puntaje_estado', self.group(['franja_puntaje', 'estado_proceso'], with_score))
        self.save('franja_puntaje_estados_porcentajes', pd.crosstab(with_score.franja_puntaje,
            with_score.estado_proceso, normalize='index').mul(100).reset_index())
        valid = self.df[self.df.intervalo_dias_apto_reglas_aplicadas.eq(True)]
        intervals = valid.groupby('documentos_completos').dias_solicitud_matricula.agg(
            intervalos_aptos='count', minimo='min', promedio='mean', mediana='median', maximo='max').reset_index()
        intervals = intervals.merge(self.group('documentos_completos')[['documentos_completos', 'registros', 'matriculados']],
                                    on='documentos_completos', validate='one_to_one')
        intervals['cobertura_intervalo_entre_matriculados_pct'] = intervals.intervalos_aptos / intervals.matriculados * 100
        self.save('intervalos_por_documentacion', intervals)
        eligible = self.df[self.df.fecha_solicitud_apta_reglas_aplicadas.eq(True)].copy()
        eligible['mes'] = pd.to_datetime(eligible.fecha_solicitud).dt.strftime('%Y-%m')
        all_dates = self.df.copy()
        all_dates['mes'] = pd.to_datetime(all_dates.fecha_solicitud).dt.strftime('%Y-%m')
        self.save('serie_mensual', all_dates.groupby('mes').size().rename('todos_registros').to_frame().join(
            eligible.groupby('mes').size().rename('fechas_aptas')).fillna(0).reset_index())
        recurrences = []
        for source, group in self.df[self.df.aspirante_id.notna()].groupby('fuente_origen'):
            count = group.groupby('aspirante_id').size()
            for amount, codes in count.value_counts().items():
                recurrences.append({'fuente_origen': source, 'solicitudes_por_codigo': int(amount),
                    'codigos': int(codes), 'registros': int(amount * codes),
                    'denominador_codigos_origen': len(count)})
        self.save('recurrencia_codigos', pd.DataFrame(recurrences).sort_values(['fuente_origen', 'solicitudes_por_codigo']))
        self.save('importes_por_programa', self.df.groupby('programa').valor_matricula_cop.agg(
            informados='count', importes_distintos='nunique', minimo='min', maximo='max',
            promedio='mean', mediana='median').reset_index().merge(
                self.group('programa')[['programa', 'registros', 'cobertura_importe_pct']],
                on='programa', validate='one_to_one'))
        return self.tables['puntajes_por_estado']

    def segmentos(self):
        dims = ['ciudad_residencia', 'programa', 'modalidad']
        result = self.group(dims).sort_values('registros', ascending=False)
        self.save('segmentos_completos', result)
        self.save('segmentos_volumen_priorizados_revision', result[
            result.programa.ne('Sin información') & ~result.grupo_pequeno].head(12))
        self.save('segmentos_por_canal_periodo', self.group([*dims, 'canal_captacion', 'periodo_academico']))
        pointer = self.root / 'reports/validacion_analisis/ultima_validacion.json'
        meta = json.loads(pointer.read_text())
        pairs_path = self.root / meta['directorio'] / 'revision_pares_oracle.csv'
        self.inputs[pointer] = sha(pointer)
        self.inputs[pairs_path] = sha(pairs_path)
        pairs = pd.read_csv(pairs_path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        oracle_ids = set(pairs.loc[pairs.compatible_para_escenario.eq('True'), 'registro_id_oracle'])
        assert len(oracle_ids) == 49 and oracle_ids <= set(self.df.registro_id)
        # Vista hipotética, no se elimina nada de la base maestra.
        hypothetical = self.df[~self.df.registro_id.isin(oracle_ids)]
        self.scenario_size = len(hypothetical)
        differences = []
        for dimensions in [['programa'], ['modalidad'], ['canal_captacion'], ['estado_proceso'], dims]:
            a = self.group(dimensions).set_index(dimensions)
            b = self.group(dimensions, hypothetical).set_index(dimensions)
            common = a.join(b, how='left', lsuffix='_base', rsuffix='_escenario')
            common['diferencia_participacion_pp'] = common.participacion_registros_pct_escenario.fillna(0) - common.participacion_registros_pct_base
            common['diferencia_matriculado_pp'] = common.proporcion_matriculado_pct_escenario - common.proporcion_matriculado_pct_base
            common['dimension'] = ', '.join(dimensions)
            differences.append(common.reset_index())
        self.save('sensibilidad_49_pares', pd.concat(differences, ignore_index=True))
        source_rows = []
        for scope, frame in [('Integrada', self.df), ('Principal', self.df[self.df.fuente_origen.eq('Principal')]),
                             ('Oracle', self.df[self.df.fuente_origen.eq('Oracle')])]:
            for dimension in ['programa', 'modalidad', 'canal_captacion', 'estado_proceso']:
                tab = self.group(dimension, frame).rename(columns={dimension:'categoria'})
                tab['dimension'] = dimension
                tab['ambito'] = scope
                source_rows.append(tab)
        self.save('comparacion_por_fuente', pd.concat(source_rows, ignore_index=True))
        return self.tables['segmentos_volumen_priorizados_revision']

    def antes_despues(self):
        path = self.root / 'data/raw/Caso2_Admisiones_Universitarias.csv'
        self.inputs[path] = sha(path)
        raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        rules_path = self.root / 'config/limpieza/estandarizacion_v1.json'
        self.inputs[rules_path] = sha(rules_path)
        rules = json.loads(rules_path.read_text())
        aligned = raw.copy()
        for column in ['programa', 'modalidad', 'canal_captacion', 'estado_proceso']:
            catalog = {key(v): v for v in rules['categorias'][column]}
            def canonical(value):
                return 'Sin información' if not value.strip() else catalog[key(value)]
            aligned[column] = raw[column].map(canonical)
        aligned['estado_proceso'] = aligned.estado_proceso.replace({'Nuevo':'Admitido'})
        aligned['matriculado'] = aligned.estado_proceso.eq('Matriculado').astype(int)
        counts = []
        for col in ['programa', 'modalidad', 'estado_proceso']:
            counts.append({'columna':col, 'etiquetas_recibidas':raw[col].nunique(),
                'categorias_agrupadas':aligned[col].nunique(), 'filas_en_ambos':len(raw)})
        self.save('efecto_escrituras_mismo_universo', pd.DataFrame(counts))
        principal = self.df[self.df.fuente_origen.eq('Principal')]
        comparison = []
        for column in ['programa', 'modalidad', 'canal_captacion', 'estado_proceso']:
            for stage, frame in [('Original con etiquetas alineadas', aligned),
                                 ('Principal conciliada con CRM', principal),
                                 ('Integrada con Oracle', self.df)]:
                for category, amount in frame[column].value_counts().items():
                    comparison.append({'variable':column, 'categoria':category, 'etapa':stage,
                        'registros':int(amount), 'denominador':len(frame),
                        'porcentaje':amount/len(frame)*100})
        self.save('antes_despues_ambitos_separados', pd.DataFrame(comparison))
        self.save('evolucion_cantidades', pd.DataFrame([
            {'etapa':'Original', 'registros':5040, 'interpretacion':'Fuente original con repeticiones'},
            {'etapa':'Principal conciliada', 'registros':5000, 'interpretacion':'38 repeticiones exactas y dos parciales consolidadas'},
            {'etapa':'Integrada', 'registros':5500, 'interpretacion':'Se incorporan 500 registros Oracle, no es efecto de limpieza'}]))
        return self.tables['efecto_escrituras_mismo_universo']

    def plot(self, name, title, fig):
        fig.tight_layout()
        fig.savefig(self.fig / f'{name}.png', dpi=180, bbox_inches='tight')
        fig.savefig(self.fig / f'{name}.pdf', bbox_inches='tight', metadata={'Author':'', 'Creator':''})
        plt.close(fig)
        self.figures.append({'archivo':name+'.png', 'titulo':title})

    def graficar(self):
        plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
        tab = pd.crosstab(self.df.programa, self.df.modalidad)
        tab = tab.reindex(tab.sum(axis=1).sort_values().index)
        tab.index = [s.replace('Especialización en ', 'Esp. ').replace('Administración de Empresas','Administración') for s in tab.index]
        fig, ax = plt.subplots(figsize=(10,5))
        tab.plot.barh(stacked=True, ax=ax, color=['#90b7c9','#246c94','#50a692'])
        ax.set(title='Registros por programa y modalidad', xlabel='Registros', ylabel='Programa')
        ax.legend(title='Modalidad', loc='lower right')
        self.plot('01_programas_modalidades','Registros por programa y modalidad',fig)
        fig, axes = plt.subplots(1,2,figsize=(12,4.5))
        a = self.tables['canal_captacion'].sort_values('registros')
        axes[0].barh(a.canal_captacion,a.registros,color='#246c94')
        axes[0].set(title='Volumen por canal',xlabel='Registros')
        b = self.tables['canales_comparables'].sort_values('proporcion_bruta_pct')
        axes[1].scatter(b.proporcion_bruta_soporte_pct,b.canal_captacion,label='Bruta en grupos comunes',color='#246c94')
        axes[1].scatter(b.proporcion_estandarizada_descriptiva_pct,b.canal_captacion,label='Con pesos comunes',color='#d98636',marker='D')
        axes[1].set(title='Proporción con estado Matriculado',xlabel='Registros Matriculado (%)',xlim=(0,30))
        axes[1].legend(loc='lower left')
        self.plot('02_canales_comparables','Canales, volumen y comparación descriptiva',fig)
        tab = pd.crosstab(self.df.documentos_completos,self.df.estado_proceso,normalize='index').mul(100)
        fig, ax = plt.subplots(figsize=(10,4))
        tab.plot.barh(stacked=True,ax=ax,colormap='tab20')
        ax.set(title='Estados según documentación registrada',xlabel='Registros de cada situación documental (%)',ylabel='Documentación',xlim=(0,100))
        ax.legend(title='Estado',bbox_to_anchor=(1.02,1),loc='upper left')
        self.plot('03_documentacion_estados','Estados según documentación registrada',fig)
        states = sorted(self.df.estado_proceso.unique())
        fig, ax = plt.subplots(figsize=(10,4.5))
        values = [self.df.loc[self.df.estado_proceso.eq(s),'puntaje_admision'].dropna().tolist() for s in states]
        ax.boxplot(values,orientation='horizontal',tick_labels=states,showmeans=True)
        ax.set(title='Puntajes disponibles según estado registrado',xlabel='Puntaje registrado',xlim=(35,105))
        self.plot('04_puntajes_estados','Puntajes disponibles según estado registrado',fig)
        fig, axes = plt.subplots(1,2,figsize=(11,4))
        advisors = self.tables['asesor']
        axes[0].bar(advisors.asesor,advisors.registros,color=['#246c94']*3+['#d98636'])
        axes[0].set(title='Asignación de asesor',ylabel='Registros')
        r = self.tables['recurrencia_codigos'];r=r[r.fuente_origen.eq('Principal')]
        axes[1].bar(r.solicitudes_por_codigo,r.codigos,color='#50a692')
        axes[1].set(title='Recurrencia en la fuente principal',xlabel='Solicitudes por código',ylabel='Códigos de aspirante')
        self.plot('05_asesor_recurrencia','Asignación y recurrencia de códigos',fig)
        heat = pd.crosstab(self.df.ciudad_residencia,self.df.programa)
        heat = heat.drop(columns='Sin información', errors='ignore')
        fig, ax = plt.subplots(figsize=(10,5))
        im = ax.imshow(heat.values,cmap='Blues',aspect='auto')
        for i,row in enumerate(heat.values):
            for j,value in enumerate(row):
                ax.text(j,i,str(value),ha='center',va='center',color='white' if value>heat.values.max()*.6 else '#222222')
        ax.set_xticks(range(len(heat.columns)),[s.replace('Especialización en ','Esp. ') for s in heat.columns],rotation=35,ha='right')
        ax.set_yticks(range(len(heat)),heat.index)
        ax.set_title('Interés registrado por ciudad y programa')
        fig.colorbar(im,ax=ax,label='Registros')
        self.plot('06_ciudades_programas','Interés registrado por ciudad y programa',fig)
        tab=self.tables['serie_mensual']
        fig, ax=plt.subplots(figsize=(11,4))
        ax.plot(tab.mes,tab.todos_registros,label='Todos los registros',marker='o',markersize=3)
        ax.plot(tab.mes,tab.fechas_aptas,label='Fechas sin las alertas aplicadas',linestyle='--')
        ax.set(title='Cobertura mensual de las solicitudes',xlabel='Mes de solicitud',ylabel='Registros')
        ax.tick_params(axis='x',rotation=55);ax.legend()
        self.plot('07_cobertura_mensual','Cobertura mensual de las solicitudes',fig)
        return self.figures

    def table_markdown(self, frame):
        rows = [list(frame.columns), *frame.fillna('Sin información').astype(str).values.tolist()]
        result = ['| ' + ' | '.join(rows[0]) + ' |', '| ' + ' | '.join([':---'] * len(rows[0])) + ' |']
        result += ['| ' + ' | '.join(row) + ' |' for row in rows[1:]]
        return '\n'.join(result)

    def redactar(self):
        programs = self.tables['programa']
        identified = programs[programs.programa.ne('Sin información')].head(2)
        top_programs = ' y '.join(identified.programa)
        top_amount = int(identified.registros.sum())
        modality = self.tables['modalidad'].set_index('modalidad')
        channels = self.tables['canales_comparables']
        best = channels.iloc[0]
        worst = channels.iloc[-1]
        docs = self.tables['documentos_completos'].set_index('documentos_completos')
        advisors = self.tables['asesor'].set_index('asesor')
        scores = self.tables['puntajes_por_estado'].set_index('estado_proceso')
        rec = self.tables['recurrencia_codigos']
        principal = rec[rec.fuente_origen.eq('Principal')]
        known_codes = int(principal.codigos.sum())
        recurring = int(principal.loc[principal.solicitudes_por_codigo.gt(1), 'codigos'].sum())
        max_requests = int(principal.solicitudes_por_codigo.max())
        contradiction = self.df[self.df.matriculado.eq(1) & self.df.documentos_completos.isin(['No', 'Pendiente'])]
        pending_yes = self.df[self.df.estado_proceso.eq('Documentación pendiente') & self.df.documentos_completos.eq('Sí')]
        total_pending = int(self.df.estado_proceso.eq('Documentación pendiente').sum())
        proportions = channels.proporcion_bruta_pct
        raw_range = float(proportions.max() - proportions.min())
        adjusted = channels.proporcion_estandarizada_descriptiva_pct
        support_range = float(channels.proporcion_bruta_soporte_pct.max() - channels.proporcion_bruta_soporte_pct.min())
        adjusted_range = float(adjusted.max() - adjusted.min())
        segment_diff = self.tables['sensibilidad_49_pares']
        segment_diff = segment_diff[segment_diff.dimension.eq('ciudad_residencia, programa, modalidad') &
                                    segment_diff.registros_base.ge(self.rules['grupos_pequenos_menores_de'])]
        max_segment_diff = segment_diff.diferencia_matriculado_pp.abs().max()
        n_support = int(channels.registros_soporte_comun.sum())
        total_mat = int(self.df.matriculado.sum())
        periods = self.tables['programa_periodo_academico']
        period_leaders = periods[periods.programa.ne('Sin información')].sort_values(
            ['periodo_academico','registros'], ascending=[True,False]).groupby('periodo_academico').head(1)
        period_text = '. '.join(f'En el periodo {int(r.periodo_academico)}, {r.programa} reúne '
            f'{fmt(r.registros)} registros y el {fmt(r.participacion_dentro_periodo_pct,2)} % de ese periodo'
            for r in period_leaders.itertuples()) + '.'
        self.save('programa_mayor_volumen_por_periodo',period_leaders)
        interval_table = self.tables['intervalos_por_documentacion'].set_index('documentos_completos')
        interval_text = '. '.join(f'{label}: {fmt(interval_table.loc[label,"mediana"])} días de mediana '
            f'con {fmt(interval_table.loc[label,"intervalos_aptos"])} intervalos aptos'
            for label in ['Sí','No','Pendiente']) + '.'
        overlap = max(scores.loc['Admitido','cuartil_1'],scores.loc['No admitido','cuartil_1']) <= min(
            scores.loc['Admitido','cuartil_3'],scores.loc['No admitido','cuartil_3'])
        overlap_text = ('Los intervalos entre el primer y tercer cuartil de ambos estados se superponen.'
                        if overlap else 'Los intervalos entre el primer y tercer cuartil no se superponen.')
        findings = [
            ['H01', 'Concentración de interés registrado',
             f'{top_programs} reúnen {fmt(top_amount)} registros, el {fmt(top_amount/self.n*100,2)} % del total. Presencial reúne {fmt(modality.loc["Presencial","registros"])} y Virtual {fmt(modality.loc["Virtual","registros"])}.',
             'Revisar capacidad, mensajes y atención para la oferta con mayor volumen registrado.',
             'Las solicitudes no representan todo el mercado ni disponibilidad de cupos.'],
            ['H02', 'Diferencias observadas entre canales',
             f'{best.canal_captacion} presenta {fmt(best.proporcion_bruta_pct,2)} % con estado Matriculado y {worst.canal_captacion} {fmt(worst.proporcion_bruta_pct,2)} %. En soporte común, la amplitud bruta es {fmt(support_range,2)} puntos y con pesos comunes es {fmt(adjusted_range,2)} puntos.',
             'Comparar campañas piloto dentro de programas, modalidades y periodos equivalentes antes de redistribuir presupuesto.',
             'Las celdas pequeñas y la composición limitan la interpretación. No se mide eficacia o rentabilidad.'],
            ['H03', 'Coherencia documental por revisar',
             f'{fmt(len(contradiction))} de {fmt(total_mat)} registros Matriculado tienen documentos No o Pendiente. Hay {fmt(len(pending_yes))} registros Documentación pendiente con documentos Sí.',
             'Revisar las reglas y actualización coordinada de documentación y estado.',
             'No se conoce la fecha de actualización de cada atributo. No se demuestra incumplimiento ni secuencia.'],
            ['H04', 'Puntajes y estados con información parcial',
             f'Promedio {fmt(scores.loc["Admitido","promedio"],2)} en Admitido y {fmt(scores.loc["No admitido","promedio"],2)} en No admitido. Se dispone de 5.254 puntajes.',
             'Examinar distribución y reglas de admisión antes de proponer cambios en criterios.',
             'Una diferencia de promedios no reconstruye la decisión ni valida un umbral institucional.'],
            ['H05', 'Asignación y recurrencia requieren dos unidades de lectura',
             f'{fmt(advisors.loc["Sin asignar","registros"])} registros, {fmt(advisors.loc["Sin asignar","participacion_registros_pct"],2)} %, figuran Sin asignar. En la principal, {fmt(recurring)} de {fmt(known_codes)} códigos tienen entre 2 y {max_requests} solicitudes.',
             'Revisar asignación y seguimiento por solicitud y código, evitando duplicar personas en los reportes.',
             'La recurrencia puede ser legítima. No se atribuye desempeño a un asesor ni se fusionan personas por fuente.'],
            ['H06', 'Segmentos para validar, no nichos confirmados',
             f'La matriz ciudad, programa y modalidad identifica concentraciones de volumen. En segmentos con al menos 30 registros, el cambio máximo en la proporción Matriculado bajo el escenario de 49 pares es {fmt(max_segment_diff,2)} puntos.',
             'Seleccionar combinaciones con volumen suficiente para campañas piloto y registrar su respuesta.',
             'La marca de 30 no prueba precisión. El escenario no resuelve los otros 451 pares ni mide mercado no captado.'],
            ['H07', 'Importes insuficientes para deducir tarifas por programa',
             'Los siete programas identificados presentan cinco importes distintos y mediana de 2.500.000 COP. Hay 4.580 importes informados y 920 ausentes.',
             'Mantener los importes como contexto y contrastar tarifas antes de presupuestar ingresos.',
             'No acredita pagos, recaudo o tarifas oficiales. No se imputa por programa.'],
        ]
        findings = pd.DataFrame(findings, columns=['codigo','hallazgo','hecho_observado','accion_propuesta','limite'])
        self.save('hallazgos_administrativos', findings)
        actions = pd.DataFrame([
            ['H03','Revisar los 514 casos documentales de Matriculado y los 393 casos con estado documental discordante',
             'Admisiones y gestión documental','Casos revisados, reglas aclaradas y registros actualizados con evidencia','Propuesta, sin ejecutar'],
            ['H05','Revisar los 1.101 registros Sin asignar y definir cómo registrar una asignación efectiva',
             'Coordinación de admisiones','Registros con asignación validada y fecha de actualización','Propuesta, sin ejecutar'],
            ['H01 y H06','Seleccionar segmentos con volumen y capacidad disponible para una campaña piloto',
             'Mercadeo y coordinación académica','Solicitudes identificadas por campaña, seguimiento, costos y matrícula validada','Hipótesis para evaluar'],
            ['H02','Comparar canales con igual oferta y seguimiento antes de modificar presupuesto',
             'Mercadeo y admisiones','Resultados con denominadores comparables y gasto registrado','Propuesta, sin ejecutar'],
            ['H04','Contrastar puntajes y decisiones con las reglas institucionales',
             'Comité de admisiones','Casos explicados por criterio, programa y periodo','Propuesta, sin ejecutar'],
            ['H05 y H07','Mejorar identificación entre fuentes, registro de eventos y catálogo de tarifas',
             'Gestión de datos y responsables de sistemas','Correspondencias confirmadas, eventos con fecha y conceptos económicos definidos','Requiere registro futuro'],
        ],columns=['evidencia','decision_o_accion','responsable_propuesto','como_evaluar','estado'])
        self.save('acciones_propuestas',actions)
        interpretation = f'''# Análisis administrativo de la base integrada

## Alcance y criterio

Se describen 5.500 registros y 18 columnas de la entrega validada. La unidad es registro de solicitud de origen.
No se confirman personas globales únicas ni independencia de solicitudes entre fuentes.
Se conservan los controles temporales de referencia del 26 de octubre de 2026, sin reinterpretarlos como una actualización de datos.
Los porcentajes de estados no son tasas definitivas de conversión. Se muestran tamaños, cobertura y diferencias observadas.
No se aplican pruebas de significación o intervalos de confianza automáticamente. No se presume independencia entre registros.
Los grupos con menos de 30 registros se marcan como pequeños y se conservan. Ese criterio visual no garantiza fiabilidad.
La existencia de distribuciones similares o la imposibilidad de recomendar una segmentación firme son resultados válidos.

## Respuesta general

{top_programs} reúnen {fmt(top_amount)} registros, equivalentes al {fmt(top_amount/self.n*100,2)} % del conjunto.
Presencial representa el {fmt(modality.loc['Presencial','participacion_registros_pct'],2)} %, Virtual el {fmt(modality.loc['Virtual','participacion_registros_pct'],2)} % e Híbrida el {fmt(modality.loc['Híbrida','participacion_registros_pct'],2)} %.
Los canales muestran volúmenes cercanos. El estado Matriculado aparece en {fmt(total_mat)} registros, el {fmt(total_mat/self.n*100,2)} %.
La distribución de estados es una fotografía del registro disponible, no un recorrido individual o embudo de transiciones.

## Tres preguntas específicas

### 1. Demanda registrada y matrícula por programa

La tabla programa_periodo_academico.csv presenta cantidades, participaciones y proporción Matriculado por programa y periodo.
{period_text}
El periodo es semestre de ingreso, no semestre calculado desde la fecha de solicitud.
La respuesta actual describe registros. La pregunta original sobre solicitudes únicas y matrículas efectivas conserva su condición de validación.
Se mantienen 26 registros Sin información en programa, dentro del denominador general.

### 2. Diferencias entre canales

La proporción bruta observada va de {fmt(proportions.min(),2)} % a {fmt(proportions.max(),2)} %.
La amplitud es {fmt(raw_range,2)} puntos porcentuales en la base completa. En el soporte común es {fmt(support_range,2)} puntos antes de ponderar y {fmt(adjusted_range,2)} con pesos comunes por programa, modalidad y periodo.
El soporte común incluye {fmt(n_support)} de {fmt(self.n)} registros y {int(channels.estratos_comunes.iloc[0])} estratos con presencia de todos los canales.
La tabla canales_comparables.csv informa cobertura, proporciones brutas y estandarizadas y celdas pequeñas por canal.
No se afirma que las diferencias desaparezcan. La estandarización descriptiva no demuestra causalidad, eficacia o rentabilidad.
No se ordenarán inversiones solo por estas proporciones.

### 3. Documentación, asesor y estado

La proporción Matriculado es {fmt(docs.loc['Sí','proporcion_matriculado_pct'],2)} % con documentos Sí,
{fmt(docs.loc['No','proporcion_matriculado_pct'],2)} % con No y {fmt(docs.loc['Pendiente','proporcion_matriculado_pct'],2)} % con Pendiente.
Estas cifras no indican que completar documentos reduzca la matrícula. Pueden reflejar diferencias de actualización o reglas no documentadas.
Hay {fmt(len(contradiction))} registros Matriculado con documentación No o Pendiente y {fmt(len(pending_yes))} Documentación pendiente con documentos Sí.
Los cruces detallados por programa, modalidad y periodo permiten revisar composición, sin atribuir las diferencias al asesor.
Los intervalos por documentación se describen aparte con los 1.035 casos aptos. No se mide tiempo por etapa ni retiro posterior.
{interval_text}

## Hallazgos y decisiones propuestas

{self.table_markdown(findings)}

{self.table_markdown(actions)}

## Segmentos e incertidumbre entre fuentes

segmentos_completos.csv conserva todos los segmentos ciudad, programa y modalidad.
segmentos_volumen_priorizados_revision.csv muestra hasta 12 combinaciones con al menos 30 registros y programa identificado, ordenadas por volumen.
Son prioridades de revisión y pruebas de captación, no nichos de mercado confirmados ni mercados potenciales estimados.
segmentos_por_canal_periodo.csv mantiene los cruces finos, incluidos los pequeños, sin clasificarlos como ganadores.

El escenario hipotético cuenta una vez los 49 pares compatibles y contiene {fmt(self.scenario_size)} registros.
La entrega no cambia. La comparación por fuente conserva Oracle y permite valorar su composición.
En segmentos con al menos 30 registros, el cambio máximo en proporción Matriculado es {fmt(max_segment_diff,2)} puntos porcentuales.
No se deduce que los otros 451 pares sean independientes ni que el mercado completo esté representado.

## Qué cambió después de la limpieza y de incorporar fuentes

Se distinguen tres efectos en las tablas de antes y después. Primero se agrupan etiquetas sobre las mismas 5.040 filas originales.
Después se compara la fuente original alineada con la principal conciliada de 5.000 registros, enriquecida con CRM.
Finalmente se incorporan los 500 registros Oracle y se obtiene el conjunto de 5.500.
El aumento de 500 registros pertenece a incorporación de fuente, no a limpieza ni a crecimiento institucional.
No se sustituyen las cifras de la exploración inicial del informe por las del conjunto integrado.

## Siguiente uso

Estos resultados respaldan la sección administrativa y la construcción del dashboard con las mismas tablas y definiciones.
No se modifica Drive automáticamente. Las propuestas aún no son decisiones institucionales adoptadas.
El dashboard y su conexión en Power BI Desktop siguen pendientes.
'''
        (self.out/'reporte_analisis_administrativo.md').write_text(interpretation,encoding='utf8')
        narrative = f'''# Análisis descriptivo de la base integrada

La base integrada reúne 5.500 registros de solicitudes. El análisis permite reconocer dónde se concentra el interés registrado y qué aspectos del seguimiento requieren atención. Los resultados corresponden a registros disponibles y no deben interpretarse como aspirantes únicos o tasas definitivas de conversión.

{top_programs} reúnen {fmt(top_amount)} registros, equivalentes al {fmt(top_amount/self.n*100,2)} % del total. Presencial representa el {fmt(modality.loc['Presencial','participacion_registros_pct'],2)} %, Virtual el {fmt(modality.loc['Virtual','participacion_registros_pct'],2)} % e Híbrida el {fmt(modality.loc['Híbrida','participacion_registros_pct'],2)} %. Estas participaciones orientan la revisión de la oferta y la atención, sin demostrar por sí solas la demanda de todo el mercado.

[Insertar aquí el gráfico 01_programas_modalidades.png.]

Los canales presentan volúmenes cercanos. {best.canal_captacion} registra una proporción Matriculado de {fmt(best.proporcion_bruta_pct,2)} % y {worst.canal_captacion} de {fmt(worst.proporcion_bruta_pct,2)} %. La amplitud entre canales es {fmt(raw_range,2)} puntos porcentuales en la base completa. En el soporte comparable es {fmt(support_range,2)} puntos antes de ponderar y {fmt(adjusted_range,2)} puntos con pesos comunes por programa, modalidad y periodo. Esta comparación utiliza {fmt(n_support)} registros en grupos con presencia de todos los canales y contiene celdas pequeñas. Por ello, sus resultados justifican profundizar la comparación, pero no reasignar presupuesto únicamente por el porcentaje observado.

[Insertar aquí el gráfico 02_canales_comparables.png.]

El estado Matriculado reúne {fmt(total_mat)} registros, equivalentes al {fmt(total_mat/self.n*100,2)} %. Dentro de ellos, {fmt(len(contradiction))} tienen documentación registrada como No o Pendiente. Además, {fmt(len(pending_yes))} registros con estado Documentación pendiente señalan documentos completos. Se recomienda revisar las reglas y la actualización de ambas columnas antes de interpretar estas diferencias como incumplimientos. La base no contiene un historial que permita reconstruir el avance de cada aspirante.

[Insertar aquí el gráfico 03_documentacion_estados.png.]

El promedio del puntaje disponible es {fmt(scores.loc['Admitido','promedio'],2)} en Admitido y {fmt(scores.loc['No admitido','promedio'],2)} en No admitido. Esta diferencia requiere contrastarse con la distribución de puntajes y los criterios de admisión, sin asumir que el promedio explica las decisiones. Los importes se mantienen como contexto económico. Los siete programas presentan cinco valores y la misma mediana de 2.500.000 COP, con 920 importes ausentes, por lo que no se deducen tarifas ni ingresos recibidos.

{overlap_text} En los intervalos temporales aptos, las medianas por documentación son 33 días para Sí, 34 para No y 33 para Pendiente. Describen únicamente los casos con ambas fechas que cumplen los controles y no permiten atribuir una demora al estado documental.

Hay {fmt(advisors.loc['Sin asignar','registros'])} registros Sin asignar, aproximadamente el {fmt(advisors.loc['Sin asignar','participacion_registros_pct'],2)} %. En la fuente principal, {fmt(recurring)} de {fmt(known_codes)} códigos de aspirante aparecen en varias solicitudes. Estas condiciones justifican mejorar la asignación y mantener separados los conteos de solicitudes y códigos identificados, sin atribuir resultados a la gestión de un asesor o declarar duplicadas todas las recurrencias.

Para explorar oportunidades de captación se identificaron combinaciones de ciudad, programa y modalidad con mayor volumen. Estas concentraciones sirven para seleccionar campañas piloto y contrastar su respuesta. No permiten afirmar que exista un nicho desatendido. Los grupos pequeños se muestran con su cantidad y las correspondencias entre fuentes conservan su incertidumbre. El escenario hipotético de contar una vez los 49 pares compatibles cambia como máximo {fmt(max_segment_diff,2)} puntos la proporción Matriculado de los segmentos con al menos 30 registros.

La comparación con la etapa inicial separa el efecto de agrupar categorías y consolidar repeticiones del efecto de incorporar Oracle. La fuente principal pasó de 5.040 a 5.000 registros por conciliación. La incorporación de 500 registros Oracle produjo la base integrada de 5.500. Este aumento no representa crecimiento de la demanda institucional.

Las acciones propuestas son revisar las inconsistencias documentales, validar la asignación de solicitudes, contrastar los criterios de admisión y evaluar campañas piloto con oferta y seguimiento comparables. Su evaluación requiere registrar responsables, fechas, costos y resultados, y no se presenta como una decisión institucional ya adoptada.
'''
        (self.out/'seccion_informe_drive.md').write_text(narrative,encoding='utf8')
        guide = '''# Ubicación en el informe

Insertar seccion_informe_drive.md después del cierre de Limpieza y transformación y antes de Preguntas e hipótesis. No reemplazar el análisis inicial de 5.040 registros. El texto tiene tres marcadores para insertar las figuras principales.

| Archivo | Pregunta o función | Ubicación |
| :--- | :--- | :--- |
| 01_programas_modalidades.png | Dónde se concentra el interés registrado | Tras el párrafo de programas y modalidades |
| 02_canales_comparables.png | Qué cambia al comparar la composición de canales | Tras el párrafo de canales |
| 03_documentacion_estados.png | Qué se observa en los estados y documentos | Tras el párrafo de documentación |
| 04_puntajes_estados.png | Cómo se distribuyen los puntajes por estado | Apoyo o anexo junto a puntajes |
| 05_asesor_recurrencia.png | Asignación y diferencia entre registros y códigos | Apoyo o anexo |
| 06_ciudades_programas.png | Concentraciones territoriales para explorar | Apoyo al apartado de segmentos |
| 07_cobertura_mensual.png | Cobertura temporal que limita comparaciones | Anexo o sección temporal |

Las notas deben indicar registros de solicitud de origen, no personas únicas. La figura de canales debe acompañarse de la explicación de soporte común y celdas pequeñas, no rotularse como eficacia o conversión definitiva.

Si se incorporan solo las tres figuras principales, irían después de la figura 6 de faltantes y serían las figuras 7, 8 y 9. Las dos figuras del actual Anexo B pasarían a 10 y 11. Las imágenes adicionales son opcionales y cambian esa secuencia. Actualizar índices y páginas después de fijar el contenido en Drive. No se garantiza la paginación de un Word anterior.

El informe de apoyo completo contiene tablas para revisión. No es obligatorio pegar todas. Si se añade una tabla nueva antes del Anexo A, renumerar también la tabla de reglas que estaba como Tabla 6. Las cifras y las notas del informe y Power BI deben coincidir.

No se ha editado el documento de Drive ni construido el dashboard. La base Excel y PostgreSQL conservan su contenido. El siguiente paso es revisar esta redacción y construir las medidas y visuales de Power BI usando las tablas calculadas.
'''
        (self.out/'guia_insercion_y_figuras.md').write_text(guide,encoding='utf8')
        return findings

    def cerrar(self, notebook_path):
        import nbformat
        nb = nbformat.read(notebook_path,as_version=4)
        code = '\n'.join(c.source for c in nb.cells if c.cell_type=='code')
        support = self.tables['canales_comparables']
        weights = self.tables['pesos_estratos_comunes']
        original_comparison = self.tables['antes_despues_ambitos_separados']
        checks = {
            'excel_intacto':sha(self.source)==self.input_sha,
            'base_en_memoria_intacta':self.base.equals(self.original),
            '5500_registros_18_columnas':self.base.shape==(5500,18),
            'llave_unica_y_joins_sin_multiplicar':self.df.registro_id.is_unique and len(self.df)==5500,
            '1179_estados_matriculado':int(self.df.matriculado.sum())==1179,
            '5254_puntajes':int(self.df.puntaje_admision.notna().sum())==5254,
            '4580_importes':int(self.df.valor_matricula_cop.notna().sum())==4580,
            '1035_intervalos_aptos':int(self.df.intervalo_dias_apto_reglas_aplicadas.sum())==1035,
            '5320_solicitudes_con_fecha_apta':int(self.df.fecha_solicitud_apta_reglas_aplicadas.sum())==5320,
            'grupos_principales_reconcilian':all(int(self.tables[c].registros.sum())==5500 for c in [
                'programa','modalidad','canal_captacion','estado_proceso','ciudad_residencia',
                'periodo_academico','fuente_origen','documentos_completos','asesor']),
            'segmentos_reconcilian':int(self.tables['segmentos_completos'].registros.sum())==5500,
            'cruces_finos_reconcilian':int(self.tables['segmentos_por_canal_periodo'].registros.sum())==5500,
            'pesos_comunes_suman_uno':abs(weights.peso_comun.sum()-1)<1e-10,
            'soporte_comun_mismo_numero_estratos':support.estratos_comunes.nunique()==1,
            'proporciones_comparables_validas':bool(support.proporcion_estandarizada_descriptiva_pct.between(0,100).all()),
            'escenario_hipotetico_no_cambia_entrega':self.scenario_size==5451 and len(self.base)==5500,
            'antes_despues_reconcilian':all(
                int(g.registros.sum())==int(g.denominador.iloc[0])
                for _,g in original_comparison.groupby(['variable','etapa'])),
            'recurrencia_sin_sumar_personas':int(self.tables['recurrencia_codigos'].codigos.sum())==3424,
            'entradas_lectura_intactas':all(sha(path)==digest for path,digest in self.inputs.items()),
            'sin_inferencia_automatica':not self.rules['inferencia_automatica'],
        }
        checks = {name:bool(value) for name,value in checks.items()}
        assert all(checks.values()), checks
        self.save('controles',pd.DataFrame(list(checks.items()),columns=['control','correcto']))
        metadata = {'entrada':self.summary['id_ejecucion'],'sha256_excel':self.input_sha,
            'sha256_codigo_notebook':hashlib.sha256(code.encode()).hexdigest(),
            'sha256_modulo':sha(Path(__file__)), 'sha256_reglas':sha(self.rules_path),
            'entradas':{str(p.relative_to(self.root)):digest for p,digest in self.inputs.items()},
            'filas_maestras':5500,'columnas_maestras':18,'filas_eliminadas':0,'valores_imputados':0,
            'controles':checks,'figuras':self.figures,
            'archivo_powerbi_creado':False,'documento_drive_modificado':False,
            'archivos':{str(p.relative_to(self.out)):sha(p) for p in sorted(self.out.rglob('*'))
                        if p.is_file() and p.name!='metadatos_analisis.json'}}
        (self.out/'metadatos_analisis.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        return pd.DataFrame(list(checks.items()),columns=['Control','Correcto'])
