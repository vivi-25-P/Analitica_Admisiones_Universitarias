"""Conciliación final y entrega formal autocontenida de BaseUnificada."""
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo
import csv
import hashlib
import json
import shutil
import textwrap
import zipfile

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from .cierre_limpieza import serial, json_literal, sha
from .revision_descriptiva import RevisionDescriptiva
from .identidad_estados import clasificar_aspirante
from .tipado_limpieza import interpretar_cop


def conciliar_importe(principal, base_crm, derechos_crm, total_crm):
    if base_crm is None or derechos_crm is None or total_crm != base_crm + derechos_crm:
        raise ValueError('Conceptos CRM ausentes o total inconsistente')
    if principal is not None and principal != base_crm:
        raise ValueError('Importe principal informado diferente de matrícula base CRM')
    return (base_crm, 'recuperado desde matrícula base CRM') if principal is None else (principal, 'principal conservado, coincide con base CRM')


def en_ventana_orientativa(fecha, periodo):
    year, term = divmod(periodo, 10)
    if term == 1:
        return date(year-1,10,1) <= fecha <= date(year,1,31)
    if term == 2:
        return date(year,5,1) <= fecha <= date(year,7,31)
    raise ValueError('Periodo sin semestre reconocido')


def indice_similitud_entre_fuentes(candidatos):
    relaciones=defaultdict(set)
    for registro,coincidencias in candidatos.items():
        for otro in coincidencias:
            relaciones[registro].add(otro)
            relaciones[otro].add(registro)
    return dict(relaciones)


class EntregaBaseUnificada:
    def __init__(self, root, code_sha):
        self.root=Path(root)
        self.parent=json.loads((self.root/'reports/limpieza/ultima_identidad_estados.json').read_text())
        self.rules_path=self.root/'config/limpieza/entrega_v1.json'
        self.rules=json.loads(self.rules_path.read_text())
        self.source=self.root/self.parent['datos_salida']/'BaseUnificada_Revision.jsonl'
        self.input_sha=sha(self.source)
        assert self.input_sha==self.parent['archivos_datos'][self.source.name]
        self.code_sha=code_sha;self.rule_sha=sha(self.rules_path);self.module_sha=sha(__file__)
        self.run=f"{self.rules['version']}_{self.input_sha[:10]}_{self.rule_sha[:8]}_{self.module_sha[:8]}_{code_sha[:8]}"
        self.audit=self.root/'reports/limpieza/ejecuciones'/self.run
        self.out=self.root/'data/processed/taller_2'/self.run
        self.fig=self.root/'reports/figuras/entrega'/self.run
        for p in [self.audit,self.out,self.fig]:p.mkdir(parents=True,exist_ok=True)
        self.parent_audit=self.root/self.parent['auditoria']
        self.destinations=self.read(self.parent_audit/'disposicion_5640_entradas.csv')
        positions={int(r['fila_salida_csv']):r for r in self.destinations}
        records=[json.loads(line,parse_float=Decimal) for line in self.source.read_text().splitlines()]
        self.headers=list(records[0])
        assert len(records)==5600 and len(self.headers)==18
        self.ids=[positions[i]['id_registro_salida'] for i in range(2,5602)]
        self.origin={r['id_registro_salida']:r['fuente'] for r in self.destinations}
        self.before={i:{c:RevisionDescriptiva.restore(v,c) for c,v in r.items()} for i,r in zip(self.ids,records)}
        self.rows={i:dict(r) for i,r in self.before.items()}
        self.mapping={i:i for i in self.ids}
        self.source_sets={i:{self.origin[i]} for i in self.ids}
        self.reference=date.fromisoformat(self.rules['fecha_referencia'])
        self.metrics={}
        self.economics=[];self.changes=[];self.crm_pairs=[]
        self.figures=[]
        original_changes=self.read(self.parent_audit/'cambios_estados_por_fila.csv')
        self.original_states={r['id_registro_salida']:r['valor_original'] for r in original_changes}

    @staticmethod
    def read(path):
        with Path(path).open(encoding='utf-8-sig',newline='') as handle:return list(csv.DictReader(handle))

    def write(self,name,rows,headers=None,folder=None):
        rows=list(rows)
        with ((folder or self.audit)/name).open('w',encoding='utf-8-sig',newline='') as handle:
            w=csv.DictWriter(handle,fieldnames=headers or (list(rows[0]) if rows else ['sin_casos']),lineterminator='\n')
            w.writeheader();w.writerows(rows)

    def conciliar_crm(self):
        raw_path=self.root/'data/raw/taller_2/Caso2 CRM Admisiones.csv'
        raw=self.read(raw_path)
        self.raw_crm_sha=sha(raw_path)
        raw_index={r['registro_aspirante_crm'].split('|')[0].strip():r for r in raw}
        principal={r['registro_id']:i for i,r in self.before.items() if self.origin[i]=='Principal'}
        assert len(principal)==5000 and len(raw_index)==100
        core=[c for c in self.headers[:15] if c not in {'registro_id','aspirante_id','valor_matricula_cop'}]
        for ident,row in self.before.items():
            if self.origin[ident]!='CRM':continue
            target=principal.get(row['registro_id'])
            if target is None:raise ValueError('CRM sin correspondencia principal')
            current=self.rows[target]
            if not all(row[c]==current[c] for c in core):raise ValueError('Atributos CRM incompatibles')
            if row['aspirante_id'] and current['aspirante_id'] and row['aspirante_id']!=current['aspirante_id']:
                raise ValueError('Conflicto de aspirante CRM')
            original=raw_index[row['registro_id']]
            base=interpretar_cop(original['matricula_base_cop'])
            rights=interpretar_cop(original['derechos_administrativos_cop'])
            total=row['valor_matricula_cop']
            previous=current['valor_matricula_cop']
            value,action=conciliar_importe(previous,base,rights,total)
            if previous is None:
                current['valor_matricula_cop']=value
                self.changes.append({'id_fila_salida':target,'registro_id':row['registro_id'],'columna':'valor_matricula_cop',
                                     'valor_anterior':'','tipo_anterior':'null','valor_posterior':serial(value),
                                     'regla':'recuperación desde matrícula base CRM para la misma solicitud',
                                     'id_fila_crm':ident,'archivo_evidencia':'Caso2 CRM Admisiones.csv'})
            self.economics.append({'registro_id':row['registro_id'],'importe_principal_anterior_COP':previous,
                                   'matricula_base_CRM_COP':base,'derechos_administrativos_CRM_COP':rights,
                                   'total_reportado_CRM_COP':total,'importe_final_COP':value,'tratamiento':action})
            self.crm_pairs.append({'id_fila_crm':ident,'id_fila_principal':target,'registro_id':row['registro_id'],
                                   'atributos_comparados':len(core),'coinciden_atributos':True,
                                   'identificador_aspirante_compatible':True,'accion':'incorporar información, conservar representante principal'})
            self.mapping[ident]=target
            self.source_sets[target].add('CRM')
            del self.rows[ident]
        self.ids_out=[i for i in self.ids if i in self.rows]
        self.all=[self.rows[i] for i in self.ids_out]
        self.principal=[r for i,r in zip(self.ids_out,self.all) if self.origin[i]=='Principal']
        self.oracle=[r for i,r in zip(self.ids_out,self.all) if self.origin[i]=='Oracle']
        self.write('conciliacion_crm.csv',self.crm_pairs)
        self.write('cambios_importes_por_celda.csv',self.changes)
        self.write('control_economico_crm.csv',self.economics)
        self.metrics['crm']={'registros_integrados':len(self.crm_pairs),'importes_principales_conservados':len(self.crm_pairs)-len(self.changes),
                             'importes_recuperados':len(self.changes),'filas_antes':5600,'filas_despues':len(self.all),
                             'importes_ausentes_principal':sum(r['valor_matricula_cop'] is None for r in self.principal)}
        assert len(self.all)==5500 and len(self.crm_pairs)==100 and len(self.changes)==13
        return pd.DataFrame([self.metrics['crm']])

    def revisar_oracle(self):
        # La sonda se aplica al punto previo a enriquecer importes para no perder
        # candidatos solo porque CRM recuperó un valor que Oracle mantiene ausente.
        columns13=[c for c in self.headers[:15] if c not in {'registro_id','aspirante_id'}]
        columns11=[c for c in columns13 if not c.startswith('fecha_')]
        idx=defaultdict(list)
        for ident,row in self.before.items():
            if self.origin[ident]=='Principal':idx[tuple(row[c] for c in columns11)].append(ident)
        self.oracle_matches=[];self.oracle_by_id={}
        for ident in self.ids_out:
            if self.origin[ident]!='Oracle':continue
            row=self.rows[ident]
            candidates=idx.get(tuple(row[c] for c in columns11),[])
            exact=[i for i in candidates if all(row[c]==self.before[i][c] for c in columns13)]
            request_dates=[serial(self.before[i]['fecha_solicitud']) for i in candidates]
            enrol_dates=[serial(self.before[i]['fecha_matricula']) for i in candidates]
            money_final=[serial(self.rows[i]['valor_matricula_cop']) for i in candidates]
            self.oracle_by_id[ident]=candidates
            self.oracle_matches.append({'registro_id_oracle':row['registro_id'],'aspirante_id_oracle':row['aspirante_id'],
                'registros_principales_candidatos':', '.join(self.rows[i]['registro_id'] for i in candidates),
                'aspirantes_principales_candidatos':', '.join(sorted({self.rows[i]['aspirante_id'] or 'Sin identificador' for i in candidates})),
                'candidatos_por_11_atributos':len(candidates),'candidatos_por_13_atributos':len(exact),
                'atributos_informados_de_11':sum(row[c] is not None and row[c]!='' for c in columns11),
                'fecha_solicitud_oracle':row['fecha_solicitud'],'fechas_solicitud_principal':', '.join(request_dates),
                'fecha_matricula_oracle':row['fecha_matricula'],'fechas_matricula_principal':', '.join(enrol_dates),
                'importe_oracle_COP':row['valor_matricula_cop'],'importes_principales_finales_COP':', '.join(money_final),
                'clasificacion':'Coincidencia de atributos y fechas' if exact else 'Coincidencia de atributos con diferencias temporales' if candidates else 'Sin correspondencia por la regla aplicada',
                'tratamiento':'Conservado en BaseUnificada. Identidad de solicitud entre sistemas no confirmada'})
        self.similarity=indice_similitud_entre_fuentes(self.oracle_by_id)
        self.write('correspondencias_oracle.csv',self.oracle_matches)
        self.metrics['oracle']={'registros_conservados':len(self.oracle),
                               'con_candidato_11_atributos':sum(r['candidatos_por_11_atributos']>0 for r in self.oracle_matches),
                               'con_candidato_13_atributos':sum(r['candidatos_por_13_atributos']>0 for r in self.oracle_matches),
                               'con_varios_candidatos':sum(r['candidatos_por_11_atributos']>1 for r in self.oracle_matches),
                               'filas_retiradas':0}
        assert len(self.oracle)==500
        return pd.DataFrame([self.metrics['oracle']])

    def calidad_y_aspirantes(self):
        parent_revision=json.loads((self.root/'reports/limpieza/ultima_revision_descriptiva.json').read_text())
        assert parent_revision['id_ejecucion']==self.parent['entrada_L10']
        old_quality=self.read(self.root/parent_revision['auditoria']/'calidad_y_variables_auxiliares.csv')
        ambiguous=set()
        for record in old_quality:
            target=self.mapping[record['id_registro_salida']]
            for col,flag in [('fecha_solicitud','solicitud_formato_ambiguo'),('fecha_matricula','matricula_formato_ambiguo')]:
                if record[flag]=='True':ambiguous.add((target,col))
        self.quality=[];self.origins=[];self.people=[];self.unknown=[]
        groups=defaultdict(list)
        for ident in self.ids_out:
            row=self.rows[ident]; source=self.origin[ident]
            request=row['fecha_solicitud'];enrol=row['fecha_matricula']
            reverse=enrol is not None and enrol<request
            future_request=request>self.reference; future_enrol=enrol is not None and enrol>self.reference
            ambiguous_request=(ident,'fecha_solicitud') in ambiguous; ambiguous_enrol=(ident,'fecha_matricula') in ambiguous
            interval_ok=enrol is not None and not any([reverse,future_request,future_enrol,ambiguous_request,ambiguous_enrol])
            self.quality.append({'registro_id':row['registro_id'],'fuente_origen':source,
                'programa_ausente':row['programa'] is None,'aspirante_id_ausente':row['aspirante_id'] is None,
                'puntaje_ausente':row['puntaje_admision'] is None,'importe_ausente':row['valor_matricula_cop'] is None,
                'fecha_matricula_ausente':enrol is None,
                'fecha_solicitud_ambigua':ambiguous_request,'fecha_matricula_ambigua':ambiguous_enrol,
                'matricula_anterior_a_solicitud':reverse,
                'solicitud_posterior_al_anio_periodo':request.year>row['periodo_academico']//10,
                'fuera_ventana_orientativa':not en_ventana_orientativa(request,row['periodo_academico']),
                'solicitud_posterior_referencia':future_request,'matricula_posterior_referencia':future_enrol,
                'matriculado_documentos_no_completos':row['estado_proceso']=='Matriculado' and row['documentos_completos']!='Sí',
                'documentacion_pendiente_con_documentos_si':row['estado_proceso']=='Documentación pendiente' and row['documentos_completos']=='Sí',
                'estado_recibido':self.original_states.get(ident,row['estado_proceso']),
                'estado_analitico':row['estado_proceso'],
                'intervalo_dias_apto_reglas_aplicadas':interval_ok,
                'dias_solicitud_matricula':(enrol-request).days if interval_ok else None,
                'fecha_solicitud_apta_reglas_aplicadas':not ambiguous_request and not future_request,
                'referencia_revision':self.reference})
            self.origins.append({'registro_id':row['registro_id'],'fuente_origen':source,
                'fuentes_asociadas':', '.join(sorted(self.source_sets[ident])),
                'crm_incorporado':'CRM' in self.source_sets[ident],
                'importe_recuperado_crm':any(c['id_fila_salida']==ident for c in self.changes),
                'similitud_entre_fuentes_detectada':bool(self.similarity.get(ident)),
                'unidad':'registro de solicitud de origen. Independencia entre sistemas no confirmada'})
            if row['aspirante_id'] is None:
                self.unknown.append({'registro_id':row['registro_id'],'fuente_origen':source,'programa':row['programa'],
                                     'estado_proceso':row['estado_proceso'],'periodo_academico':row['periodo_academico'],
                                     'motivo':'Identificador de aspirante no informado. Cantidad de personas no determinada'})
            else:groups[(source,row['aspirante_id'])].append(row)
        for (source,code),rows in sorted(groups.items()):
            states=sorted({r['estado_proceso'] for r in rows})
            self.people.append({'fuente_origen':source,'aspirante_id':code,
                'clave_identificador_origen':source+':'+code,'registros':len(rows),
                'programas_distintos_informados':len({r['programa'] for r in rows if r['programa']}),
                'periodos_distintos':len({r['periodo_academico'] for r in rows}),
                'estados_observados':', '.join(states),'clasificacion_observada':clasificar_aspirante(states),
                'codigos_registro':', '.join(sorted(r['registro_id'] for r in rows)),
                'alcance':'Código de origen. Equivalencia de personas entre sistemas sin confirmar'})
        self.quality_by_id={q['registro_id']:q for q in self.quality}
        self.origin_by_id={r['registro_id']:r for r in self.origins}
        self.write('control_calidad_final.csv',self.quality)
        self.write('origen_registros.csv',self.origins)
        self.write('aspirantes_por_origen.csv',self.people)
        self.write('solicitudes_sin_identificador.csv',self.unknown)
        self.metrics['calidad']={k:sum(bool(r[k]) for r in self.quality) for k in [
            'programa_ausente','aspirante_id_ausente','puntaje_ausente','importe_ausente','fecha_matricula_ausente',
            'fecha_solicitud_ambigua','fecha_matricula_ambigua','matricula_anterior_a_solicitud',
            'solicitud_posterior_al_anio_periodo','fuera_ventana_orientativa','solicitud_posterior_referencia',
            'matricula_posterior_referencia','matriculado_documentos_no_completos','documentacion_pendiente_con_documentos_si',
            'intervalo_dias_apto_reglas_aplicadas']}
        self.metrics['identidad']={'identificadores_por_origen':len(self.people),
            'identificadores_principal':sum(r['fuente_origen']=='Principal' for r in self.people),
            'identificadores_oracle':sum(r['fuente_origen']=='Oracle' for r in self.people),
            'registros_sin_identificador':len(self.unknown),'personas_globales_unicas_confirmadas':False}
        self.metrics['fuentes']={'Principal':len(self.principal),'Oracle':len(self.oracle),
                                'principal_con_crm':sum(r['crm_incorporado'] for r in self.origins),
                                'registros_con_similitud_entre_fuentes':sum(r['similitud_entre_fuentes_detectada'] for r in self.origins)}
        return pd.DataFrame([self.metrics['calidad']]),pd.DataFrame([self.metrics['identidad']])

    def describir(self):
        self.frequencies=[];self.numbers=[];self.crossings=[]
        for scope,rows in [('Integrada',self.all),('Principal',self.principal),('Oracle',self.oracle)]:
            for col in ['programa','modalidad','canal_captacion','estado_proceso','documentos_completos','ciudad_residencia','asesor','periodo_academico','facultad','nivel_formacion']:
                for value,count in Counter(r[col] for r in rows).most_common():
                    self.frequencies.append({'alcance':scope,'variable':col,'categoria':serial(value) if value is not None else 'Sin información',
                        'registros':count,'denominador_registros':len(rows),'porcentaje':round(count*100/len(rows),2)})
            for col in ['puntaje_admision','valor_matricula_cop','duracion_semestres']:
                nums=[Decimal(r[col]) for r in rows if r[col] is not None]
                self.numbers.append({'alcance':scope,'variable':col,'registros':len(rows),'informados':len(nums),
                    'ausentes':len(rows)-len(nums),'minimo':serial(min(nums)),'maximo':serial(max(nums)),
                    'promedio':serial(sum(nums)/len(nums)),'mediana':serial(median(nums)),
                    'unidad':'COP, importe reportado. No acredita pago' if col=='valor_matricula_cop' else 'semestres' if col=='duracion_semestres' else 'puntaje registrado'})
        for first,second in [('programa','modalidad'),('canal_captacion','estado_proceso'),('ciudad_residencia','modalidad')]:
            counts=Counter((r[first],r[second]) for r in self.all);totals=Counter(r[first] for r in self.all)
            for (a,b),count in counts.items():
                self.crossings.append({'variable_grupo':first,'categoria_grupo':a or 'Sin información',
                    'variable_comparacion':second,'categoria_comparacion':b,'registros':count,
                    'denominador_grupo':totals[a],'porcentaje_grupo':round(count*100/totals[a],2),
                    'unidad':'Registros integrados. No personas únicas confirmadas'})
        months=defaultdict(lambda:{'Principal':0,'Oracle':0,'sin_alertas':0})
        for ident in self.ids_out:
            row=self.rows[ident];month=row['fecha_solicitud'].strftime('%Y-%m')
            months[month][self.origin[ident]]+=1
            months[month]['sin_alertas']+=int(self.quality_by_id[row['registro_id']]['fecha_solicitud_apta_reglas_aplicadas'])
        self.months=[{'mes':month,**counts,'total_registros':counts['Principal']+counts['Oracle']} for month,counts in sorted(months.items())]
        self.write('frecuencias_finales.csv',self.frequencies)
        self.write('estadisticas_numericas_finales.csv',self.numbers)
        self.write('cruces_integrados.csv',self.crossings)
        self.write('serie_mensual_por_fuente.csv',self.months)
        return pd.DataFrame(self.numbers)

    def graficar(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
        plt.rcParams.update({'font.size':10,'figure.dpi':140,'axes.spines.top':False,'axes.spines.right':False})
        frame=pd.DataFrame(self.all)
        def save(fig,name,title):
            fig.tight_layout()
            for ext in ['png','pdf']:fig.savefig(self.fig/f'{name}.{ext}',bbox_inches='tight')
            plt.close(fig);self.figures.append((name,title))
        counts=frame['estado_proceso'].value_counts().sort_values()
        fig,ax=plt.subplots(figsize=(10,5));bars=ax.barh(counts.index,counts.values,color='#246C94')
        ax.bar_label(bars,labels=[f'{v:,} ({v/55:.1f} %)'.replace(',','.') for v in counts],padding=4)
        ax.set_xlim(0,max(counts)*1.25);ax.set_xlabel('Registros integrados, n = 5.500');ax.set_title('Estados registrados del proceso de admisión')
        save(fig,'01_estados_integrados','Estados del proceso de admisión')
        matrix=pd.crosstab(frame['programa'].fillna('Sin información'),frame['modalidad'])
        matrix=matrix.loc[matrix.sum(axis=1).sort_values().index]
        fig,ax=plt.subplots(figsize=(12,6));matrix.plot.barh(stacked=True,ax=ax,color=['#8BBECD','#246C94','#DBAC4D'])
        ax.set_xlabel('Registros integrados');ax.set_ylabel('');ax.set_title('Programa académico y modalidad');ax.legend(title='Modalidad',loc='lower right')
        save(fig,'02_programas_modalidades','Programas y modalidades')
        matrix=pd.crosstab(frame['canal_captacion'],frame['estado_proceso'])
        fig,ax=plt.subplots(figsize=(12,5.5));matrix.plot.barh(stacked=True,ax=ax,cmap='tab20')
        ax.set_xlabel('Registros integrados');ax.set_ylabel('');ax.set_title('Canal de captación y estado registrado');ax.legend(title='Estado',bbox_to_anchor=(1.02,1),loc='upper left')
        save(fig,'03_canales_estados','Canales de captación y estados')
        mods=['Presencial','Virtual','Híbrida']
        values=[[float(r['valor_matricula_cop']) for r in self.all if r['modalidad']==mod and r['valor_matricula_cop'] is not None] for mod in mods]
        fig,ax=plt.subplots(figsize=(8,5));ax.boxplot(values,tick_labels=[f'{mod}\nn = {len(v)}' for mod,v in zip(mods,values)],showmeans=True)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1e6:.2f}'.replace('.',',')))
        ax.set_ylabel('Millones de COP');ax.set_title('Distribución de importes reportados por modalidad')
        ax.text(0,-.24,'Línea naranja: mediana. Triángulo verde: promedio. No representa tarifas oficiales.',transform=ax.transAxes,fontsize=8)
        save(fig,'04_importes_modalidad','Importes reportados por modalidad')
        monthly=pd.DataFrame(self.months)
        fig,ax=plt.subplots(figsize=(12,5));ax.plot(monthly['mes'],monthly['Principal'],marker='o',label='Principal enriquecida con CRM')
        ax.plot(monthly['mes'],monthly['Oracle'],marker='.',label='Oracle');ax.plot(monthly['mes'],monthly['sin_alertas'],linestyle='--',label='Total sin alertas de formato o fecha futura')
        ax.tick_params(axis='x',rotation=60);ax.set_ylabel('Registros');ax.set_title('Cobertura mensual por fuente');ax.legend(fontsize=8)
        ax.text(0,-.4,'La principal termina el 12 de septiembre de 2026. Las fechas futuras se identifican respecto al 26 de octubre.',transform=ax.transAxes,fontsize=8)
        save(fig,'05_cobertura_temporal','Cobertura temporal por fuente')
        matrix=pd.crosstab(frame['ciudad_residencia'],frame['modalidad'])
        fig,ax=plt.subplots(figsize=(11,5));matrix.plot.barh(stacked=True,ax=ax,color=['#8BBECD','#246C94','#DBAC4D'])
        ax.set_xlabel('Registros integrados');ax.set_ylabel('');ax.set_title('Ciudad de residencia y modalidad');ax.legend(title='Modalidad',bbox_to_anchor=(1.02,1),loc='upper left')
        save(fig,'06_ciudades_modalidades','Ciudades y modalidades')
        return [self.fig/f'{name}.png' for name,_ in self.figures]

    def diccionario(self):
        descriptions=[
            ('registro_id','Texto identificador','Código de solicitud de su sistema de origen. Único en el archivo entregado. No prueba independencia del evento entre sistemas.'),
            ('aspirante_id','Texto identificador','Código de aspirante informado. Se interpreta junto con la fuente. Vacío cuando no está disponible.'),
            ('fecha_solicitud','Fecha','Fecha reportada de la solicitud. Presentación año, mes y día. Alertas de interpretación en Control_Calidad.'),
            ('programa','Categoría de texto','Programa académico solicitado. Se conserva ausente cuando no existe información recuperable.'),
            ('modalidad','Categoría de texto','Modalidad de la solicitud: Presencial, Virtual o Híbrida. No se reemplaza por la modalidad del catálogo.'),
            ('canal_captacion','Categoría de texto','Canal registrado de captación. Su frecuencia no acredita por sí sola eficacia comercial.'),
            ('estado_proceso','Categoría de texto','Estado analítico. Nuevo se agrupa con Admitido. Los estados recibidos se conservan en Control_Calidad.'),
            ('puntaje_admision','Número decimal','Puntaje informado, sin sustituir ausencias por cero ni deducir una escala institucional oficial.'),
            ('documentos_completos','Categoría de texto','Sí, No o Pendiente. Pendiente conserva significado y no se convierte en ausencia.'),
            ('valor_matricula_cop','Número decimal, COP','Importe de matrícula reportado. Para CRM se utiliza matrícula base y se separan derechos administrativos. No acredita pago ni tarifa oficial.'),
            ('ciudad_residencia','Categoría de texto','Ciudad de residencia reportada, con escritura homologada.'),
            ('asesor','Categoría de texto','Asesor asignado o Sin asignar. No se completa una asignación por suposición.'),
            ('fecha_matricula','Fecha','Fecha de matrícula informada. Puede preceder al inicio de estudios. No determina automáticamente el periodo académico.'),
            ('correo','Texto de contacto','Correo reportado. La estructura compatible no prueba entregabilidad o identidad civil.'),
            ('periodo_academico','Código entero categórico','Semestre de ingreso reportado: 20252, 20261 o 20262. No se suma ni promedia. No se deriva desde las fechas.'),
            ('facultad','Categoría de texto','Facultad según el catálogo de trabajo adoptado. No se presenta como validación institucional externa.'),
            ('duracion_semestres','Entero, semestres','Duración según el catálogo de trabajo adoptado. Ausente si el programa no está identificado.'),
            ('nivel_formacion','Categoría de texto','Pregrado o Posgrado según el catálogo de trabajo adoptado.')]
        return [{'columna':c,'tipo':t,'descripcion':d,'tratamiento_ausencia':'Celda vacía. Motivos y criterios documentados'} for c,t,d in descriptions]

    def metodologia(self):
        return [
            {'aspecto':'Título','criterio':'BaseUnificada Entregable'},
            {'aspecto':'Institución','criterio':'Instituto Universitario Horizonte'},
            {'aspecto':'Fecha de preparación','criterio':'26 de octubre de 2026'},
            {'aspecto':'Unidad de la tabla principal','criterio':'Registro de solicitud identificado por su código de origen. 5.500 registros y 18 columnas.'},
            {'aspecto':'Fuentes incorporadas','criterio':'5.000 registros principales, 100 aportes CRM incorporados a esos registros y 500 registros Oracle conservados.'},
            {'aspecto':'Conciliación CRM','criterio':'Mismo código de solicitud y 12 atributos compatibles. Se conservan 87 importes y se recuperan 13 matrículas base. Derechos separados.'},
            {'aspecto':'Tratamiento Oracle','criterio':'Los 500 registros están incluidos. Las coincidencias con la principal se identifican como candidatas. No se asume identidad del evento por semejanza.'},
            {'aspecto':'Estados','criterio':'Nuevo se agrupa analíticamente con Admitido. Matriculado permanece separado. No se inventan pagos ni fechas.'},
            {'aspecto':'Periodo académico','criterio':'Semestre de ingreso reportado. Se conserva y no se recalcula desde solicitud o matrícula.'},
            {'aspecto':'Ventana orientativa del primer periodo','criterio':'Octubre del año anterior a enero del año de ingreso, como referencia descriptiva sin validar calendario oficial.'},
            {'aspecto':'Ventana orientativa del segundo periodo','criterio':'Mayo a julio del año de ingreso, como referencia descriptiva. Estar fuera no causa exclusión ni corrección.'},
            {'aspecto':'Fechas','criterio':'Presentación año, mes y día. Se señalan ambigüedades, orden inverso y fechas posteriores a la referencia del 26 de octubre de 2026.'},
            {'aspecto':'Intervalos','criterio':'Solo se calculan con ambas fechas y sin las alertas definidas. El periodo académico no se exige igual al semestre de las fechas.'},
            {'aspecto':'Importes','criterio':'COP exactos con dos decimales. No se completan por programa, modalidad, promedio, moda o mediana.'},
            {'aspecto':'Personas','criterio':'Aspirantes_Origen tiene una fila por código informado y fuente. No representa una cantidad global de personas únicas confirmadas.'},
            {'aspecto':'Identificadores ausentes','criterio':'Los vacíos y nan se representan como ausencia real. Los registros permanecen. No se inventan identificadores.'},
            {'aspecto':'Clasificación por aspirante','criterio':'Presencia de matrícula en alguna solicitud. Después admisión sin matrícula. Después otros estados. Es una clasificación excluyente por código de origen, no estado actual.'},
            {'aspecto':'Conteos por grupos','criterio':'Un mismo código puede aparecer en varios programas, canales o estados. No sumar esos conteos como personas nuevas.'},
            {'aspecto':'Procedencia y calidad','criterio':'Origen_Registros y Control_Calidad se relacionan con BaseUnificada por registro_id, sin multiplicar filas.'},
            {'aspecto':'Alcance','criterio':'Preparación técnica terminada para revisión y análisis descriptivo. Las correspondencias entre sistemas y los datos no recuperables mantienen limitaciones explícitas.'},
            {'aspecto':'Decisiones de preparación aplicadas','criterio':'CRM incorporado, Oracle incluido, periodos conservados, ausencias explícitas y Nuevo agrupado con Admitido. No son tareas de preparación pendientes.'},
            {'aspecto':'Similitud entre fuentes','criterio':'La marca indica atributos coincidentes y se informa en ambos registros relacionados. El cruce ya fue ejecutado. La similitud no confirma identidad de solicitud o persona.'},
            {'aspecto':'Datos no confirmados','criterio':'Persisten correspondencias entre sistemas, valores desconocidos y observaciones temporales. Son límites de la información, no transformaciones omitidas.'}]

    def guia_hojas(self):
        return [
            {'hoja':'BaseUnificada','filas':5500,'uso':'Tabla principal para analizar los registros integrados. Contiene 18 columnas.'},
            {'hoja':'Diccionario_Datos','filas':18,'uso':'Significado, tipo y tratamiento de las 18 columnas.'},
            {'hoja':'Origen_Registros','filas':5500,'uso':'Procedencia y aportes CRM. Señala similitudes detectadas entre fuentes, sin afirmar identidad.'},
            {'hoja':'Control_Calidad','filas':5500,'uso':'Observaciones por registro, estado recibido y condiciones para cálculos de fechas.'},
            {'hoja':'Resumen_Calidad','filas':len(self.metrics['calidad']),'uso':'Conteos de observaciones. Pueden superponerse y no deben sumarse como filas distintas.'},
            {'hoja':'Aspirantes_Origen','filas':len(self.people),'uso':'Una fila por código de aspirante y sistema de origen. No es un total global confirmado de personas.'},
            {'hoja':'Coincidencias_Oracle','filas':500,'uso':'Comparación de registros Oracle con candidatos principales, con fechas e importes.'},
            {'hoja':'Control_Economico','filas':100,'uso':'Evidencia de matrícula base, derechos y total CRM, junto con el importe conservado o recuperado.'},
            {'hoja':'Registros_Sin_ID','filas':90,'uso':'Registros incluidos en la base que no tienen código de aspirante. No son filas adicionales.'},
            {'hoja':'Metodologia','filas':len(self.metodologia()),'uso':'Reglas aplicadas, decisiones cerradas, denominadores y límites de interpretación.'}]

    def exportar(self,preserve_empty_text):
        self.public=self.out/'entregable'
        self.public.mkdir(parents=True,exist_ok=True)
        csv_path=self.public/'BaseUnificada_Entregable.csv'
        json_path=self.public/'BaseUnificada_Entregable.jsonl'
        excel_path=self.public/'BaseUnificada_Entregable.xlsx'
        self.write(csv_path.name,[{c:serial(r[c]) for c in self.headers} for r in self.all],headers=self.headers,folder=self.public)
        with json_path.open('w',encoding='utf8') as handle:
            for row in self.all:handle.write('{'+', '.join(json.dumps(c)+': '+json_literal(row[c]) for c in self.headers)+'}\n')
        self.write('Origen_Registros.csv',self.origins,folder=self.public)
        self.write('Control_Calidad.csv',self.quality,folder=self.public)
        self.write('Diccionario_Datos.csv',self.diccionario(),folder=self.public)
        self.write('Aspirantes_Origen.csv',self.people,folder=self.public)
        self.write('Coincidencias_Oracle.csv',self.oracle_matches,folder=self.public)
        self.write('Control_Economico.csv',self.economics,folder=self.public)
        self.write('Registros_Sin_ID.csv',self.unknown,folder=self.public)
        self.write('Frecuencias.csv',self.frequencies,folder=self.public)
        self.write('Estadisticas_Numericas.csv',self.numbers,folder=self.public)
        self.write('Cruces_Descriptivos.csv',self.crossings,folder=self.public)
        self.write('Serie_Mensual.csv',self.months,folder=self.public)
        self.write('Guia_Hojas.csv',self.guia_hojas(),folder=self.public)
        guide=['# Guía de hojas de BaseUnificada Entregable','','La tabla para el análisis es BaseUnificada. Las otras hojas explican, controlan o resumen sus mismos registros. No se suman como fuentes nuevas.','','| Hoja | Filas | Uso |','| :--- | ---: | :--- |']
        guide.extend(f"| {r['hoja']} | {r['filas']} | {r['uso']} |" for r in self.guia_hojas())
        guide.extend(['','El cruce entre fuentes ya se ejecutó. La similitud detectada es un resultado de ese control y no demuestra por sí sola identidad del evento. Las reglas de preparación están aplicadas. Persisten datos no confirmados y ausencias que se conservan explícitamente.'])
        (self.public/'Guia_Hojas.md').write_text('\n'.join(guide)+'\n',encoding='utf8')
        quality_summary=[{'observacion':name.replace('_',' '),'registros':count,
                          'denominador':5500,'porcentaje':round(count/55,2),
                          'interpretacion':'Observaciones superpuestas. No sumar como registros diferentes. No acreditan error por sí solas.'}
                          for name,count in self.metrics['calidad'].items()]
        book=Workbook();book.remove(book.active)
        sheets=[('BaseUnificada',self.all),('Diccionario_Datos',self.diccionario()),('Origen_Registros',self.origins),
                ('Control_Calidad',self.quality),('Resumen_Calidad',quality_summary),('Aspirantes_Origen',self.people),
                ('Coincidencias_Oracle',self.oracle_matches),('Control_Economico',self.economics),
                ('Registros_Sin_ID',self.unknown),('Metodologia',self.metodologia())]
        for name,rows in sheets:
            ws=book.create_sheet(name);headers=list(rows[0]);ws.append(headers)
            for row in rows:ws.append([row[c] for c in headers])
            for j,c in enumerate(headers,1):
                width=65 if c in ['descripcion','criterio','interpretacion','alcance','tratamiento'] else 42 if 'programa' in c else 28
                ws.column_dimensions[get_column_letter(j)].width=width
                for n in range(2,len(rows)+2):
                    cell=ws.cell(n,j)
                    if isinstance(cell.value,Decimal):cell.number_format='"COP" #,##0.00' if ('COP' in c or c=='valor_matricula_cop') else '0.00'
                    elif isinstance(cell.value,date):cell.number_format='yyyy-mm-dd'
                    elif isinstance(cell.value,int) and not isinstance(cell.value,bool):cell.number_format='0'
            table=Table(displayName=name,ref=f'A1:{get_column_letter(len(headers))}{len(rows)+1}')
            table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium9',showRowStripes=True)
            ws.add_table(table);ws.freeze_panes='A2'
        book.properties.creator='';book.properties.lastModifiedBy='';book.properties.title='BaseUnificada Entregable'
        book.properties.description='Integración de solicitudes de admisión y controles para revisión externa.'
        book.save(excel_path);book.close()
        preserve_empty_text(excel_path,[tuple(r[c] for c in self.headers) for r in self.all])
        positions={i:n for n,i in enumerate(self.ids_out,2)}
        output_sha=sha(csv_path)
        destinations=[]
        for record in self.destinations:
            prior=record['id_registro_salida'];target=self.mapping[prior]
            status='integrada_CRM' if prior!=target else record['estado_destino']
            destinations.append({**record,'id_representante_L11':prior,'id_registro_salida':target,
                'registro_id_salida':self.rows[target]['registro_id'],'fila_salida_csv':positions[target],
                'estado_destino':status,'sha256_csv_salida':output_sha})
        self.write('disposicion_5640_entradas.csv',destinations)
        self.write('registro_pasos_finales.csv',[
            {'paso':'Conciliación CRM','filas_antes':5600,'filas_despues':5500,'filas_integradas':100,'celdas_recuperadas':13,'filas_excluidas':0},
            {'paso':'Revisión Oracle','filas_antes':5500,'filas_despues':5500,'filas_integradas':0,'celdas_recuperadas':0,'filas_excluidas':0},
            {'paso':'Reglas temporales e identidad','filas_antes':5500,'filas_despues':5500,'filas_integradas':0,'celdas_recuperadas':0,'filas_excluidas':0},
            {'paso':'Exportación externa','filas_antes':5500,'filas_despues':5500,'filas_integradas':0,'celdas_recuperadas':0,'filas_excluidas':0}])
        self.public_paths={'csv':csv_path,'jsonl':json_path,'xlsx':excel_path}
        return self.validar(preserve_empty_text)

    def validar(self,preserve_empty_text=None):
        excel_path=self.public_paths['xlsx'];json_path=self.public_paths['jsonl'];csv_path=self.public_paths['csv']
        book=load_workbook(excel_path,read_only=True,data_only=True)
        values=list(book['BaseUnificada'].values)
        excel_rows=[{c:RevisionDescriptiva.restore(v,c) for c,v in zip(self.headers,row)} for row in values[1:]]
        oracle_sheet_rows=book['Coincidencias_Oracle'].max_row-1
        people_sheet_rows=book['Aspirantes_Origen'].max_row-1
        book.close()
        json_rows=[{c:RevisionDescriptiva.restore(v,c) for c,v in json.loads(line,parse_float=Decimal).items()} for line in json_path.read_text().splitlines()]
        csv_rows=self.read(csv_path)
        expected_csv=[{c:serial(r[c]) for c in self.headers} for r in self.all]
        allowed={(r['id_fila_salida'],r['columna']) for r in self.changes}
        values_ok=all(self.rows[i][c]==self.before[i][c] or (i,c) in allowed for i in self.ids_out for c in self.headers)
        destinations=self.read(self.audit/'disposicion_5640_entradas.csv')
        original_ok=True
        for manifest in ['docs/referencias/integridad.json','docs/referencias/taller_2/integridad.json']:
            for path,item in json.loads((self.root/manifest).read_text()).items():
                original_ok &= sha(self.root/path)==(item if isinstance(item,str) else item['sha256'])
        meta=json.loads((self.root/'data/prepared/taller_2/BaseUnificada.metadata.json').read_text())
        prepared_ok=all(sha(self.root/'data/prepared/taller_2'/name)==v['sha256'] for name,v in meta['archivos'].items())
        prepared_ok &= sha(self.root/meta['libro_origen'])==meta['sha256_libro_origen']
        checks=[('5500 registros de salida',len(self.all)==5500),('18 columnas de negocio',list(values[0])==self.headers and len(self.headers)==18),
                ('500 Oracle conservados',len(self.oracle)==500 and sum(self.origin[i]=='Oracle' for i in self.ids_out)==500),
                ('100 CRM integrados con evidencia',len(self.crm_pairs)==100 and all(r['coinciden_atributos'] for r in self.crm_pairs)),
                ('13 importes recuperados y 87 conservados',len(self.changes)==13 and self.metrics['crm']['importes_principales_conservados']==87),
                ('Cambios limitados a importes recuperados',values_ok),
                ('Fechas periodos estados e IDs intactos',all(self.rows[i][c]==self.before[i][c] for i in self.ids_out for c in ['fecha_solicitud','fecha_matricula','periodo_academico','estado_proceso','registro_id','aspirante_id'])),
                ('Códigos de registro únicos',len({r['registro_id'] for r in self.all})==5500),
                ('5640 entradas con destino',len(destinations)==len({r['id_fila_entrada'] for r in destinations})==5640),
                ('Destinos existentes',set(r['id_registro_salida'] for r in destinations)==set(self.ids_out)),
                ('Fuentes cubiertas',sum(r['crm_incorporado'] for r in self.origins)==100 and len(self.origins)==5500),
                ('Lectura completa Excel',excel_rows==self.all),('Lectura completa JSONL',json_rows==self.all),('Lectura completa CSV',csv_rows==expected_csv),
                ('500 correspondencias Oracle en entregable',oracle_sheet_rows==500),
                ('3424 identificadores por origen',len(self.people)==people_sheet_rows==3424),
                ('Identificadores de origen únicos',len({r['clave_identificador_origen'] for r in self.people})==len(self.people)),
                ('90 registros sin ID conservados',len(self.unknown)==90),
                ('Registros explicados por vistas de aspirantes',sum(r['registros'] for r in self.people)+len(self.unknown)==5500),
                ('COP con dos decimales exactos',all(r['valor_matricula_cop'] is None or r['valor_matricula_cop'].as_tuple().exponent==-2 for r in self.all)),
                ('Fuentes originales intactas',original_ok),('Entrada preparada y libro intactos',prepared_ok),
                ('Entrada L11 intacta',sha(self.source)==self.input_sha),
                ('Similitud señalada en ambos registros relacionados',all(j in self.similarity.get(i,set()) for j,items in self.similarity.items() for i in items))]
        self.write('controles_finales.csv',[{'control':k,'correcto':bool(v)} for k,v in checks])
        assert all(v for _,v in checks),[k for k,v in checks if not v]
        self.metrics['controles_correctos']=len(checks)
        return pd.DataFrame([{'control':k,'correcto':bool(v)} for k,v in checks])

    def informe(self):
        n=lambda x:f'{x:,}'.replace(',','.')
        c=self.metrics['calidad'];o=self.metrics['oracle'];ids=self.metrics['identidad']
        lines=['# BaseUnificada Entregable','', '## Informe de preparación e integración de datos','',
            'Instituto Universitario Horizonte. Fecha de preparación: 26 de octubre de 2026.','',
            '## 1. Resultado y alcance','',
            '**La base entregada contiene 5.500 registros y 18 columnas.** Integra información principal, CRM y Oracle. Se conservan los 500 registros Oracle y se incorpora el aporte de los 100 registros CRM a sus solicitudes correspondientes. El archivo está preparado para revisión externa y análisis descriptivo de registros, con procedencia y observaciones de calidad identificadas.',
            '', 'Un registro es una solicitud identificada por su código de origen. La unicidad de ese código en el entregable no confirma que los sistemas describan eventos independientes. Las coincidencias Oracle permanecen visibles y no se eliminan por semejanza. Tampoco se presenta el número de códigos de aspirante por origen como una cantidad global de personas civiles únicas.',
            '', '| Componente | Cantidad | Interpretación |','| :--- | ---: | :--- |',
            '| Registros principales | 5.000 | Incluyen el enriquecimiento CRM cuando corresponde. |',
            '| Aportes CRM incorporados | 100 | Información integrada a los registros principales, sin filas adicionales. |',
            '| Registros Oracle | 500 | Incluidos en la tabla principal y en los gráficos integrados. |',
            '| Total de filas entregadas | 5.500 | No sumar nuevamente los aportes CRM. |',
            '', '## 2. Preparación realizada','',
            '| Operación | Resultado |','| :--- | :--- |',
            '| Conservación del origen | Las 5.640 entradas consolidadas inicialmente mantienen un destino documentado. |',
            '| Estandarización | Homologación de espacios, tildes, categorías, formatos y tipos. |',
            '| Ausencias | Separación de valores desconocidos y marcadores. Los identificadores vacíos y nan se representan como ausencia real. |',
            '| Repeticiones exactas | 38 filas adicionales consolidadas con evidencia de igualdad. |',
            '| Registros parciales | Dos filas complementarias consolidadas. Cinco valores recuperados para REG003600 y REG004804. |',
            '| Estados | Nuevo agrupado analíticamente como Admitido. Matriculado conservado y estado recibido disponible en Control_Calidad. |',
            '| CRM | 100 aportes incorporados mediante correspondencia por código y 12 atributos. 13 importes recuperados. |',
            '| Oracle | 500 registros conservados. Sus coincidencias y diferencias se exportan para revisión. |',
            '| Periodos | Códigos 20252, 20261 y 20262 conservados como semestres de ingreso, sin recalcularlos desde las fechas. |',
            '| Exportación | Excel con datos y controles, CSV, JSONL, informe y gráficos. |',
            '', 'La conciliación de cantidades es: 5.640 entradas, menos 38 repeticiones exactas, menos dos parciales y menos 100 aportes CRM integrados, igual a 5.500 registros. No se retiran registros por ser Oracle, tener información faltante o estar fuera de una ventana temporal orientativa.',
            '', '## 3. Conceptos económicos y recuperación CRM','',
            'En los 100 cruces CRM, los códigos y 12 atributos comparados son compatibles. En 87 casos la matrícula principal coincide con la matrícula base CRM y se conserva. En 13 casos el principal está ausente y se recupera la matrícula base desde el CRM. Los derechos administrativos y el total CRM se mantienen en Control_Economico. No se suman silenciosamente al importe de matrícula.',
            '', f"La principal conserva {n(self.metrics['crm']['importes_ausentes_principal'])} importes ausentes. El conjunto integrado tiene {n(c['importe_ausente'])} ausencias de importe. No se completaron por programa, modalidad, promedio, mediana o moda. El importe reportado no acredita un pago ni una tarifa institucional oficial.",
            '', '## 4. Revisión Oracle y procedencia','',
            f"Los 500 registros Oracle se conservaron. {o['con_candidato_11_atributos']} presentan candidatos al comparar 11 atributos excluyendo identificadores y fechas. {o['con_candidato_13_atributos']} coinciden también en los dos atributos de fecha comparados. Las reglas utilizan igualdad numérica y mantienen explícitas las ausencias. Una ausencia compartida no constituye evidencia independiente de identidad.",
            '', 'Las sondas se documentan sobre el punto previo a recuperar importes CRM, para no perder candidatos por una recuperación posterior. Coincidencias_Oracle muestra las fechas y los importes finales disponibles. No se cambian los códigos Oracle ni se fusionan personas o solicitudes únicamente por la coincidencia de atributos.',
            '', 'Origen_Registros tiene una fila por registro final y distingue la fuente de origen y las fuentes asociadas. Sus filas se relacionan con BaseUnificada por registro_id y no se anexan como registros nuevos.',
            '', 'El control de similitud ya está aplicado. Se señala en ambos registros relacionados, incluidos los de la principal. Describe atributos coincidentes, sin afirmar identidad del evento ni una tarea de preparación sin ejecutar. Los distintos códigos son convenciones de origen y no se declaran errores.',
            '', '## 5. Fechas, periodos y oportunidad','',
            'El periodo académico representa el semestre de ingreso reportado. Una solicitud de octubre de 2025 puede corresponder al primer periodo de 2026. Una matrícula realizada antes del inicio de clases no determina por sí sola un periodo distinto. Los códigos recibidos se conservan y no se hacen coincidir automáticamente con las fechas.',
            '', 'Se utiliza una ventana descriptiva de octubre a enero para el primer periodo y de mayo a julio para el segundo. Esta referencia no acredita el calendario oficial. Estar fuera de esa ventana solo genera una observación. No provoca exclusión o reasignación del periodo.',
            '', f"Hay {n(c['solicitud_posterior_al_anio_periodo'])} registros cuya solicitud tiene un año posterior al periodo reportado. Se mantienen para revisión, sin inventar cuál dato debe cambiarse. Hay {n(c['matricula_anterior_a_solicitud'])} matrículas anteriores a la solicitud. Las fechas posteriores al 26 de octubre de 2026 se identifican como posteriores a la referencia de preparación, sin afirmar que sean errores o actividades ya realizadas.",
            '', f"Los intervalos entre solicitud y matrícula se calculan para {n(c['intervalo_dias_apto_reglas_aplicadas'])} registros con ambas fechas y sin las alertas definidas. El periodo académico no se exige igual al semestre de las fechas. No existe fecha de actualización de estado y no se reconstruyen transiciones ni un último estado por persona.",
            '', '## 6. Identidad y prevención del doble conteo','',
            f"Se registran {n(ids['identificadores_principal'])} códigos de aspirante informados en la principal y {n(ids['identificadores_oracle'])} en Oracle: {n(ids['identificadores_por_origen'])} identificadores por origen. La vista Aspirantes_Origen incluye ambos sistemas. Esta suma no confirma personas únicas entre sistemas, porque las correspondencias de identidad siguen siendo candidatas.",
            '', f"Se conservan {n(ids['registros_sin_identificador'])} registros sin código de aspirante. No se interpretan como ese mismo número de personas ni se agrupan como una sola persona. Un código de aspirante puede tener varias solicitudes de distintos programas o periodos. La clasificación por código se basa en cualquier solicitud con matrícula, después admisión sin matrícula y finalmente otros estados. No representa el estado actual.",
            '', 'Para medir registros se cuenta registro_id. Para describir identificadores de aspirante se utiliza la clave de origen de Aspirantes_Origen. Los conteos de aspirantes por programa, canal o estado pueden solaparse y no deben sumarse como nuevas personas. No se presentan tasas definitivas de conversión de personas entre sistemas.',
            '', '## 7. Perfil descriptivo integrado','',
            'Las siguientes frecuencias y gráficos utilizan los 5.500 registros integrados, incluidos los 500 Oracle. Describen registros, sin afirmar personas únicas o independencia confirmada de todos los eventos.',
            '', '| Variable | Categoría | Registros | Porcentaje |','| :--- | :--- | ---: | ---: |']
        for col in ['programa','modalidad','canal_captacion','estado_proceso']:
            for item in self.frequencies:
                if item['alcance']=='Integrada' and item['variable']==col:
                    lines.append(f"| {col} | {item['categoria']} | {n(item['registros'])} | {item['porcentaje']:.2f} % |")
        lines += ['', '| Variable numérica | Informados | Ausentes | Mínimo | Máximo | Promedio | Mediana |',
                  '| :--- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for row in self.numbers:
            if row['alcance']=='Integrada':
                if row['variable']=='valor_matricula_cop':
                    monetary=lambda value:format(Decimal(value),',.2f').translate(str.maketrans(',.','.,'))
                    minimum,maximum,average,mid=[monetary(row[c]) for c in ['minimo','maximo','promedio','mediana']]
                else:
                    minimum,maximum,average,mid=row['minimo'],row['maximo'],f"{Decimal(row['promedio']):.2f}",row['mediana']
                lines.append(f"| {row['variable']} | {n(row['informados'])} | {n(row['ausentes'])} | {minimum} | {maximum} | {average} | {mid} |")
        lines += ['', 'Los importes de la tabla se expresan en COP y los puntajes en su unidad reportada. La presencia de concentraciones por programa, ciudad o canal identifica patrones del registro disponible. No demuestra causalidad comercial, capacidad de oferta o rentabilidad. Para evaluar oportunidad de mercado se debe mantener esta distinción.',
                  '', '## 8. Observaciones que acompañan la revisión','',
                  '| Observación | Registros |','| :--- | ---: |']
        for key in ['programa_ausente','aspirante_id_ausente','puntaje_ausente','importe_ausente','fecha_matricula_ausente',
                    'fecha_solicitud_ambigua','fecha_matricula_ambigua','matricula_anterior_a_solicitud',
                    'solicitud_posterior_al_anio_periodo','solicitud_posterior_referencia','matricula_posterior_referencia',
                    'matriculado_documentos_no_completos','documentacion_pendiente_con_documentos_si']:
            lines.append(f"| {key.replace('_',' ')} | {n(c[key])} |")
        lines += ['', 'Las observaciones pueden superponerse en una misma fila y no deben sumarse como solicitudes diferentes. Una ausencia puede ser pertinente para un estado y limitar otro indicador. La falta de fecha de matrícula en una solicitud no matriculada no se declara automáticamente error.',
                  '', '## 9. Estado de cierre y condiciones de uso','',
                  f"La preparación técnica y la conciliación CRM están completadas. Pasaron {self.metrics['controles_correctos']} controles finales, con lectura completa de Excel, CSV y JSONL y conservación de fuentes. El archivo puede entregarse para revisión y utilizarse en análisis descriptivo de registros con su procedencia y sus alertas.",
                  '', 'Para afirmar cantidades globales de personas únicas o conversiones entre sistemas sería necesario validar las correspondencias de identidad. Para presentar tarifas, ingresos cobrados o un calendario institucional oficial se requeriría una validación de esos conceptos. Estas limitaciones no provocan la eliminación de registros ni impiden revisar el conjunto integrado.',
                  '', 'El criterio Nuevo a Admitido y el catálogo de programas son decisiones analíticas documentadas. Su eventual ajuste deberá conservar los valores recibidos y repetir los controles. La versión entregada no presupone que todas las observaciones de negocio estén resueltas o que la información refleje sin error cada hecho real.',
                  '', '## 10. Contenido del paquete','',
                  'BaseUnificada_Entregable.xlsx contiene BaseUnificada, Diccionario_Datos, Origen_Registros, Control_Calidad, Resumen_Calidad, Aspirantes_Origen, Coincidencias_Oracle, Control_Economico, Registros_Sin_ID y Metodologia. Las hojas auxiliares se relacionan con la principal y no se suman como nuevos registros.',
                  '', 'Se incluyen CSV y JSONL del conjunto, controles CSV, tablas descriptivas, seis gráficos y este informe. Los metadatos contienen versión, cantidades, formatos y huellas de integridad de los archivos. El conjunto no contiene consultas dependientes de rutas locales ni conexiones a bases de datos.']
        body='\n'.join(lines)+'\n'
        (self.public/'Informe_BaseUnificada_Entregable.md').write_text(body,encoding='utf8')
        report=self.root/'reports/limpieza/reporte_final_integracion_y_entrega.md'
        appendix=f"\n## Trazabilidad interna de la ejecución\n\nDatos versionados: `{self.out.relative_to(self.root)}`.\n\nAuditoría: `{self.audit.relative_to(self.root)}`.\n\nLa ejecución {self.run} conserva cambios por celda, cruces CRM, comparaciones Oracle y destinos de las 5.640 entradas. El resumen vigente será reports/limpieza/ultima_entrega.json. Las fuentes y tablas Docker conservan su estado. El notebook principal reproduce las etapas previas y la preparación del entregable.\n"
        report.write_text(body+appendix,encoding='utf8')
        return body

    def pdf_informe(self,body):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        from PIL import Image
        pdf_path=self.public/'Informe_BaseUnificada_Entregable.pdf'
        lines=[]
        for raw in body.splitlines():
            if raw.startswith('| :') or raw.startswith('| ---'):continue
            if raw.startswith('|'):
                raw='. '.join(p.strip() for p in raw.strip('|').split('|'))
            raw=raw.replace('**','').replace('`','')
            if raw.startswith('#'):raw=raw.lstrip('#').strip().upper()
            lines.extend(textwrap.wrap(raw,width=94,break_long_words=False,break_on_hyphens=False) or [''])
        metadata={'Title':'BaseUnificada Entregable: informe de preparación e integración','Author':'','Subject':'Revisión descriptiva de admisiones universitarias','Creator':'','Producer':''}
        with PdfPages(pdf_path,metadata=metadata) as pdf:
            for start in range(0,len(lines),49):
                fig=plt.figure(figsize=(8.27,11.69));fig.patch.set_facecolor('white')
                fig.text(.08,.965,'INSTITUTO UNIVERSITARIO HORIZONTE',fontsize=10,color='#246C94',weight='bold')
                fig.text(.08,.94,'BaseUnificada Entregable',fontsize=15,weight='bold')
                for j,line in enumerate(lines[start:start+49]):fig.text(.08,.9-j*.0163,line,fontsize=9.3,va='top')
                fig.text(.08,.035,'Preparación y revisión de datos de admisiones | 26 de octubre de 2026',fontsize=8,color='#555555')
                fig.text(.91,.035,str(start//49+1),fontsize=8,ha='right')
                pdf.savefig(fig);plt.close(fig)
            for name,title in self.figures:
                fig,ax=plt.subplots(figsize=(11.69,8.27));ax.imshow(Image.open(self.fig/f'{name}.png'));ax.axis('off')
                fig.suptitle(title,fontsize=15)
                fig.text(.08,.03,'Unidad: registros integrados. Las correspondencias entre fuentes no confirman eventos independientes.',fontsize=9)
                pdf.savefig(fig,bbox_inches='tight');plt.close(fig)
        return pdf_path

    def cerrar_paquete(self):
        body=self.informe();self.pdf_informe(body)
        graphics=self.public/'Graficos';graphics.mkdir(exist_ok=True)
        for name,_ in self.figures:
            for ext in ['png','pdf']:shutil.copy2(self.fig/f'{name}.{ext}',graphics/f'{name}.{ext}')
        (self.public/'LEEME.md').write_text(
            '# BaseUnificada Entregable\n\nInstituto Universitario Horizonte. Versión 1.1, 26 de octubre de 2026.\n\n'
            'Abra BaseUnificada_Entregable.xlsx y consulte Guia_Hojas.md, Metodologia y Diccionario_Datos. La hoja BaseUnificada contiene 5.500 registros y 18 columnas. Incluye los 500 registros Oracle y los aportes de 100 CRM incorporados a la principal.\n\n'
            'Origen_Registros y Control_Calidad se relacionan por registro_id y tienen una fila por registro. Las otras hojas son controles o resúmenes, no fuentes que se suman a la base.\n\n'
            'Aspirantes_Origen agrupa códigos de aspirante por sistema. Sus 3.424 filas no representan personas globales únicas confirmadas. Los 90 registros sin identificador se conservan aparte.\n\n'
            'CSV: UTF8 con BOM, separador coma, punto decimal y fechas año, mes y día. JSONL conserva null y números decimales. Excel conserva números y fechas reales. Los separadores visuales dependen de la configuración regional.\n\n'
            'Consulte Informe_BaseUnificada_Entregable.pdf para resultados, metodología y limitaciones. Los gráficos y controles forman parte de la entrega. No existen conexiones externas, macros ni consultas dependientes del equipo de preparación.\n',encoding='utf8')
        public_files=[p for p in self.public.rglob('*') if p.is_file() and p.name!='Metadatos_Entrega.json']
        public_meta={'titulo':'BaseUnificada Entregable','institucion':'Instituto Universitario Horizonte','version':self.rules['version_presentacion'],
            'fecha_preparacion':'2026-10-26','filas':5500,'columnas':18,
            'fuentes':{'registros_principales':5000,'aportes_crm_integrados':100,'registros_oracle_incluidos':500},
            'identificadores_aspirante_por_origen':3424,'personas_globales_unicas_confirmadas':False,
            'registros_sin_identificador':90,'control_final':{'comprobaciones_correctas':self.metrics['controles_correctos']},
            'formatos':{'csv':'UTF8 con BOM, coma delimitadora, punto decimal','fecha':'AAAA-MM-DD','moneda':'COP, dos decimales'},
            'archivos':{str(p.relative_to(self.public)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(public_files)}}
        (self.public/'Metadatos_Entrega.json').write_text(json.dumps(public_meta,ensure_ascii=False,indent=2)+'\n')
        zip_path=self.out/'BaseUnificada_Entregable.zip'
        with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.public.rglob('*')):
                if path.is_file():archive.write(path,arcname='BaseUnificada_Entregable/'+str(path.relative_to(self.public)))
        self.verificar_paquete(zip_path,public_meta)
        # Ubicación estable y sencilla para entregar; la versión interna conserva historia.
        delivery=self.root/self.rules.get('directorio_entrega','deliverables');delivery.mkdir(parents=True,exist_ok=True)
        for name in ['BaseUnificada_Entregable.xlsx','BaseUnificada_Entregable.csv',
                     'Informe_BaseUnificada_Entregable.pdf','Informe_BaseUnificada_Entregable.md','Metadatos_Entrega.json','Guia_Hojas.md']:
            shutil.copy2(self.public/name,delivery/name)
        shutil.copy2(zip_path,delivery/zip_path.name)
        summary={'id_ejecucion':self.run,'etapa':'L12 a L14 conciliación final y entrega',
            'ejecutado_en':datetime.now(ZoneInfo('America/Bogota')).isoformat(),'entrada_L11':self.parent['id_ejecucion'],
            'sha256_entrada':self.input_sha,'sha256_reglas':self.rule_sha,'sha256_modulo':self.module_sha,
            'sha256_codigo_notebook':self.code_sha,'sha256_crm_original':self.raw_crm_sha,
            'filas_entrada':5600,'filas_salida':5500,'columnas':18,'entradas_originales_con_destino':5640,
            'aportes_crm_integrados':100,'importes_recuperados':13,'oracle_conservados':500,
            'metricas':self.metrics,'datos_salida':str(self.out.relative_to(self.root)),
            'auditoria':str(self.audit.relative_to(self.root)),'figuras':str(self.fig.relative_to(self.root)),
            'entregable':str((delivery/'BaseUnificada_Entregable.xlsx').relative_to(self.root)),
            'paquete':str((delivery/'BaseUnificada_Entregable.zip').relative_to(self.root)),
            'archivos_entregables':{str(p.relative_to(self.root)):sha(p) for p in sorted(delivery.iterdir()) if p.is_file()},
            'estado':'Preparación técnica completada y entregable listo para revisión externa',
            'limitaciones':['Identidad de eventos y personas entre sistemas no confirmada','Ausencias conservadas',
                           'Calendario orientativo sin validación institucional externa','Sin fecha de actualización de estado']}
        (self.audit/'resumen_ejecucion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (self.root/'reports/limpieza/ultima_entrega.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        return summary

    def verificar_paquete(self,zip_path,public_meta):
        for relative,item in public_meta['archivos'].items():assert sha(self.public/relative)==item['sha256'],relative
        bad_terms=['BU000','BU001','/mnt/','C:/Users','Codex','ChatGPT','L12','L11','notebook','el usuario','porfa']
        for path in self.public.rglob('*'):
            if path.suffix.lower() in ['.md','.json','.csv','.jsonl']:
                content=path.read_text(encoding='utf-8-sig')
                assert not any(term.casefold() in content.casefold() for term in bad_terms),path
                assert ';' not in content,('Punto y coma en archivo de entrega',path)
        book=load_workbook(self.public/'BaseUnificada_Entregable.xlsx',read_only=True,data_only=True)
        for sheet in book:
            for row in sheet.values:
                for value in row:
                    if isinstance(value,str):
                        assert not any(term.casefold() in value.casefold() for term in bad_terms),(sheet.title,value)
                        assert ';' not in value,('Punto y coma en celda',sheet.title,value)
        book.close()
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            for path in self.public.rglob('*'):
                if path.is_file():
                    entry='BaseUnificada_Entregable/'+str(path.relative_to(self.public))
                    assert hashlib.sha256(archive.read(entry)).hexdigest()==sha(path)
        self.write('control_paquete_externo.csv',[{'control':'Sin notas personales ni rutas locales','correcto':True},
            {'control':'Huellas de archivos coinciden con metadatos','correcto':True},
            {'control':'Archivo ZIP íntegro y contenido verificado','correcto':True},
            {'control':'Textos y listas sin punto y coma','correcto':True}])
