# Bitácora del proyecto de admisiones

Este documento registra el avance, las decisiones, las comprobaciones y los pendientes. Cada cambio de estructura o tratamiento de datos debe incorporar una entrada con fecha de Bogotá, objetivo, archivos afectados, validación y resultado. Las propuestas se distinguen de los cambios aplicados. No se guardan contraseñas en esta bitácora.

## 17 de octubre de 2026. Antecedentes consolidados

Esta entrada es un resumen retrospectivo del trabajo realizado durante la sesión. No constituye un registro de horas exactas ni un historial de commits.

| Trabajo realizado | Decisión y resultado | Evidencia |
|---|---|---|
| Reconocimiento de archivos | Se identificaron el CSV, la guía del caso y dos presentaciones de teoría. Calidad de datos es la referencia principal. | docs/referencias y docs/teoria |
| Organización del proyecto | Se separaron datos originales, documentación, scripts, consultas y resultados. El contenido de los archivos originales se conservó mediante comprobaciones SHA256. | README.md y docs/referencias/integridad.json |
| Preparación de Python | Se creó el proyecto con uv y Python 3.12. Dependencias y versiones quedaron declaradas y bloqueadas. | pyproject.toml y uv.lock |
| Carga inicial | Se preparó PostgreSQL 17 con Docker Compose. La tabla public.admisiones_original contiene 5.040 filas y 15 columnas TEXT. Se conservan vacíos, espacios, variantes y duplicados. | compose.yaml, docker/init/01_cargar.sql y docker/origen.json |
| Integración con WSL | El primer arranque se realizó desde Windows. Posteriormente se habilitó la integración con Ubuntu. Las sesiones antiguas necesitaron actualizar sus grupos para acceder al socket. | docs/base_datos.md |
| Verificación de carga | Se compararon encabezados y multiplicidades de todas las filas con el CSV. La comprobación no depende del orden de almacenamiento. | src/analitica_admisiones/database.py |
| Perfilamiento | Se calcularon completitud, frecuencias, estadísticas y controles exploratorios. Las alertas no se trataron automáticamente como errores confirmados. | reports/exploracion |
| Repeticiones | Se identificaron 38 pares exactos y dos identificadores con discrepancias. No se eliminaron filas. | reports/exploracion/duplicados_exactos_detalle.csv |
| Gráficos | Se generaron distribuciones originales y figuras alternativas con equivalencias de presentación. El informe exploratorio utiliza las categorías originales. Las equivalencias siguen pendientes de validación para la limpieza. | reports/figuras y scripts de visualización |
| Notebook | Se ejecutaron las 16 celdas de código, con seis figuras incrustadas y 34 verificaciones correctas. Se exportó una vista HTML y tablas de respaldo. | notebooks/01_respaldo_informe_descriptivo.ipynb y reports/01_respaldo_informe_descriptivo.html |
| Criterio del informe | Se distinguen registros, solicitudes únicas, aspirantes y matrículas efectivas. No se presentan conversiones definitivas ni conclusiones causales. | Notebook y documentos de guía |

## 17 de octubre de 2026. Bitácora y preparación del mantenimiento de PostgreSQL

**Objetivo.** Comenzar a documentar los cambios y preparar el trabajo posterior sobre tipos de datos sin perder la referencia del primer informe.

**Cambios aplicados.** Se creó esta bitácora, se agregó un script de respaldo local y se documentó la ruta de preparación de una segunda tabla. Los respaldos se excluyeron del seguimiento de Git mediante .gitignore.

**Archivos afectados.** BITACORA.md, scripts/respaldar_bd.py, docs/plan_preparacion_base.md, docs/base_datos.md, README.md y .gitignore.

**Respaldo generado.** data/backups/admisiones_20261017_134108_581408.dump, con formato personalizado de PostgreSQL. Se generaron también metadatos e índice en archivos vecinos. Su tamaño es de 131.276 bytes.

**SHA256 del respaldo.** 7d6cbc13d0b4ec2c0f46c89b84ae99288e635b5d1730c63e4817b5ba985a4e7d

**Validaciones.** pg_dump finalizó correctamente. La cabecera corresponde al formato PGDMP y pg_restore pudo leer el índice, incluyendo los datos de public.admisiones_original. Docker Compose informó PostgreSQL en ejecución y saludable, con el puerto local 5433 publicado.

**Límite de la comprobación.** Se verificó la legibilidad del archivo y su índice; todavía no se realizó una restauración completa en una base temporal.

**Resultado.** Se dispone de respaldo y documentación para preparar los siguientes cambios. La tabla original no se modificó y todavía no se creó ni cargó una tabla preparada.

## Próximo trabajo

| Paso | Estado | Criterio de cierre |
|---|---|---|
| Probar una restauración aislada del respaldo | Pendiente | Restauración completa y comparación con el origen |
| Definir reglas y excepciones de transformación | Propuesto | Reglas identificadas y decisiones pendientes explícitas |
| Preparar una migración versionada para la segunda tabla | Pendiente | SQL revisable, tipos definidos y trazabilidad del origen |
| Crear y cargar la tabla preparada | Pendiente | Conservar filas iniciales y registrar valores no interpretables |
| Decidir el tratamiento de duplicados | Pendiente de regla de negocio | Separar pares exactos, discrepancias y solicitudes legítimas |
| Comparar antes y después | Pendiente | Conteos, importes, fechas, categorías y excepciones conciliados |

## Plantilla para nuevas entradas

**Fecha y hora de Bogotá:**

**Objetivo:**

**Decisión y motivo:**

**Cambios aplicados y archivos afectados:**

**Validación y resultado:**

**Respaldo o reversión disponible:**

**Limitaciones y pendientes:**


## 17 de octubre de 2026. Tipos de datos sin limpieza

**Instrucción del usuario.** La limpieza se reserva para la siguiente actividad. La etapa actual solo prepara los tipos conservando íntegra la información. El modelo estrella y el ETL para Power BI se analizan, sin implementarlos.

**Decisión.** Se conserva public.admisiones_original y se crea public.admisiones_tipadas. Las fechas usan DATE y puntajes e importes, NUMERIC sin redondeo impuesto. Los identificadores y categorías continúan como TEXT. No se homologan nombres ni se eliminan duplicados.

**Trazabilidad.** Cada fila incorpora posición en el CSV, hash de origen, los 15 valores TEXT en datos_originales y observaciones de tipado. Si un texto no tiene representación numérica o de fecha, el campo tipado queda NULL, pero el contenido y su motivo permanecen disponibles. No se equiparan vacío, Pendiente, por definir y No aplica.

**Respaldo previo.** data/backups/admisiones_20261017_134557_186521.dump. Cabecera e índice verificados; la restauración completa de prueba continúa pendiente.

**Archivos principales.** sql/migrations/001_admisiones_tipadas.sql, scripts/preparar_tipos.py, tests/test_tipado.py, docs/estructura_tipado_sin_limpieza.md y docs/analisis_modelo_estrella_powerbi.md.

**Aplicación.** La carga se realiza en una transacción y no sobrescribe una proyección existente diferente. El primer intento se revirtió por un delimitador incorrecto en el flujo COPY. Se corrigió el delimitador y se completó la carga. La tabla original no fue modificada.

**Validación.** Se reconstruyeron por posición los 15 valores originales de las 5.040 filas a partir de datos_originales y coincidieron con el CSV. La tabla original también se comparó por multiplicidades contra el origen. Se ejecutaron nueve pruebas con resultado correcto, incluyendo conservación de espacios, precisión numérica, textos no convertibles y fechas inválidas sin corrección.

**Representación disponible.** 5.040 fechas de solicitud, 1.085 fechas de matrícula, 4.811 puntajes y 4.179 importes. Los restantes contenidos permanecen íntegros en la representación original. No se deduplicó ni se unificaron categorías.

**Análisis dimensional.** Es viable proyectar una tabla de hechos de solicitudes y dimensiones de programa, modalidad, canal, estado, fechas, periodo, asesor, ciudad y aspirante. Primero se debe definir la solicitud única y validar la identidad y las matrículas. No se creó un modelo estrella ni un ETL dimensional.

**Actualización de pendientes.** La migración técnica y su carga están completadas. La limpieza, decisión sobre duplicados y construcción del modelo dimensional quedan para actividades posteriores; las propuestas anteriores de limpieza no son acciones ejecutadas.

## 21 de octubre de 2026. Sincronización de bases mediante Git y soporte de pip

**Objetivo.** Permitir que otros computadores reproduzcan los datos actuales y apliquen versiones SQL nuevas después de descargar cambios del repositorio. Añadir una alternativa a uv sin realizar la limpieza pendiente.

**Cambios aplicados.** Se creó scripts/sincronizar_bd.py. Levanta Docker, verifica las 5.040 filas originales, reproduce la tabla tipada y aplica versiones de sql/migrations. Registra archivo, SHA256 y fecha en public.migraciones_proyecto. Omite versiones ya aplicadas y rechaza versiones modificadas, ausentes u ordenadas antes de la última existente. Genera respaldo antes de aplicar pendientes.

**Preservación.** Cada versión se ejecuta dentro de una transacción. Las tablas original y tipada se comparan antes y después; una alteración revierte la versión. La limpieza posterior deberá escribir en otra tabla y publicarse mediante un procedimiento reproducible. Git pull descarga los archivos y el sincronizador los aplica explícitamente; no se instalaron hooks de ejecución automática.

**Dependencias.** Se exportó requirement.pip desde uv.lock con todas las herramientas del notebook, versiones y hashes. requirements.txt remite al mismo archivo. La comprobación de instalación en modo de simulación revisó 66 paquetes y no requirió cambios. No se exportaron rutas de esta máquina ni la .venv.

**Portabilidad.** Se agregó .gitattributes para conservar los bytes del CSV y fijar LF en scripts y SQL. Las rutas de Compose son relativas. La ejecución real en macOS todavía no se ha probado.

**Pruebas.** Pasaron 13 pruebas locales y tres pruebas de integración en un proyecto Docker aislado llamado admisiones_validacion_sync. Se recrearon las 5.040 filas y ambas tablas desde un volumen nuevo. Una segunda sincronización encontró cero versiones pendientes. Una versión de prueba se aplicó una sola vez. Las dos pruebas que intentaban alterar las bases original y tipada provocaron reversiones completas, según lo esperado.

**Base de trabajo.** Se ejecutó el sincronizador y se registró 001_admisiones_tipadas.sql sin alterar los datos. Respaldo previo: data/backups/admisiones_20261021_102528_091080.dump, con SHA256 2d6a291de02a3c805779f2a787fb2062ee335a5b56b88c684f9b48638d0227e7. La prueba de restauración completa de este respaldo sigue pendiente.

**Limpieza de la prueba.** Se retiraron solo el contenedor, la red y el volumen del proyecto aislado de validación. La base de trabajo permanece saludable. Las versiones SQL de prueba no se incorporaron al repositorio.

**Documentación.** README.md, docs/trabajo_compartido.md, docs/base_datos.md y sql/migrations/README.md describen instalación, actualización, límites y mantenimiento. La limpieza de datos no se ha implementado ni aplicado. El repositorio no se ha publicado ni se ha configurado un remoto durante este trabajo.

## 21 de octubre de 2026. Reporte del estado actual

**Objetivo.** Entregar un reporte completo y comprobado del proyecto en este equipo.

**Comprobaciones.** PostgreSQL está en ejecución y saludable. Se consultaron 5.040 filas en admisiones_original, 5.040 en admisiones_tipadas y una versión en migraciones_proyecto. Se verificó nuevamente la igualdad del CSV con la tabla original y la reconstrucción por posición de los valores originales desde la tabla tipada. El SHA256 del CSV no cambió.

**Estado de Git.** La consulta en el entorno real confirmó que esta carpeta todavía no es un repositorio Git válido. Los archivos de configuración están preparados, pero no se ha inicializado un historial ni configurado un remoto.

**Entregables.** docs/estado_proyecto_2026_10_21.md y reports/estructura/estado_actual_20261021.json. El reporte distingue implementaciones, pruebas históricas, verificaciones realizadas hoy y pendientes. No se ejecutó limpieza ni se aplicaron nuevas migraciones durante esta revisión.

## 21 de octubre de 2026. Propuesta de limpieza y código entero de periodo

**Solicitud.** Explicar la limpieza futura y evaluar el uso de 20261 y 20262 para organizar el periodo académico.

**Documento generado.** docs/plan_limpieza_datos.md, con reglas por las 15 columnas, duplicados, excepciones, trazabilidad, validación y publicación futura mediante Git.

**Propuesta de periodo.** Código INTEGER construido como año por 10 más número de periodo, con etiqueta legible obtenida mediante vista o catálogo. Se preservaría el valor original y no se resolverían por esta conversión las discrepancias con las fechas. Los conteos previos a deduplicación serían 981 en 20252, 2.033 en 20261 y 2.026 en 20262.

**Alcance.** Se trata de una propuesta. No se creó admisiones_limpias, no se aplicó una migración nueva, no se ejecutó limpieza y no se modificaron los tipos actuales de periodo en las tablas existentes. La implementación requiere distinguir reglas técnicas de decisiones pendientes de validación institucional.


## 23 de octubre de 2026. Preparación de Git y GitHub CLI

Se inicializó Git con la rama main y la identidad configurada JLosada-Dev. Se instaló GitHub CLI 2.103.2 en el usuario WSL, verificando el archivo descargado con el SHA256 publicado en la distribución oficial.

Se preparó el primer commit con Conventional Commits, sin trailers ni atribuciones adicionales. Se verificó la exclusión de .env, .venv y data/backups; no se encontraron patrones de credenciales en los archivos candidatos. Pasaron 13 pruebas locales; tres pruebas de integración Docker se omitieron porque requieren activación y una base aislada.

La creación del repositorio privado y el primer push quedan pendientes de completar la autenticación de GitHub. Esta preparación no ejecuta limpieza ni modifica las tablas de datos.


## 23 de octubre de 2026. Publicación del repositorio privado

Se completó la autenticación de GitHub CLI en WSL con la cuenta JLosada-Dev. Se creó el repositorio privado https://github.com/JLosada-Dev/analitica_admisiones_universitaria y se publicó el commit inicial 6552746 en main. El remoto origin utiliza HTTPS y main quedó vinculada a origin/main.

Los mensajes siguen Conventional Commits, sin trailers ni atribuciones adicionales. Se mantienen excluidos .env, .venv y los respaldos locales. La publicación incluye el CSV original, documentación, código, notebook y evidencias del análisis, sin ejecutar limpieza de datos.


## 24 de octubre de 2026. Organización y revisión del Taller 2

Se trasladaron los cuatro archivos nuevos desde la raíz a docs/referencias/taller_2, data/raw/taller_2 y sql/fuentes/taller_2. Se verificó que los hashes antes y después coincidieran y se registró el manifiesto integridad.json. El SQL permanece fuera de las migraciones y de la inicialización automática.

Se analizaron las tres páginas del PDF y se creó docs/analisis_taller_2.md con requisitos de Oracle y Power Query, entregables, rúbrica, perfil de fuentes, riesgos y continuación del informe. Se extrajo el texto para consulta en docs/teoria/taller_2_texto.md.

El script scripts/revisar_fuentes_taller_2.py inspecciona las fuentes sin ejecutarlas y produce reports/taller_2/revision_fuentes.json. Se encontraron nueve filas de catálogo, 100 de CRM y un export Oracle de cinco tablas con 500 solicitudes. Los 100 códigos de solicitud CRM ya aparecen en la base original. La normalización del catálogo revela dos filas de Data Analytics con atributos distintos y riesgo de multiplicación de filas. Los 500 códigos de solicitud Oracle son distintos de los originales, pero 490 filas de aspirantes comparten correo con la base principal, sin que eso demuestre duplicación de solicitudes.

No se aplicó limpieza, no se ejecutó el SQL ni se modificaron las tablas de PostgreSQL. La vista Oracle, el proceso Power Query y el Excel Base_unificada siguen pendientes.


## 24 de octubre de 2026. Oracle en Docker y vista del Taller 2

Se inició Docker Desktop y se descargó la imagen oficial Oracle Free Lite 23.26.0.0. Se creó compose.oracle.yaml como proyecto independiente admisiones_oracle, con volumen persistente, caracteres AL32UTF8 y puerto 127.0.0.1:1521. Las claves de administración y CASO2 se generaron únicamente en .env, excluido de Git.

El script scripts/preparar_oracle.py crea FREEPDB1.USERS si falta y el usuario CASO2 con permisos acotados para el ejercicio. La primera tentativa detectó la ausencia de USERS en Lite antes de crear el usuario; se adaptó la preparación y se completó la carga sin modificar el export. Se leyó el SQL original como cp1252 y se envió a SQL*Plus con UTF8. Se verificó igualdad de todas las filas de C2_SOLICITUDES (500), C2_ASPIRANTES (500), C2_PROGRAMAS (8), C2_CANALES (6) y C2_ASESORES (4) frente a los INSERT.

Se creó CASO2.V_ADMISIONES_BASE mediante sql/oracle/01_vista_admisiones.sql y se verificaron 500 filas, 500 registro_id distintos y las 15 columnas compatibles. Los resultados están en reports/taller_2/verificacion_oracle.json. Se confirmó accesibilidad TCP desde Windows a localhost:1521. La conexión autenticada desde DBeaver y Excel sigue pendiente; no se instaló OCMT.

Se documentó la conexión y operación en docs/oracle_taller_2.md y se dejó una plantilla M en powerquery/taller_2/Oracle_Admisiones.pq. No se modificaron las tablas PostgreSQL ni las fuentes y no se ejecutó limpieza ni integración entre fuentes.

**Repetición y controles finales.** Una segunda ejecución reconoció la fuente ya cargada, no insertó filas y repitió correctamente la comparación completa y la verificación de la vista. Se comprobaron los hashes de las ocho fuentes originales y pasaron 13 pruebas locales; las tres pruebas Docker de integración PostgreSQL siguen requiriendo su entorno aislado y se omitieron.


## 24 de octubre de 2026. Reporte comparativo y descriptivo de las cuatro fuentes

Se consultó la vista Oracle mediante SELECT y se guardó una lectura completa de 500 filas y sus 15 columnas, con metadatos y fecha, en reports/taller_2/oracle_vista_lectura.json. El capturador scripts/capturar_vista_oracle.py valida nombres y estructura antes de guardar. PostgreSQL estaba detenido; la referencia principal fue su CSV original con hash verificado. No se inició ni se alteró PostgreSQL para esta revisión.

Se creó scripts/analizar_relaciones_taller_2.py y docs/reporte_comparativo_fuentes_taller_2.md. Los perfiles y cruces están en reports/taller_2/comparacion, con frecuencias, calidad, estadísticas, relaciones y revisión temporal. Se confirmó compatibilidad de las 15 columnas de negocio y se distinguieron las cuatro columnas técnicas de la tabla tipada.

CRM: los 100 registro_id ya existen; sus 12 columnas compartidas coinciden por registro. Hay 87 importes iguales y 13 importes principales vacíos con matrícula base CRM disponible. Este universo incluye los cuatro aspirantes nan, a diferencia del control anterior limitado a 96 pares completos. Un código CRM corresponde a dos filas principales, por lo que enriquecería 101 filas sin aumentar las 5.040.

Oracle: 498 filas encuentran candidatos por 11 atributos normalizados excluyendo identificadores y fechas, 49 por los 13 atributos excluyendo solo identificadores y 60 por correo, fecha, programa, modalidad y periodo. Se identificaron 16 candidatos compatibles con intercambio de día y mes y otras diferencias no explicables por ese intercambio. Son sondas, no duplicados confirmados. Las fechas Oracle llegan hasta diciembre de 2026; 15 solicitudes son posteriores a la fecha de revisión, sin corte institucional validado.

Los originales conservan su integridad. No se modificaron tablas, no se aplicó limpieza ni se integraron fuentes. El notebook inicial permanece como respaldo de la primera actividad; este análisis nuevo se respalda en scripts y CSV separados.


## 24 de octubre de 2026. Exportación plana de la vista Oracle

Se creó scripts/exportar_vista_oracle.py y se extrajo en vivo CASO2.V_ADMISIONES_BASE a data/exports/taller_2/Caso2_Oracle_Admisiones.csv. Se conservan las 15 columnas, se serializan fechas como año, mes y día y NULL como celdas vacías. Se utiliza UTF8 con BOM, coma como separador y punto decimal. Se ordena por registro_id para facilitar la revisión.

Se verificó la lectura completa del CSV contra las 500 filas serializadas de la vista. El archivo metadata.json registra conteos, fecha de consulta, hash y tipos. Se separó la función de lectura en capturar_vista_oracle.py para reutilizarla sin sobrescribir la evidencia del análisis anterior. La exportación no limpia ni integra datos, no modifica Oracle y no acredita una conexión Power Query al servidor.


## 24 de octubre de 2026. Preparación de la publicación del Taller 2

Se agruparon para compartir las fuentes nuevas, el entorno Oracle, la vista, los scripts de revisión y exportación, el CSV plano con metadatos y los reportes descriptivos. Se verificaron los hashes originales y el CSV de 500 filas y 15 columnas. No se detectaron credenciales locales en los archivos candidatos. .env, .venv y los respaldos continúan excluidos. Pasaron las 13 pruebas locales; se omitieron tres pruebas de integración que requieren un entorno aislado explícito. La publicación usa Conventional Commits sin trailers ni atribuciones adicionales y no ejecuta limpieza ni cambia bases de datos.

**Preservación en Git.** Se exceptuaron los SQL de sql/fuentes de la normalización de saltos de línea, igual que los CSV. Se conservan los espacios y finales de línea de los datos originales; los controles de estilo no los corrigen. El texto extraído del PDF, que es un documento derivado, se ajustó únicamente para retirar espacios al final de línea.


## 24 de octubre de 2026. Verificación de la hoja BaseUnificada de Excel

Se revisó en modo de lectura data/BaseUnificada.xlsx, su hoja BaseUnificada y el código M guardado. La consulta usa Table.Combine con una sola fuente principal, el CRM transformado y el CSV Oracle. Contiene 5.640 filas, 15 columnas con los nombres y orden esperados y no presenta celdas de error en la salida guardada.

Se compararon todos los valores de los tres bloques: 5.040 registros principales con identificadores recortados, 100 CRM con separación de identificadores, recorte y suma económica acordada por el usuario para esta fase, y 500 Oracle iguales al CSV exportado. Los tres bloques coinciden. El periodo académico Oracle ya conserva sus etiquetas de texto. Programas permanece separado con nueve filas.

La preparación conserva 5.500 registro_id distintos, cuatro aspirante_id nan y 25 programas con solo espacios. No se eliminaron duplicados ni se aplicaron reglas adicionales. La consolidación es provisional y no acredita solicitudes únicas ni equivalencia entre conceptos económicos. El detalle está en reports/taller_2/revision_baseunificada_excel.json. No se modificó el libro de Excel.


## 24 de octubre de 2026. Diagnóstico de referencia rota en Power Query CRM

La captura de Excel y el código M guardado muestran que la consulta Caso2_CRM_Admisiones busca una tabla interna con ese nombre que ya no existe. La tabla con sufijo final no es una sustitución directa del origen original. BaseUnificada hereda el fallo al depender de CRM. Se preparó powerquery/taller_2/CRM_Admisiones_desde_csv.pq con origen directo al CSV recibido y los mismos pasos de transformación existentes. El control de Windows devolvió un error de rutas de la sesión WSL antes de poder actuar sobre Excel. No se modificó el libro abierto ni se verificó aún su actualización.


## 24 de octubre de 2026. Revisión del Merge guardado en Excel

La hoja BaseUnificada_ConProgramas_Merg contiene 5.640 filas y 19 columnas. Se comprobó que conserva los valores de las 15 columnas originales y el orden completo de las filas de BaseUnificada. La consulta usa Table.FuzzyNestedJoin LeftOuter, expande atributos y retira únicamente programa del catálogo. No se detectaron celdas de error en la salida guardada. Hay 5.613 correspondencias y 27 sin atributos de catálogo.

modalidad1 corresponde al catálogo; modalidad conserva la solicitud. Coinciden en 2.228 casos y difieren en 3.385 con ambos datos disponibles. Estas diferencias no prueban errores: el catálogo reducido no representa todas las modalidades de las solicitudes. Se recomienda retirar modalidad1 de la salida analítica conservando modalidad y los atributos facultad, duración y nivel. El resultado esperado sería de 18 columnas. No se modificó el Excel. Respaldo: reports/taller_2/revision_merge_excel.json.


## 24 de octubre de 2026. Pull, organización de data y nueva base de partida

Se ejecutó git pull --ff-only desde c654c3a hasta 37986c7, sin conflictos ni sobrescritura de los cambios locales. Se recibió data/Nueva carpeta/BaseUnificada.xlsx y un bloqueo de Office. El libro se conservó byte por byte en data/workbooks/recibidos/BaseUnificada_Git_37986c7.xlsx con metadatos de procedencia. El bloqueo recibido se apartó en data/backups/temporales_excel y se agregó la exclusión de bloqueos nuevos de Office.

Se exportó la hoja BaseUnificada_ConProgramas_Merg de data/BaseUnificada_Manejo.xlsx a data/prepared/taller_2/BaseUnificada.csv y BaseUnificada.xlsx. Ambos contienen 5.640 filas y 18 columnas. El Excel tiene una sola hoja y una tabla BaseUnificada, sin consultas ni vínculos. Se verificaron todos sus valores contra la hoja de origen y la lectura completa del CSV contra las filas serializadas. Se preservaron los textos vacíos en el Excel, sin convertirlos a celdas ausentes. El CSV no distingue esas dos representaciones. No se aplicó limpieza adicional ni se cambiaron las fechas o duplicados.

Se creó scripts/exportar_base_unificada.py. Se añadió el grupo opcional excel con openpyxl a pyproject.toml y uv.lock y se regeneró requirement.pip con todas las dependencias y hashes. Los conteos, origen y hashes de las exportaciones están en BaseUnificada.metadata.json. Se documentó data en su README y se mantuvo el libro de manejo en su ruta, al estar abierto en Excel. No se modificaron las bases de datos ni se realizó push de estos cambios.


## 24 de octubre de 2026. Preparación para compartir la base de partida

Se revisaron los cambios locales de organización, libro de manejo, exportaciones BaseUnificada, corrección del origen CRM y evidencias de revisión. Las contraseñas y temporales de Office se mantienen excluidos. Se verificaron los hashes de los archivos preparados para la limpieza. Se publica mediante Conventional Commits, sin trailers ni atribuciones adicionales. El traslado del libro recibido conserva su contenido y el bloqueo de Office deja de formar parte del repositorio.


## 24 de octubre de 2026. Actualización del plan de limpieza y controles de entrada

Se contrastó el plan del 21 de octubre con la entrada consolidada de 5.640 filas y 18 columnas. Se conservó el documento anterior en docs/historial y se actualizó docs/plan_limpieza_datos.md para contemplar Power Query como herramienta principal del taller, Python como respaldo, las tres columnas del catálogo, los cambios ya realizados y la trazabilidad por ejecución.

El script scripts/diagnosticar_base_unificada.py verificó el hash de entrada y generó reports/limpieza/diagnostico_entrada.json, inventario_entrada.csv e identificadores_repetidos.csv. El inventario identifica las 5.640 filas de esa versión. Se recalcularon 5.500 registro_id distintos, 139 grupos repetidos con 279 filas y 38 repeticiones exactas adicionales. Se corrigió el alcance del plan: el solapamiento CRM, los conceptos económicos, las fechas Oracle y las decisiones del catálogo requieren tratamiento separado.

Se prepararon cuatro plantillas vacías de pasos, cambios por celda, disposición de filas e incidencias. Las cantidades de cambios de valor, cambios de tipo y filas retiradas deben registrarse separadamente. La conciliación obliga a explicar el destino de cada fila de entrada. Se verificó que el inventario tenga 5.640 claves únicas y que los hashes del CSV y Excel preparados no cambiaran. No se ejecutó limpieza, no se eliminaron registros ni se cargó una tabla nueva.


## 24 de octubre de 2026. Notebook principal y estandarización L00 a L02

Por decisión del usuario, el notebook será el lugar principal del proceso y seguirá la secuencia del plan. Se preparó y ejecutó notebooks/02_limpieza_base_unificada.ipynb con 10 celdas de código y su HTML de lectura. El ejecutor admite seleccionar notebook, conservando el respaldo inicial como predeterminado. El constructor y el catálogo de reglas estandarizacion_v1 quedan versionados.

L00 verificó la entrada de 5.640 filas y 18 columnas y el inventario. L01 comprobó la procedencia de los tres bloques contra el libro de manejo congelado, su hash, sus hojas y el orden de Table.Combine: 5.040 principal, 100 CRM y 500 Oracle. Se documentaron las decisiones todavía abiertas sobre identidad, importes, fechas y catálogo.

L02 aplicó catálogos explícitos de textos y categorías, con 14.209 cambios de celda en 5.404 filas, conservando todas las filas y columnas. Los periodos se homologaron aún como texto. No se cambiaron fechas, puntajes, importes o duración, ni se resolvieron ausencias; esos pasos corresponden a L03 y L04. Los cuatro nan y las 38 repeticiones exactas adicionales permanecen. No hubo eliminación ni consolidación.

Los datos intermedios CSV y Excel se guardan en data/interim/taller_2 con versión y hashes. La auditoría registra procedencia, decisiones pendientes, cambios por celda, equivalencias, frecuencias antes y después, reglas y destino de las 5.640 filas. Diez controles pasaron, incluida la idempotencia de las reglas y la lectura completa de los dos formatos exportados. Se actualizó el plan para distinguir lo ejecutado de las etapas L03 a L09 pendientes.


## 24 de octubre de 2026. Identificadores conservados hasta los cruces

El usuario decidió posponer la comparación de identificadores entre fuentes. Se mantienen los códigos Oracle y los de las otras fuentes, así como los marcadores recibidos en los identificadores. La revisión no bloquea la estandarización y no autoriza eliminar registros por este motivo. El índice BU sigue siendo técnico para auditoría. Se aclaró el alcance en el plan, el notebook, su constructor y su HTML. No se cambió el código ejecutado ni los datos; se comprobó que el hash de las celdas de código coincide con la auditoría existente.


## 24 de octubre de 2026. Revisión de remoto y consistencia antes de L03

Se consultó origin/main y continuaba en bc5ee3e, sin commits remotos nuevos ni diferencias de CSV. Los cambios locales pendientes eran aclaraciones de alcance sobre identificadores. Se ajustó también el texto de L03 para conservar los cuatro nan de aspirante_id hasta los cruces, sin alterar las celdas de código ejecutadas.

Se verificaron los hashes de los archivos preparados, los resultados intermedios, el código del notebook y la integridad de los dos cuadernos con sus salidas existentes. La revisión no ejecuta L03 ni cambia datos. Se conserva el trabajo realizado y se prepara su publicación con Conventional Commits, sin trailers ni atribuciones adicionales.


## 24 de octubre de 2026. Periodo como código entero y ajuste del plan

Se descartó un commit local no publicado que había guardado de nuevo BaseUnificada.csv desde Excel, con separador punto y coma, fechas reescritas y fin de línea CRLF. Ese archivo no coincidía con el hash de los metadatos y habría detenido el notebook. El CSV preparado volvió a su versión registrada.

El usuario confirmó que periodo_academico se manejará con los códigos enteros 20252, 20261 y 20262; la conversión se aplicará en L04. En el plan se corrigió además la referencia al código M en las salidas, porque la auditoría ahora identifica el código del notebook y las reglas mediante hashes. No se cambiaron datos ni código ejecutado.


## 24 de octubre de 2026. L03, tratamiento de ausencias

Se amplió y ejecutó de principio a fin el notebook de limpieza, ahora con 14 celdas de código. La reejecución de L02 produce el mismo contenido CSV de estandarización, con una nueva firma del código del cuaderno y sin acumular transformaciones. Se aplicó L03 con reglas versionadas en config/limpieza/ausencias_v1.json.

Se normalizaron como ausencia 5.866 celdas en 4.705 filas: 4.409 vacíos de columnas no identificadoras, 1.369 No aplica de fecha de matrícula, 51 Pendiente de puntaje, 35 por definir de importe y dos programas Sin especificar. Se conserva por celda el valor anterior y su motivo. Pendiente en documentación y Sin asignar en asesor permanecen como categorías. Los identificadores, incluidos 92 vacíos y cuatro nan, no se modifican.

Se mantienen 5.640 registros y 18 columnas, sin imputaciones, exclusiones ni consolidaciones. Se comprobaron 11 controles L03 y la lectura completa de CSV, Excel y JSONL. JSONL permite mantener null distinto de texto vacío; CSV requiere el control de ausencia. Cada una de las entradas conserva su destino documentado. Entrada preparada e importes y fechas informados se mantienen sin cambios.

Se actualizaron plan, README y HTML; las salidas intermedias y la auditoría están referenciadas en reports/limpieza/ultima_ausencias.json. L04, conversión de tipos y validaciones, queda como siguiente etapa.

**Integración del avance remoto.** Durante la publicación llegó 134f970, con la decisión de periodo entero en L04 y la corrección de referencias de auditoría. Se conservaron ambos cambios del plan y las dos entradas de bitácora; el conflicto era únicamente la inserción de texto al final. El commit remoto no modificó el CSV ni los datos o el código ejecutado.

## 24 de octubre de 2026. L04, fechas e importes en COP

Se ejecutó el notebook completo con 19 celdas de código. Según la decisión del usuario, las fechas se presentan como AAAA-MM-DD y los importes se manejan como decimales exactos en pesos colombianos, con dos posiciones decimales y sin redondear. La presentación colombiana usa COP 2.200.000,00; CSV y JSONL conservan números sin separador de miles y con punto decimal. Excel contiene números y fechas reales, con formato de presentación sujeto a la configuración regional. El periodo académico pasa a los códigos enteros 20252, 20261 y 20262.

Se convirtieron 28.186 celdas sin errores de interpretación. Permanecen las 5.640 filas, 18 columnas y 5.866 ausencias. No se cambiaron identificadores, incluidos 92 vacíos y cuatro nan; no hubo imputaciones, exclusiones ni conciliaciones de fuentes. Las reejecuciones previas conservan el contenido de sus resultados y quedan registradas como puntos de control.

Se registraron 1.293 alertas en 1.159 filas: 524 de documentación en matriculados, 470 de año de solicitud posterior al periodo, 237 de formatos de día y mes ambiguos, 32 matrículas anteriores a solicitud y 30 fechas posteriores a la referencia del 24 de octubre de 2026. Son casos de revisión, sin correcciones automáticas; la referencia no representa un corte institucional confirmado. La igualdad de moneda tampoco confirma que los conceptos económicos sean equivalentes.

Pasaron los 12 controles de L04 y la lectura completa de CSV, Excel y JSONL. Una revisión independiente confirmó los hashes de ocho fuentes y de las salidas de L02, L03 y L04, la conservación de identificadores e importes y las 19 celdas ejecutadas sin error. La suite completó 21 pruebas correctas; tres pruebas de integración Docker requieren una base aislada y no se ejecutaron. Las reglas están en config/limpieza/tipos_v1.json, la guía en docs/formatos_fechas_cop.md y las rutas y hashes en reports/limpieza/ultima_tipificacion.json. L05 queda pendiente.

## 26 de octubre de 2026. Preparación de L05 a L09

El usuario solicitó completar los pasos pendientes, registrar cada acción y presentar las decisiones necesarias para cerrar la limpieza. Se prepararon reglas versionadas en config/limpieza/cierre_v1.json y las etapas finales en src/analitica_admisiones/cierre_limpieza.py, integradas mediante scripts/celdas_cierre_limpieza.py en el constructor del notebook.

Se autoriza operativamente la consolidación de repeticiones exactas de una misma fuente, exigiendo igualdad en las 18 columnas originales y tipadas. El menor índice BU será el representante técnico y cada entrada mantendrá su destino. No se atribuye mayor vigencia a ese índice. Los registros parciales, las diferencias económicas y temporales y la identidad de Oracle requieren evidencia antes de fusionarse.

Se prepararon cinco pruebas de conservación de orígenes, diferencias originales, fuentes e identificadores y todas pasaron. La revisión del catálogo reproducirá una clave normalizada única y verificará sus atributos, sin afirmar que recupera el nombre descartado por el fuzzy histórico. L08 utilizará el 26 de octubre como referencia de revisión; no se declara como corte institucional. Las salidas se llamarán BaseUnificada_Revision hasta resolver las decisiones administrativas. La ejecución completa y sus conteos se registrarán en la siguiente entrada.

## 26 de octubre de 2026. Ejecución L05 a L09 y exportación de revisión

Se ejecutó de principio a fin el notebook 02 con 24 celdas de código y se actualizó su HTML. L05 reprodujo 5.613 correspondencias del catálogo de trabajo, comprobando los tres atributos sin discrepancias, y registró 27 programas sin identificación útil. Se conservó la modalidad de solicitud ante 3.385 diferencias con el catálogo. La reproducción no recupera el nombre fuzzy histórico que fue retirado de la salida.

L06 consolidó 38 repeticiones exactas de la fuente principal, con igualdad original y tipada. Cada grupo tiene dos entradas y un representante técnico por menor índice BU. La salida conserva 5.602 registros y 18 columnas: 5.002 principal, 100 CRM y 500 Oracle. Las 5.640 entradas tienen destino; ninguna fue excluida sin representante. No se imputaron valores ni se alteraron los datos informados o los identificadores de los representantes.

L07 identificó 102 grupos de registro_id repetido con diferencias, que involucran 204 filas. Los 100 CRM coinciden en 12 atributos distintos de IDs e importe; 96 comparten aspirante_id y cuatro mantienen nan. Trece importes principales faltantes tienen información económica CRM, pero no se completaron sin acordar el concepto. REG003600 y REG004804 permanecen como conflictos de importe y programa, respectivamente.

Oracle produjo 500 candidatos por 11 atributos y 49 por 13. La revisión de detalle explicó el aumento frente a los 498 iniciales: dos programas Sin especificar y programas vacíos pasan a una ausencia común en L03. No se considera nueva evidencia de identidad; los valores de programa originales y las ausencias compartidas se registran por par. Hay 16 filas Oracle compatibles con intercambio de día y mes frente a un candidato principal. No se cambiaron fechas ni se fusionaron códigos. El módulo y su auditoría se precisaron después de la primera ejecución y se volvió a ejecutar el notebook; los contenidos CSV y JSONL de salida son idénticos en ambas ejecuciones. Se conservan las dos evidencias.

L08 revisó coherencia sobre los representantes: 466 solicitudes posteriores al año del periodo, 521 matriculados con documentación No o Pendiente, 95 identificadores de aspirante vacíos o nan, 32 matrículas anteriores a solicitud y 28 fechas posteriores a la referencia de revisión del 26 de octubre. La evidencia L04 conserva su referencia histórica del día 24. Los 5.471 correos informados tienen estructura compatible y 131 están ausentes; no se verificó entregabilidad. No se encontraron negativos ni valores fuera del criterio intercuartílico aplicado. Los importes se resumieron por fuente, sin asumir un concepto económico común.

L09 exportó BaseUnificada_Revision en CSV, Excel y JSONL bajo data/processed/taller_2, con 18 columnas, valores COP exactos y fechas ISO. El Excel incluye Alcance; índices y controles permanecen fuera de la tabla de negocio. Se generaron disposición de filas, incidencias, decisiones, completitud y diccionario, estadísticas, frecuencias antes y después y por fuente. Hay 2.110 incidencias en 1.766 filas de salida distintas; los motivos se superponen. El reporte de cierre documenta diez decisiones sobre programa faltante, catálogo, CRM y parciales, Oracle, fechas, periodos, estados y documentación, identidad y contacto, conceptos monetarios y reglas numéricas, y ausencias y aprobación final.

Pasaron 16 controles L09 y la lectura completa de los tres formatos. La verificación independiente contrastó hashes de salidas y reglas, las 24 celdas sin errores, las 5.640 correspondencias y todos los valores contra L04; confirmó 5.602 filas sin repeticiones exactas. Los controles del notebook verificaron además las fuentes originales y la entrada preparada. La suite ejecutó 26 pruebas correctas; tres de integración Docker no se ejecutaron porque requieren una base aislada. No se modificaron los libros originales ni las tablas Docker. El estado vigente está en reports/limpieza/ultimo_cierre.json y el reporte en reports/limpieza/reporte_cierre_limpieza.md.

La preparación técnica está ejecutada. La versión permite descripción provisional de registros; la conciliación administrativa sigue pendiente para solicitudes o aspirantes únicos, tasas definitivas y medidas económicas comparables. Se actualizaron el plan y las guías de organización para reflejar este alcance.
