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
