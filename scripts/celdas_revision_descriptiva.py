"""Extensión ejecutable del notebook principal para revisión y parciales."""


def agregar_revision(md, code):
    md('''
    ## L10. Resolver los dos registros parciales

    La revisión continúa desde el cierre L09, conservado como punto de control.
    Se complementan únicamente REG003600 y REG004804: un solo valor informado,
    ausencia en la otra fila y todos los demás atributos iguales. Los dos orígenes
    siguen documentados. No se fusionan otras fuentes ni se imputan importes.
    ''')
    code('''
    from analitica_admisiones.revision_descriptiva import RevisionDescriptiva
    revision = RevisionDescriptiva(ROOT, CODE_SHA)
    display(pd.DataFrame([revision.resolver_parciales()]))
    display(pd.DataFrame(revision.changes))
    ''')
    md('''
    ### Estados, categorías y cruces administrativos

    Nuevo se conserva distinto de Admitido. No existe una equivalencia acreditada
    entre ambas etiquetas. La agrupación en fases es auxiliar y no modifica las
    18 columnas. Las comparaciones institucionales utilizan la fuente principal
    con 5.000 códigos de solicitud distintos; no suman CRM y Oracle como nuevas solicitudes.
    ''')
    code('''
    display(revision.explorar_categorias())
    display(pd.read_csv(revision.audit / 'agrupaciones_estados.csv', encoding='utf-8-sig'))
    ''')
    md('''
    ### Importes por programa, modalidad y periodo

    Se calculan mínimo, máximo, promedio, mediana, valores distintos e información
    faltante. CRM se separa por su concepto económico. La comparación virtual frente
    a presencial no acredita tarifas ni una causa. Se evalúa si existe un importe
    deducible antes de considerar imputaciones.
    ''')
    code('''
    display(revision.explorar_importes())
    display(pd.DataFrame([revision.metrics['importes']]))
    ''')
    md('''
    ### Fechas e identificadores

    Se conservan fechas y códigos informados. El texto vacío y nan de identificadores
    se homologan como ausencia real, con su marcador original en auditoría.
    Los controles auxiliares indican qué
    registros tienen alertas y cuáles pueden entrar en el resumen de intervalos.
    No se convierten fechas ambiguas solo para aumentar coincidencias.
    aspirante_id sirve para revisar solicitudes repetidas y trazabilidad;
    las coincidencias por correo se presentan como candidatos, sin asignación automática.
    ''')
    code('''
    fechas_revision, ids_revision = revision.explorar_fechas_identificadores()
    display(fechas_revision)
    display(ids_revision)
    display(pd.DataFrame([revision.metrics['fechas']]))
    ''')
    md('''
    ### Gráficos de la exploración actual

    Cada figura utiliza la cohorte principal de 5.000 solicitudes y declara su unidad.
    Los intervalos usan solo el subconjunto sin las alertas revisadas.
    El mes final incompleto y los importes sin diligenciar se consideran al interpretar.
    ''')
    code('''
    from IPython.display import Image
    figuras_revision = revision.graficar()
    for figura in figuras_revision:
        display(Image(filename=str(figura)))
    ''')
    md('''
    ### Salidas actuales y controles

    El Excel mantiene el consolidado de 5.600 registros y una hoja Principal_Analisis
    de 5.000 códigos principales distintos. Los controles permanecen separados.
    Estas dos vistas no deben sumarse entre sí. CRM y Oracle aún requieren conciliación.
    ''')
    code('''
    resumen_revision = revision.exportar(preserve_empty_text)
    df_revision = pd.DataFrame(revision.all, columns=HEADERS, index=revision.ids_out, dtype=object)
    df_principal = pd.DataFrame(revision.main, columns=HEADERS, index=revision.main_ids, dtype=object)
    df_revision.index.name = df_principal.index.name = 'id_registro_salida'
    display(df_principal.head())
    display(pd.read_csv(revision.audit / 'controles.csv', encoding='utf-8-sig'))
    texto_revision = (ROOT / 'reports/limpieza/revision_descriptiva_y_parciales.md').read_text()
    display(Markdown(texto_revision.split('## Gráficos')[0]))
    print('Datos actuales:', resumen_revision['datos_salida'])
    print('Tablas, calidad y trazabilidad:', resumen_revision['auditoria'])
    ''')
