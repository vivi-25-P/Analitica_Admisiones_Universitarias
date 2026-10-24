# Propuesta completa de limpieza de admisiones

**Estado:** planificación. No se aplica ninguna limpieza ni se modifican las tablas actuales.

**Fecha:** 21 de octubre de 2026.

## 1. Objetivo

Preparar una tabla de datos analíticos consistente, con reglas reproducibles y con toda decisión trazable al archivo recibido. El objetivo no es completar artificialmente la información ni asegurar que todas las filas sean correctas. Los casos sin evidencia suficiente deben permanecer identificados como pendientes.

## 2. Tablas y flujo propuesto

| Componente | Tratamiento |
|---|---|
| admisiones_original | Se mantiene intacta con 5.040 filas y las 15 columnas TEXT. |
| admisiones_tipadas | Se mantiene intacta como base técnica. Conserva fechas y números representables, valores originales y observaciones. |
| admisiones_limpias | Nueva tabla futura con el resultado de las reglas aplicadas. Su número final de filas dependerá de las decisiones sobre duplicados. |
| Control de limpieza | Relación entre filas de origen, registros resultantes, reglas, decisiones, incidencias y ejecución. El nombre definitivo se fijará al implementar. |

Python leería admisiones_tipadas junto con datos_originales y observaciones_tipado. El procesamiento trabajaría sobre una copia. Los resultados se guardarían en tablas nuevas después de validar, sin actualizar las bases de referencia.

## 3. Periodo académico como código entero

La propuesta del usuario es adecuada como representación práctica: 20261 para el primer periodo de 2026 y 20262 para el segundo. El tipo recomendado para el código es INTEGER. Su función es identificar y ordenar periodos; no es un importe ni una cantidad de solicitudes.

La regla de construcción sería año por 10 más número de periodo. El catálogo actual reconoce periodos 1 y 2. Las equivalencias y el calendario deben validarse institucionalmente antes de aplicar la regla en producción.

| Valor original | Código propuesto | Etiqueta para presentación | Filas originales |
|---|---:|---|---:|
| 2025-2 | 20252 | 2025, segundo periodo | 981 |
| 2026-I | 20261 | 2026, primer periodo | 1.005 |
| 2026-1 | 20261 | 2026, primer periodo | 1.028 |
| 2026 II | 20262 | 2026, segundo periodo | 1.042 |
| 2026-2 | 20262 | 2026, segundo periodo | 984 |

Antes de cualquier tratamiento de duplicados, las sumas serían 981 registros en 20252, 2.033 en 20261 y 2.026 en 20262. No son los conteos definitivos de una tabla limpia.

La implementación mínima puede guardar solo el código en la columna del periodo de la tabla limpia y obtener la etiqueta, año y número de periodo mediante una vista o una futura DimPeriodo. No se necesita añadir cuatro columnas físicas a la tabla principal únicamente para obtener esas representaciones.

Para Power BI, usar el código sin suma automática y un eje categórico cuando se represente como categoría. Puede mostrarse una etiqueta legible y ordenarla por el código. Los códigos no deben promediarse y su resta no mide periodos transcurridos.

La conversión no corrige la coherencia con las fechas. Los 410 registros del segundo periodo de 2025 con solicitudes de 2026 seguirían marcados para revisión; no se debe deducir el periodo correcto a partir de la fecha sin una regla institucional.

## 4. Reglas propuestas por columna

| Columna | Propuesta de limpieza | Qué se conserva o valida |
|---|---|---|
| registro_id | Revisar espacios externos y patrón. Separar identificadores repetidos por tipo de caso. | Mantener el código original y la referencia a cada fila. No asumir unicidad. |
| aspirante_id | Convertir ausencia real a un faltante explícito en la salida. Validar estructura y posibles asociaciones. | No inventar identificadores ni reconstruirlos automáticamente desde el correo. Hay 92 vacíos originales. |
| fecha_solicitud | Confirmar las convenciones de los cinco patrones y utilizar DATE. Las fechas no interpretables se registrarían como excepción. | No intercambiar día y mes por suposición ni corregir fechas por proximidad. |
| programa | Eliminar espacios externos y aplicar equivalencias explícitas del catálogo: Derecho y Especialización en Data Analytics. | Los 25 valores con solo espacio pasarían a faltante con motivo. La etiqueta Sin programa registrado se usaría para presentación, no como programa real. |
| modalidad | Unificar Virtual, Presencial e Híbrida mediante mapeo explícito. | Categorías desconocidas se señalan, no se asignan por parecido. |
| canal_captacion | Revisar espacios y concordancia con el catálogo. | No modificar atribución de canal sin evidencia. Actualmente hay seis etiquetas sin variantes evidentes. |
| estado_proceso | Homologar Admitido y Matriculado con sus variantes de escritura. | Conservar los siete estados distintos resultantes y validar su significado. No inferir secuencias históricas. |
| puntaje_admision | Mantener los números interpretables y distinguir valor registrado, pendiente y no informado. | 179 vacíos y 50 Pendiente no pasan a cero. No imputar media o mediana. Rango de aceptación pendiente de regla institucional. |
| documentos_completos | Homologar Sí, sí y SI a Sí. Conservar No y Pendiente como categorías diferentes. | No convertir a booleano perdiendo la categoría pendiente. |
| valor_matricula_cop | Mantener NUMERIC con precisión decimal, separando importe disponible, por definir y no informado. | 826 vacíos y 35 por definir no pasan a cero. No sustituir precios a partir del programa sin tarifas oficiales. |
| ciudad_residencia | Recortar espacios y mapear BOGOTA, Popayan y Cali con espacio a sus denominaciones acordadas. | No eliminar acentos de todos los nombres ni corregir ciudades por similitud automática. |
| asesor | Homologar asesor 1 a Asesor 1. Mantener el significado de Sin asignar. | No atribuir registros al asesor con más casos ni completar la asignación por suposición. |
| fecha_matricula | Aplicar convenciones de fecha confirmadas. Distinguir No aplica, no informado y fecha disponible. | No rellenar la fecha con la de solicitud ni inferirla del estado. Validar coherencia temporal. |
| correo | Revisar espacios externos y estructura; normalizar el dominio si procede. | No corregir direcciones por adivinación ni convertir la parte local a minúsculas sin una regla. Un patrón válido no prueba entregabilidad o identidad. |
| periodo_academico | Utilizar código INTEGER como 20252, 20261 y 20262 a partir de equivalencias confirmadas. | Conservar el texto de origen y tratar aparte las discrepancias con las fechas. |

## 5. Tratamiento separado de duplicados

### Duplicados exactos

Se detectaron 38 pares, que involucran 76 filas. La propuesta es conservar una representación por par solo después de aprobar que cada par describe el mismo registro duplicado. La fila de menor posición puede ser el representante reproducible, pero su posición no demuestra que sea la versión más reciente o correcta.

Todas las filas relacionadas deben quedar enlazadas con el registro resultante. Si únicamente se excluyen esas 38 repeticiones adicionales, el resultado intermedio sería 5.002 filas. Esto todavía no acredita 5.002 solicitudes únicas.

### Pares con discrepancias

REG004804 tiene un espacio en programa en una fila e Ingeniería de Sistemas en la otra. REG003600 tiene por definir en un importe y 1.800.000 en el otro. No elegir automáticamente el valor más completo como verdad ni conservar solo la última posición del CSV. Se deben contrastar con la fuente.

Mientras no se resuelvan, pueden permanecer como registros con conflicto en la tabla de trabajo y excluirse solo de indicadores que exijan una solicitud inequívoca, dejando explícito el criterio. No se eliminan del repositorio de evidencia.

### Aspirantes repetidos

No deduplicar por aspirante_id solamente. Una persona puede presentar solicitudes legítimas. La clave de solicitud debe definirse antes de fusionar casos por programa y periodo. La normalización de categorías puede revelar nuevos candidatos, que deben revisarse y no eliminarse automáticamente.

## 6. Ausencias, atípicos y coherencia de negocio

Los vacíos se convertirían a NULL en la tabla limpia cuando corresponda, manteniendo su motivo en el control. Pendiente, No aplica, Sin asignar y por definir conservan sus diferencias de significado.

Los valores atípicos se revisarían con criterio estadístico y reglas institucionales. No se eliminarían por posición en un diagrama. Actualmente no se detectaron negativos ni extremos según el criterio intercuartílico utilizado en puntajes e importes.

Las alertas de negocio no se resuelven mediante cambios automáticos. Entre ellas están los 410 registros de periodo y fecha dispares, y la relación entre matrícula y documentación. Los 465 casos de matriculados con No o Pendiente se calcularon sobre la base original; después de deduplicar deben recalcularse con el nuevo denominador.

Las siete fechas de matrícula posteriores al 17 de octubre se detectaron usando esa referencia, no un corte institucional confirmado. No deben tratarse como errores por defecto. Al cambiar la fecha de referencia cambia ese control, no los datos históricos.

La disponibilidad parcial de septiembre de 2026 no se corrige inventando solicitudes. Debe quedar documentada como cobertura.

## 7. Qué pasaría con las cuatro columnas técnicas

| Columna actual | Uso durante la limpieza |
|---|---|
| fila_origen_csv | Referencia a cada fila recibida. No se renumera para ocultar exclusiones. Un resultado que represente varias filas necesita conservar todas sus relaciones. |
| origen_sha256 | Se conserva como referencia del archivo, preferiblemente registrada también en el lote de ejecución. |
| datos_originales | Permanece intacta en admisiones_tipadas. La salida limpia puede consultarla por referencia, sin duplicar otra vez todo el JSON. |
| observaciones_tipado | Permanece como diagnóstico técnico original. Las decisiones de limpieza se registran aparte, sin sobrescribirlo. |

La salida tendría una clave técnica propia y un enlace de trazabilidad a una o varias filas de origen. Para no acumular columnas operativas en la tabla analítica, se propone un control separado con identificador de ejecución, registro resultante, fila de origen, columna, valor anterior, valor posterior, regla, decisión y fecha. Su diseño definitivo se revisará al implementar.

Los códigos enteros de periodo serían una decisión de modelado de negocio en la salida, mientras que las columnas de trazabilidad solo registran su procedencia y tratamiento.

## 8. Ejecución propuesta desde Python

1. Generar respaldo y verificar CSV, versión de reglas y tablas de referencia.
2. Leer admisiones_tipadas incluyendo valores originales y motivos de tipado.
3. Identificar duplicados y conflictos con claves de origen, sin perder sus relaciones.
4. Aplicar las reglas de formato y categorías que estén confirmadas.
5. Construir el código entero de periodo mediante catálogo explícito.
6. Mantener sin resolver los casos que dependan de una fuente externa y registrar sus incidencias.
7. Validar cantidades, tipos, correspondencia de valores y trazabilidad.
8. Cargar la nueva tabla limpia y el control de cambios en una transacción. Si falla, no publicar una carga parcial.
9. Exportar un resumen del antes y después y actualizar la bitácora.

## 9. Comprobaciones de aceptación

| Control | Resultado esperado |
|---|---|
| CSV y tablas de referencia | Sin modificaciones |
| Conciliación de filas | Todas las filas de entrada explicadas como conservadas, vinculadas a una fusión o pendientes; no sumar incidencias superpuestas como si fueran filas diferentes |
| Códigos de periodo | Cada equivalencia aceptada produce el código documentado; valores desconocidos quedan señalados |
| Categorías | Coinciden con el catálogo aplicado y quedan disponibles sus valores anteriores |
| Ausencias numéricas | No pasan a cero ni se imputan sin metodología |
| Conflictos | Permanecen visibles mientras falte evidencia |
| Trazabilidad | Todo registro resultante puede vincularse con sus filas de origen y reglas |
| Repetición del proceso | La misma entrada y versión de reglas produce el mismo resultado sin duplicar la salida |
| Estadísticas | Se comparan antes y después con sus denominadores y exclusiones |

## 10. Compartir el resultado entre equipos

La nueva estructura se incorporaría mediante una migración posterior a 001_admisiones_tipadas.sql, sin editar la versión aplicada. El procedimiento Python y sus reglas se guardarían en Git.

El sincronizador actual aplica SQL y reproduce la base tipada. La ejecución versionada de una limpieza Python debe integrarse expresamente cuando se desarrolle; no basta con subir un archivo nuevo para que se ejecute. Cada ejecución necesita registrar versión, origen y resultado, y omitir una repetición ya aplicada o reconstruirla de forma controlada.

Después de pull, los demás equipos ejecutarían el sincronizador actualizado para reproducir la estructura y el tratamiento aprobados. Las modificaciones manuales dentro de una base local no se propagan por Git.

## 11. Decisiones pendientes antes de implementar

Confirmar catálogos y equivalencias, aprobar el tratamiento de duplicados exactos, resolver los dos pares discrepantes, definir solicitud única, confirmar convenciones de fecha, escala de puntajes, tarifas y significado del periodo académico. Las acciones técnicas pueden prepararse, pero las decisiones que necesitan evidencia no deben convertirse en correcciones inventadas.

## Referencias

Microsoft Learn, orden de una columna por otra: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-sort-by-column?tabs=powerbi-desktop

Evidencia local: reports/exploracion/revision_diagnostico_propuesto.json, notebook de respaldo y docs/estructura_tipado_sin_limpieza.md.
