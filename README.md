# Analítica de admisiones universitarias

**Única base para entregar:** [BaseUnificada_Entregable.xlsx](deliverables/BaseUnificada_Entregable.xlsx), con **5.500 registros y 18 columnas**. Incluye los 500 registros Oracle y los 100 aportes CRM incorporados a sus solicitudes principales, con 13 importes recuperados. El diccionario, la metodología y los controles están dentro del mismo Excel. El otro entregable es el informe administrativo mantenido en Drive. Los CSV, paquetes, informes de apoyo y puntos de control permanecen como evidencia interna, fuera de la carpeta de entrega. `reports/limpieza/ultima_entrega.json` identifica el Excel vigente y su huella. No hay carpetas de versiones en deliverables.

La preparación técnica está completada para revisión externa y análisis descriptivo de registros. Los 3.424 identificadores de aspirante por origen no se afirman como personas globales únicas; las correspondencias Oracle, las ausencias y las observaciones temporales permanecen explícitas. Los periodos se conservan como semestres de ingreso y no se recalculan desde las fechas. PostgreSQL ya publica la misma entrega en analitica.base_unificada, conservando las tablas originales y tipadas. Consulta la guía de conexión a PostgreSQL y Excel enlazada más abajo.

Para la entrega del informe, el documento principal es el informe administrativo en Drive junto con BaseUnificada. El PDF generado queda como apoyo interno. La [sección de limpieza lista para copiar](reports/apoyo_informe_drive/seccion_limpieza_transformacion.md) propone una tabla y una [figura de conciliación](reports/apoyo_informe_drive/conciliacion_registros.png). Se añadieron [estados antes y después](reports/apoyo_informe_drive/homologacion_estados.png) y [cobertura temporal](reports/apoyo_informe_drive/cobertura_temporal.png) para explicar tratamientos y fechas. La [guía de ubicación](reports/apoyo_informe_drive/ubicacion_graficos.md) distingue limpieza del análisis descriptivo. Estos apoyos se regeneran con `python scripts/generar_apoyo_seccion_limpieza.py`.

La marca `similitud_entre_fuentes_detectada` reemplaza la denominación anterior de coincidencia pendiente y se informa en ambos registros relacionados. Es un resultado del cruce ya ejecutado, no una tarea técnica sin realizar. Las similitudes no acreditan identidad del evento. Los formatos técnicos de fecha y los códigos permanecen intactos.

La [organización de data](data/README.md) distingue las fuentes originales, los libros de manejo y la nueva base de partida. [BaseUnificada.xlsx](data/prepared/taller_2/BaseUnificada.xlsx) y [BaseUnificada.csv](data/prepared/taller_2/BaseUnificada.csv) contienen la hoja consolidada exportada con 5.640 filas y 18 columnas, sin aplicar limpieza adicional. Para regenerarlos se utiliza el grupo opcional `excel` de uv y `scripts/exportar_base_unificada.py`.

El [plan de limpieza actualizado](docs/plan_limpieza_datos.md) contempla las 18 columnas, las fuentes integradas y la auditoría por pasos. `python scripts/diagnosticar_base_unificada.py` verifica la entrada y genera su diagnóstico e inventario en `reports/limpieza/`. Todavía no ejecuta limpieza. Las plantillas de control están en `docs/plantillas_limpieza/`.

El [notebook de limpieza](notebooks/02_limpieza_base_unificada.ipynb) es el lugar principal de trabajo por etapas. Está ejecutado hasta L14. Los párrafos siguientes describen sus puntos de control históricos, no entregas alternativas. Puede leerse también en [HTML](reports/02_limpieza_base_unificada.html). Sus reglas están en `config/limpieza/estandarizacion_v1.json`, los resultados intermedios en `data/interim/taller_2` y el resumen de auditoría en `reports/limpieza/ultima_estandarizacion.json`.

L03 también está ejecutado: normaliza ausencias de las demás variables conservando su motivo, sin cambiar identificadores, imputar o quitar filas. Las reglas están en `config/limpieza/ausencias_v1.json` y la salida de esta etapa se identifica en `reports/limpieza/ultima_ausencias.json`. El CSV requiere la auditoría para distinguir tipos de ausencia; JSONL los representa como null y conserva texto vacío cuando corresponde.

L04 ya está ejecutado: fechas AAAA-MM-DD, números exactos en COP y periodo entero, sin eliminar filas. [La guía de formatos](docs/formatos_fechas_cop.md) explica el Excel y el intercambio CSV/JSONL. `reports/limpieza/ultima_tipificacion.json` identifica la salida tipada, sus hashes y sus alertas de revisión. Los resúmenes de L02 a L04 describen sus propios puntos de control.

L05 a L09 se ejecutaron con revisión del catálogo, cruces entre fuentes, controles administrativos y exportaciones. Ese punto de control contiene 5.602 registros tras consolidar 38 repeticiones exactas. El [reporte L09](reports/limpieza/reporte_cierre_limpieza.md) y `reports/limpieza/ultimo_cierre.json` conservan su evidencia histórica.

**Punto de control L10:** se resolvieron REG003600 y REG004804, recuperando cinco celdas y consolidando dos filas. El consolidado contiene 5.600 registros y 18 columnas y la cohorte principal tiene 5.000 códigos de solicitud distintos. La [revisión descriptiva L10](reports/limpieza/revision_descriptiva_y_parciales.md) conserva siete gráficos previos y su estado de categorías antes de la aclaración semántica posterior. `reports/limpieza/ultima_revision_descriptiva.json` identifica ese punto de control. Se homologaron 94 identificadores no informados a null, incluidos cuatro textos nan; el original y el motivo se conservan en auditoría.

**Punto de control L11:** Nuevo se agrupó analíticamente con Admitido y Matriculado permaneció separado. La revisión conservó 5.600 registros antes de incorporar CRM y ofreció las vistas de 5.000 solicitudes principales, 2.924 códigos de aspirante principales y 90 solicitudes sin ID. El [reporte L11](reports/limpieza/reporte_estados_personas_y_cierre.md) y `reports/limpieza/ultima_identidad_estados.json` conservan esa evidencia histórica. La entrega actual incorpora CRM y mantiene Oracle dentro de la tabla integrada.

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group notebooks --group excel python scripts/ejecutar_notebook.py --notebook notebooks/02_limpieza_base_unificada.ipynb
```

## Taller 2: múltiples fuentes

Los cuatro archivos recibidos están organizados en `docs/referencias/taller_2`, `data/raw/taller_2` y `sql/fuentes/taller_2`, con sus bytes originales y hashes registrados. Consulta [el análisis del taller y la ruta de trabajo](docs/analisis_taller_2.md).

La revisión de fuentes se reproduce con `python scripts/revisar_fuentes_taller_2.py` y genera `reports/taller_2/revision_fuentes.json`. Es una inspección de archivos. La vista Oracle y la integración en Power Query están respaldadas en los archivos del proyecto y en el libro de manejo. El notebook de limpieza continúa ese proceso y genera una versión de revisión; la aprobación administrativa definitiva está pendiente.

Para preparar la fuente Oracle del taller, con Docker activo, ejecuta `python scripts/preparar_oracle.py`. Usa un proyecto Docker independiente y crea el esquema CASO2 y una vista compatible. Consulta [la guía de conexión desde DBeaver y Excel](docs/oracle_taller_2.md). La limpieza actual se ejecuta en Python; su notebook no acredita que las mismas transformaciones se hayan realizado en Power Query.

El [reporte comparativo de las cuatro fuentes](docs/reporte_comparativo_fuentes_taller_2.md) describe la compatibilidad de las 15 columnas y los perfiles y solapamientos. Su respaldo está en `reports/taller_2/comparacion/`. Para actualizarlo, captura primero la vista con `python scripts/capturar_vista_oracle.py` y ejecuta `python scripts/analizar_relaciones_taller_2.py`. Estos comandos no aplican limpieza ni integración.

## Instalar o actualizar la base compartida

Después de clonar el repositorio o ejecutar `git pull --ff-only`, con Docker en ejecución:

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group notebooks --group excel python scripts/sincronizar_bd.py
```

Con pip y un entorno Python 3.12 activado:

```bash
python -m pip install -r requirement.pip
python scripts/sincronizar_bd.py
```

También se admite `requirements.txt`. El sincronizador crea `.env` con contraseña local si falta, verifica el CSV, reproduce las dos tablas actuales y aplica una sola vez cada versión SQL pendiente. Las versiones se registran en `public.migraciones_proyecto`. La limpieza integrada se ejecuta en los notebooks. Este sincronizador conserva las tablas de la etapa original y tipada y carga la entrega final en la capa analítica con trazabilidad.

Consulta [la guía para trabajar en varios computadores](docs/trabajo_compartido.md). Git comparte archivos y procedimientos; cada equipo mantiene su propio volumen PostgreSQL. El pull descarga las migraciones y el comando anterior las aplica. No se modifican los datos originales ni se copian volúmenes entre equipos.


Proyecto académico para explorar el CSV del Instituto Universitario Horizonte y preparar el primer informe descriptivo. La referencia principal es la clase **Calidad de datos**; el alcance se define en la guía del caso.

## Estado

- Proyecto Python 3.12 administrado con **uv**, entorno `.venv` y versiones reproducibles en `uv.lock`.
- Dependencias: pandas para análisis, matplotlib para gráficos, psycopg para PostgreSQL y python-dotenv para configuración local.
- CSV y materiales originales conservados; hashes de integridad registrados.
- PostgreSQL 17 preparado en Docker con una tabla `public.admisiones_original`, 15 columnas TEXT, sin deduplicación ni limpieza.
- Perfil estructural ejecutable sin Docker; guía teórica, plan y plantilla de informe preparados.
- **Base montada y verificada:** PostgreSQL está en ejecución en Docker Desktop; sus 5.040 filas y 15 columnas coinciden con el CSV, incluidos duplicados, vacíos y espacios. Las consultas exploratorias se ejecutaron correctamente.
- **Pendiente del informe:** completar fechas, reglas de negocio, cruces y visualizaciones. La integración con Ubuntu ya está activa. Si una terminal antigua muestra `permission denied`, ejecuta `newgrp docker` para actualizar los grupos de esa sesión.

## Organización

```text
.
├── data/raw/                   # CSV original, sin editar
├── docs/
│   ├── referencias/            # Guía PDF, dos presentaciones y hashes
│   ├── teoria/                 # Síntesis aplicada y textos de apoyo
│   ├── base_datos.md           # Conexión, carga y persistencia
│   ├── diccionario_datos.md    # Significado provisional y controles
│   └── plan_informe_exploratorio.md
├── docker/                    # SQL de inicialización y manifiesto del CSV
├── notebooks/                 # Espacio reservado para exploración interactiva
├── reports/
│   ├── exploracion/            # Perfil generado y evidencia inicial
│   └── plantillas/             # Estructura del informe por completar
├── sql/exploracion/            # Consultas de solo lectura
├── src/analitica_admisiones/   # Perfilamiento y arranque/verificación de BD
├── tests/                     # Pruebas de preservación de valores
├── compose.yaml
├── iniciar_bd.py              # Entrada compatible para iniciar la BD
├── pyproject.toml
└── uv.lock
```

## Preparar Python en WSL

Desde esta carpeta:

```bash
uv sync --locked
```

No es necesario activar manualmente el entorno cuando usas `uv run`. La versión base está indicada en `.python-version`. No reutilices la `.venv` de WSL desde Python de Windows: recrea el entorno para el sistema donde trabajes.

## Empezar mientras se instala Docker

```bash
uv run analitica-admisiones perfilar
```

Genera en `reports/exploracion/`:

- `perfil_inicial.json`: estructura, duplicados, vacíos y resumen numérico.
- `completitud.csv`: cantidad y porcentaje de vacíos por campo.
- `frecuencias_originales.csv`: categorías sin normalizar; incluye representación JSON para hacer visibles espacios y vacíos.

El comando verifica el hash del CSV antes y después. Los porcentajes de categorías usan las 5.040 filas originales. Las estadísticas numéricas se calculan en memoria sobre valores finitos interpretables e incluyen su denominador y valores rechazados; no certifican su validez de negocio. Las fechas aún no se interpretan automáticamente para evitar resolver ambigüedades sin una regla.

## Cuando Docker esté listo

Mantén Docker Desktop en ejecución y habilita su integración con tu WSL. Comprueba `docker version` y `docker compose version`.

En esta instalación ya existe `.env` con una contraseña local generada. En una copia nueva del proyecto, copia `.env.example` a `.env` y reemplaza la contraseña de ejemplo antes de iniciar.

```bash
uv run analitica-admisiones bd
```

También sigue funcionando `uv run python iniciar_bd.py`. Arranca PostgreSQL, importa el CSV al inicializar un volumen vacío y compara todas las filas cargadas con el original, incluyendo sus multiplicidades. La comprobación no depende del orden de las filas.

Conexión local: `localhost:5433`, base `admisiones`, usuario `analista`, contraseña en `.env`. El volumen conserva los datos al detener el contenedor. El puerto es configurable en `.env`.

Para ejecutar las consultas preparadas desde WSL:

```bash
docker compose exec -T postgres psql -X -v ON_ERROR_STOP=1 -U analista -d admisiones < sql/exploracion/01_perfil_original.sql
```

Consulta [las instrucciones de la base](docs/base_datos.md) para detalles. Las consultas se validaron sobre PostgreSQL en Docker Desktop.

## Preparar el informe

1. Lee [el marco teórico aplicado](docs/teoria/marco_para_informe.md), basado principalmente en Calidad de datos.
2. Sigue [el plan de trabajo](docs/plan_informe_exploratorio.md).
3. Revisa [el diccionario](docs/diccionario_datos.md) y las evidencias generadas.
4. Completa [la plantilla](reports/plantillas/informe_exploratorio.md).

La guía exige **cinco hallazgos**, **al menos tres tablas o gráficos**, diagnóstico de calidad y **tres preguntas posteriores a la limpieza**. La extensión sugerida es de **2–4 páginas**, sin anexos. Los documentos preparados son apoyo de trabajo, no un informe final terminado.

## Verificación

```bash
uv run python -m unittest discover -s tests -v
uv sync --locked --check
```

Las pruebas comprueban que se conserven espacios, vacíos, campos con comas y duplicados, que se rechacen filas mal formadas y que valores no interpretables no se conviertan a cero.

## Reglas del proyecto

- No editar `data/raw/` ni modificar `admisiones_original` durante la primera exploración.
- Mantener las categorías tal como están; cualquier agrupación posterior requiere una regla documentada.
- Distinguir filas, solicitudes, aspirantes únicos y matrículas efectivas.
- No deducir causalidad ni tasas definitivas de conversión sin definir entidad, denominador y ventana temporal.
- Documentar fuente, regla, evidencia, impacto y limitaciones de cada hallazgo.
- No compartir `.env`. El repositorio utiliza Conventional Commits sin trailers ni atribuciones.

## Gráficos descriptivos

`uv run analitica-admisiones graficar` genera seis figuras en PNG y PDF sin modificar el CSV. Consulta [la guía de lectura](reports/figuras/guia_lectura.md) para su interpretación y selección en el informe. Incluye distribuciones categóricas, numéricas con diagramas de caja, cobertura temporal y completitud.

## Notebook ejecutado del informe

El respaldo principal está en `notebooks/01_respaldo_informe_descriptivo.ipynb`. La vista HTML se exporta a `reports/01_respaldo_informe_descriptivo.html` e incluye tablas y gráficos. Las evidencias tabulares quedan en `reports/respaldo_notebook/`.

Para instalar las herramientas del cuaderno:

```bash
uv sync --locked --group notebooks --group excel
```

Para ejecutar de nuevo todas sus celdas y exportar HTML:

```bash
uv run --group notebooks python scripts/ejecutar_notebook.py
```

La ejecución necesita comunicaciones locales entre Jupyter y su kernel. No requiere Docker ni conexión a PostgreSQL: el origen es el CSV intacto. No necesita acceso a Internet después de sincronizar las dependencias.

El cuaderno separa datos originales, controles de calidad, frecuencias y porcentajes, cruces, estadísticas numéricas, gráficos, equivalencias propuestas e hipótesis pendientes. Sus verificaciones finales contrastan las cifras del informe y el hash del CSV.

`scripts/construir_notebook.py` reconstruye las celdas desde la plantilla y borra las salidas guardadas; úsalo solo para regenerar el cuaderno, seguido de la ejecución anterior.

## Seguimiento y mantenimiento

La comprobación de la entrega antes del análisis está en [el notebook 03](notebooks/03_validacion_previa_analisis.ipynb), ejecutado con tablas y gráfico de cobertura. Complementa el notebook de limpieza sin modificar sus datos ni volver a publicar el entregable. Revisa faltantes por grupo, los 500 pares Oracle contra los valores finales, un escenario hipotético para los 49 pares compatibles y los denominadores de cada indicador. Consulta [la última validación](reports/validacion_analisis/ultima_validacion.json) para localizar el reporte y las evidencias.

Para reproducir esta comprobación:

```bash
uv run --group notebooks python scripts/ejecutar_notebook.py --notebook notebooks/03_validacion_previa_analisis.ipynb
```

`scripts/construir_notebook_validacion_analisis.py` reconstruye la plantilla del notebook 03 y borra sus resultados guardados. Después debe ejecutarse con el comando anterior. El escenario de sensibilidad no elimina registros de BaseUnificada y no confirma duplicados entre sistemas.

Consulta [la bitácora](BITACORA.md) para decisiones, verificaciones y pendientes. La preparación de una segunda tabla está descrita en [el plan de la base](docs/plan_preparacion_base.md). `python3 scripts/respaldar_bd.py` crea un respaldo local y verifica su índice. Los cambios de estructura se documentarán antes y después de aplicarlos.

## Estructura tipada sin limpieza

Se creó `public.admisiones_tipadas` con las mismas 5.040 filas, tipos DATE y NUMERIC, categorías originales y trazabilidad completa. Cada fila conserva sus 15 valores TEXT de origen en `datos_originales`; los textos que no caben en una fecha o número permanecen allí con su motivo en `observaciones_tipado`. La tabla `admisiones_original` sigue intacta.

Consulta [el alcance del tipado](docs/estructura_tipado_sin_limpieza.md) y [el análisis del futuro modelo estrella](docs/analisis_modelo_estrella_powerbi.md). No se ha realizado limpieza ni construido un ETL dimensional.

Para validar o repetir la proyección sin duplicar filas: `uv run --group notebooks python scripts/preparar_tipos.py`. El script falla si la proyección existente fue alterada, en vez de reemplazar datos. La migración pertenece a `sql/migrations/` y no exige reinicializar Docker.

## Análisis administrativo y Power BI

La siguiente fase sigue [el plan de análisis y dashboard](docs/plan_analisis_administrativo_powerbi.md). El informe y Power BI utilizarán la misma base y definiciones de indicadores. El notebook 04 ya calcula el análisis y deja un borrador administrativo para revisión. El dashboard está construido y verificado contra ese análisis; se describe en [Dashboard en Power BI](#dashboard-en-power-bi). Las acciones son propuestas, no decisiones institucionales adoptadas.

## Base analítica en PostgreSQL y alternativa Excel

PostgreSQL está actualizado con la base final, sus fuentes y trazabilidad. La vista `analitica.base_unificada` contiene los mismos 5.500 registros y 18 columnas del Excel entregable. Las tablas originales y tipadas de 5.040 filas se conservan. [La guía de conexión y sincronización](docs/postgresql_base_unificada_powerbi.md) explica los esquemas, las pruebas y cómo elegir PostgreSQL o Excel para Power BI. La [plantilla Power Query](powerbi/BaseUnificada.pq) prepara una consulta con fuentes alternativas. No se anexan las dos copias. El dashboard usa esta plantilla con origen Excel y su carga se comprobó en Power BI Desktop; la opción PostgreSQL sigue disponible en la misma plantilla.

## Análisis administrativo ejecutado

El [notebook 04](notebooks/04_analisis_administrativo.ipynb), disponible también en [HTML](reports/04_analisis_administrativo.html), responde la pregunta general, las tres específicas y la línea adicional de segmentos. Incluye canales comparables, puntajes y documentación por estado, asesor, recurrencia, intervalos aptos y antes y después con universos separados. El análisis no aplica inferencia automática ni presenta registros como personas independientes.

La [redacción para el informe en Drive](reports/analisis_administrativo/seccion_informe_drive.md) tiene marcadores de las tres figuras principales. La [guía de inserción](reports/analisis_administrativo/guia_insercion_y_figuras.md) explica qué agregar y cómo revisar la numeración de figuras. El [reporte de respaldo](reports/analisis_administrativo/reporte_analisis_administrativo.md) conserva las preguntas, hallazgos y acciones propuestas. Las tablas y siete figuras en PNG y PDF están en reports/analisis_administrativo. La base de entrega no se modifica. No se actualizó Drive ni se creó un PBIX en esta fase.

Para repetir únicamente el análisis:

```bash
uv run --locked --group notebooks --group excel python scripts/ejecutar_notebook.py --notebook notebooks/04_analisis_administrativo.ipynb
```

La plantilla se reconstruye con scripts/construir_notebook_analisis_administrativo.py. El cálculo está en src/analitica_admisiones/analisis_administrativo.py y sus criterios en config/analisis_administrativo.json. Los metadatos registran entradas, código, reglas, archivos generados y controles.

## Interpretación de negocio y cuadro de indicadores

El notebook 04 incorpora respuestas explícitas a la pregunta general y las tres hipótesis, diez indicadores con sus definiciones y seis decisiones propuestas. [La síntesis de inteligencia de negocios](reports/analisis_administrativo/sintesis_inteligencia_negocios.md) resume qué sabemos, qué oportunidades priorizar para revisión y qué indicadores aún no se pueden calcular. [La misma redacción administrativa](reports/analisis_administrativo/seccion_informe_drive.md) integra esta lectura, sin crear otra versión de la base. Los responsables y metas son propuestas para acordar con la institución. La incorporación al informe principal en Drive sigue pendiente; el dashboard ya muestra estas respuestas, indicadores y decisiones.

La respuesta a H3 ya incluye la distribución de los seis estados por documentación y asesor dentro de programa, modalidad y periodo, además de los porcentajes globales. Los perfiles condicionados y sus detalles están en las tablas H3 del mismo análisis. Esta ampliación deja 28 controles correctos y mantiene las condiciones de identidad y actualización. La incorporación de la sección al informe principal en Drive continúa pendiente.

## Dashboard en Power BI

El proyecto de Power BI está en `powerbi/DashboardAdmisiones/`, en formato PBIP. Lo genera `scripts/construir_dashboard_powerbi.py` a partir de la [plantilla Power Query](powerbi/BaseUnificada.pq), con el Excel entregable como origen. No modifica la base ni repite la limpieza.

Para configurar la ruta del equipo y abrirlo, cierra primero el proyecto en Power BI y ejecuta desde la raíz:

```powershell
uv run python scripts/configurar_powerbi_windows.py
```

También funciona con `python scripts/configurar_powerbi_windows.py`, sin dependencias adicionales. Después abre `powerbi/DashboardAdmisiones/DashboardAdmisiones.pbip` y pulsa Actualizar. Un único parámetro RutaProyecto resuelve el Excel y los seis CSV mediante rutas relativas. Cada integrante configura su carpeta una vez, sin regenerar el dashboard. La [guía para Windows](powerbi/README.md) explica las alternativas, el trabajo compartido y la entrega PBIX. El generador completo se reserva para reconstrucciones deliberadas porque reemplaza archivos del modelo y del informe.

El modelo es un esquema estrella: la tabla de hechos FactRegistros, con una fila por registro y 22 medidas, y nueve dimensiones (programa con facultad, duración y nivel; modalidad, canal, estado, ciudad, asesor, periodo, fuente y fecha). Las relaciones son de uno a varios y filtran en una sola dirección. DimFecha está marcada como tabla de fechas; la fecha de matrícula tiene una relación inactiva cuyo uso requiere una medida específica con `USERELATIONSHIP`. Aparte hay seis tablas de respaldo que leen `reports/analisis_administrativo/tablas/`: canales con pesos comunes, H3 con pesos comunes, escenario de 49 pares, respuestas, indicadores y decisiones. No se relacionan con la estrella porque son resultados calculados sobre la base completa.

| Página | Contenido |
| :--- | :--- |
| Inicio | Portada académica con identificación del caso y accesos a las seis páginas de análisis. |
| Panorama de admisiones | Registros, Matriculado, proporción observada y códigos por origen; barras por programa, canal, estado y modalidad. |
| Captación y segmentos | Matriz programa por ciudad, % Matriculado por canal y segmentos de ciudad, programa y modalidad. |
| Seguimiento del proceso | Estados por documentación y por asesor, puntaje por estado, días a matrícula y recurrencia de códigos por fuente. |
| Cobertura y condiciones | Serie mensual con fechas aptas, registros por fuente y cobertura de puntaje e importe por programa. |
| Comparaciones controladas | Brecha entre canales bruta y con pesos comunes, H3 con pesos comunes y segmentos de al menos 30 registros en el escenario de 49 pares. |
| Respuestas y decisiones | Respuestas a la pregunta general, H1, H2, H3 y mercado; indicadores K01 a K10 y decisiones D1 a D6. |

Las cuatro primeras páginas de análisis comparten seis filtros: periodo, programa, modalidad, canal, ciudad y fuente. Las dos últimas no cambian con los filtros y lo indican en su subtítulo. La unidad es el registro de solicitud de origen, no la persona, y % Matriculado es una proporción observada, no una conversión definitiva.

Las medidas y tablas se consultaron en el motor de Power BI Desktop y coinciden con el notebook 04: 5.500 registros, 1.179 Matriculado, 3.424 códigos por origen, 90 sin código, 5.254 puntajes, 4.580 importes, 5.320 fechas aptas, 1.035 intervalos con mediana de 33 días, 514 Matriculado sin documentos completos, 20,0 % sin asesor, brecha entre canales de 4,03 y 3,20 puntos, 5.474 registros comparables y cambio máximo de 2,37 puntos con los 49 pares.
