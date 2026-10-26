"""Reclasificación semántica documentada y vistas sin doble conteo por aspirante."""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import csv
import json
from zoneinfo import ZoneInfo

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from .cierre_limpieza import sha


def clasificar_aspirante(estados):
    values=set(estados)
    if 'Matriculado' in values: return 'Matrícula registrada en alguna solicitud'
    if 'Admitido' in values: return 'Admitido sin matrícula registrada'
    return 'Otros estados sin admisión o matrícula registrada'


class IdentidadEstados:
    def __init__(self, root, code_sha):
        self.root=Path(root)
        self.parent=json.loads((self.root/'reports/limpieza/ultima_revision_descriptiva.json').read_text())
        self.rule_path=self.root/'config/limpieza/identidad_estados_v1.json'
        self.rules=json.loads(self.rule_path.read_text())
        self.source=self.root/self.parent['datos_salida']/'BaseUnificada_Revision.csv'
        self.input_sha=sha(self.source)
        assert self.input_sha==self.parent['archivos_datos'][self.source.name]
        self.code_sha=code_sha
        self.module_sha=sha(__file__); self.rule_sha=sha(self.rule_path)
        self.run=f"{self.rules['version']}_{self.input_sha[:10]}_{self.rule_sha[:8]}_{self.module_sha[:8]}_{code_sha[:8]}"
        self.audit=self.root/'reports/limpieza/ejecuciones'/self.run
        self.out=self.root/'data/processed/taller_2'/self.run
        self.fig=self.root/'reports/figuras/identidad_estados'/self.run
        for p in [self.audit,self.out,self.fig]: p.mkdir(parents=True,exist_ok=True)
        self.before=list(csv.DictReader(self.source.open(encoding='utf-8-sig')))
        self.headers=list(self.before[0]); assert len(self.before)==5600 and len(self.headers)==18
        self.parent_audit=self.root/self.parent['auditoria']
        destinations=list(csv.DictReader((self.parent_audit/'disposicion_5640_entradas.csv').open(encoding='utf-8-sig')))
        by_position={int(r['fila_salida_csv']):r for r in destinations}
        self.ids=[by_position[p]['id_registro_salida'] for p in range(2,5602)]
        self.origin={r['id_registro_salida']:r['fuente'] for r in destinations}
        self.parent_destinations=destinations
        self.changes=[]
        self.rows=[]
        for ident,original in zip(self.ids,self.before):
            row=dict(original)
            row['estado_proceso']=self.rules['estado_equivalencias'][original['estado_proceso']]
            self.rows.append(row)
            if row['estado_proceso']!=original['estado_proceso']:
                self.changes.append({'id_registro_salida':ident,'fuente':self.origin[ident],
                                     'registro_id':row['registro_id'],'columna':'estado_proceso',
                                     'valor_original':original['estado_proceso'],'valor_consolidado':row['estado_proceso'],
                                     'motivo':'Nuevo agrupado analíticamente como Admitido, según contexto del usuario y sin imputar matrícula'})
        self.main_ids=[i for i in self.ids if self.origin[i]=='Principal']
        self.main=[r for i,r in zip(self.ids,self.rows) if self.origin[i]=='Principal']
        self.original_main=[r for i,r in zip(self.ids,self.before) if self.origin[i]=='Principal']
        self.groups=defaultdict(list)
        self.original_groups=defaultdict(list)
        self.unknown=[]
        for ident,row,original in zip(self.ids,self.rows,self.before):
            if self.origin[ident]!='Principal': continue
            if row['aspirante_id']:
                self.groups[row['aspirante_id']].append((ident,row))
                self.original_groups[row['aspirante_id']].append(original)
            else: self.unknown.append({'id_registro_salida':ident,**row})
        self.people=[]
        for ident,items in sorted(self.groups.items()):
            rows=[r for _,r in items]
            states=sorted({r['estado_proceso'] for r in rows})
            dates=sorted(r['fecha_solicitud'] for r in rows)
            self.people.append({'aspirante_id':ident,'solicitudes':len(rows),
                                'programas_distintos':len({r['programa'] for r in rows if r['programa']}),
                                'periodos_distintos':len({r['periodo_academico'] for r in rows}),
                                'estados_distintos':len(states),'estados_observados':', '.join(states),
                                'clasificacion_analitica':clasificar_aspirante(states),
                                'estado_actual_confirmado':False,
                                'primera_fecha_solicitud_interpretada':dates[0],
                                'ultima_fecha_solicitud_interpretada':dates[-1],
                                'codigos_solicitud':', '.join(sorted(r['registro_id'] for r in rows)),
                                'ids_fila':', '.join(i for i,_ in items)})
        self.metrics={'solicitudes_principales':len(self.main),'aspirante_id_distintos_informados':len(self.people),
                      'solicitudes_sin_aspirante_id':len(self.unknown),
                      'aspirantes_con_varias_solicitudes':sum(len(g)>1 for g in self.groups.values()),
                      'aspirantes_con_varios_estados_originales':sum(len({r['estado_proceso'] for r in g})>1 for g in self.original_groups.values()),
                      'aspirantes_con_varios_estados_consolidados':sum(r['estados_distintos']>1 for r in self.people),
                      'aspirantes_con_varios_programas':sum(r['programas_distintos']>1 for r in self.people),
                      'aspirantes_con_varios_periodos':sum(r['periodos_distintos']>1 for r in self.people),
                      'suma_conteos_aspirantes_por_estado_original':sum(len({r['estado_proceso'] for r in g}) for g in self.original_groups.values()),
                      'suma_conteos_aspirantes_por_estado_consolidado':sum(r['estados_distintos'] for r in self.people),
                      'celdas_estado_reclasificadas':len(self.changes),
                      'filas_eliminadas':0,
                      'clasificacion_excluyente':dict(Counter(r['clasificacion_analitica'] for r in self.people)),
                      'estados_solicitudes_principales':dict(Counter(r['estado_proceso'] for r in self.main))}

    def write(self, name, rows, headers=None, directory=None):
        rows=list(rows)
        with ((directory or self.audit)/name).open('w',encoding='utf-8-sig',newline='') as handle:
            w=csv.DictWriter(handle,fieldnames=headers or (list(rows[0]) if rows else ['sin_casos']),lineterminator='\n')
            w.writeheader();w.writerows(rows)

    def revisar(self):
        self.write('cambios_estados_por_fila.csv',self.changes)
        self.write('aspirantes_principales.csv',self.people,directory=self.out)
        self.write('solicitudes_sin_aspirante_id.csv',self.unknown,directory=self.out)
        repetitions=[]
        for columns,name in [(['aspirante_id','programa','periodo_academico'],'aspirante_programa_periodo'),
                             (['aspirante_id','programa','modalidad','periodo_academico'],'aspirante_programa_modalidad_periodo')]:
            groups=defaultdict(list)
            for r in self.original_main:
                if r['aspirante_id']:groups[tuple(r[c] for c in columns)].append(r)
            repeated=[(key,rows) for key,rows in groups.items() if len(rows)>1]
            for key,rows in repeated:
                repetitions.append({'criterio':name,'aspirante_id':key[0],
                                    'programa':rows[0]['programa'],'periodo_academico':rows[0]['periodo_academico'],
                                    'modalidad':rows[0]['modalidad'] if 'modalidad' in columns else 'varias posibles',
                                    'solicitudes':len(rows),'estados_originales':', '.join(sorted({r['estado_proceso'] for r in rows})),
                                    'codigos_solicitud':', '.join(sorted(r['registro_id'] for r in rows)),
                                    'accion':'conservar solicitudes; no hay prueba de historial de una misma solicitud'})
            self.metrics[name]={'grupos_repetidos':len(repeated),'solicitudes_en_grupos':sum(len(r) for _,r in repeated),
                                'grupos_con_varios_estados':sum(len({r['estado_proceso'] for r in rows})>1 for _,rows in repeated)}
        self.write('grupos_para_revisar_historial.csv',repetitions)
        comparisons=[]
        for version,rows in [('Original',self.original_main),('Consolidado',self.main)]:
            for state,count in Counter(r['estado_proceso'] for r in rows).items():
                people={r['aspirante_id'] for r in rows if r['estado_proceso']==state and r['aspirante_id']}
                comparisons.append({'version':version,'estado':state,'solicitudes':count,
                                    'porcentaje_solicitudes':round(100*count/len(rows),2),
                                    'aspirantes_distintos_con_ese_estado':len(people),
                                    'denominador_aspirantes_informados':len(self.people),
                                    'conteos_por_estado_no_aditivos':True})
        self.write('comparacion_solicitudes_aspirantes_estados.csv',comparisons)
        definitions=[
            {'indicador':'Solicitudes principales','unidad':'solicitud','regla':'COUNT DISTINCT registro_id en Principal','denominador':5000,'precaucion':'No sumar CRM y Oracle como solicitudes nuevas'},
            {'indicador':'Aspirantes identificados','unidad':'código de aspirante informado','regla':'COUNT DISTINCT aspirante_id no ausente en Principal','denominador':len(self.people),'precaucion':'90 solicitudes sin ID fuera del conteo de personas; no asumir 90 personas'},
            {'indicador':'Distribución excluyente por aspirante','unidad':'código de aspirante informado','regla':'Una clasificación por código: alguna matrícula registrada, luego admitido sin matrícula, luego otros','denominador':len(self.people),'precaucion':'No representa estado actual; considera cualquier solicitud disponible'},
            {'indicador':'Aspirantes por programa, canal o estado','unidad':'código de aspirante dentro de grupo','regla':'COUNT DISTINCT aspirante_id en cada grupo','denominador':len(self.people),'precaucion':'Un código puede aparecer en varios grupos; no sumar como personas únicas'},
            {'indicador':'Admitido consolidado','unidad':'solicitud o aspirante según denominador explícito','regla':'Estado original Nuevo o Admitido, según criterio analítico documentado','denominador':'declarar por indicador','precaucion':'No acredita fecha de matrícula, pago o matrícula formal en Nuevo'}]
        self.write('diccionario_indicadores_y_denominadores.csv',definitions)
        return pd.DataFrame([self.metrics]),pd.DataFrame(comparisons)

    def graficar(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import textwrap
        original=Counter(r['estado_proceso'] for r in self.original_main)
        consolidated=Counter(r['estado_proceso'] for r in self.main)
        states=['Nuevo','Admitido','Matriculado','Inscrito','Documentación pendiente','No admitido','Retirado']
        fig,ax=plt.subplots(figsize=(11,5))
        y=list(range(len(states)))
        ax.barh([v-.2 for v in y],[original[s] for s in states],height=.38,label='Estado recibido',color='#89A9BC')
        bars=ax.barh([v+.2 for v in y],[consolidated[s] for s in states],height=.38,label='Estado analítico consolidado',color='#226C95')
        ax.bar_label(bars,padding=3)
        ax.set_yticks(y,states);ax.invert_yaxis();ax.set_xlabel('Solicitudes principales, n = 5.000')
        ax.set_title('Nuevo se agrupa con Admitido; Matriculado permanece separado')
        ax.legend(loc='lower right');fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(self.fig/f'01_estados_consolidados.{ext}',bbox_inches='tight')
        plt.close(fig)
        counts=Counter(r['clasificacion_analitica'] for r in self.people)
        names=self.rules['clasificacion_persona']
        fig,ax=plt.subplots(figsize=(11,5.3));bars=ax.barh([textwrap.fill(s,36) for s in names],[counts[s] for s in names],color=['#226C95','#67A6A1','#B8BFCA'])
        ax.bar_label(bars,labels=[f'{counts[s]:,} ({100*counts[s]/len(self.people):.1f} %)' for s in names],padding=4)
        ax.set_xlim(0,max(counts.values())*1.27);ax.invert_yaxis()
        ax.set_xlabel('Códigos de aspirante distintos informados, n = 2.924')
        ax.set_title('Una clasificación por aspirante según sus solicitudes disponibles')
        ax.text(0,-.25,'No representa estado actual. Las 90 solicitudes sin ID no se incluyen como personas.',transform=ax.transAxes,fontsize=9)
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(self.fig/f'02_aspirantes_sin_doble_conteo.{ext}',bbox_inches='tight')
        plt.close(fig)
        return [self.fig/'01_estados_consolidados.png',self.fig/'02_aspirantes_sin_doble_conteo.png']

    def exportar(self,preserve_empty_text):
        from decimal import Decimal
        from .revision_descriptiva import RevisionDescriptiva
        from .cierre_limpieza import json_literal
        def typed(row):
            return {c:RevisionDescriptiva.restore(None if v=='' else v,c) for c,v in row.items()}
        typed_all=[typed(r) for r in self.rows]
        typed_main=[typed(r) for r in self.main]
        csv_path=self.out/'BaseUnificada_Revision.csv'
        main_path=self.out/'Principal_Analisis.csv'
        json_path=self.out/'BaseUnificada_Revision.jsonl'
        excel_path=self.out/'BaseUnificada_Revision.xlsx'
        self.write(csv_path.name,self.rows,headers=self.headers,directory=self.out)
        self.write(main_path.name,self.main,headers=self.headers,directory=self.out)
        with json_path.open('w',encoding='utf8') as handle:
            for row in typed_all: handle.write('{'+', '.join(json.dumps(c)+': '+json_literal(row[c]) for c in self.headers)+'}\n')
        book=Workbook();book.remove(book.active)
        for title,data in [('BaseUnificada_Revision',typed_all),('Principal_Analisis',typed_main)]:
            ws=book.create_sheet(title);ws.append(self.headers)
            for row in data:ws.append([row[c] for c in self.headers])
            for j,c in enumerate(self.headers,1):
                fmt='yyyy-mm-dd' if c.startswith('fecha_') else '"COP" #,##0.00' if c=='valor_matricula_cop' else '0.00' if c=='puntaje_admision' else '0' if c in ['periodo_academico','duracion_semestres'] else '@'
                for i in range(2,len(data)+2):ws.cell(i,j).number_format=fmt
                ws.column_dimensions[get_column_letter(j)].width=42 if c=='programa' else 24
            table=Table(displayName=title,ref=f'A1:R{len(data)+1}')
            table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium9',showRowStripes=True)
            ws.add_table(table);ws.freeze_panes='A2'
        ws=book.create_sheet('Aspirantes_Principal')
        people_headers=list(self.people[0]);ws.append(people_headers)
        for row in self.people:ws.append([row[c] for c in people_headers])
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        ws=book.create_sheet('Solicitudes_Sin_ID')
        unknown_headers=list(self.unknown[0]);ws.append(unknown_headers)
        for row in self.unknown:ws.append([row[c] for c in unknown_headers])
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        ws=book.create_sheet('Alcance')
        for row in [
            ['Aspecto','Criterio'],['Consolidado','5.600 registros de 3 fuentes; no es un total global de personas o solicitudes nuevas'],
            ['Principal_Analisis','5.000 códigos de solicitud principales distintos'],
            ['Aspirantes_Principal','2.924 códigos de aspirante informados; una fila por código'],
            ['Solicitudes_Sin_ID','90 solicitudes principales sin código; cantidad de personas desconocida'],
            ['Nuevo','Agrupado analíticamente con Admitido según contexto del usuario; original en auditoría'],
            ['Matriculado','Conservado; no se infiere matrícula formal a partir de Nuevo'],
            ['Clasificación por aspirante','Presencia de alguna matrícula, luego admisión sin matrícula, luego otros. No es estado actual'],
            ['Último estado','No determinado: no hay fecha de actualización de estado'],
            ['Auditoría',str(self.audit.relative_to(self.root))]]:ws.append(row)
        book.save(excel_path);book.close()
        preserve_empty_text(excel_path,[tuple(r[c] for c in self.headers) for r in typed_all])
        preserve_empty_text(excel_path,[tuple(r[c] for c in self.headers) for r in typed_main],worksheet_index=2)
        csv_sha=sha(csv_path)
        destinations=[{**r,'sha256_csv_salida':csv_sha} for r in self.parent_destinations]
        self.write('disposicion_5640_entradas.csv',destinations)
        for c in ['programa','modalidad','canal_captacion','estado_proceso','periodo_academico']:
            cases=defaultdict(list)
            for row in self.main:cases[row[c]].append(row)
            self.write(f'frecuencias_{c}_solicitudes_y_aspirantes.csv',[
                {'valor':v,'solicitudes':len(rows),'aspirantes_distintos_informados':len({r['aspirante_id'] for r in rows if r['aspirante_id']}),
                 'solicitudes_sin_id':sum(not r['aspirante_id'] for r in rows),
                 'conteos_aspirantes_entre_grupos_no_aditivos':True} for v,rows in sorted(cases.items())])
        book=load_workbook(excel_path,read_only=True,data_only=True)
        all_read=list(book['BaseUnificada_Revision'].values)
        main_read=list(book['Principal_Analisis'].values)
        people_read=list(book['Aspirantes_Principal'].values)
        unknown_read=list(book['Solicitudes_Sin_ID'].values);book.close()
        # Las cadenas vacías de columnas de texto corresponden a null en la entrada.
        def restored(rows):
            return [{c:RevisionDescriptiva.restore(v,c) for c,v in zip(self.headers,row)} for row in rows[1:]]
        json_read=[{c:RevisionDescriptiva.restore(v,c) for c,v in json.loads(line,parse_float=Decimal).items()} for line in json_path.read_text().splitlines()]
        with csv_path.open(encoding='utf-8-sig',newline='') as handle:csv_read=list(csv.DictReader(handle))
        states_ok=all(a['estado_proceso']==self.rules['estado_equivalencias'][b['estado_proceso']] for a,b in zip(self.rows,self.before))
        other_ok=all(a[c]==b[c] for a,b in zip(self.rows,self.before) for c in self.headers if c!='estado_proceso')
        counts=Counter(r['clasificacion_analitica'] for r in self.people)
        checks=[('5600 registros y 18 columnas conservados',len(self.rows)==5600 and len(self.headers)==18),
                ('Estados conforme a equivalencia documentada',states_ok),('Otros 17 atributos intactos',other_ok),
                ('620 Nuevo reclasificados y sin cambio de Matriculado',len(self.changes)==620 and all(r['valor_original']=='Nuevo' for r in self.changes)),
                ('5000 solicitudes principales distintas',len(self.main)==len({r['registro_id'] for r in self.main})==5000),
                ('2924 aspirantes informados sin duplicados',len(self.people)==len({r['aspirante_id'] for r in self.people})==2924),
                ('90 solicitudes sin ID conservadas aparte',len(self.unknown)==90),
                ('4910 solicitudes enlazadas a aspirantes informados',sum(r['solicitudes'] for r in self.people)+len(self.unknown)==5000),
                ('Clasificación excluyente suma 2924',sum(counts.values())==2924),
                ('5640 entradas con destino',len(destinations)==len({r['id_fila_entrada'] for r in destinations})==5640),
                ('Lectura completa CSV',csv_read==self.rows),('Lectura completa JSONL',json_read==typed_all),
                ('Lectura completa Excel consolidado',restored(all_read)==typed_all),
                ('Lectura completa Excel principal',restored(main_read)==typed_main),
                ('Hoja de aspirantes sin pérdida',list(people_read[0])==people_headers and list(people_read[1:])==[tuple(r[c] for c in people_headers) for r in self.people]),
                ('Solicitudes sin ID exportadas',len(unknown_read)-1==90),
                ('Entrada L10 intacta',sha(self.source)==self.input_sha)]
        self.write('controles.csv',[{'control':k,'correcto':bool(v)} for k,v in checks])
        assert all(v for _,v in checks),[k for k,v in checks if not v]
        self.metrics['controles_correctos']=len(checks)
        files=[csv_path,main_path,json_path,excel_path,self.out/'aspirantes_principales.csv',self.out/'solicitudes_sin_aspirante_id.csv']
        summary={'id_ejecucion':self.run,'etapa':'L11 estados y unidades de análisis',
                 'ejecutado_en':datetime.now(ZoneInfo('America/Bogota')).isoformat(),
                 'entrada_L10':self.parent['id_ejecucion'],'sha256_entrada':self.input_sha,
                 'sha256_modulo':self.module_sha,'sha256_reglas':self.rule_sha,'sha256_codigo_notebook':self.code_sha,
                 'filas_entrada':5600,'filas_salida':5600,'columnas':18,'metricas':self.metrics,
                 'datos_salida':str(self.out.relative_to(self.root)), 'auditoria':str(self.audit.relative_to(self.root)),
                 'figuras':str(self.fig.relative_to(self.root)),'archivos_datos':{p.name:sha(p) for p in files},
                 'estado':'Unidades de análisis separadas y estados agrupados; conciliación entre fuentes pendiente'}
        (self.audit/'resumen_ejecucion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (self.root/'reports/limpieza/ultima_identidad_estados.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        self.report(summary)
        return summary

    def report(self,summary):
        m=self.metrics; n=lambda v:f'{v:,}'.replace(',','.')
        lines=['# Estados, aspirantes y cierre de limpieza','', 'Revisión del 26 de octubre de 2026.','',
               '## Decisión sobre Nuevo','',
               'El usuario aclaró que Nuevo describe a una persona que ya ingresó y comenzará estudios. Para el análisis se adopta Nuevo como Admitido, conservando el estado recibido en la auditoría. En la principal, ninguno de los 560 Nuevo tiene fecha de matrícula, mientras que los 1.079 Matriculado sí la tienen. La ausencia de fecha no demuestra una equivalencia institucional; la agrupación es un criterio de trabajo que incorpora el contexto del usuario. No se infieren pagos ni matrículas formalizadas.',
               '', 'Se mantienen 5.600 registros y 18 columnas. Cambian 620 celdas de estado: 560 principales, nueve CRM y 51 Oracle. Admitido pasa de 1.105 a 1.665 solicitudes principales; Matriculado conserva 1.079. No se elimina una solicitud por reclasificarla.',
               '', '## Riesgo de doble conteo','',
               f"La fuente principal tiene 5.000 códigos de solicitud distintos, {n(m['aspirante_id_distintos_informados'])} códigos de aspirante informados distintos y 90 solicitudes sin código de aspirante. Son unidades distintas. Las gráficas anteriores estaban denominadas como solicitudes; para responder cuántas personas hay debe usarse la vista por aspirante.",
               '', '| Comprobación en la principal | Resultado |', '| :--- | ---: |',
               f"| Códigos con varias solicitudes | {n(m['aspirantes_con_varias_solicitudes'])} |",
               f"| Códigos con varios estados originales | {n(m['aspirantes_con_varios_estados_originales'])} |",
               f"| Códigos con varios estados después de consolidar Nuevo | {n(m['aspirantes_con_varios_estados_consolidados'])} |",
               f"| Códigos presentes en varios programas | {n(m['aspirantes_con_varios_programas'])} |",
               f"| Códigos presentes en varios periodos | {n(m['aspirantes_con_varios_periodos'])} |",
               '',f"Si se suman los aspirantes distintos de cada estado original se obtienen {n(m['suma_conteos_aspirantes_por_estado_original'])} pertenencias a categorías. Tras agrupar Nuevo con Admitido se obtienen {n(m['suma_conteos_aspirantes_por_estado_consolidado'])}. Ninguna suma equivale a los {n(len(self.people))} códigos únicos. Consolidar etiquetas reduce categorías, pero no resuelve por sí solo la repetición de una persona en distintas solicitudes.",
               '', '## Vistas disponibles para analizar sin inflar personas','',
               '| Vista | Filas | Uso |', '| :--- | ---: | :--- |',
               '| BaseUnificada_Revision | 5.600 | Consolidado con las tres fuentes y trazabilidad. No sumar como solicitudes o personas nuevas. |',
               '| Principal_Analisis | 5.000 | Demanda y solicitudes de la fuente principal, una fila por registro_id. |',
               '| Aspirantes_Principal | 2.924 | Una fila por aspirante_id informado; recurrencia, programas y estados observados. |',
               '| Solicitudes_Sin_ID | 90 | Solicitudes cuya persona no puede contarse con certeza. No equivalen a 90 personas ni se agrupan como una sola persona. |',
               '', 'La clasificación por aspirante es excluyente y suma exactamente 2.924: primero quienes tienen alguna solicitud Matriculado, después quienes tienen Admitido y ninguna Matriculado, y finalmente los demás. Describe evidencia en cualquiera de sus solicitudes disponibles, sin afirmar el estado actual ni una secuencia de transiciones.',
               '', '| Clasificación por aspirante | Códigos distintos | Porcentaje de 2.924 |', '| :--- | ---: | ---: |']
        counts=m['clasificacion_excluyente']
        for label in self.rules['clasificacion_persona']:
            count=counts.get(label,0)
            lines.append(f'| {label} | {n(count)} | {100*count/len(self.people):.2f} % |')
        detail=m['aspirante_programa_modalidad_periodo']
        lines += ['', '## Solicitudes repetidas y evolución del estado','',
                  f"Hay {detail['grupos_repetidos']} grupos con el mismo aspirante, programa, modalidad y periodo, que incluyen {detail['solicitudes_en_grupos']} solicitudes. En {detail['grupos_con_varios_estados']} grupos aparecen distintos estados originales. Se exportan para revisión. No hay prueba de que todos sean versiones de una misma solicitud; por eso no se borran por compartir aspirante.",
                  '', 'La base tiene fecha de solicitud y fecha de matrícula, pero no fecha de actualización del estado. Por tanto, no permite elegir con certeza el último estado ni reconstruir una trayectoria completa. Una persona con Matriculado en un programa y Retirado en otro no debe reclasificarse globalmente como si ambos eventos fueran el mismo proceso.',
                  '', '## Resumen del trabajo documentado','',
                  '| Trabajo | Resultado |', '| :--- | :--- |',
                  '| Integración | 5.640 entradas y 18 columnas, con procedencia de principal, CRM y Oracle. |',
                  '| Estandarización | Catálogos, tildes, espacios, tipos, fechas ISO, importes COP y periodos enteros. |',
                  '| Ausencias | Motivos conservados; 94 identificadores no informados homologados a null, incluidos cuatro nan. |',
                  '| Repeticiones exactas | 38 filas adicionales consolidadas con vínculo al representante. |',
                  '| Parciales | REG003600 y REG004804 resueltos: cinco celdas recuperadas y dos filas consolidadas. |',
                  '| Exploración L10 | Siete gráficos y tablas por programa, modalidad, canal, ciudad, estados, importes y fechas. |',
                  '| Estados L11 | Nuevo agrupado como Admitido; Matriculado conservado; 620 originales registrados por celda. |',
                  '| Unidad de análisis L11 | Vistas de solicitudes y aspirantes separadas, con reglas de conteo y 90 solicitudes sin ID aparte. |',
                  '', 'Los puntos de control L09 y L10 se conservan como históricos. El estado vigente de estados y personas está en reports/limpieza/ultima_identidad_estados.json. Las tablas auxiliares no aumentan las 18 columnas de la tabla administrativa.',
                  '', '## Qué falta para cerrar la sesión de limpieza','',
                  '| Prioridad | Acción concreta | Criterio de cierre |', '| :--- | :--- | :--- |',
                  '| 1 | Conciliar los 100 CRM por solicitud y concepto económico. | Confirmar matrícula base como medida, recuperar los 13 importes disponibles y mantener derechos y origen en auditoría. |',
                  '| 2 | Resolver la política Oracle. | Establecer si será fuente de contraste o si sus candidatos se integrarán mediante correspondencias documentadas. No sumar sus 500 códigos como personas nuevas. |',
                  '| 3 | Aplicar reglas temporales a cada indicador. | Conservar fechas y periodos, señalar las alertas y declarar los subconjuntos utilizados; no inventar actualizaciones de estado. |',
                  '| 4 | Cerrar el tratamiento de los 90 casos sin ID. | Mantenerlos aparte o adoptar una regla explícita de recuperación con la evidencia interna; no inventar personas. |',
                  '| 5 | Aprobar los indicadores y congelar la versión. | Totales por unidad, controles de destinos, estados originales auditados y un único resumen vigente para el análisis. |',
                  '', 'No se recomienda completar matrícula por programa o modalidad: las 63 combinaciones de programa, modalidad y periodo de la principal contienen los cinco valores observados. Tampoco eliminar aspirante_id, porque permite este control de recurrencia y conteo.',
                  '', f"Pasaron {m['controles_correctos']} controles de la nueva etapa, con lectura completa de CSV, JSONL y las hojas principales de Excel. Las fechas, importes, identificadores y otros atributos conservan sus valores. No se modificaron fuentes ni tablas Docker.",
                  '', '## Gráficos actualizados','',
                  f'![Estados consolidados](../figuras/identidad_estados/{self.run}/01_estados_consolidados.png)','',
                  f'![Aspirantes sin doble conteo](../figuras/identidad_estados/{self.run}/02_aspirantes_sin_doble_conteo.png)','',
                  '## Documentación y respaldo','',f"Datos: `{summary['datos_salida']}`.",'',f"Auditoría: `{summary['auditoria']}`.",'',
                  'La auditoría contiene cambios de estado, correspondencias de las 5.640 entradas, grupos para revisión de historial, comparación entre solicitudes y aspirantes, frecuencias con ambos conteos y un diccionario de indicadores y denominadores. El notebook principal reproduce todas las etapas. Los conteos por programa, canal, modalidad o estado pueden solaparse entre aspirantes y no deben sumarse como un total de personas.']
        report=self.root/'reports/limpieza/reporte_estados_personas_y_cierre.md'
        report.write_text('\n'.join(lines)+'\n',encoding='utf8')
        docs=[('BITACORA.md','Decisiones y acciones por fecha'),('README.md','Guía de la salida vigente'),
              ('docs/plan_limpieza_datos.md','Secuencia y reglas'),
              ('notebooks/02_limpieza_base_unificada.ipynb','Respaldo ejecutable'),
              ('config/limpieza/identidad_estados_v1.json','Definición de estados y unidades'),
              ('reports/limpieza/ultima_revision_descriptiva.json','Punto de control L10 previo'),
              ('reports/limpieza/ultima_identidad_estados.json','Estado vigente L11'),
              ('reports/limpieza/reporte_estados_personas_y_cierre.md','Reporte de revisión y cierre')]
        self.write('inventario_documentacion_revisada.csv',[{'archivo':p,'contenido':scope,'existe':(self.root/p).is_file()} for p,scope in docs])
        assert all((self.root/p).is_file() for p,_ in docs)
