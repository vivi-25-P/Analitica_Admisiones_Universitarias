"""Convierte resultados calculados en respuestas, indicadores y decisiones revisables."""

from pathlib import Path

import pandas as pd

from .analisis_administrativo import fmt, sha


def generar_conocimiento(analysis):
    d = analysis.df
    n = len(d)
    mat = d.matriculado.eq(1)
    docs_missing = d.documentos_completos.isin(['No','Pendiente'])
    no_advisor = d.asesor.eq('Sin asignar')
    pending = d.estado_proceso.eq('Documentación pendiente')
    retired = d.estado_proceso.eq('Retirado')
    pending_or_retired = pending | retired
    diagnostics = []
    for variable, mask, labels in [
        ('Documentación',docs_missing,('No o Pendiente','Sí')),
        ('Asignación de asesor',no_advisor,('Sin asignar','Con asesor registrado'))]:
        for condition, label in [(mask,labels[0]),(~mask,labels[1])]:
            group = d[condition]
            diagnostics.append({'variable':variable,'grupo':label,'registros':len(group),
                'documentacion_pendiente':int(pending.loc[group.index].sum()),
                'retirado':int(retired.loc[group.index].sum()),
                'pendiente_o_retirado':int(pending_or_retired.loc[group.index].sum()),
                'proporcion_pendiente_o_retirado_pct':pending_or_retired.loc[group.index].mean()*100})
    comparison = analysis.save('contraste_hipotesis_documentacion_asesor',pd.DataFrame(diagnostics))

    # Cada indicador define el ámbito y no confunde una foto de estados con una transición.
    indicators = []
    def rate(code,name,kind,numerator,denominator,formula,owner,interpretation,trigger):
        indicators.append({'codigo':code,'indicador':name,'clasificacion':kind,
            'numerador':int(numerator),'denominador':int(denominator),
            'valor':numerator/denominator*100,'unidad':'%', 'formula':formula,
            'ambito':'Base integrada o grupo filtrado, salvo indicación explícita',
            'responsable_propuesto':owner,'lectura':interpretation,
            'accion_de_seguimiento':trigger,'meta':'Por acordar con la institución',
            'frecuencia_propuesta':'En cada carga validada y por periodo de ingreso',
            'estado':'Línea de referencia calculada. Meta y responsabilidad sin aprobar'})
    rate('K01','Proporción observada con estado Matriculado','Resultado registrado',mat.sum(),n,
         'Registros Matriculado / registros del mismo ámbito * 100','Coordinación de admisiones',
         'No es conversión definitiva de personas o solicitudes independientes',
         'Comparar con la línea de referencia del mismo periodo y cobertura antes de actuar')
    rate('K02','Cobertura de asignación','Operativo',(~no_advisor).sum(),n,
         'Registros con asesor informado distinto de Sin asignar / registros * 100',
         'Coordinación de admisiones','Asignación registrada, no atención efectiva comprobada',
         'Revisar la cola Sin asignar y comprobar responsable, fecha y siguiente acción')
    rate('K03','Documentación declarada completa','Operativo',d.documentos_completos.eq('Sí').sum(),n,
         'Registros con documentos Sí / registros * 100','Gestión documental',
         'No acredita verificación documental externa','Revisar por programa, periodo y estado')
    rate('K04','Matriculado con documentación No o Pendiente','Control de coherencia',
         (mat & docs_missing).sum(),mat.sum(),
         'Matriculado con documentos No o Pendiente / registros Matriculado * 100',
         'Admisiones y gestión documental','Situación por validar, no incumplimiento confirmado',
         'Comprobar reglas de matrícula y actualización del registro antes de corregir')
    rate('K05','Estado Documentación pendiente con documentos Sí','Control de coherencia',
         (pending & d.documentos_completos.eq('Sí')).sum(),pending.sum(),
         'Documentación pendiente con documentos Sí / registros Documentación pendiente * 100',
         'Admisiones y gestión documental','Puede reflejar reglas o momentos de actualización distintos',
         'Revisar los casos y registrar la explicación o corrección respaldada')
    rate('K06','Proporción observada de estado Retirado','Resultado registrado',retired.sum(),n,
         'Registros Retirado / registros * 100','Coordinación de admisiones',
         'No es tasa de abandono de una cohorte ni identifica la etapa del retiro',
         'Registrar fecha y motivo de retiro para mejorar el seguimiento futuro')
    rate('K07','Disponibilidad de correo','Calidad de contacto',d.correo.notna().sum(),n,
         'Registros con correo informado / registros * 100','Gestión de datos',
         'No es tasa de contacto exitoso o correo entregable','Validar estructura y recopilar contacto faltante con evidencia')
    rate('K08','Cobertura de puntaje','Calidad analítica',d.puntaje_admision.notna().sum(),n,
         'Puntajes informados / registros * 100','Admisiones',
         'Mostrar esta cobertura al comparar puntajes','Distinguir prueba pendiente de puntaje no registrado')
    rate('K09','Cobertura de importe','Calidad económica',d.valor_matricula_cop.notna().sum(),n,
         'Importes informados / registros * 100','Admisiones y área financiera',
         'Importe registrado, no pago o ingreso recibido','Validar tarifas y conceptos antes de estimar recaudo')
    principal = d[d.fuente_origen.eq('Principal') & d.aspirante_id.notna()]
    codes = principal.groupby('aspirante_id').size()
    rate('K10','Códigos principales con varias solicitudes','Contexto de identidad',codes.gt(1).sum(),len(codes),
         'Códigos principales con varias solicitudes / códigos principales informados * 100',
         'Gestión de datos','No es retención, recompra o duplicación confirmada',
         'Separar volumen de solicitudes y códigos, conservando los intereses por programa y periodo')
    indicators[-1]['ambito']='Solo códigos informados de la fuente Principal'
    registry = analysis.save('cuadro_indicadores_negocio',pd.DataFrame(indicators))
    time_values = d.loc[d.intervalo_dias_apto_reglas_aplicadas.eq(True),'dias_solicitud_matricula']
    analysis.save('indicadores_tiempo',pd.DataFrame([{
        'indicador':'Días entre solicitud y matrícula','mediana_dias':time_values.median(),
        'percentil_90_dias':time_values.quantile(.9),'intervalos_aptos':len(time_values),
        'ambito':'Solo registros con las dos fechas y controles temporales aptos',
        'limite':'No mide tiempo de primera atención o permanencia por etapa',
        'meta':'Por acordar, sin tratar esta mediana como un plazo institucional'}]))
    unavailable = pd.DataFrame([
        ['Conversión definitiva a matrícula','Falta validar unidad única, matrícula efectiva y ventana de seguimiento',
         'Proporción observada Matriculado disponible como indicador distinto'],
        ['Costo por solicitud o adquisición','Faltan inversión atribuible y unidad de adquisición validada',
         'No se divide un gasto supuesto por los 5.500 registros'],
        ['ROI','Faltan ingresos y costos atribuibles, incluido el costo relevante del servicio',
         'No calcular con importes de matrícula como si fueran pagos'],
        ['ROAS','Faltan inversión publicitaria e ingresos atribuibles a campañas',
         'No se calcula una rentabilidad estimada para completar el dashboard'],
        ['Cumplimiento de primera atención','Faltan fecha de asignación, contacto y plazo acordado',
         'La asignación registrada no prueba atención ni cumplimiento de un SLA'],
        ['Conversión entre etapas','Falta historial de eventos con fechas y unidad consistente',
         'Los estados actuales no forman un embudo de transiciones'],
    ],columns=['indicador','por_que_no_se_calcula','tratamiento'])
    analysis.save('indicadores_no_calculables',unavailable)

    channels = analysis.tables['canales_comparables']
    brute_support = channels.proporcion_bruta_soporte_pct.max()-channels.proporcion_bruta_soporte_pct.min()
    adjusted = channels.proporcion_estandarizada_descriptiva_pct.max()-channels.proporcion_estandarizada_descriptiva_pct.min()
    advisor_no = comparison[comparison.grupo.eq('Sin asignar')].iloc[0]
    advisor_yes = comparison[comparison.grupo.eq('Con asesor registrado')].iloc[0]
    docs_no = comparison[comparison.grupo.eq('No o Pendiente')].iloc[0]
    docs_yes = comparison[comparison.grupo.eq('Sí')].iloc[0]
    responses = pd.DataFrame([
        ['General','Distribución por programa, modalidad y canal, y estados',
         'Respondida para registros disponibles',
         'Derecho y Data Analytics reúnen 44,53 %. Presencial y Virtual tienen participaciones cercanas. Matriculado representa 21,44 %.',
         'Priorizar seguimiento y comparar la oferta con capacidad disponible',
         'No equivale a demanda total del mercado o personas únicas'],
        ['H1','La participación y proporción de matrícula por programa pueden cambiar al depurar y unificar',
         'Comparación descriptiva completada. Conversión definitiva sin confirmar',
         'Sobre la misma fuente, Data Analytics pasa de 22,5397 % a 22,5400 % y Derecho de 22,2619 % a 22,2600 %. La concentración ya existía. El cambio de orden en el conjunto final ocurre al incorporar Oracle.',
         'Mantener el foco de atención en ambos programas sin atribuir el volumen a una expansión del mercado',
         'Las categorías recibidas fragmentaban el conteo, pero no creaban nuevas solicitudes al agruparse'],
        ['H2','Las diferencias entre canales podrían relacionarse con su composición de oferta y periodo',
         'Comparación ajustada descriptiva completada. Causalidad sin confirmar',
         f'En los mismos grupos comparables, la amplitud entre canales baja de {fmt(brute_support,2)} a {fmt(adjusted,2)} puntos. Las diferencias no desaparecen.',
         'Evaluar canales con igual oferta, calendario y seguimiento antes de cambiar presupuesto',
         'Muchas celdas son pequeñas. No demuestra eficacia o rentabilidad'],
        ['H3','Documentación incompleta y ausencia de asesor podrían asociarse con más pendientes o retirados',
         'La comparación bruta no respalda una conclusión general',
         f'Pendiente o Retirado: {fmt(docs_no.proporcion_pendiente_o_retirado_pct,2)} % con documentos No o Pendiente y {fmt(docs_yes.proporcion_pendiente_o_retirado_pct,2)} % con Sí. Sin asignar: {fmt(advisor_no.proporcion_pendiente_o_retirado_pct,2)} % frente a {fmt(advisor_yes.proporcion_pendiente_o_retirado_pct,2)} % con asesor.',
         'Revisar coherencia y actualización. No responsabilizar al asesor ni inferir que documentos incompletos favorecen matrícula',
         'No es rechazo estadístico o prueba de ausencia de asociación. Los cruces detallados y fechas conservan límites'],
        ['Mercado','Qué combinaciones merecen explorar captación o seguimiento',
         'Lista de oportunidades priorizadas para revisión',
         'Se distinguen segmentos con proporción observada alta y segmentos con volumen alto y seguimiento por revisar.',
         'Pilotos acotados y revisión de estados, con medición de nuevos resultados',
         'No se confirman nichos desatendidos, tamaño de mercado o beneficios futuros'],
    ],columns=['referencia','pregunta_o_hipotesis','estado_de_respuesta','conocimiento_obtenido','uso_administrativo','limite'])
    analysis.save('respuestas_preguntas_hipotesis',responses)

    candidates = [
        ('Cali','Administración de Empresas','Virtual','Captación piloto'),
        ('Bogotá','Administración de Empresas','Virtual','Captación piloto'),
        ('Medellín','Contaduría Pública','Presencial','Exploración con tamaño reducido'),
        ('Bogotá','Derecho','Virtual','Revisión de seguimiento'),
        ('Popayán','Derecho','Presencial','Revisión de seguimiento'),
        ('Popayán','Derecho','Virtual','Contraste dentro de ciudad y programa'),
    ]
    segments = analysis.tables['segmentos_completos']
    sensitivity = analysis.tables['sensibilidad_49_pares']
    sensitivity = sensitivity[sensitivity.dimension.eq('ciudad_residencia, programa, modalidad')]
    opportunities = []
    for city,program,mode,reason in candidates:
        match = segments[(segments.ciudad_residencia==city)&(segments.programa==program)&(segments.modalidad==mode)]
        assert len(match)==1
        row = match.iloc[0]
        sensitivity_row = sensitivity[(sensitivity.ciudad_residencia==city)&(sensitivity.programa==program)&(sensitivity.modalidad==mode)].iloc[0]
        opportunities.append({'ciudad':city,'programa':program,'modalidad':mode,
            'tipo_oportunidad':reason,'registros':int(row.registros),'matriculados':int(row.matriculados),
            'proporcion_matriculado_pct':row.proporcion_matriculado_pct,
            'cambio_pp_escenario_49_pares':sensitivity_row.diferencia_matriculado_pp,
            'accion':'Validar capacidad y probar captación con seguimiento comparable' if 'piloto' in reason
                     else 'Revisar composición por periodo, fuente y estados antes de intervenir',
            'criterio':'Selección exploratoria documentada, no ranking de eficacia o rentabilidad',
            'meta':'Definir con capacidad, costo y resultado de una prueba',
            'advertencia':'Porcentaje observado con muestra de registros, no conversión definitiva'})
    analysis.save('oportunidades_negocio',pd.DataFrame(opportunities))
    decision_rows = [
        ['D1','Revisar coherencia documental','Acción operativa de revisión',
         '514 Matriculado con documentos No o Pendiente y 393 Documentación pendiente con Sí',
         'Validar reglas y fechas de actualización antes de corregir registros','Admisiones y gestión documental','K04 y K05'],
        ['D2','Comprobar cobertura real de asignación','Acción operativa de revisión',
         '1.101 registros Sin asignar. La diferencia bruta en Pendiente o Retirado es solo de 0,50 puntos',
         'No atribuir pérdidas al asesor. Comprobar responsable, contacto y siguiente acción','Coordinación de admisiones','K02'],
        ['D3','Probar Administración virtual en Cali y Bogotá','Piloto comercial propuesto',
         '19 de 44 y 22 de 66 registros Matriculado respectivamente',
         'Validar capacidad, registrar campaña y comparar cohortes con mismo seguimiento','Mercadeo y coordinación académica','K01 y costo de captación cuando esté disponible'],
        ['D4','Revisar Derecho virtual en Bogotá y presencial en Popayán','Investigación operativa propuesta',
         '21 de 133 y 13 de 101 registros Matriculado respectivamente',
         'Examinar estados, periodos y fuentes. No asumir solicitudes perdidas o modalidad menos eficaz','Coordinación de admisiones','K01 dentro del segmento y periodo'],
        ['D5','Evaluar canales antes de redistribuir presupuesto','Experimento propuesto',
         'Diferencias residuales de 3,20 puntos tras comparación de composición',
         'Registrar inversión y resultado atribuible. No recortar por un porcentaje bruto','Mercadeo y área financiera','Costo y retorno pendientes de información'],
        ['D6','Definir identidad de solicitud y registro de eventos','Mejora de medición propuesta',
         'Recurrencia de códigos y correspondencias Oracle no confirmadas',
         'Conservar la evidencia actual y definir prospectivamente claves, fechas y resultados','Gestión de datos y admisiones','K10 y conversión definitiva cuando sea medible'],
    ]
    analysis.save('decisiones_negocio',pd.DataFrame(decision_rows,columns=[
        'codigo','decision_propuesta','tipo','evidencia','condicion_para_ejecutar','responsable_propuesto','indicador_de_evaluacion']))

    old_text = (analysis.out/'seccion_informe_drive.md').read_text()
    # Una sola redacción vigente. La síntesis añade respuestas y decisiones al análisis existente.
    prefix = '''# Análisis de admisiones y oportunidades de mejora

El análisis transforma la información disponible en prioridades de atención, oportunidades de captación y criterios para evaluar decisiones. Se distinguen hechos observados, explicaciones por revisar y acciones que pueden comprobarse mediante seguimiento. Las metas y los responsables son propuestas para acordar con la institución.

'''
    old_text = old_text.split('\n',1)[1].lstrip()
    executive = f'''
## Respuesta a las preguntas e hipótesis

### Interés y matrícula por programa

La concentración de interés en Derecho y Data Analytics ya estaba presente en la fuente principal. Agrupar sus distintas escrituras hizo visible ese interés. La conciliación de repeticiones cambió muy poco sus participaciones dentro de la misma fuente. La incorporación de Oracle modificó la composición y el orden de los programas. Por tanto, no debe atribuirse ese cambio a crecimiento institucional ni a un aumento de demanda provocado por la limpieza.

### Diferencias entre canales

Las diferencias entre canales se mantienen al comparar una misma composición de programas, modalidades y periodos. En los grupos comunes, la amplitud baja de {fmt(brute_support,2)} a {fmt(adjusted,2)} puntos porcentuales. Esto permite plantear pruebas comerciales con oferta equivalente, pero no decidir qué canal es más rentable con la información actual.

### Documentación, asesor y estado

La hipótesis de que la documentación incompleta se relaciona con más registros pendientes o retirados no se observa de forma general en la comparación bruta: esos estados representan el {fmt(docs_no.proporcion_pendiente_o_retirado_pct,2)} % con documentos No o Pendiente y el {fmt(docs_yes.proporcion_pendiente_o_retirado_pct,2)} % con documentos Sí. La diferencia entre Sin asignar y Con asesor es de aproximadamente {fmt(advisor_no.proporcion_pendiente_o_retirado_pct-advisor_yes.proporcion_pendiente_o_retirado_pct,2)} puntos. Estas cifras orientan a revisar la calidad y actualización del seguimiento, sin culpar a asesores ni afirmar que los documentos incompletos favorecen la matrícula.

## Oportunidades comerciales y de seguimiento

Administración virtual en Cali presenta 19 registros Matriculado de 44, el 43,18 %, y en Bogotá 22 de 66, el 33,33 %. Son combinaciones para evaluar campañas piloto, con capacidad disponible y seguimiento comparable. Su tamaño impide tratarlas como ventajas comerciales confirmadas. Contaduría presencial en Medellín presenta 13 de 31, el 41,94 %, y requiere especial prudencia por su tamaño reducido.

Derecho virtual en Bogotá combina 133 registros con 21 Matriculado, el 15,79 %. Derecho presencial en Popayán presenta 13 de 101, el 12,87 %, mientras Derecho virtual en la misma ciudad reúne 29 de 106, el 27,36 %. Estas diferencias justifican revisar la distribución de estados, periodos y fuentes antes de aumentar captación o atribuir un problema a la modalidad. No permiten declarar perdidas las solicitudes que todavía no figuran Matriculado.

## Indicadores para gestionar el proceso

La línea de referencia incluye 21,44 % de registros Matriculado, 79,98 % con asesor registrado y 59,73 % con documentos Sí. La coherencia documental requiere revisar el 43,60 % de Matriculado con documentos No o Pendiente y el 61,60 % de Documentación pendiente que indica documentos Sí. Los intervalos aptos presentan mediana de {fmt(time_values.median())} días entre solicitud y matrícula, sin representar tiempos de primera atención o permanencia por etapa.

Cada indicador debe mostrarse con su numerador, denominador, periodo y cobertura. Sus metas deben acordarse con la institución. El retorno de inversión, el retorno publicitario y el costo de adquisición quedan pendientes de gastos e ingresos atribuibles. No se sustituyen esos datos por importes de matrícula registrados. La conversión definitiva también requiere validar unidad única, resultado y ventana de seguimiento.

## Decisiones que estos resultados permiten preparar

Se propone comenzar por revisar los casos documentales y la asignación efectiva. En captación, se propone una prueba acotada de Administración virtual en Cali y Bogotá y una revisión del seguimiento de Derecho en las combinaciones señaladas. Antes de redistribuir presupuesto por canal, debe registrarse inversión y resultado atribuible. Cada acción debe tener responsable acordado, plazo, línea de referencia y revisión posterior. Estas son decisiones propuestas a partir de evidencia, no acciones institucionales ya ejecutadas ni beneficios garantizados.
'''
    intro = '\n\n'.join(old_text.split('\n\n')[:3])
    executive = executive.replace(
        'Las diferencias entre canales se mantienen al comparar una misma composición',
        '[Insertar aquí el gráfico 02_canales_comparables.png.]\n\nLas diferencias entre canales se mantienen al comparar una misma composición')
    executive = executive.replace(
        '## Oportunidades comerciales y de seguimiento',
        '[Insertar aquí el gráfico 03_documentacion_estados.png.]\n\n## Oportunidades comerciales y de seguimiento')
    (analysis.out/'seccion_informe_drive.md').write_text(prefix+intro+'\n'+executive,encoding='utf8')
    summary = f'''# Síntesis de inteligencia de negocios

## Preguntas e hipótesis

{analysis.table_markdown(responses)}

## Cuadro de indicadores

{analysis.table_markdown(registry[['codigo','indicador','numerador','denominador','valor','unidad']])}

Los indicadores con su fórmula, responsable propuesto, interpretación, ámbito, frecuencia y meta pendiente están en cuadro_indicadores_negocio.csv.
La mediana temporal se encuentra en indicadores_tiempo.csv y los indicadores todavía no medibles en indicadores_no_calculables.csv.
La línea de referencia describe la entrega, no establece un objetivo institucional aprobado ni una serie de evolución.

## Oportunidades y decisiones

{analysis.table_markdown(analysis.tables['oportunidades_negocio'])}

{analysis.table_markdown(analysis.tables['decisiones_negocio'])}

La proporción Matriculado es un indicador de estado observado, no una conversión definitiva.
La ausencia de una asociación bruta clara no demuestra que dos grupos sean equivalentes.
La selección comercial es exploratoria y depende de capacidad y de una prueba futura con seguimiento e inversión registrados.
Referencia conceptual para retorno económico: [Google Ads, medición del ROI](https://support.google.com/google-ads/answer/1722066?hl=es).

## Entrega y dashboard

La redacción administrativa vigente permanece en seccion_informe_drive.md. Debe incorporarse después de limpieza y antes de las preguntas futuras, actualizando estas últimas según las respuestas actuales.
Power BI mostrará una portada ejecutiva con indicadores, respuestas y decisiones propuestas, seguida de captación, seguimiento y calidad.
Los objetivos y semáforos de cumplimiento no se publicarán como aprobados mientras la institución no defina las metas.
El archivo de Power BI y la incorporación al documento de Drive siguen pendientes.
'''
    (analysis.out/'sintesis_inteligencia_negocios.md').write_text(summary,encoding='utf8')
    guide = analysis.out/'guia_insercion_y_figuras.md'
    guide.write_text(guide.read_text()+'''

## Respuestas y conocimiento de negocio

La sección vigente ahora se titula Análisis de admisiones y oportunidades de mejora. Además de los resultados incorpora las respuestas explícitas a las tres hipótesis, las oportunidades concretas, el cuadro de indicadores y las decisiones propuestas. Mantener estas conclusiones en el cuerpo del informe. Las fichas completas de indicadores y las comparaciones extensas pueden quedar en anexo.

El apartado anterior Preguntas e hipótesis para el análisis posterior debe actualizarse: ya no presentar las tres como si no se hubieran examinado. Referir su respuesta actual y conservar como preguntas futuras las condiciones aún no medibles, como conversión definitiva, rentabilidad y tiempos por etapa.
''',encoding='utf8')
    analysis.inputs[Path(__file__)] = sha(Path(__file__))
    analysis.checks_negocio = {
        'diez_indicadores_con_formulas_y_responsables':len(registry)==10 and registry.formula.notna().all() and registry.responsable_propuesto.notna().all(),
        'porcentajes_negocio_recalculados':bool(registry.valor.sub(registry.numerador/registry.denominador*100).abs().lt(1e-10).all()),
        'pregunta_general_tres_hipotesis_y_mercado':set(responses.referencia)=={'General','H1','H2','H3','Mercado'},
        'oportunidades_reconcilian_y_no_son_conversiones':all(r['matriculados']<=r['registros'] for r in opportunities),
        'metas_no_inventadas':registry.meta.eq('Por acordar con la institución').all(),
    }
    return responses,registry,analysis.tables['oportunidades_negocio'],analysis.tables['decisiones_negocio']
