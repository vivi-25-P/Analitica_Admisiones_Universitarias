# BaseUnificada en PostgreSQL y Excel

## Fuente vigente

PostgreSQL expone analitica.base_unificada con los mismos 5.500 registros y 18 columnas de deliverables/BaseUnificada_Entregable.xlsx, hoja BaseUnificada. Son dos formas de acceder a los mismos datos. No se anexan entre sí ni se cuentan como fuentes adicionales.

La carga utiliza la entrega y sus controles ya validados. No aplica otra limpieza, no imputa importes, no cambia estados y no modifica el Excel de entrega o su copia de Drive. Las fechas se almacenan como DATE, el importe como NUMERIC(18,2), el puntaje como NUMERIC y el periodo y duración como enteros. Los identificadores y las categorías son texto. Las ausencias siguen como NULL.

## Organización

| Ubicación | Contenido y función |
| :--- | :--- |
| public.admisiones_original | Las 5.040 filas originales, sin modificaciones. |
| public.admisiones_tipadas | La proyección histórica de 5.040 filas, con sus valores originales y observaciones. |
| fuentes.archivos | Bytes completos y SHA256 de las fuentes, integración, reglas y evidencias utilizadas. |
| fuentes.filas | Filas de los cuatro CSV fuente y de la entrada integrada, como valores originales de texto, sin transformar espacios o vacíos. |
| trazabilidad.ejecuciones | Identidad de la carga y manifiesto de los archivos utilizados. |
| trazabilidad.archivos_ejecucion | Relación entre cada ejecución, las rutas de evidencia y los archivos conservados. |
| trazabilidad.hojas | Las nueve hojas auxiliares del Excel, conservadas fila por fila. |
| trazabilidad.destinos | Los 5.640 vínculos entre fila de integración y registro final, incluidos los casos consolidados. |
| analitica.registros | Datos tipados por carga. Las cargas históricas permanecen para trazabilidad. |
| trazabilidad.publicacion_actual | Identifica la única carga que exponen las vistas vigentes. |
| analitica.base_unificada | Vista de los 18 atributos de negocio para análisis y Power BI. |
| analitica.origen_registros | Procedencia, incorporación CRM y similitud entre fuentes. |
| analitica.control_calidad | Ausencias, alertas y elegibilidad de fechas e intervalos. |
| analitica.control_economico | Los 100 aportes CRM y sus conceptos económicos separados. |

Los archivos completos de auditoría por etapa quedan consultables en fuentes.archivos. No se convierte cada uno de sus CSV históricos en una tabla analítica nueva. Los números de fila se refieren a registros CSV, con encabezado en la posición 1.

La exportación Oracle se conserva como captura de CASO2.V_ADMISIONES_BASE junto con el SQL recibido. No se consulta Oracle en vivo durante esta carga ni se exige mantener ese contenedor encendido para consultar PostgreSQL.

## Sincronizar en este PC o en otro equipo

Desde la raíz del repositorio, con Docker disponible:

```bash
git pull --ff-only
uv sync --locked --group notebooks --group excel
uv run --locked --group notebooks --group excel python scripts/sincronizar_bd.py
```

Con pip dentro de un entorno Python 3.12:

```bash
python -m pip install -r requirement.pip
python scripts/sincronizar_bd.py
```

La sincronización inicia PostgreSQL, verifica la tabla original contra su CSV, respalda la base, comprueba la proyección histórica y aplica las migraciones pendientes. Después carga o verifica la entrega integrada. Las migraciones 001 y 002 se registran una sola vez. No se editan migraciones ya aplicadas.

La carga se identifica mediante las huellas de los archivos y del código de carga. Repetir la misma carga verifica el contenido sin insertar otra copia. Si cambian las entradas se conserva una nueva instantánea interna y se publica solo después de validar todo dentro de una transacción. La vista vigente nunca suma las instantáneas históricas.

Si una carga existente está alterada, la sincronización falla en lugar de reemplazarla silenciosamente. No use analitica.registros directamente para contar la base vigente. Use analitica.base_unificada.

## Conexión desde Power BI Desktop

Opción PostgreSQL: Obtener datos, Base de datos PostgreSQL. Servidor localhost:5433, base admisiones y usuario analista. La contraseña es el valor local de POSTGRES_PASSWORD en .env. El puerto puede variar si POSTGRES_PORT fue configurado en otro valor. Seleccione Importar y la vista analitica.base_unificada.

Opción Excel: Obtener datos, Libro de Excel. Seleccione deliverables/BaseUnificada_Entregable.xlsx y la hoja BaseUnificada. Mantenga el nombre de la consulta de destino para que el resto del modelo utilice la misma tabla.

La plantilla [BaseUnificada.pq](../powerbi/BaseUnificada.pq) permite elegir Origen igual a PostgreSQL o Excel en una única consulta. Se pega en el editor avanzado y se ajustan el origen, servidor, base y ruta local del Excel. La plantilla mantiene el orden y los tipos de las 18 columnas. Es una plantilla de conexión, todavía no probada dentro de Power BI Desktop. No es un dashboard ni un archivo PBIX.

Si se utilizan controles en el modelo, sus alternativas Excel son las hojas Origen_Registros, Control_Calidad y Control_Economico. Se relacionan por registro_id y no se anexan como más solicitudes. La guía del dashboard especificará las relaciones y medidas.

No se incluyen credenciales en la consulta M, Git o el informe. El puerto del contenedor sigue publicado únicamente en localhost. El archivo Excel permite continuar el análisis si PostgreSQL no está iniciado. Su copia en Drive no se actualiza automáticamente al cargar la base.

La actualización programada en Power BI Service es una tarea posterior. Un servicio en la nube no accede al localhost de este PC como si fuera su propio PostgreSQL. La conectividad y actualización en Desktop se comprobarán durante la construcción del dashboard.

Documentación oficial: [conector PostgreSQL](https://learn.microsoft.com/en-us/power-query/connectors/postgresql) y [conector Excel](https://learn.microsoft.com/en-us/power-query/connectors/excel).

## Evidencia y pruebas

reports/limpieza/carga_postgresql.json registra la carga vigente, los controles y la igualdad de las tablas anteriores. Los 15 controles comparan todas las filas de la base final, las nueve hojas auxiliares, los 5.640 destinos, los archivos completos y sus huellas, las fuentes originales y las vistas de origen, calidad y economía.

data/backups conserva respaldos locales fuera de Git. scripts/verificar_carga_aislada.py restaura uno anterior a la migración 002 en una base temporal nueva. Aplica la migración, carga dos veces y comprueba que no duplique registros. Repite el escenario desde una instalación nueva con originales y tipadas. En ambos casos simula una alteración dentro de una transacción de prueba y exige que se detecte. La base temporal se retira al finalizar y la base de trabajo no se modifica.

No se han confirmado identidades globales entre Oracle y la principal, tarifas oficiales o pagos efectivos. PostgreSQL conserva los límites y las decisiones de la limpieza, no los resuelve por almacenar la información.
