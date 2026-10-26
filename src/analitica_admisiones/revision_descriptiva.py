"""Resolución acotada de parciales y exploración descriptiva de la base de revisión."""
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
import csv
import hashlib
import itertools
import json
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from .cierre_limpieza import serial, json_literal, sha
from .tipado_limpieza import interpretar_cop, interpretar_decimal, interpretar_entero


def consolidar_parcial(filas, columnas_permitidas):
    """Complementa nulos sin aceptar conflicto de valores informados."""
    if len(filas) != 2 or list(filas[0]) != list(filas[1]):
        raise ValueError('Se requieren dos filas con el mismo esquema')
    result = dict(filas[0])
    changes = []
    for col in result:
        a, b = filas[0][col], filas[1][col]
        if a == b:
            continue
        if col not in columnas_permitidas or a is not None and b is not None:
            raise ValueError(f'Diferencia no autorizada o conflicto en {col}')
        result[col] = b if a is None else a
        if result[col] != a:
            changes.append((col, a, result[col]))
    return result, changes


def normalizar_ausencias_identificadores(fila, marcadores):
    result = dict(fila)
    changes = []
    for col in ['registro_id', 'aspirante_id']:
        value = result.get(col)
        if isinstance(value, str) and value.strip().casefold() in marcadores:
            result[col] = None
            changes.append((col, value))
    return result, changes


class RevisionDescriptiva:
    def __init__(self, root, code_sha):
        self.root = Path(root)
        self.input_summary = json.loads((self.root/'reports/limpieza/ultimo_cierre.json').read_text())
        self.rules_path = self.root/'config/limpieza/revision_descriptiva_v1.json'
        self.rules = json.loads(self.rules_path.read_text())
        self.source = self.root/self.input_summary['datos_salida']/'BaseUnificada_Revision.jsonl'
        self.input_sha = sha(self.source)
        assert self.input_sha == self.input_summary['archivos_datos'][self.source.name]
        self.rule_sha, self.module_sha, self.code_sha = sha(self.rules_path), sha(__file__), code_sha
        self.run = f"{self.rules['version']}_{self.input_sha[:10]}_{self.rule_sha[:8]}_{self.module_sha[:8]}_{code_sha[:8]}"
        self.audit = self.root/'reports/limpieza/ejecuciones'/self.run
        self.out = self.root/'data/processed/taller_2'/self.run
        self.fig = self.root/'reports/figuras/revision_descriptiva'/self.run
        for p in [self.audit,self.out,self.fig]: p.mkdir(parents=True,exist_ok=True)
        self.input_audit = self.root/self.input_summary['auditoria']
        self.destinations = list(csv.DictReader((self.input_audit/'L09_disposicion_filas.csv').open(encoding='utf-8-sig')))
        representatives = sorted([r for r in self.destinations if r['id_fila_entrada']==r['id_registro_salida']], key=lambda r:int(r['fila_salida_csv']))
        self.ids = [r['id_registro_salida'] for r in representatives]
        self.origin = {r['id_registro_salida']:r['fuente'] for r in representatives}
        received = [json.loads(line,parse_float=Decimal) for line in self.source.read_text().splitlines()]
        self.headers = list(received[0])
        self.before = {i:{c: self.restore(v,c) for c,v in row.items()} for i,row in zip(self.ids,received)}
        assert len(self.before)==5602 and len(self.headers)==18
        self.rows = {i:dict(row) for i,row in self.before.items()}
        self.mapping = {i:i for i in self.ids}
        self.changes = []
        self.absence_changes = []
        self.metrics = {}
        self.ref = date.fromisoformat(self.rules['fecha_referencia'])
        self.figures = []

    @staticmethod
    def restore(v,c):
        if v is None: return None
        if c.startswith('fecha_'): return v.date() if isinstance(v,datetime) else v if isinstance(v,date) else date.fromisoformat(v)
        if c=='valor_matricula_cop': return interpretar_cop(str(v))
        if c=='puntaje_admision': return interpretar_decimal(str(v))
        if c in ['duracion_semestres','periodo_academico']: return interpretar_entero(str(v))
        return v

    def write(self,name,rows,headers=None):
        rows = list(rows)
        with (self.audit/name).open('w',encoding='utf-8-sig',newline='') as handle:
            w=csv.DictWriter(handle,fieldnames=headers or (list(rows[0]) if rows else ['sin_casos']),lineterminator='\n')
            w.writeheader(); w.writerows(rows)

    def resolver_parciales(self):
        groups=[]
        for reg,allowed in self.rules['parciales'].items():
            ids=sorted(i for i,r in self.rows.items() if self.origin[i]=='Principal' and r['registro_id']==reg)
            if len(ids)!=2: raise ValueError(f'{reg} no tiene dos filas principales')
            representative=ids[0]
            combined,changes=consolidar_parcial([self.rows[i] for i in ids],allowed)
            for col,before,after in changes:
                witnesses=[i for i in ids if self.rows[i][col]==after]
                self.changes.append({'id_ejecucion':self.run,'paso':'L10','registro_id':reg,
                                     'id_representante':representative,'columna':col,'valor_anterior':serial(before),
                                     'tipo_anterior':'ausencia','valor_posterior':serial(after),
                                     'tipo_posterior':type(after).__name__,'fila_evidencia':', '.join(witnesses),
                                     'regla':'complementar ausencia con único valor informado; resto de atributos iguales'})
            self.rows[representative]=combined
            for i in ids:
                self.mapping[i]=representative
                groups.append({'registro_id':reg,'id_fila_previa':i,'id_registro_salida':representative,
                               'accion':'representante complementado' if i==representative else 'consolidado parcial',
                               'columnas_recuperadas':', '.join(allowed)})
                if i!=representative: del self.rows[i]
        self.write('L10_cambios_por_celda.csv',self.changes)
        self.write('L10_parciales_resueltos.csv',groups)
        self.ids_out=[i for i in self.ids if i in self.rows]
        for ident in self.ids_out:
            row, changes = normalizar_ausencias_identificadores(self.rows[ident], self.rules['marcadores_ausencia_identificadores'])
            self.rows[ident] = row
            for col, before in changes:
                self.absence_changes.append({'id_registro_salida': ident, 'columna': col,
                    'valor_original': before, 'tipo_original': 'texto', 'valor_posterior': '',
                    'tipo_posterior': 'null', 'motivo': 'no_informado' if before.strip()=='' else 'marcador_nan',
                    'accion': 'homologar ausencia; conservar solicitud y no inventar identificador'})
        self.write('L10_ausencias_identificadores.csv', self.absence_changes,
                   ['id_registro_salida','columna','valor_original','tipo_original','valor_posterior','tipo_posterior','motivo','accion'])
        self.main_ids=[i for i in self.ids_out if self.origin[i]=='Principal']
        self.main=[self.rows[i] for i in self.main_ids]
        self.all=[self.rows[i] for i in self.ids_out]
        self.metrics['L10']={'filas_entrada':len(self.before),'filas_salida':len(self.rows),
                             'filas_consolidadas':len(self.before)-len(self.rows),'celdas_recuperadas':len(self.changes),
                             'registros_principales':len(self.main),'registro_id_principal_distintos':len({r['registro_id'] for r in self.main})}
        self.metrics['L10']['ausencias_identificadores_homologadas'] = len(self.absence_changes)
        self.metrics['L10']['marcadores_nan_identificadores'] = sum(r['motivo']=='marcador_nan' for r in self.absence_changes)
        assert len(self.rows)==5600 and len(self.main)==5000
        assert len({r['registro_id'] for r in self.main})==5000
        assert len(self.changes)==5
        return self.metrics['L10']

    def explorar_categorias(self):
        frequencies=[]
        for scope,ids in [('Todas las fuentes',self.ids_out),('Principal',self.main_ids),
                          ('CRM',[i for i in self.ids_out if self.origin[i]=='CRM']),('Oracle',[i for i in self.ids_out if self.origin[i]=='Oracle'])]:
            for c in ['programa','modalidad','canal_captacion','estado_proceso','documentos_completos','ciudad_residencia','asesor','periodo_academico','facultad','nivel_formacion']:
                for value,count in Counter(self.rows[i][c] for i in ids).most_common():
                    frequencies.append({'cohorte':scope,'columna':c,'valor':serial(value),'registros':count,
                                        'denominador':len(ids),'porcentaje':round(100*count/len(ids),2)})
        self.write('frecuencias_por_cohorte.csv',frequencies)
        phases=Counter(self.rules['fases_analiticas'][r['estado_proceso']] for r in self.main)
        self.write('agrupaciones_estados.csv',[{'estado_original':s,'fase_presentacion':p,
                   'registros_principal':sum(r['estado_proceso']==s for r in self.main),
                   'regla':'agrupación auxiliar de presentación, sin equivalencias ni transiciones acreditadas'}
                   for s,p in self.rules['fases_analiticas'].items()])
        crossings=[]
        for a,b in [('programa','modalidad'),('canal_captacion','estado_proceso'),('estado_proceso','documentos_completos'),('ciudad_residencia','modalidad')]:
            counts=Counter((r[a],r[b]) for r in self.main)
            totals=Counter(r[a] for r in self.main)
            for (x,y),n in counts.items():
                crossings.append({'variable_fila':a,'valor_fila':serial(x),'variable_columna':b,'valor_columna':serial(y),
                                  'registros':n,'denominador_grupo':totals[x],'porcentaje_en_grupo':round(100*n/totals[x],2),
                                  'cohorte':'Principal, 5.000 códigos de solicitud distintos'})
        self.write('cruces_descriptivos.csv',crossings)
        self.crossings=crossings
        self.metrics['categorias']={'estados_principal':dict(Counter(r['estado_proceso'] for r in self.main)),
                                    'fases_presentacion':dict(phases),
                                    'documentacion_pendiente_con_documentos_si':sum(r['estado_proceso']=='Documentación pendiente' and r['documentos_completos']=='Sí' for r in self.main),
                                    'matriculados_documentos_no_o_pendiente':sum(r['estado_proceso']=='Matriculado' and r['documentos_completos']!='Sí' for r in self.main)}
        return pd.DataFrame([f for f in frequencies if f['cohorte']=='Principal' and f['columna']=='estado_proceso'])

    def explorar_importes(self):
        stats=[]
        for source in ['Principal','CRM','Oracle']:
            ids=[i for i in self.ids_out if self.origin[i]==source]
            for dimensions in [('modalidad',),('programa','modalidad'),('programa','modalidad','periodo_academico')]:
                groups=defaultdict(list)
                for i in ids: groups[tuple(self.rows[i][c] for c in dimensions)].append(self.rows[i]['valor_matricula_cop'])
                for group,values in groups.items():
                    nums=[v for v in values if v is not None]
                    record={'fuente':source,'agrupacion':', '.join(dimensions),
                            'programa':serial(group[dimensions.index('programa')]) if 'programa' in dimensions else '',
                            'modalidad':group[dimensions.index('modalidad')],
                            'periodo_academico':serial(group[dimensions.index('periodo_academico')]) if 'periodo_academico' in dimensions else '',
                            'registros':len(values),'informados':len(nums),'ausentes':len(values)-len(nums),
                            'valores_distintos':len(set(nums)),'minimo_COP':serial(min(nums)) if nums else '',
                            'maximo_COP':serial(max(nums)) if nums else '',
                            'promedio_COP':serial(sum(nums)/len(nums)) if nums else '',
                            'mediana_COP':serial(median(nums)) if nums else '',
                            'concepto':'base más derechos administrativos' if source=='CRM' else 'importe reportado, concepto sin homologar'}
                    stats.append(record)
        self.write('importes_por_programa_modalidad_periodo.csv',stats)
        comparisons=[]
        for prog in sorted({r['programa'] for r in self.main if r['programa']}):
            for period in sorted({r['periodo_academico'] for r in self.main}):
                groups={mod:[r['valor_matricula_cop'] for r in self.main if r['programa']==prog and r['periodo_academico']==period and r['modalidad']==mod and r['valor_matricula_cop'] is not None] for mod in ['Presencial','Virtual']}
                p,v=groups['Presencial'],groups['Virtual']
                if p and v:
                    comparisons.append({'programa':prog,'periodo_academico':period,
                                        'informados_presencial':len(p),'informados_virtual':len(v),
                                        'mediana_presencial_COP':serial(median(p)),'mediana_virtual_COP':serial(median(v)),
                                        'diferencia_mediana_virtual_menos_presencial_COP':serial(median(v)-median(p)),
                                        'media_presencial_COP':serial(sum(p)/len(p)), 'media_virtual_COP':serial(sum(v)/len(v)),
                                        'limitacion':'compara importes observados; no acredita tarifa, descuento o causalidad'})
        self.write('comparacion_virtual_presencial.csv',comparisons)
        strata=[r for r in stats if r['fuente']=='Principal' and r['agrupacion']=='programa, modalidad, periodo_academico' and r['programa']]
        self.money_stats=stats
        self.metrics['importes']={'grupos_programa_modalidad_periodo':len(strata),
                                 'grupos_con_cinco_importes':sum(r['valores_distintos']==5 for r in strata),
                                 'grupos_con_importe_unico':sum(r['valores_distintos']==1 for r in strata),
                                 'comparaciones_virtual_presencial':len(comparisons),
                                 'virtual_mediana_menor':sum(Decimal(r['diferencia_mediana_virtual_menos_presencial_COP'])<0 for r in comparisons),
                                 'virtual_mediana_igual':sum(Decimal(r['diferencia_mediana_virtual_menos_presencial_COP'])==0 for r in comparisons),
                                 'virtual_mediana_mayor':sum(Decimal(r['diferencia_mediana_virtual_menos_presencial_COP'])>0 for r in comparisons),
                                 'importes_principales_ausentes':sum(r['valor_matricula_cop'] is None for r in self.main)}
        return pd.DataFrame([s for s in stats if s['fuente']=='Principal' and s['agrupacion']=='modalidad'])

    def explorar_fechas_identificadores(self):
        prior_issues=list(csv.DictReader((self.input_audit/'L09_incidencias_pendientes.csv').open(encoding='utf-8-sig')))
        ambiguous=set()
        for r in prior_issues:
            if r['tipo']=='formato_dia_mes_ambiguo': ambiguous.add((self.mapping[r['id_registro_salida']],r['columna']))
        quality=[]
        groups=Counter(r['registro_id'] for r in self.all)
        for ident in self.ids_out:
            row=self.rows[ident]
            request_ambiguous=(ident,'fecha_solicitud') in ambiguous
            enrol_ambiguous=(ident,'fecha_matricula') in ambiguous
            enrol=row['fecha_matricula']
            request_future=row['fecha_solicitud']>self.ref
            enrol_future=enrol is not None and enrol>self.ref
            reverse=enrol is not None and enrol<row['fecha_solicitud']
            request_usable=not request_ambiguous and not request_future
            duration_usable=enrol is not None and request_usable and not enrol_ambiguous and not enrol_future and not reverse
            quality.append({'id_registro_salida':ident,'fuente':self.origin[ident],'registro_id':row['registro_id'],
                            'fase_analitica':self.rules['fases_analiticas'][row['estado_proceso']],
                            'programa_sin_identificar':row['programa'] is None,
                            'registro_id_compartido_entre_fuentes':groups[row['registro_id']]>1,
                            'aspirante_id_ausente_o_nan':row['aspirante_id'] in ['',None,'nan'],
                            'solicitud_formato_ambiguo':request_ambiguous,'matricula_formato_ambiguo':enrol_ambiguous,
                            'solicitud_posterior_referencia':request_future,'matricula_posterior_referencia':enrol_future,
                            'matricula_anterior_solicitud':reverse,
                            'solicitud_posterior_anio_periodo':row['fecha_solicitud'].year>row['periodo_academico']//10,
                            'matriculado_documentacion_no_completa':row['estado_proceso']=='Matriculado' and row['documentos_completos']!='Sí',
                            'fecha_solicitud_sin_alertas_revisadas':request_usable,
                            'intervalo_dias_sin_alertas_revisadas':duration_usable,
                            'dias_solicitud_matricula':(enrol-row['fecha_solicitud']).days if duration_usable else None})
        self.quality=quality
        self.quality_by_id={r['id_registro_salida']:r for r in quality}
        self.write('calidad_y_variables_auxiliares.csv',quality)
        date_summary=[]
        for source in ['Principal','CRM','Oracle']:
            ids=[i for i in self.ids_out if self.origin[i]==source]
            for col in ['fecha_solicitud','fecha_matricula']:
                dates=[self.rows[i][col] for i in ids if self.rows[i][col] is not None]
                date_summary.append({'fuente':source,'columna':col,'filas':len(ids),'informadas':len(dates),
                                     'ausentes':len(ids)-len(dates),'minimo':serial(min(dates)) if dates else '',
                                     'maximo':serial(max(dates)) if dates else '',
                                     'formatos_ambiguos':sum((i,col) in ambiguous for i in ids),
                                     'posteriores_referencia':sum(v>self.ref for v in dates),'referencia_revision':str(self.ref)})
        self.write('revision_fechas_por_fuente.csv',date_summary)
        intervals=[]
        for i in self.main_ids:
            q=self.quality_by_id[i]; r=self.rows[i]
            if r['fecha_matricula'] is not None:
                intervals.append({'id_registro_salida':i,'registro_id':r['registro_id'],
                                  'fecha_solicitud':serial(r['fecha_solicitud']),'fecha_matricula':serial(r['fecha_matricula']),
                                  'dias_observados':(r['fecha_matricula']-r['fecha_solicitud']).days,
                                  'incluir_resumen_intervalos':q['intervalo_dias_sin_alertas_revisadas'],
                                  'formato_solicitud_ambiguo':q['solicitud_formato_ambiguo'],
                                  'formato_matricula_ambiguo':q['matricula_formato_ambiguo'],
                                  'matricula_anterior_solicitud':q['matricula_anterior_solicitud'],
                                  'fecha_posterior_referencia':q['solicitud_posterior_referencia'] or q['matricula_posterior_referencia']})
        self.write('revision_intervalos_matricula.csv',intervals)
        monthly=defaultdict(lambda: {'todos':0,'sin_alertas_revisadas':0})
        for i in self.main_ids:
            month=self.rows[i]['fecha_solicitud'].strftime('%Y-%m')
            monthly[month]['todos']+=1
            monthly[month]['sin_alertas_revisadas']+=int(self.quality_by_id[i]['fecha_solicitud_sin_alertas_revisadas'])
        self.monthly=[{'mes':m,'solicitudes_fecha_interpretada':v['todos'],
                       'solicitudes_sin_alertas_revisadas':v['sin_alertas_revisadas'],
                       'con_alertas_de_formato_o_referencia':v['todos']-v['sin_alertas_revisadas']} for m,v in sorted(monthly.items())]
        self.write('solicitudes_mensuales.csv',self.monthly)
        known=[r['aspirante_id'] for r in self.main if r['aspirante_id'] not in ['',None,'nan']]
        counts=Counter(known)
        by_email=defaultdict(set)
        for r in self.main:
            if r['correo'] and r['aspirante_id'] not in ['',None,'nan']: by_email[r['correo']].add(r['aspirante_id'])
        candidates=[]
        for i in self.main_ids:
            row=self.rows[i]
            if row['aspirante_id'] not in ['',None,'nan']: continue
            options=sorted(by_email.get(row['correo'],set()))
            candidates.append({'id_registro_salida':i,'registro_id':row['registro_id'],'aspirante_id_original':row['aspirante_id'],
                               'correo':row['correo'],'cantidad_ids_en_otras_filas_mismo_correo':len(options),
                               'ids_candidatos':', '.join(options),'accion':'sin asignación automática; identidad por correo no validada'})
        self.write('aspirante_id_candidatos_revision.csv',candidates)
        score=[]
        for status in sorted({r['estado_proceso'] for r in self.main}):
            nums=[r['puntaje_admision'] for r in self.main if r['estado_proceso']==status and r['puntaje_admision'] is not None]
            score.append({'estado_proceso':status,'puntajes_informados':len(nums),'minimo':serial(min(nums)),
                          'maximo':serial(max(nums)),'promedio':serial(sum(nums)/len(nums)),'mediana':serial(median(nums))})
        self.write('puntajes_por_estado.csv',score)
        usable=[r['dias_observados'] for r in intervals if r['incluir_resumen_intervalos']]
        self.metrics['fechas']={'matriculados_principal':sum(r['estado_proceso']=='Matriculado' for r in self.main),
                               'fechas_matricula_principal':len(intervals),
                               'matricula_en_estado_distinto':sum(r['estado_proceso']!='Matriculado' and r['fecha_matricula'] is not None for r in self.main),
                               'matricula_ausente_en_matriculados':sum(r['estado_proceso']=='Matriculado' and r['fecha_matricula'] is None for r in self.main),
                               'solicitudes_principales_formato_ambiguo':sum(self.quality_by_id[i]['solicitud_formato_ambiguo'] for i in self.main_ids),
                               'matriculas_principales_anteriores_solicitud':sum(self.quality_by_id[i]['matricula_anterior_solicitud'] for i in self.main_ids),
                               'intervalos_sin_alertas_revisadas':len(usable),'intervalos_excluidos_del_resumen':len(intervals)-len(usable),
                               'mediana_dias_intervalos_sin_alertas':serial(median(usable)) if usable else '',
                               'fecha_maxima_solicitud_principal':serial(max(r['fecha_solicitud'] for r in self.main))}
        self.metrics['identificadores']={'solicitudes_principales':len(self.main),'registro_id_distintos':len({r['registro_id'] for r in self.main}),
                                        'aspirante_id_informados':len(known),'aspirante_id_distintos_informados':len(counts),
                                        'filas_aspirante_id_ausente':len(candidates),'ids_con_mas_de_una_solicitud':sum(n>1 for n in counts.values()),
                                        'ausentes_con_un_id_candidato_por_correo':sum(r['cantidad_ids_en_otras_filas_mismo_correo']==1 for r in candidates),
                                        'ids_recuperados_automaticamente':0}
        return pd.DataFrame(date_summary), pd.DataFrame([self.metrics['identificadores']])

    def graficar(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
        plt.rcParams.update({'figure.dpi':130,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
        frame=pd.DataFrame(self.main)
        def save(fig,name):
            fig.tight_layout()
            for ext in ['png','pdf']: fig.savefig(self.fig/f'{name}.{ext}',bbox_inches='tight')
            plt.close(fig)
            self.figures.append(name)
        counts=frame['estado_proceso'].value_counts().sort_values()
        fig,ax=plt.subplots(figsize=(9,4.5)); bars=ax.barh(counts.index,counts.values,color='#226C95')
        ax.bar_label(bars,labels=[f'{n:,} ({100*n/len(frame):.1f} %)'.replace(',','.') for n in counts],padding=4)
        ax.set_xlim(0,max(counts)*1.3); ax.set_xlabel('Solicitudes de fuente principal'); ax.set_title('Estado registrado de las 5.000 solicitudes principales')
        save(fig,'01_estados')
        programs=frame.assign(programa=frame['programa'].fillna('Sin programa informado'))
        matrix=pd.crosstab(programs['programa'],programs['modalidad'])
        matrix=matrix.loc[matrix.sum(axis=1).sort_values().index]
        fig,ax=plt.subplots(figsize=(11,5.5)); matrix.plot.barh(stacked=True,ax=ax,color=['#78B7C5','#226C95','#E5AF4A'])
        ax.set_xlabel('Solicitudes de fuente principal'); ax.set_ylabel(''); ax.set_title('Distribución por programa y modalidad'); ax.legend(title='Modalidad',loc='lower right')
        save(fig,'02_programas_modalidades')
        matrix=pd.crosstab(frame['canal_captacion'],frame['estado_proceso'])
        fig,ax=plt.subplots(figsize=(11,5)); matrix.plot.barh(stacked=True,ax=ax,cmap='tab20')
        ax.set_xlabel('Solicitudes de fuente principal'); ax.set_ylabel(''); ax.set_title('Canal de captación y estado registrado'); ax.legend(title='Estado',bbox_to_anchor=(1.02,1),loc='upper left')
        save(fig,'03_canales_estados')
        mods=['Presencial','Virtual','Híbrida']
        data=[[float(r['valor_matricula_cop']) for r in self.main if r['modalidad']==mod and r['valor_matricula_cop'] is not None] for mod in mods]
        fig,ax=plt.subplots(figsize=(8,4.6)); ax.boxplot(data,tick_labels=[f'{m}\nn = {len(v)}' for m,v in zip(mods,data)],showmeans=True)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1e6:.1f}'.replace('.',',')))
        ax.set_ylabel('Importe reportado, millones de COP'); ax.set_title('Importes observados por modalidad, fuente principal')
        ax.text(0,-.25,'Solo importes informados. No representa una tabla oficial de tarifas.',transform=ax.transAxes,fontsize=9)
        save(fig,'04_importes_modalidad')
        monthly=pd.DataFrame(self.monthly)
        fig,ax=plt.subplots(figsize=(11,4.8)); ax.plot(monthly['mes'],monthly['solicitudes_fecha_interpretada'],marker='o',label='Todas las fechas interpretadas')
        ax.plot(monthly['mes'],monthly['solicitudes_sin_alertas_revisadas'],marker='.',label='Sin alertas de formato o referencia')
        ax.tick_params(axis='x',rotation=60); ax.set_ylabel('Solicitudes de fuente principal'); ax.set_title('Solicitudes por mes con revisión de fechas'); ax.legend(fontsize=8)
        ax.text(0,-.4,'Septiembre de 2026 contiene datos hasta el día 12; no comparar como mes completo.',transform=ax.transAxes,fontsize=9)
        save(fig,'05_solicitudes_mensuales')
        data=[q['dias_solicitud_matricula'] for q in self.quality if q['fuente']=='Principal' and q['intervalo_dias_sin_alertas_revisadas']]
        fig,ax=plt.subplots(figsize=(8,4.7)); ax.hist(data,bins=20,color='#226C95',edgecolor='white')
        ax.set_xlabel('Días entre solicitud y matrícula'); ax.set_ylabel('Solicitudes incluidas'); ax.set_title(f'Intervalos sin las alertas revisadas, n = {len(data)}')
        ax.text(0,-.22,'Subconjunto con dos fechas, sin ambigüedad señalada, fechas futuras u orden inverso.',transform=ax.transAxes,fontsize=8)
        save(fig,'06_intervalos_matricula')
        matrix=pd.crosstab(frame['ciudad_residencia'],frame['modalidad'])
        fig,ax=plt.subplots(figsize=(10,4.5)); matrix.plot.barh(stacked=True,ax=ax,color=['#78B7C5','#226C95','#E5AF4A'])
        ax.set_xlabel('Solicitudes de fuente principal'); ax.set_ylabel(''); ax.set_title('Demanda registrada por ciudad y modalidad'); ax.legend(title='Modalidad',bbox_to_anchor=(1.02,1),loc='upper left')
        save(fig,'07_ciudades_modalidades')
        return [self.fig/f'{name}.png' for name in self.figures]

    def exportar(self,preserve_empty_text):
        csv_path=self.out/'BaseUnificada_Revision.csv'
        json_path=self.out/'BaseUnificada_Revision.jsonl'
        excel_path=self.out/'BaseUnificada_Revision.xlsx'
        principal_path=self.out/'Principal_Analisis.csv'
        with csv_path.open('w',encoding='utf-8-sig',newline='') as handle:
            w=csv.writer(handle,lineterminator='\n'); w.writerow(self.headers)
            w.writerows([[serial(row[c]) for c in self.headers] for row in self.all])
        with principal_path.open('w',encoding='utf-8-sig',newline='') as handle:
            w=csv.writer(handle,lineterminator='\n'); w.writerow(self.headers)
            w.writerows([[serial(row[c]) for c in self.headers] for row in self.main])
        with json_path.open('w',encoding='utf8') as handle:
            for row in self.all: handle.write('{'+', '.join(json.dumps(c)+': '+json_literal(row[c]) for c in self.headers)+'}\n')
        book=Workbook(); sheet=book.active; sheet.title='BaseUnificada_Revision'
        sheet.append(self.headers)
        for row in self.all: sheet.append([row[c] for c in self.headers])
        for j,c in enumerate(self.headers,1):
            fmt='yyyy-mm-dd' if c.startswith('fecha_') else '"COP" #,##0.00' if c=='valor_matricula_cop' else '0.00' if c=='puntaje_admision' else '0' if c in ['periodo_academico','duracion_semestres'] else '@'
            for i in range(2,len(self.all)+2): sheet.cell(i,j).number_format=fmt
            sheet.column_dimensions[get_column_letter(j)].width=42 if c=='programa' else 24
        table=Table(displayName='BaseUnificada_Revision',ref=f'A1:R{len(self.all)+1}')
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium9',showRowStripes=True)
        sheet.add_table(table); sheet.freeze_panes='A2'
        principal_sheet=book.create_sheet('Principal_Analisis')
        principal_sheet.append(self.headers)
        for row in self.main: principal_sheet.append([row[c] for c in self.headers])
        for j,c in enumerate(self.headers,1):
            principal_sheet.column_dimensions[get_column_letter(j)].width=sheet.column_dimensions[get_column_letter(j)].width
            for i in range(2,len(self.main)+2): principal_sheet.cell(i,j).number_format=sheet.cell(2,j).number_format
        principal_table=Table(displayName='Principal_Analisis',ref=f'A1:R{len(self.main)+1}')
        principal_table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium9',showRowStripes=True)
        principal_sheet.add_table(principal_table); principal_sheet.freeze_panes='A2'
        scope=book.create_sheet('Alcance')
        for values in [['Aspecto','Descripción'],['Registros totales',5600],['Principal',5000],['CRM',100],['Oracle',500],
                       ['Parciales','REG003600 y REG004804 complementados y consolidados'],
                       ['Estados','Nuevo permanece distinto de Admitido; agrupaciones solo auxiliares'],
                       ['Importes','No se imputan; CRM conserva base más derechos, separado en el análisis'],
                       ['Solicitudes únicas globales','No confirmadas; CRM se solapa con principal y Oracle tiene candidatos'],
                       ['Identificadores','Se conservan; código de solicitud distinto de aspirante'],
                       ['Controles',str(self.audit.relative_to(self.root))]]: scope.append(values)
        book.save(excel_path); book.close()
        preserve_empty_text(excel_path,[tuple(r[c] for c in self.headers) for r in self.all])
        preserve_empty_text(excel_path,[tuple(r[c] for c in self.headers) for r in self.main],worksheet_index=2)
        positions={i:n for n,i in enumerate(self.ids_out,2)}
        out_sha=sha(csv_path)
        destinations=[]
        for r in self.destinations:
            previous=r['id_registro_salida']; target=self.mapping[previous]
            destinations.append({'id_fila_entrada':r['id_fila_entrada'],'id_representante_L09':previous,
                                 'id_registro_salida':target,'fila_salida_csv':positions[target],
                                 'fuente':r['fuente'],'estado_destino':'consolidada_parcial' if previous!=target else r['estado_destino'],
                                 'sha256_csv_salida':out_sha})
        self.write('disposicion_5640_entradas.csv',destinations)
        prior=[]
        for item in csv.DictReader((self.input_audit/'L09_incidencias_pendientes.csv').open(encoding='utf-8-sig')):
            row=dict(item); target=self.mapping[row['id_registro_salida']]; row['id_registro_salida']=target
            resolved=(row['tipo']=='programa_sin_identificar' and self.rows[target]['programa'] is not None) or (row['tipo']=='identificador_compartido_con_diferencias' and row['registro_id'] in self.rules['parciales'])
            row['estado']='resuelta_por_complementacion_L10' if resolved else 'pendiente'
            prior.append(row)
        self.write('incidencias_heredadas_actualizadas.csv',prior)
        # Lectura completa y conservación fuera de las cinco celdas autorizadas.
        reread=[{c:self.restore(v,c) for c,v in json.loads(l,parse_float=Decimal).items()} for l in json_path.read_text().splitlines()]
        checkbook=load_workbook(excel_path,read_only=True,data_only=True)
        vals=list(checkbook['BaseUnificada_Revision'].values)
        principal_values=list(checkbook['Principal_Analisis'].values); checkbook.close()
        excel_rows=[{c:self.restore(v,c) for c,v in zip(self.headers,row)} for row in vals[1:]]
        principal_excel_rows=[{c:self.restore(v,c) for c,v in zip(self.headers,row)} for row in principal_values[1:]]
        with csv_path.open(encoding='utf-8-sig',newline='') as handle: csv_rows=list(csv.reader(handle))
        allowed={(r['id_representante'],r['columna']) for r in self.changes}
        allowed.update((r['id_registro_salida'],r['columna']) for r in self.absence_changes)
        changes_ok=all(self.rows[i][c]==self.before[i][c] or (i,c) in allowed for i in self.ids_out for c in self.headers)
        checked=[('5602 menos dos consolidados igual 5600',len(self.all)==5600),
                 ('18 columnas originales',all(list(r)==self.headers for r in self.all) and len(self.headers)==18),
                 ('Cinco celdas recuperadas y solo ausencias de ID homologadas',len(self.changes)==5 and changes_ok),
                 ('Estados conservados',all(self.rows[i]['estado_proceso']==self.before[i]['estado_proceso'] for i in self.ids_out)),
                 ('Importes no imputados',all(self.rows[i]['valor_matricula_cop']==self.before[i]['valor_matricula_cop'] for i in self.ids_out if self.before[i]['registro_id']!='REG003600')),
                 ('Fechas e identificadores informados conservados',all(self.rows[i][c]==self.before[i][c] for i in self.ids_out for c in ['fecha_solicitud','fecha_matricula','registro_id','aspirante_id'] if (i,c) not in {(r['id_registro_salida'],r['columna']) for r in self.absence_changes})),
                 ('Sin nan o textos vacíos en identificadores',all(r[c] is None or isinstance(r[c],str) and r[c].strip().casefold() not in ['', 'nan'] for r in self.all for c in ['registro_id','aspirante_id'])),
                 ('5000 códigos principales únicos',len(self.main)==len({r['registro_id'] for r in self.main})==5000),
                 ('5640 entradas con destino',len(destinations)==len({r['id_fila_entrada'] for r in destinations})==5640),
                 ('Destinos existentes',set(r['id_registro_salida'] for r in destinations)==set(self.ids_out)),
                 ('Lectura íntegra JSONL',reread==self.all),('Lectura íntegra Excel',excel_rows==self.all),
                 ('Lectura íntegra CSV',csv_rows==[self.headers,*[[serial(r[c]) for c in self.headers] for r in self.all]]),
                 ('Lectura íntegra de cohorte principal Excel',principal_excel_rows==self.main),
                 ('Entrada L09 intacta',sha(self.source)==self.input_sha)]
        self.write('controles.csv',[{'control':k,'correcto':bool(v)} for k,v in checked])
        assert all(v for k,v in checked),[k for k,v in checked if not v]
        self.metrics['controles_correctos']=len(checked)
        self.metrics['incidencias_heredadas_resueltas']=sum(r['estado']=='resuelta_por_complementacion_L10' for r in prior)
        summary={'id_ejecucion':self.run,'etapa':'L10 resolución parcial y exploración descriptiva',
                 'ejecutado_en':datetime.now(ZoneInfo('America/Bogota')).isoformat(),'entrada_L09':self.input_summary['id_ejecucion'],
                 'sha256_entrada_jsonl':self.input_sha,'sha256_codigo_notebook':self.code_sha,
                 'sha256_modulo':self.module_sha,'sha256_reglas':self.rule_sha,
                 'filas_entrada':5602,'filas_salida':5600,'columnas':18,'solicitudes_principal':5000,
                 'metricas':self.metrics,'datos_salida':str(self.out.relative_to(self.root)),
                 'auditoria':str(self.audit.relative_to(self.root)),'figuras':str(self.fig.relative_to(self.root)),
                 'archivos_datos':{p.name:sha(p) for p in [csv_path,excel_path,json_path,principal_path]},
                 'alcance':'Cohorte Principal de 5000 códigos de solicitud para exploración. Consolidado de 5600 registros aún con solapamiento entre fuentes; no suma de solicitudes únicas.'}
        (self.audit/'resumen_ejecucion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (self.root/'reports/limpieza/ultima_revision_descriptiva.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        self.report(summary)
        return summary

    def report(self,summary):
        n=lambda v:f'{v:,}'.replace(',','.')
        metrics=self.metrics; counts=metrics['categorias']['estados_principal']
        rows=['# Revisión descriptiva y avance de limpieza','', 'Fecha: 26 de octubre de 2026.','',
              '**Resultado:** los dos registros parciales se complementaron y consolidaron. El consolidado conserva 5.600 registros y 18 columnas. La fuente principal contiene 5.000 códigos de solicitud distintos; CRM aporta 100 registros solapados y Oracle 500 registros con correspondencias candidatas. Las comparaciones administrativas siguientes utilizan la fuente principal, sin sumar CRM y Oracle como solicitudes adicionales.',
              '', '## 1. Qué se corrigió','',
              '| Solicitud | Tratamiento |', '| :--- | :--- |',
              '| REG003600 | Se recuperó 1.800.000 COP de su otra fila y se consolidaron las dos entradas. |',
              '| REG004804 | Se recuperaron Ingeniería de Sistemas, Ingeniería, 8 semestres y Pregrado desde su otra fila, y se consolidaron ambas entradas. |',
              '', 'Se comprobó la igualdad de todos los demás atributos, incluido el código de solicitud, antes de complementar las ausencias. Se recuperaron cinco celdas y se consolidaron dos filas; no se imputaron promedios ni se eligió entre valores informados contradictorios. La auditoría mantiene el destino de las 5.640 entradas originales.',
              '', f"Se homologaron como ausencias reales {metrics['L10']['ausencias_identificadores_homologadas']} identificadores no informados, incluidos {metrics['L10']['marcadores_nan_identificadores']} textos nan. Son null en JSONL, None en Python y celdas vacías en Excel. Se conserva el marcador original y su motivo en L10_ausencias_identificadores.csv. No se eliminó ninguna solicitud por esta normalización y se conservaron los códigos informados.",
              '', '## 2. Estados: Nuevo no se reclasifica como Admitido','',
              'Las fuentes utilizan ambas etiquetas y no contienen un diccionario que las declare equivalentes. La presencia de puntaje o documentos completos tampoco demuestra admisión. Se conservan los siete estados y se ofrece una agrupación auxiliar para presentar el proceso, sin afirmar transiciones.',
              '', '| Estado registrado | Solicitudes principales | Porcentaje | Fase auxiliar de presentación |', '| :--- | ---: | ---: | :--- |']
        for status,count in sorted(counts.items(),key=lambda x:-x[1]): rows.append(f"| {status} | {n(count)} | {count/50:.2f} % | {self.rules['fases_analiticas'][status]} |")
        rows += ['',f"Hay {n(metrics['categorias']['documentacion_pendiente_con_documentos_si'])} solicitudes con estado Documentación pendiente y documentos Sí, y {n(metrics['categorias']['matriculados_documentos_no_o_pendiente'])} con estado Matriculado y documentos No o Pendiente. Son discrepancias para seguimiento, no una regla para sustituir automáticamente el estado. También podrían reflejar estados o documentos actualizados en momentos distintos; esa explicación es una hipótesis.",
                 '', '## 3. Importes por programa, modalidad y periodo','',
                 f"Las {metrics['importes']['grupos_programa_modalidad_periodo']} combinaciones de programa identificado, modalidad y periodo de la fuente principal contienen cinco importes distintos. Ninguna tiene una tarifa única deducible. No se puede completar una matrícula solo porque otra solicitud tenga el mismo programa y modalidad.",
                 '', '| Modalidad | Importes informados | Ausentes | Promedio COP | Mediana COP |', '| :--- | ---: | ---: | ---: | ---: |']
        money=lambda s:format(Decimal(s),',.2f').translate(str.maketrans(',.','.,'))
        for r in self.money_stats:
            if r['fuente']=='Principal' and r['agrupacion']=='modalidad':
                rows.append(f"| {r['modalidad']} | {n(r['informados'])} | {n(r['ausentes'])} | {money(r['promedio_COP'])} | {money(r['mediana_COP'])} |")
        m=metrics['importes']
        rows += ['',f"En las {m['comparaciones_virtual_presencial']} comparaciones dentro de un mismo programa y periodo, la mediana virtual es menor en {m['virtual_mediana_menor']}, igual en {m['virtual_mediana_igual']} y mayor en {m['virtual_mediana_mayor']}. Esto describe los importes disponibles y no acredita que una modalidad tenga una tarifa más baja. No se aplicó imputación por modalidad.",
                 '', 'CRM conserva un concepto distinto: base más derechos administrativos. Sus importes se describen por separado. La comprobación anterior encontró 87 matrículas principales iguales a la base CRM y 13 principales ausentes recuperables desde la base CRM; esa conciliación económica es una regla pendiente de aplicar y no forma parte de las cinco celdas recuperadas aquí.',
                 '', '## 4. Las fechas de matrícula sí aportan','']
        f=metrics['fechas']
        rows += [f"En la fuente principal, los {n(f['matriculados_principal'])} registros con estado Matriculado tienen fecha de matrícula y no se observan fechas de matrícula en otros estados. Por ello la columna aporta información para estudiar cuándo se registra la matrícula y el intervalo frente a la solicitud.",
                 '',f"Se detectan {n(f['solicitudes_principales_formato_ambiguo'])} fechas de solicitud con formato ambiguo señalado y {n(f['matriculas_principales_anteriores_solicitud'])} matrículas anteriores a la solicitud. El resumen de intervalos utiliza {n(f['intervalos_sin_alertas_revisadas'])} casos sin las alertas revisadas y deja fuera del cálculo {n(f['intervalos_excluidos_del_resumen'])}; estos últimos permanecen en la base. La mediana del subconjunto es {f['mediana_dias_intervalos_sin_alertas']} días. No representa un tiempo promedio institucional validado.",
                 '',f"La fuente principal llega hasta {f['fecha_maxima_solicitud_principal']}. Septiembre de 2026 termina en el día 12: una caída de su conteo no demuestra una caída mensual de demanda. Oracle tiene otra cobertura temporal y no se mezcla en esta serie. Las fechas no se intercambiaron ni se ajustaron a un periodo supuesto.",
                 '', '## 5. Aporte de aspirante_id','']
        i=metrics['identificadores']
        rows += [f"Los {n(i['registro_id_distintos'])} códigos de solicitud principales contienen {n(i['aspirante_id_distintos_informados'])} códigos de aspirante informados distintos. Hay {n(i['filas_aspirante_id_ausente'])} solicitudes sin código de aspirante y {n(i['ids_con_mas_de_una_solicitud'])} códigos presentes en varias solicitudes. Solicitud y aspirante son unidades diferentes.",
                 '',f"Entre los identificadores ausentes, {n(i['ausentes_con_un_id_candidato_por_correo'])} tienen un único código candidato en otras filas con el mismo correo. Esa coincidencia se exporta para revisión y no se aplica como prueba de identidad. Se conserva aspirante_id en el respaldo y se omite de las agrupaciones de mercado; borrarlo impediría revisar recurrencia y procedencia.",
                 '', '## 6. Lectura administrativa y oportunidades de análisis','',
                 'Los cruces de programa, modalidad y ciudad permiten describir dónde se concentra la demanda registrada. Los cruces de canal y estado permiten ubicar solicitudes en gestión inicial o con matrícula registrada. Sus cantidades y proporciones se exportan con el denominador de cada grupo.',
                 '', 'Una concentración de solicitudes identifica interés observado. Para llamarla oportunidad comercial conviene considerar también costos, capacidad y campañas, que no están disponibles. La proporción de registros Matriculado por canal no mide por sí sola la eficacia causal ni una conversión comercial definitiva. Los datos disponibles tampoco permiten reconstruir cuánto duró cada etapa del proceso, porque no hay fechas de transición de estado.',
                 '', 'Preguntas útiles: ¿qué combinaciones de programa, modalidad y ciudad concentran solicitudes? ¿Qué canales concentran gestión inicial y matrícula registrada? ¿Dónde hay estados y documentación discordantes? ¿Cómo cambian las fechas de matrícula dentro del subconjunto sin alertas? ¿Qué solicitudes repiten código de aspirante?',
                 '', '## 7. Qué queda pendiente para la versión definitiva','',
                 '| Tema | Siguiente tratamiento |', '| :--- | :--- |',
                 '| CRM | Aprobar y aplicar la conciliación de 100 correspondencias y el concepto económico antes de recuperar los 13 importes. |',
                 '| Oracle | Acordar la regla de identidad para integrar sus candidatos; conservarlo separado del volumen principal mientras tanto. |',
                 '| Fechas y periodos | Conservar valores, indicar casos no elegibles para cada cálculo y resolver solo con evidencia interna suficiente. |',
                 '| Estados y catálogo | Mantener denominaciones actuales; usar agrupaciones auxiliares explícitas. No convertir Nuevo en Admitido. |',
                 '| Vacíos | Mantener ausencias no recuperables. No completar importes por programa o modalidad sin una regla sustentada. |',
                 '',f"Pasaron {metrics['controles_correctos']} controles, incluida la lectura completa de CSV, Excel y JSONL. Los estados, códigos informados, fechas e importes ajenos a REG003600 conservan sus valores; los identificadores no informados se representan como null. La salida permite continuar análisis descriptivo por fuente; la identidad global y los conceptos económicos todavía requieren reglas de cierre.",
                 '', '## Gráficos','']
        titles=['Estados registrados','Programas y modalidades','Canales y estados','Importes por modalidad','Solicitudes por mes','Intervalos de matrícula revisados','Ciudades y modalidades']
        for title,name in zip(titles,self.figures): rows += [f'### {title}','',f'![{title}](../figuras/revision_descriptiva/{self.run}/{name}.png)','']
        rows += ['## Archivos de respaldo','',f"Datos: `{summary['datos_salida']}`.",'',f"Auditoría y tablas descriptivas: `{summary['auditoria']}`.",'',
                 'El resumen vigente está en reports/limpieza/ultima_revision_descriptiva.json. Los controles auxiliares no aumentan las 18 columnas de negocio. La base de cierre L09 conserva su condición de punto de control histórico; esta revisión L10 es su actualización para los dos parciales. No se modificaron las tablas Docker.']
        (self.root/'reports/limpieza/revision_descriptiva_y_parciales.md').write_text('\n'.join(rows)+'\n',encoding='utf8')
