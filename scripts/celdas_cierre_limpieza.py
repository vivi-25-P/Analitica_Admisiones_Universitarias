"""Celdas de las etapas finales, incorporadas por el constructor del notebook."""


def agregar_cierre(md, code):
    md('''
    ## L05. Revisión del catálogo y de las asignaciones

    Se reproduce la correspondencia por una clave normalizada única desde el catálogo
    guardado. Se verifican facultad, duración y nivel; se conserva la modalidad de la
    solicitud. El nombre del fuzzy histórico fue retirado, por lo que esta comprobación
    demuestra compatibilidad con el catálogo de trabajo y no recupera ese nombre.
    ''')
    code('''
    from analitica_admisiones.cierre_limpieza import CierreLimpieza
    cierre = CierreLimpieza(ROOT, df_tipadas, original, ids_fila, origen_df,
                           alertas_l04_df, resumen_l04, CODE_SHA)
    resultado_l05 = cierre.l05(MANEJO, codigo_integracion)
    display(pd.DataFrame([resultado_l05]))
    ''')
    md('''
    ## L06. Consolidación de repeticiones exactas

    Se aplica la autorización de completar la limpieza del 26 de octubre. Solo se
    consolidan filas de la misma fuente que sean idénticas en las 18 columnas originales
    y tipadas. Se conserva el menor índice BU como representante técnico. El inventario
    de destinos mantiene cada entrada, con sus valores y motivos de ausencia previos.
    ''')
    code('''
    resultado_l06 = cierre.l06()
    display(pd.DataFrame([resultado_l06]))
    ''')
    md('''
    ## L07. Conciliación de fuentes y repeticiones parciales

    Se cruzan los identificadores compartidos de CRM y la principal y se muestran las
    diferencias por atributo. Oracle se compara mediante sondas de 11 y 13 atributos,
    sin cambiar sus códigos. La igualdad incluye ausencias, que no aportan evidencia
    independiente. Los candidatos se conservan hasta confirmar su identidad y precedencia.
    ''')
    code('''
    resultado_l07 = cierre.l07()
    display(pd.DataFrame([resultado_l07]))
    display(pd.read_csv(cierre.audit / 'L07_diferencias_por_par.csv',
                        encoding='utf-8-sig', keep_default_na=False).head(8))
    ''')
    md('''
    ## L08. Coherencia administrativa y valores inusuales

    Se revisan fechas, estados, documentos, identificadores, correo y categorías.
    Los controles numéricos utilizan el criterio intercuartílico inclusivo, por fuente
    para importes. Los valores inusuales no se eliminan. La referencia temporal del
    26 de octubre es una fecha de revisión; requiere confirmar el corte institucional.
    ''')
    code('''
    resultado_l08 = cierre.l08()
    display(pd.DataFrame(list(resultado_l08['alertas_negocio_en_representantes'].items()),
                         columns=['Alerta', 'Casos en representantes']))
    display(pd.read_csv(cierre.audit / 'L08_estadisticas_numericas.csv', encoding='utf-8-sig'))
    ''')
    md('''
    ## L09. Exportación, conciliación y decisiones pendientes

    Cada entrada debe tener un destino. Se exportan 18 columnas de negocio en CSV,
    Excel y JSONL, con auditoría separada y lectura íntegra de los tres archivos.
    La salida se llama BaseUnificada_Revision: permite descripción provisional de
    registros; las solicitudes únicas, conversión y comparación monetaria requieren
    las decisiones de negocio documentadas. No se actualizan tablas de Docker.
    ''')
    code('''
    resultado_cierre = cierre.l09(preserve_empty_text)
    display(pd.DataFrame(cierre.steps))
    display(pd.DataFrame(cierre.decisions)[['id_decision', 'tema', 'filas_salida_en_alcance', 'que_decidir']])
    display(pd.read_csv(cierre.audit / 'L09_controles.csv', encoding='utf-8-sig'))
    display(Markdown((ROOT / 'reports/limpieza/reporte_cierre_limpieza.md').read_text()))
    print('Salida:', resultado_cierre['datos_salida'])
    print('Auditoría:', resultado_cierre['auditoria'])
    ''')
