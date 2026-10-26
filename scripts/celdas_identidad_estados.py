"""Celdas de revisión de estados y unidades de análisis."""


def agregar_identidad(md, code):
    md('''
    ## L11. Estados y conteo por solicitud o aspirante

    El usuario aclaró que Nuevo describe una persona que ingresó y comenzará estudios.
    Se agrupa analíticamente con Admitido, conservando el estado original en auditoría.
    Matriculado permanece separado: todos los matriculados principales tienen fecha
    de matrícula y los Nuevo no la tienen. No se infiere una matrícula formal por esa agrupación.

    Contar solicitudes y contar aspirantes responde preguntas distintas. Se conserva
    la tabla de solicitudes y se crea una vista con una fila por aspirante_id informado.
    No se elige un último estado con la fecha de solicitud, porque no existe fecha de
    actualización de estado. Los 90 casos principales sin ID permanecen aparte.
    ''')
    code('''
    from analitica_admisiones.identidad_estados import IdentidadEstados
    identidad = IdentidadEstados(ROOT, CODE_SHA)
    resumen_personas, comparacion_estados = identidad.revisar()
    display(comparacion_estados)
    display(pd.DataFrame([identidad.metrics]))
    display(pd.DataFrame(identidad.people).head())
    ''')
    code('''
    for figura in identidad.graficar():
        display(Image(filename=str(figura)))
    ''')
    code('''
    resumen_identidad = identidad.exportar(preserve_empty_text)
    df_solicitudes_actual = pd.DataFrame(identidad.main, columns=HEADERS)
    df_aspirantes_actual = pd.DataFrame(identidad.people)
    display(pd.read_csv(identidad.audit / 'controles.csv', encoding='utf-8-sig'))
    texto_identidad = (ROOT / 'reports/limpieza/reporte_estados_personas_y_cierre.md').read_text()
    display(Markdown(texto_identidad.split('## Gráficos actualizados')[0]))
    print('Datos actuales:', resumen_identidad['datos_salida'])
    print('Auditoría y denominadores:', resumen_identidad['auditoria'])
    ''')
