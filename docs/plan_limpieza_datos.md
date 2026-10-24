# Plan de limpieza y transformación de BaseUnificada

Actualización: 24 de octubre de 2026.

Estado: diagnóstico e inventario preparados y primer avance ejecutado en notebooks/02_limpieza_base_unificada.ipynb. Se completaron L00, la comprobación de procedencia y documentación de pendientes de L01, y la estandarización textual de L02. Se mantienen 5.640 filas y 18 columnas. No se eliminaron ni consolidaron registros y no se modificaron los archivos BaseUnificada de partida.

## 1. Qué cambia respecto al plan anterior

El plan del 21 de octubre partía del CSV inicial de 5.040 filas y 15 columnas, y proponía procesar admisiones_tipadas desde Python. La entrada actual es la base consolidada de 5.640 filas y 18 columnas, después de transformaciones e integración realizadas en Excel y Power Query.

La versión anterior se conserva en docs/historial/plan_limpieza_datos_2026_10_21.md. Sus cifras siguen describiendo la fuente inicial, pero no deben reutilizarse como diagnóstico de la base consolidada.

| Aspecto | Ajuste del plan |
| :--- | :--- |
| Entrada | data/prepared/taller_2/BaseUnificada.xlsx y su CSV equivalente, con hash registrado |
| Herramienta principal | Notebook de Python, según la decisión de trabajo del usuario; la integración previa permanece documentada en Power Query |
| Columnas | Incluir facultad, duracion_semestres y nivel_formacion, además de las 15 iniciales |
| Punto de partida | Reconocer las transformaciones ya hechas; no presentarlas como nuevas correcciones |
| Duplicados | Revisar repeticiones internas y solapamientos entre principal, CRM y Oracle por separado |
| Importes | Distinguir el total calculado de CRM de los importes recibidos de las otras fuentes |
| Catálogo | Registrar la selección de siete programas y revisar la asignación mediante fuzzy |
| Seguimiento | Identificar cada fila de entrada y registrar pasos, cambios, exclusiones y correspondencias de salida |
| Resultado | Nueva salida limpia con controles, sin sobrescribir la base de partida |

La entrada ya incorpora separación de identificadores CRM, suma económica, Clean y Trim en identificadores, capitalización y tratamiento de espacios en determinadas categorías, selección del catálogo y Merge de atributos. La fecha de corte de este plan no acredita que todos los criterios de negocio estén validados.

El notebook es ahora la bitácora ejecutable del proceso y seguirá la secuencia de reglas de este documento. Mantendrá código, explicaciones y resultados. Si el entregable académico exige demostrar las mismas transformaciones en Power Query, deberán replicarse y documentarse allí; el notebook no acredita por sí solo esa ejecución en Excel.

Decisión de alcance del usuario, 24 de octubre: la comparación de identificadores entre sistemas se pospone hasta la etapa de cruces. Los códigos de Oracle se conservan como llegaron, igual que los de las demás fuentes. No se exige que coincidan, no se crean equivalencias de personas ni se eliminan filas por compartir o diferir en identificador durante las primeras etapas. Esta revisión posterior no impide continuar la estandarización. El índice BU sirve exclusivamente para auditar filas y no sustituye los códigos de negocio.

## 2. Diagnóstico actualizado de entrada

Las cifras se recalcularon desde el CSV preparado, cuyo SHA256 coincide con sus metadatos. La serialización CSV representa nulos y textos vacíos como celdas vacías; para recuperar el significado anterior debe consultarse la fuente correspondiente.

| Control | Resultado actual |
| :--- | ---: |
| Filas | 5.640 |
| Columnas de negocio | 18 |
| registro_id distintos | 5.500 |
| Grupos con registro_id repetido | 139 |
| Filas involucradas en esos grupos | 279 |
| Repeticiones adicionales de registro_id | 140 |
| Repeticiones exactas adicionales de las 18 columnas | 38 |
| aspirante_id vacíos | 92 |
| aspirante_id con texto nan | 4 |
| Programa vacío | 25 |
| Programa Sin Especificar | 2 |
| Facultad, duración y nivel sin asignar | 27 en cada columna; corresponden a las mismas filas |
| Puntaje vacío | 200 |
| Puntaje Pendiente | 51 |
| Valores de matrícula vacíos | 907 |
| Valores de matrícula por definir | 35 |
| Correo vacío | 131 |
| Fecha de matrícula vacía | 3.065 |
| Fecha de matrícula No aplica | 1.369 |

Hay 5.389 puntajes numéricos y 4.698 importes numéricos. Los puntajes están entre 40 y 100. Los importes llegan hasta 3.807.591 COP por la incorporación del total CRM. Ese máximo no se debe declarar error por superar los 3.500.000 COP observados en la primera fuente.

Con las convenciones actuales se interpretan las 5.640 fechas de solicitud y 1.206 fechas de matrícula. Interpretar una fecha no demuestra su exactitud. La cobertura de solicitudes llega ahora hasta el 10 de diciembre de 2026 por la fuente Oracle; ya no corresponde describir toda la base como cortada en septiembre.

Las alertas de periodo y documentación también cambian: hay 470 solicitudes de 2026 asociadas al segundo periodo de 2025 y 524 filas con estado Matriculado y documentos No o Pendiente. Son conteos previos a la conciliación, no errores confirmados.

## 3. Primera acción: congelar e identificar la entrada

La base preparada queda como versión de referencia y no se sobrescribe al limpiar. Antes de trabajar se verifica su hash y se genera una identificación técnica por fila, ligada a esa versión.

Se preparó reports/limpieza/inventario_entrada.csv con 5.640 identificadores desde BU000001 hasta BU005640, posición en CSV, identificadores de negocio, hash de la fila y hash del archivo. El número de fila CSV incluye el encabezado; por ejemplo, BU000001 corresponde a la posición 2.

Este identificador es necesario porque registro_id no es único. En Power Query se puede añadir un índice temporal antes de ordenar, filtrar o consolidar. El índice y el hash de entrada deben conservarse en la auditoría, aunque no formen parte de las 18 columnas de la salida administrativa.

El origen de cada registro debe reconstruirse a partir de las fuentes y del libro de manejo. Los rangos iniciales del anexado solo pueden utilizarse si se confirma el orden de la versión congelada: 5.040 principal, 100 CRM y 500 Oracle. No se debe volver a inferir el origen por posición después de ordenar o filtrar. Los códigos REG y ANX2 no bastan para separar principal de CRM.

## 4. Secuencia de trabajo y reglas

| Paso | Acción propuesta | Efecto esperado sobre las filas | Evidencia |
| :--- | :--- | :--- | :--- |
| L00 | Congelar entrada, verificar hash y asignar índice | Mantener 5.640 | Inventario de entrada |
| L01 | Reconstruir procedencia y confirmar conceptos y catálogos | Mantener filas | Relación con fuentes y decisiones pendientes |
| L02 | Normalizar categorías mediante equivalencias explícitas | No elimina filas | Cambios por columna y frecuencias antes y después |
| L03 | Tratar ausencias y separar motivos | No elimina filas | Vacíos, pendientes, no aplica y valores no interpretables |
| L04 | Representar números y fechas con reglas documentadas | No elimina filas | Conversiones exitosas, alertas y excepciones |
| L05 | Revisar el enriquecimiento de programas y sus coincidencias | No elimina filas por defecto | Programa original, programa asignado y regla |
| L06 | Revisar duplicados exactos | Reducción solo si se acuerda consolidarlos | Todas las filas vinculadas al representante |
| L07 | Conciliar repeticiones parciales y solapamientos entre fuentes | Cantidad pendiente de decisiones | Evidencia, fuente preferida por atributo y conflictos |
| L08 | Evaluar coherencia administrativa | Mantener casos pendientes visibles | Incidencias, sin inventar correcciones |
| L09 | Validar, exportar y comparar resultados | Conciliar todas las entradas | Base limpia, auditoría y reporte final |

Este orden separa las reglas de representación de las decisiones de identidad. Después de normalizar pueden aparecer nuevas coincidencias exactas; deben volver a contarse y distinguirse de las 38 observadas al inicio.

## 5. Tratamiento de las 18 columnas

| Columna | Tratamiento propuesto | Qué no debe decidirse automáticamente |
| :--- | :--- | :--- |
| registro_id | Conservar el código de origen; posponer correspondencias y validación entre sistemas hasta los cruces | Cambiar códigos Oracle o eliminar filas por su identificador |
| aspirante_id | Conservar vacíos, códigos y marcadores recibidos; mantener su diagnóstico sin resolver identidades todavía | Crear identificadores, convertir nan del identificador en esta etapa o unir personas solo por correo |
| fecha_solicitud | Aplicar reglas por formato y conservar valor previo y procedencia | Intercambiar día y mes o sustituir la fecha Oracle por la principal sin evidencia |
| programa | Unificar nombres y tildes mediante catálogo aprobado | Asignar un programa a los 27 casos sin identificación útil |
| modalidad | Conservar la modalidad de la solicitud y su catálogo de tres valores | Sustituirla por la modalidad única del catálogo reducido |
| canal_captacion | Revisar que las seis categorías actuales coincidan con el catálogo adoptado | Cambiar la atribución comercial por semejanza de texto |
| estado_proceso | Mantener siete estados con nombres acordados y significado documentado | Inferir transiciones o reclasificar matriculados por documentación |
| puntaje_admision | Representar números; mantener motivo de ausencia para 200 vacíos y 51 Pendiente | Sustituir por cero, media o mediana; asumir escala oficial por el rango observado |
| documentos_completos | Unificar Sí, sí y SI en Sí; conservar No y Pendiente | Reducir a booleano perdiendo la situación pendiente |
| valor_matricula_cop | Representar el importe reportado y registrar su concepto por fuente | Sumar, restar o sustituir importes entre fuentes sin una definición común |
| ciudad_residencia | Unificar Bogota con Bogotá y Popayan con Popayán; revisar presentación de nombres | Corregir ciudades desconocidas por parecido |
| asesor | Mantener las categorías actuales y el significado de Sin Asignar | Completar una asignación por suposición |
| fecha_matricula | Interpretar fechas y distinguir ausencia de No aplica en el control | Inventar fechas o interpretar toda ausencia como un error |
| correo | Revisar espacios y estructura; conservar el valor recibido como evidencia | Corregir cuentas por adivinación o asumir identidad y entregabilidad |
| periodo_academico | Convertir en L04 mediante equivalencias a INTEGER con códigos 20252, 20261 y 20262, según la decisión del usuario del 24 de octubre | Tratarlo como fecha o corregirlo a partir del año de solicitud |
| facultad | Revisar asignación del catálogo y conservar 27 pendientes | Presentar la selección de Ingeniería para Data Analytics como validación oficial |
| duracion_semestres | Representar como entero; validar duraciones adoptadas; mantener 27 pendientes | Asumir que los ajustes manuales acreditan la duración institucional |
| nivel_formacion | Mantener Pregrado y Posgrado según catálogo validado; conservar 27 pendientes | Inferir el nivel como dato confirmado solo por el nombre del programa |

### Equivalencias observadas que deben quedar documentadas

Data Analytics aparece en 574 filas sin tilde y 676 con tilde. Si se acepta una denominación común, ambas sumarían 1.250 filas antes de deduplicar. Las 574 equivalencias de nombre modifican celdas, no eliminan 574 solicitudes.

En documentación, Sí aparece 1.332 veces, sí 1.020 y SI 1.019. Su agrupación daría 3.371 respuestas afirmativas antes de deduplicar. No y Pendiente conservan su significado.

En ciudad, Bogota tiene 605 filas y Bogotá 702; Popayan tiene 509 y Popayán 657. Los cambios de escritura deben registrarse por fila, manteniendo su correspondencia.

### Controles de validez adicionales

La revisión de patrones y correspondencias de identificadores se reserva para los cruces posteriores. REG, A y ANX2 pertenecen a convenciones distintas; su diferencia no se declara un error ni obliga a cambiar los códigos. Los conteos de repeticiones permanecen como diagnóstico, sin usarse como criterio de eliminación en las primeras etapas.

La duración actual utiliza 2, 8 y 10 semestres según el catálogo adoptado. Estos valores se contrastan con ese catálogo y con la referencia institucional disponible. En correos se revisará una regla explícita de estructura y los casos sin información; una dirección que cumpla el patrón no acredita entregabilidad.

No se detectaron negativos ni atípicos mediante el criterio intercuartílico del diagnóstico actual en puntajes, importes o duración. Se conservarán los controles y se documentará su método. Para comparar importes se resolverá primero la diferencia de concepto económico entre fuentes. No se eliminará un valor por ser extremo ni se calculará una corrección automática por programa.

## 6. Periodo académico actualizado

| Etiqueta actual | Filas de entrada | Código adoptado |
| :--- | ---: | ---: |
| 2025-2 | 1.102 | 20252 |
| 2026-1 | 1.271 | 20261 |
| 2026-I | 1.020 | 20261 |
| 2026-2 | 1.177 | 20262 |
| 2026 II | 1.070 | 20262 |

El usuario confirmó el 24 de octubre que el periodo se manejará con estos códigos enteros. L02 ya homologó las etiquetas como texto; la conversión a INTEGER se aplica en L04.

La regla año por 10 más número de periodo produce 1.102 filas en 20252, 2.291 en 20261 y 2.247 en 20262, antes de consolidar repeticiones. Las etiquetas pueden obtenerse en una vista o catálogo de presentación. El código identifica y ordena; no debe sumarse ni promediarse.

Los 470 casos con periodo 20252 y fecha de solicitud en 2026 siguen siendo incidencias por verificar. Cambiar el formato del periodo no resuelve esa diferencia administrativa.

## 7. Tres decisiones críticas antes de consolidar registros

### 7.1. Duplicados y solapamientos

Las 140 repeticiones adicionales de registro_id no son 140 eliminaciones autorizadas. Los 139 grupos incluyen repeticiones exactas, los dos conflictos históricos y solicitudes presentes tanto en la principal como en CRM. Un mismo grupo puede tener filas exactas y otra fila diferente.

Si únicamente se consolidaran las 38 repeticiones exactas observadas al inicio, quedarían 5.602 filas. Esta es una simulación condicionada a esa decisión, no el número final esperado. Cada fila consolidada debe vincularse con el representante, que se elige mediante una regla reproducible y no por su posición como prueba de actualidad.

Los 100 códigos CRM ya existen en la principal, pero sus importes fueron sumados y difieren del concepto registrado en la principal. Deben conciliarse por solicitud y por atributo, no borrar una fuente entera automáticamente. Los dos conflictos originales REG004804 y REG003600 siguen necesitando resolución documentada.

Oracle tiene otros identificadores. La comparación anterior encontró 498 candidatos por 11 atributos excluyendo identificadores y fechas, y 49 por 13 atributos excluyendo solo identificadores, bajo las sondas documentadas. Ninguna cifra define por sí sola cuántas solicitudes deben eliminarse. Un correo común tampoco identifica una solicitud única.

### 7.2. Importes con conceptos diferentes

En CRM, valor_matricula_cop es matrícula base más derechos administrativos por la transformación realizada. En las otras fuentes no se acreditó esa misma definición. Unificar el tipo numérico no unifica el significado económico.

La propuesta inicial es conservar el importe reportado y registrar su concepto y procedencia en la auditoría. Si se decide una medida económica común, habrá que reconstruirla desde las columnas originales del CRM con una regla aprobada, registrando valor anterior y posterior. Hasta entonces no deben presentarse promedios consolidados como importes plenamente comparables ni como ingresos cobrados.

### 7.3. Fechas y catálogo

Las diferencias temporales Oracle deben conservarse como alertas. Se encontraron candidatos compatibles con intercambio de día y mes, pero también otras discrepancias. La regla por formato requiere confirmación para los casos ambiguos; no se intercambian fechas solo para aumentar coincidencias.

En programas, la selección de una sola fila de Data Analytics y los ajustes de facultad, duración y nivel son decisiones documentadas del catálogo de trabajo. Debe recuperarse la correspondencia de nombres antes y después del fuzzy desde el paso de expansión, porque el nombre asignado se retiró de la salida final. Revisar los pares de denominaciones distintos y conservar evidencia de los 27 casos sin correspondencia.

## 8. Cómo registrar cada paso

Los Pasos aplicados de la integración en Power Query forman parte del respaldo histórico. La limpieza continuará en el notebook con controles explícitos por celda, regla y registro, además de las explicaciones y salidas visibles. Se conserva el código M de integración y se generan controles separados de la tabla administrativa.

| Control | Contenido mínimo |
| :--- | :--- |
| Inventario de entrada | Identificador de fila, posición, registro_id, hash de fila y de archivo; ya preparado para las 5.640 filas |
| Registro de pasos | Ejecución, regla, versión, artefacto y celda o paso, criterio, filas antes y después, filas modificadas únicas, celdas modificadas, filas excluidas, repeticiones consolidadas y pendientes |
| Cambios por celda | Identificador de entrada, columna, valor anterior y posterior, tipo o motivo de ausencia, regla y justificación |
| Disposición de filas | Cada entrada vinculada a una salida o a una exclusión documentada; las consolidaciones conservan todos sus orígenes |
| Incidencias pendientes | Caso, regla, evidencia, motivo, alcance en indicadores y estado de resolución |

Se incluyen plantillas generales vacías en docs/plantillas_limpieza. La primera ejecución del notebook ya genera sus controles reales en reports/limpieza/ejecuciones, separados de esas plantillas. Cada acción posterior debe generar sus filas de control al aplicarse.

Una fila puede cambiar en varias columnas. Por eso se cuentan por separado celdas modificadas y filas distintas modificadas. Una fila pendiente puede permanecer en la salida; no se suma otra vez como si fuera un registro adicional.

En el notebook se conserva un DataFrame de entrada y se trabaja sobre una copia por etapa. Los índices de auditoría se mantienen fuera de las columnas administrativas. Antes de retirar filas o agruparlas se conserva la relación entre cada entrada y su destino. Quitar duplicados sin esa relación no ofrece trazabilidad suficiente.

## 9. Conciliación y criterios de aceptación

En cada paso debe cumplirse:

```text
filas_salida = filas_entrada
               menos filas_excluidas
               menos repeticiones_consolidadas
               más filas_generadas_justificadas
```

No se espera generar filas nuevas durante esta limpieza. Una modificación de categoría, fecha o tipo mantiene las filas. Las repeticiones consolidadas cuentan únicamente las filas adicionales retiradas de la salida, no todos los integrantes de sus grupos.

Al finalizar, cada una de las 5.640 entradas debe tener un destino: conservada como salida individual, vinculada a un resultado consolidado o excluida con motivo. Los casos pendientes que se mantengan dentro de la salida continúan contándose allí. No sumar incidencias superpuestas como si fueran personas o filas diferentes.

| Comprobación | Condición |
| :--- | :--- |
| Entrada y fuentes | Hashes originales conservados |
| Inventario | 5.640 identificadores técnicos únicos y todos con destino |
| Cantidades | Conciliación por paso y global sin diferencias inexplicadas |
| Categorías | Valores del catálogo aplicado o excepciones visibles |
| Tipos | Sin errores de conversión silenciosos; motivos conservados |
| Integración previa | Sin multiplicaciones por catálogo y con asignaciones fuzzy revisadas |
| Importes | Conceptos identificados antes de comparar medidas económicas |
| Identidad | Solicitudes y personas distinguidas; claves de origen conservadas |
| Repetición del proceso | Misma entrada y versión de reglas producen los mismos valores y decisiones |
| Comunicación | Conteos, porcentajes y estadísticas con sus nuevos denominadores y limitaciones |

El número final de filas no se fija antes de resolver los grupos. Tampoco se exige que registro_id sea único si quedan conflictos o si la definición de solicitud todavía no está confirmada. Esa limitación debe quedar explícita en la salida y en los indicadores.

## 10. Archivos de salida propuestos

La limpieza generará data/processed/taller_2/BaseUnificada_Limpia.xlsx y BaseUnificada_Limpia.csv, con su versión, fecha y hashes. El Excel podrá incluir hojas de control además de la base; los CSV de auditoría se guardarán en reports/limpieza/ejecuciones junto a la identificación de la ejecución, con los hashes del código del notebook y de las reglas utilizadas.

Las 18 columnas actuales son de negocio. Los índices, estados de revisión y correspondencias se mantienen en controles separados o en consultas auxiliares. Si se acuerda añadir una variable analítica nueva, se documentará el cambio del esquema y del diccionario.

No se reemplazará BaseUnificada_Manejo.xlsx ni data/prepared/taller_2/BaseUnificada. El notebook anterior seguirá respaldando la primera exploración. La limpieza y su comparación antes y después requieren su propio respaldo actualizado, sin presentar los resultados iniciales como cifras de la base nueva.

Una carga futura a PostgreSQL necesita una nueva estructura que contemple las 18 columnas y los controles de ejecución. El sincronizador actual no aplica automáticamente las transformaciones manuales de Excel. No se editan migraciones anteriores ni se sobrescriben admisiones_original o admisiones_tipadas.

## 11. Qué está listo y qué sigue pendiente

Está listo el diagnóstico de entrada, el inventario de las 5.640 filas, el listado de identificadores repetidos, la actualización del plan y las plantillas de control. Se reproducen con python scripts/diagnosticar_base_unificada.py.

El primer notebook se ejecutó de principio a fin con 10 celdas de código y 10 controles correctos. Verificó 5.040 procedencias principales, 100 CRM y 500 Oracle contra el libro congelado y el código de anexado. L02 estandarizó textos y categorías con config/limpieza/estandarizacion_v1.json: hubo 14.209 cambios de celda en 5.404 filas. Se conservaron las 5.640 filas, las 18 columnas y las 38 repeticiones exactas adicionales. Fechas, puntajes, importes y duración permanecen iguales a la entrada textual.

Los datos intermedios están en data/interim/taller_2 bajo una carpeta de versión. Los cambios por celda, equivalencias, procedencias, disposición de las 5.640 filas y controles están en reports/limpieza/ejecuciones. reports/limpieza/ultima_estandarizacion.json identifica la ejecución y sus hashes. Existe un HTML de lectura en reports/02_limpieza_base_unificada.html.

El siguiente paso es L03, tratamiento de ausencias de las demás variables, conservando los identificadores y sus marcadores sin cambios hasta los cruces. No se adelantan decisiones sobre eliminación de filas. Después se realizará L04, conversión de tipos y validaciones. Las decisiones de identidad, precedencia económica, fechas conflictivas y catálogo institucional siguen pendientes y se resolverán con evidencia.

Todavía no se ejecutaron L03 a L09 ni existe una base final depurada generada por este plan.
