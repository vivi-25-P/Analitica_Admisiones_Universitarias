# Reporte de estado del proyecto

**Proyecto:** Analítica de admisiones universitarias.

**Equipo actual:** Windows con Ubuntu en WSL y Docker Desktop.

**Fecha de comprobación:** 21 de octubre de 2026, 10:29 a. m., hora de Bogotá.

**Carpeta:** C:\Users\jdlos\Desktop\analitica_admisiones_universitaria. En esta sesión WSL se utiliza /mnt/c/users/jdlos/desktop/analitica_admisiones_universitaria.

## 1. Estado general

El proyecto funciona localmente y permite reproducir el análisis descriptivo, consultar PostgreSQL, reconstruir las tablas actuales y sincronizar versiones SQL. Los datos originales están intactos. La limpieza, el modelo estrella y el ETL dimensional permanecen pendientes por decisión del usuario.

La carpeta aún no es un repositorio Git válido. La consulta realizada en el entorno real devolvió not a git repository. No hay commits ni un remoto verificado en esta ubicación. Los archivos necesarios para compartir el proyecto están preparados, pero no se ha publicado en GitHub.

## 2. Organización del proyecto

| Ubicación | Contenido |
|---|---|
| data/raw | CSV original del caso |
| data/backups | Cuatro archivos de respaldo PostgreSQL locales y sus metadatos |
| docker | Inicialización de PostgreSQL y manifiesto de origen |
| sql/exploracion | Consultas de solo lectura |
| sql/migrations | Migración versionada 001_admisiones_tipadas.sql e instrucciones |
| src/analitica_admisiones | Perfilamiento, gráficos y arranque con verificación |
| scripts | Ejecución del notebook, respaldo, tipado y sincronización |
| notebooks | Notebook ejecutado que respalda el informe |
| reports | HTML, tablas, gráficos y evidencias de comprobación |
| docs/referencias | Guía PDF y dos presentaciones PowerPoint originales |
| docs/teoria | Síntesis aplicada y extracciones de texto |
| docs | Guías de datos, diagnóstico, instalación y propuestas de modelado |
| tests | Pruebas locales y de integración |
| BITACORA.md | Historia de decisiones, validaciones y pendientes |

Se conservaron la guía y los materiales de Calidad de datos y Conceptos BI. La bitácora diferencia antecedentes retrospectivos, acciones aplicadas y propuestas.

## 3. Python y dependencias

Se creó un proyecto con Python 3.12, entorno .venv y administración mediante uv. pyproject.toml declara las dependencias y uv.lock fija las versiones y condiciones por plataforma.

Las dependencias de análisis incluyen pandas, matplotlib, psycopg y python-dotenv. El grupo notebooks incluye nbformat, nbclient, ipykernel y nbconvert para generar, ejecutar y exportar el cuaderno.

requirement.pip es una exportación desde uv.lock con versiones, hashes y herramientas de notebook. requirements.txt remite a ese archivo. La exportación no contiene rutas de esta computadora ni una copia de .venv. La simulación de instalación comprobó 66 paquetes en este entorno sin requerir cambios.

No se ha realizado una instalación real de prueba en macOS. Los archivos están preparados con rutas relativas y resolución de dependencias por plataforma; esa preparación no equivale a una prueba ejecutada en cada sistema.

## 4. Estado actual de Docker y PostgreSQL

| Elemento | Resultado actual |
|---|---|
| Imagen | postgres:17 |
| Servicio Compose | postgres |
| Contenedor | analitica_admisiones_universitaria-postgres-1 |
| Estado | En ejecución y saludable |
| Base | admisiones |
| Usuario | analista |
| Dirección local | localhost |
| Puerto del equipo | 5433 |
| Puerto del contenedor | 5432 |
| Persistencia | Volumen admisiones_data gestionado por Compose |
| Contraseña | Archivo .env local, sin incluir su contenido en el reporte |
| Origen CSV | Montado en modo de solo lectura |

La integración de Docker con WSL funciona con Docker Desktop abierto. Las sesiones que todavía no tienen actualizado el grupo docker pueden necesitar newgrp docker. En esta sesión se usó sg docker para las comprobaciones.

El volumen conserva los datos cuando se detiene el contenedor. Git no transporta ese volumen; los demás equipos reconstruyen la base con los archivos y procedimientos del repositorio.

## 5. Tablas y preservación de datos

| Tabla | Filas comprobadas | Columnas | Función |
|---|---:|---:|---|
| public.admisiones_original | 5.040 | 15 | Referencia fiel del CSV con todas las columnas TEXT |
| public.admisiones_tipadas | 5.040 | 19 | Representación tipada más cuatro columnas de trazabilidad |
| public.migraciones_proyecto | 1 | 3 | Control de versiones SQL aplicadas |

En admisiones_tipadas, fecha_solicitud y fecha_matricula son DATE. Puntaje e importe son NUMERIC sin una precisión que fuerce redondeo. Las categorías, identificadores, correo, documentación y periodo permanecen como TEXT.

Las cuatro columnas técnicas son fila_origen_csv, origen_sha256, datos_originales y observaciones_tipado. Cada fila conserva los 15 valores originales en datos_originales, además de su posición y motivos de ausencia de representación tipada.

Un valor como Pendiente no cabe en NUMERIC. Su representación numérica queda NULL, pero el texto y su significado no desaparecen. También se conserva la diferencia entre vacío, No aplica y por definir. Este tipado técnico no ejecuta las decisiones de limpieza.

La representación disponible contiene 5.040 fechas de solicitud, 1.085 fechas de matrícula, 4.811 puntajes y 4.179 importes numéricos. No se eliminaron los 38 pares exactos ni se resolvieron las dos discrepancias de identificador. No se homologaron Derecho y DERECHO ni otras categorías.

### Comprobación realizada hoy

Se volvió a comparar admisiones_original con el CSV, contando también las multiplicidades de cada fila. Luego se reconstruyeron por posición los 15 valores del CSV desde datos_originales de admisiones_tipadas. Ambas comprobaciones resultaron correctas.

El SHA256 del CSV es 0d4c756649ccff9dcf5c2c2cc5edba0ced8f8e3c157ee2c1f5b4bd2939b8f467 y coincide con el manifiesto. La evidencia está en reports/estructura/estado_actual_20261021.json.

## 6. Análisis descriptivo y entregables

Se prepararon el reconocimiento del conjunto, diccionario inicial, diagnóstico por columna, revisión de duplicados, formatos de fechas y comparaciones entre variables. Se documentaron las limitaciones de exactitud, oportunidad, unicidad y causalidad.

El notebook notebooks/01_respaldo_informe_descriptivo.ipynb conserva 16 celdas de código ejecutadas sin salidas de error, seis gráficos incrustados y 34 verificaciones de cifras correctas. Su vista HTML está en reports/01_respaldo_informe_descriptivo.html. Las tablas exportadas se encuentran en reports/respaldo_notebook.

El cuaderno utiliza el CSV original. No necesita PostgreSQL para reproducir la exploración y no aplica limpieza. Las equivalencias propuestas se muestran en un apartado separado.

Existen ocho figuras en PNG y sus ocho versiones PDF. Las figuras 1 a 6 muestran distribuciones originales, puntajes, importes, cobertura temporal y completitud. Las figuras 7 y 8 son variantes administrativas con equivalencias explícitas; para el informe exploratorio se acordó utilizar las categorías originales y dejar esas equivalencias como propuestas de limpieza.

Se redactaron apoyos para cinco hallazgos, recomendaciones y tres preguntas con hipótesis pendientes. El documento administrativo trabajado por el usuario permanece como un entregable separado en Google Docs; el repositorio conserva los respaldos analíticos y las guías, no una publicación automática de ese documento.

## 7. Sincronización entre computadores

scripts/sincronizar_bd.py es la entrada para una instalación nueva o después de descargar cambios mediante Git.

El comando levanta Docker, verifica el CSV y la tabla original, reproduce el tipado técnico y aplica las versiones SQL pendientes. Si .env falta, genera una contraseña local sin mostrarla. No reemplaza una contraseña existente.

Cada migración se registra con nombre, SHA256 y fecha. Las versiones ya aplicadas se omiten. Una versión modificada, desaparecida o agregada fuera de orden provoca una detención. Se genera respaldo antes de aplicar pendientes y cada migración utiliza una transacción.

Las tablas original y tipada se comparan antes y después; una migración que las modifica se revierte. Las futuras reglas de limpieza deberán escribir en otra tabla. Si el procedimiento futuro está en Python, su ejecución versionada se incorporará explícitamente al sincronizador durante esa actividad.

La única versión real aplicada actualmente es 001_admisiones_tipadas.sql. Su SHA256 coincide con el archivo local: 29385d54c95d60f173c4243552954cb41daf7bb10b71e7704eace2477036b7d5. Se registró el 21 de octubre de 2026 a las 10:25:29, hora de Bogotá.

Git pull descarga los archivos; la aplicación de SQL se hace con el comando de sincronización. No se instalaron hooks de ejecución automática.

## 8. Pruebas y respaldos

Pasaron 13 pruebas locales y tres de integración en Docker. En el proyecto aislado de prueba se reconstruyó la base desde un volumen nuevo y se repitió la sincronización sin duplicar filas. Una migración de prueba se aplicó una sola vez. Los intentos de alterar las tablas original y tipada provocaron reversiones completas, según lo esperado.

El contenedor, la red y el volumen aislados se retiraron al finalizar. No se incorporaron versiones de prueba al directorio de migraciones del proyecto.

Hay cuatro archivos dump locales. Uno proviene de la validación aislada, por lo que no debe asumirse que todos representan el mismo contexto. El respaldo de la base de trabajo previo al registro de versiones del 21 de octubre es data/backups/admisiones_20261021_102528_091080.dump.

Se verificaron cabecera e índice de los respaldos. Todavía está pendiente una restauración completa de prueba; crear una base nueva desde el CSV no equivale a restaurar un dump.

## 9. Archivos excluidos y portabilidad

.gitignore excluye .env, .venv, cachés y data/backups. .env.example documenta la configuración sin incluir la contraseña local.

.gitattributes conserva los bytes del CSV y fija finales de línea LF para scripts, SQL y otros archivos de texto relevantes. Esto ayuda a mantener los hashes entre plataformas al versionar el proyecto.

Estas reglas están preparadas como archivos, pero se aplicarán al seguimiento real cuando se inicialice y utilice Git en esta carpeta.

## 10. Comandos principales

### Primera instalación o actualización con uv

```bash
uv sync --locked --group notebooks
uv run --locked --group notebooks python scripts/sincronizar_bd.py
```

Después de publicar y clonar un repositorio real, las actualizaciones comenzarán con git pull --ff-only.

### Alternativa con pip

Con Python 3.12 y un entorno virtual activado:

```bash
python -m pip install -r requirement.pip
python scripts/sincronizar_bd.py
```

### Repetir el análisis

```bash
uv run --locked --group notebooks analitica-admisiones perfilar
uv run --locked --group notebooks analitica-admisiones graficar
uv run --locked --group notebooks python scripts/ejecutar_notebook.py
```

### Estado y respaldo

```bash
docker compose ps
python scripts/sincronizar_bd.py --estado
python scripts/respaldar_bd.py
```

El modo estado levanta y verifica Docker y crea el registro de versiones si falta, pero no aplica migraciones pendientes. Los comandos de base requieren acceso al socket de Docker.

## 11. Pendientes reales

| Pendiente | Situación |
|---|---|
| Inicializar Git y configurar el remoto | No realizado |
| Publicar el proyecto y comprobar un clon | No realizado |
| Prueba real en macOS y en otro equipo Linux | Pendiente |
| Restaurar un respaldo completo en una base temporal | Pendiente |
| Ejecutar la actividad de limpieza | Reservada para la siguiente actividad |
| Crear admisiones_limpias | No creada |
| Implementar ETL de limpieza y publicación de resultados | No realizado |
| Construir dimensiones y hechos de un modelo estrella | Solo analizado teóricamente |
| Conectar y construir el reporte en Power BI Desktop | No realizado |

## 12. Próxima etapa recomendada

El proyecto ya está preparado para compartir sus archivos y reconstruir las dos tablas actuales. El siguiente trabajo de colaboración consiste en inicializar un repositorio Git real, revisar los archivos que se incluirán, configurar un remoto y comprobar una instalación desde un clon.

La limpieza se desarrollará como una actividad independiente con sus reglas, excepciones y validaciones. Su resultado se guardará en otra tabla y se integrará al mecanismo de sincronización para que los demás equipos puedan reproducirlo.
