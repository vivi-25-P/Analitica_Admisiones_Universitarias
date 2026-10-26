# Análisis de un futuro modelo estrella para Power BI

Este documento conserva la propuesta histórica previa a la limpieza. El estado actual y la ruta de construcción del dashboard están en [el plan de análisis administrativo y Power BI](plan_analisis_administrativo_powerbi.md). La entrega actual ya contiene 5.500 registros con controles, y su granularidad analítica es registro de solicitud de origen, sin independencia global de eventos confirmada.

## Conclusión y alcance

La información permite proyectar un modelo estrella después de la actividad de limpieza. En esta etapa no se crean dimensiones, tabla de hechos ni un ETL dimensional. La estructura actual es una base de exploración y tipado, no un modelo analítico validado.

La propuesta se apoya en la guía oficial de Microsoft: https://learn.microsoft.com/es-es/power-bi/guidance/star-schema. Las dimensiones describen entidades de análisis y la tabla de hechos reúne eventos o resultados a un nivel de detalle uniforme.

## Decisión principal: qué representa una fila de hechos

El objetivo sería una fila por solicitud única validada, asociada a su aspirante, programa, modalidad y periodo. La combinación exacta que identifica esa solicitud debe confirmarse con admisiones. registro_id no se puede usar todavía como clave única: hay 38 pares exactos y dos pares con discrepancias. Tampoco se puede asumir que un aspirante solo tiene una solicitud.

El identificador técnico fila_origen_csv sirve para trazabilidad de la carga, no para demostrar unicidad del negocio. Si se necesitara estudiar el registro recibido tal como está, el hecho tendría que llamarse y medirse como registro de origen, con un significado diferente.

## Componentes candidatos

| Componente futuro | Información de origen | Criterio pendiente |
|---|---|---|
| FactSolicitudes | Claves de dimensiones, identificador de solicitud, puntaje, valor de matrícula y fechas | Solicitud única, estado representado y matrícula efectiva |
| DimPrograma | programa | Denominaciones oficiales y equivalencias |
| DimModalidad | modalidad | Catálogo validado |
| DimCanal | canal_captacion | Significado de atribución del canal |
| DimEstado | estado_proceso | Catálogo y semántica de cada estado |
| DimDocumentacion o atributo de situación | documentos_completos | Distinguir Sí, No y Pendiente; decidir si basta como atributo de baja cardinalidad |
| DimAsesor | asesor | Identidad del asesor y tratamiento de Sin asignar |
| DimCiudad | ciudad_residencia | Catálogo y residencia asociada a la solicitud, sin asumir que es estable por persona |
| DimPeriodo | periodo_academico | Calendario institucional y correspondencia con fechas |
| DimAspirante | aspirante_id y, si el objetivo lo requiere, atributos de contacto | Identidad, ausencias y posibles discrepancias entre registros del mismo aspirante |
| DimFecha | fecha_solicitud y fecha_matricula | Calendario continuo y dos usos de la fecha |

No es obligatorio convertir cada columna en una dimensión separada. Se debe evitar una dimensión para el identificador de registro si no añade atributos útiles. Estado y documentación pueden modelarse como dimensiones pequeñas o como una dimensión de situación, según el diseño final.

## Relaciones y fechas

Las dimensiones necesitan claves técnicas únicas; se relacionarán con muchas solicitudes mediante esas claves. Las filas desconocidas o pendientes requieren un tratamiento explícito sin aparentar que representan una persona identificada. No se deben relacionar tablas usando nombres con variantes sin resolver.

Solicitud y matrícula son dos roles de fecha. En Power BI puede utilizarse una relación activa y otra inactiva con medidas explícitas, o dos dimensiones de fecha por rol si se necesita filtrar ambas fechas de forma independiente. La selección depende del informe, no de que existan dos columnas DATE.

Fuente oficial de fechas: https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables.

## Medidas posibles y límites

| Medida | Condición |
|---|---|
| Número de solicitudes | Contar filas de hechos solo después de validar su granularidad |
| Aspirantes distintos | Identidad validada; no interpretar una clave de desconocido como persona real |
| Promedio y mediana de puntaje | Mostrar cantidad de puntajes utilizados; no sumar puntajes como indicador de desempeño |
| Valor de matrícula registrado | No llamarlo recaudo o ingreso cobrado; definir cuándo tiene sentido sumar |
| Proporción de solicitudes matriculadas | Definir numerador, denominador, periodo y ventana de seguimiento |
| Días entre solicitud y matrícula | Fechas válidas y reglas para secuencias inconsistentes |

La base representa estados registrados, sin historial de transiciones. No permite reconstruir embudos reales, tiempos por etapa o retiro posterior a documentación pendiente. Una carga de este archivo tampoco crea por sí sola un historial de estados. Se necesitaría una fuente de eventos o capturas periódicas con fecha de observación.

## Ruta de ETL futura

1. Extraer del origen conservado y de su proyección tipada, incluyendo motivos y valores originales.
2. Ejecutar la actividad de limpieza con reglas versionadas y trazabilidad.
3. Resolver claves de solicitud y aspirante, duplicados, equivalencias, fechas y excepciones.
4. Cargar las dimensiones con claves estables y una política para desconocidos.
5. Cargar los hechos al nivel de detalle validado, con referencia a las filas de origen.
6. Conciliar conteos, agregados, registros excluidos y excepciones contra la etapa previa.
7. Conectar Power BI a las tablas analíticas y definir medidas y relaciones consistentes.

El flujo debe poder repetirse sin duplicar hechos o dimensiones. La política de nuevas cargas y cambios de estado se definirá cuando exista una fuente periódica; el CSV actual no aporta esa política.

## Decisiones que aún requieren validación

Definición de solicitud única, matrícula efectiva y periodo; catálogos oficiales; regla para pares con discrepancias; obligatoriedad de documentación; atribución del canal; correspondencia entre aspirante y contacto; fecha de corte o extracción. Estas decisiones afectan el modelo y no deben sustituirse por suposiciones técnicas.
