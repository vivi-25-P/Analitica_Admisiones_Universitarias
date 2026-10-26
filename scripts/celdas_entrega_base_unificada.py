"""Etapas finales de conciliación, análisis integrado y entrega externa."""


def agregar_entrega(md,code):
    md('''
    ## L12. Conciliación CRM y recuperación de importes

    Se integra cada aporte CRM a su solicitud principal por código y 12 atributos.
    Se conserva la matrícula principal cuando coincide con la base CRM y se recupera
    únicamente la ausencia. Derechos y total CRM se mantienen separados en el control
    económico. No se estiman importes por programa o modalidad.
    ''')
    code('''
    from analitica_admisiones.entrega_base_unificada import EntregaBaseUnificada
    entrega = EntregaBaseUnificada(ROOT, CODE_SHA)
    display(entrega.conciliar_crm())
    display(pd.DataFrame(entrega.economics).head())
    ''')
    md('''
    ## L13. Oracle, periodos, fechas e identidad del conjunto integrado

    Se conservan las 500 filas Oracle en la misma tabla principal. Las coincidencias
    se documentan sin afirmar identidad del evento por semejanza. El periodo académico
    permanece como semestre de ingreso; no se recalcula por la fecha de solicitud o
    matrícula. La ventana orientativa no excluye filas. La vista de aspirantes incluye
    los códigos de ambos sistemas y no los presenta como personas globales únicas.
    ''')
    code('''
    display(entrega.revisar_oracle())
    calidad_entrega, identidad_entrega = entrega.calidad_y_aspirantes()
    display(calidad_entrega)
    display(identidad_entrega)
    ''')
    code('''
    display(entrega.describir())
    for figura in entrega.graficar():
        display(Image(filename=str(figura)))
    ''')
    md('''
    ## L14. BaseUnificada Entregable y cierre técnico

    Se exporta un paquete formal para revisión externa, sin notas de conversación
    ni rutas locales. Excel conserva 18 columnas en BaseUnificada y ofrece controles
    de origen, calidad, aspirantes por origen, coincidencias Oracle, conceptos económicos
    y metodología. Se verifica el contenido completo de los formatos y del paquete ZIP.
    ''')
    code('''
    display(entrega.exportar(preserve_empty_text))
    resumen_entrega = entrega.cerrar_paquete()
    df_base_unificada_entregable = pd.DataFrame(entrega.all, columns=HEADERS,
                                               index=entrega.ids_out, dtype=object)
    df_base_unificada_entregable.index.name = 'id_registro_auditoria'
    display(df_base_unificada_entregable.head())
    display(pd.DataFrame(entrega.guia_hojas()))
    display(pd.DataFrame([{'Registros integrados': len(entrega.all), 'Columnas': len(HEADERS),
        'Aportes CRM incorporados': 100, 'Oracle incluidos': 500, 'Importes recuperados': 13,
        'Controles correctos': entrega.metrics['controles_correctos']}]))
    display(Markdown('La última celda valida y exporta el entregable. La similitud entre fuentes es un resultado del cruce ejecutado, no una tarea sin realizar. Las identidades no confirmadas y los valores ausentes permanecen explícitos.'))
    print('Entregable para revisión:', resumen_entrega['entregable'])
    print('Paquete completo:', resumen_entrega['paquete'])
    print('Auditoría:', resumen_entrega['auditoria'])
    ''')
