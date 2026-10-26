# Plan de limpieza y transformación de BaseUnificada

Actualización: 26 de octubre de 2026.

Estado: notebook ejecutado de L00 a L14. Se consolidaron 38 repeticiones exactas, dos parciales y 100 aportes CRM incorporados a solicitudes existentes. La entrega contiene 5.500 registros y 18 columnas, incluidos los 500 Oracle, con 13 importes recuperados desde matrícula base CRM. Cada una de las 5.640 entradas mantiene un destino. Los periodos se conservan como semestres de ingreso. La preparación técnica está completada para revisión externa y análisis descriptivo, con observaciones de identidad y negocio explícitas. El estado vigente es reports/limpieza/ultima_entrega.json y el archivo externo deliverables/BaseUnificada_Entregable.xlsx. La entrada preparada y las fuentes permanecen intactas.

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
| L10 | Resolver dos parciales, revisar categorías, importes, fechas e identificadores y explorar por fuente | Dos filas complementarias consolidadas; 5.600 de salida | Cinco celdas recuperadas, 94 ausencias de ID homologadas, controles y siete gráficos |
| L11 | Consolidar estados según contexto y separar solicitudes de aspirantes | Mantiene las 5.600 filas; añade vistas auxiliares | Estados originales, una fila por código de aspirante, clasificación excluyente y denominadores |
| L12 | Incorporar 100 CRM a solicitudes correspondientes y recuperar matrícula base ausente | 5.500 registros | Correspondencias por código y 12 atributos, conceptos económicos y 13 recuperaciones |
| L13 | Conservar Oracle, revisar correspondencias y aplicar reglas temporales e identidad | Mantiene 5.500 registros | Las 500 filas Oracle incluidas, controles por fuente y periodos sin recalcular |
| L14 | Validar y publicar BaseUnificada Entregable | 5.500 registros y 18 columnas | Excel, CSV, JSONL, informe formal, gráficos, controles, hashes y ZIP sin notas personales |

Este orden separa las reglas de representación de las decisiones de identidad. Después de normalizar pueden aparecer nuevas coincidencias exactas; deben volver a contarse y distinguirse de las 38 observadas al inicio.

## 5. Tratamiento de las 18 columnas

| Columna | Tratamiento propuesto | Qué no debe decidirse automáticamente |
| :--- | :--- | :--- |
| registro_id | Conservar el código de origen; posponer correspondencias y validación entre sistemas hasta los cruces | Cambiar códigos Oracle o eliminar filas por su identificador |
| aspirante_id | Conservar códigos informados y diagnóstico; L10 homologa vacíos y nan como null, conservando el original por celda | Crear identificadores o unir personas solo por correo |
| fecha_solicitud | Aplicar reglas por formato y conservar valor previo y procedencia | Intercambiar día y mes o sustituir la fecha Oracle por la principal sin evidencia |
| programa | Unificar nombres y tildes mediante catálogo aprobado | Asignar un programa a los 27 casos sin identificación útil |
| modalidad | Conservar la modalidad de la solicitud y su catálogo de tres valores | Sustituirla por la modalidad única del catálogo reducido |
| canal_captacion | Revisar que las seis categorías actuales coincidan con el catálogo adoptado | Cambiar la atribución comercial por semejanza de texto |
| estado_proceso | L11 agrupa Nuevo con Admitido y conserva seis estados analíticos; el original se guarda por fila | Inferir transiciones, matrícula formal desde Nuevo o reclasificar matriculados por documentación |
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

L06 consolidó las 38 repeticiones exactas con la autorización del usuario del 26 de octubre para completar los pasos pendientes. Se exigió igualdad de las 18 columnas originales y tipadas y una misma fuente. La salida tiene 5.602 filas. El menor índice BU identifica al representante técnico, sin acreditar mayor actualidad. Cada entrada conserva su vínculo; la cantidad definitiva de solicitudes sigue pendiente de la conciliación parcial.

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

La ejecución genera BaseUnificada_Revision.xlsx, BaseUnificada_Revision.csv y BaseUnificada_Revision.jsonl en data/processed/taller_2 bajo una carpeta de versión. El nombre identifica las decisiones administrativas pendientes y evita presentar como definitiva una base con conflictos por resolver. El Excel incluye una hoja Alcance. Los controles CSV se guardan en reports/limpieza/ejecuciones junto a los hashes de código y reglas. reports/limpieza/ultimo_cierre.json identifica la salida vigente. Una versión BaseUnificada_Limpia se publicará tras resolver las decisiones y repetir los controles.

Las 18 columnas actuales son de negocio. Los índices, estados de revisión y correspondencias se mantienen en controles separados o en consultas auxiliares. Si se acuerda añadir una variable analítica nueva, se documentará el cambio del esquema y del diccionario.

No se reemplazará BaseUnificada_Manejo.xlsx ni data/prepared/taller_2/BaseUnificada. El notebook anterior seguirá respaldando la primera exploración. La limpieza y su comparación antes y después requieren su propio respaldo actualizado, sin presentar los resultados iniciales como cifras de la base nueva.

Una carga futura a PostgreSQL necesita una nueva estructura que contemple las 18 columnas y los controles de ejecución. El sincronizador actual no aplica automáticamente las transformaciones manuales de Excel. No se editan migraciones anteriores ni se sobrescriben admisiones_original o admisiones_tipadas.

## 11. Qué está listo y qué sigue pendiente

Está listo el diagnóstico de entrada, el inventario de las 5.640 filas, el listado de identificadores repetidos, la actualización del plan y las plantillas de control. Se reproducen con python scripts/diagnosticar_base_unificada.py.

El notebook se ejecutó de principio a fin con 37 celdas de código. Verificó 5.040 procedencias principales, 100 CRM y 500 Oracle contra el libro congelado y el código de anexado. L02 estandarizó textos y categorías con config/limpieza/estandarizacion_v1.json: hubo 14.209 cambios de celda en 5.404 filas. En esa etapa se conservaron las 5.640 filas, las 18 columnas y las 38 repeticiones exactas adicionales. L02 no modificó fechas, puntajes, importes ni duración.

Los datos intermedios están en data/interim/taller_2 bajo una carpeta de versión. Los cambios por celda, equivalencias, procedencias, disposición de las 5.640 filas y controles están en reports/limpieza/ejecuciones. reports/limpieza/ultima_estandarizacion.json identifica la ejecución y sus hashes. Existe un HTML de lectura en reports/02_limpieza_base_unificada.html.

L03 se aplicó con config/limpieza/ausencias_v1.json. Representó 5.866 celdas como ausentes en 4.705 filas y registró sus motivos: 4.409 no informadas en la base, 1.369 No aplica de fecha de matrícula, 51 Pendiente de puntaje, 35 por definir de importe y 2 Sin especificar de programa. Los 92 identificadores de aspirante vacíos y los cuatro nan se conservaron sin cambios. Pendiente de documentación y Sin asignar de asesor siguen como categorías. No hubo imputación ni cambios de valores informados.

Los controles L03 verifican 11 condiciones, incluida la conservación de filas, identificadores, valores informados y la idempotencia. Las tres salidas CSV, Excel y JSONL se compararon íntegramente. JSONL preserva la diferencia entre null y texto vacío; el CSV requiere el control por celda para recuperar esa diferencia. La salida y auditoría de L03 se identifican en reports/limpieza/ultima_ausencias.json. La repetición de L02 para ejecutar todo el cuaderno conserva el mismo contenido CSV de estandarización; no representa nuevas transformaciones acumuladas sobre la base inicial.

L04 utiliza config/limpieza/tipos_v1.json y el módulo de interpretación src/analitica_admisiones/tipado_limpieza.py. Se tiparon 28.186 valores informados sin errores de conversión: 5.640 fechas de solicitud, 1.206 fechas de matrícula, 5.389 puntajes, 4.698 importes, 5.613 duraciones y 5.640 periodos. Las fechas se presentan como AAAA-MM-DD, el importe es Decimal COP con escala 2, y el periodo usa los enteros 20252, 20261 y 20262. Los identificadores y las 5.866 ausencias permanecen intactos.

L04 dejó 1.293 alertas en 1.159 filas distintas: 524 de documentación en matriculados, 470 de año de solicitud posterior al periodo, 237 formatos de día y mes ambiguos, 32 matrículas anteriores a solicitud y 30 fechas posteriores a la referencia del 24 de octubre de 2026. Varias alertas pueden corresponder a una misma fila. No se corrigen por suposición ni se declaran todas como errores. La referencia no es un corte institucional confirmado.

Los 12 controles L04 y la lectura completa de CSV, Excel y JSONL pasaron. El Excel mantiene números y fechas reales con formato; el CSV conserva punto decimal y fechas ISO; JSONL representa decimales exactos como números y fechas como texto ISO. La salida vigente se identifica en reports/limpieza/ultima_tipificacion.json. docs/formatos_fechas_cop.md explica los formatos y su relación con la configuración regional. Las reejecuciones de las etapas previas mantienen sus mismos datos CSV o JSONL y no son nuevas transformaciones acumuladas.

L05 comprobó 5.613 correspondencias reproducibles con los siete programas y 27 ausencias de programa útil. Los atributos coinciden con el catálogo de trabajo, sin recuperar el nombre descartado por el fuzzy histórico. Se conservó la modalidad de solicitud ante las 3.385 diferencias frente a la modalidad única del catálogo. L06 consolidó 38 repeticiones exactas, con 5.602 registros de salida: 5.002 principal, 100 CRM y 500 Oracle.

L07 conservó 102 grupos con registro_id repetido y diferencias, que involucran 204 filas. Los 100 CRM coinciden con la principal en 12 atributos ajenos a los identificadores y al importe; 96 tienen también el mismo aspirante_id y cuatro mantienen nan. Trece tienen candidato principal sin importe. Los conflictos REG003600 y REG004804 permanecen documentados.

Oracle tiene candidatos en 500 filas mediante la sonda de 11 atributos, frente a los 498 del diagnóstico anterior. Dos coincidencias aparecen al representar Sin especificar y programa vacío como una misma ausencia; no constituyen evidencia nueva de identidad. Se conservan ambos programas originales y las ausencias compartidas en la comparación. La sonda de 13 atributos identifica 49 filas candidatas y 16 casos son compatibles con intercambio de día y mes de solicitud. No se cambiaron fechas ni códigos.

L08 revisó las filas representativas y registró 466 casos de solicitud posterior al año del periodo, 521 matriculados con documentación No o Pendiente, 95 identificadores de aspirante vacíos o nan, 32 matrículas anteriores a solicitud y 28 fechas posteriores a la referencia del 26 de octubre. El control de correos encontró 5.471 estructuras compatibles y 131 ausencias. No se detectaron negativos ni valores fuera del criterio intercuartílico aplicado; los importes se analizaron por fuente y concepto.

L09 verificó 16 controles, la lectura íntegra de CSV, Excel y JSONL y los destinos de las 5.640 entradas. Registra 2.110 incidencias en 1.766 filas de salida, con superposición de motivos. Existen diez decisiones abiertas sobre programas ausentes, catálogo, CRM y conflictos parciales, Oracle, fechas, periodos, estados y documentación, identidad y contacto, conceptos monetarios y reglas numéricas, y ausencias y aprobación final. Su alcance no equivale a errores confirmados.

Las reglas L09 están en config/limpieza/cierre_v1.json y el respaldo ejecutable en src/analitica_admisiones/cierre_limpieza.py y las celdas del notebook. El reporte L09 está en reports/limpieza/reporte_cierre_limpieza.md y su punto de control en reports/limpieza/ultimo_cierre.json. La versión posterior L10 se describe a continuación. Solicitudes únicas globales, tasas definitivas y comparación económica consolidada requieren resolver las decisiones y volver a ejecutar el proceso. Las tablas de Docker no se modificaron.

## 12. Revisión L10 y salida actual

El usuario pidió explorar la versión de revisión para evaluar estados, importes, fechas, identificadores y posibilidades de análisis administrativo. L10 aplica config/limpieza/revision_descriptiva_v1.json. Complementó REG003600 con 1.800.000 COP y REG004804 con programa, facultad, duración y nivel desde sus otras filas. Se exigió igualdad de los demás atributos y ausencia de contradicciones informadas. Se recuperaron cinco celdas y se consolidaron dos filas. El consolidado contiene 5.600 registros y la fuente principal 5.000 códigos de solicitud distintos. Cinco incidencias históricas quedan resueltas y cada entrada conserva su vínculo.

La aclaración del usuario sobre nan motivó homologar 94 identificadores no informados a null, incluidos cuatro textos nan y 90 textos vacíos. Los marcadores originales se registran por celda. No se crean códigos ni se unen personas por correo. Pendiente sigue siendo una categoría de documentación. Las reglas L03 y L04 conservan sus resultados históricos de identificadores sin modificar; esta decisión se aplica después, en L10.

En el punto de control L10, Nuevo se mantuvo distinto de Admitido antes de la aclaración posterior del usuario. Las fases de presentación se incluyeron en un control auxiliar. Ese punto tiene 560 Nuevo, 572 Inscrito, 570 Documentación pendiente, 1.105 Admitido, 1.079 Matriculado, 550 No admitido y 564 Retirado. L11 aplica la agrupación posterior documentada. Se observan 351 Documentación pendiente con documentos Sí y 462 Matriculado con documentos No o Pendiente, sin reemplazar estados por esa relación.

Las 63 combinaciones de programa identificado, modalidad y periodo tienen los cinco importes observados. En 21 comparaciones virtual frente a presencial por programa y periodo, 18 medianas son iguales, una es menor en virtual y dos mayores. No se deduce una tarifa ni se imputan matrículas. Los importes CRM se describen por separado por concepto económico.

La fecha de matrícula está informada en los 1.079 matriculados principales y no en otros estados. Hay 165 solicitudes principales con formatos ambiguos señalados y ninguna matrícula principal anterior a solicitud. Se resumen 977 intervalos sin las alertas revisadas, con mediana de 33 días; 102 se conservan fuera de ese cálculo. La cobertura principal llega al 12 de septiembre de 2026, por lo que el mes final no se trata como completo. Las 32 fechas de matrícula anteriores a solicitud del consolidado L09 no pertenecen a la fuente principal.

Hay 2.924 códigos de aspirante principales informados distintos y 90 solicitudes principales sin código. 1.363 códigos aparecen en varias solicitudes. De los 90 ausentes, 62 tienen un único código candidato en otras filas con el mismo correo; no se asignan por esa coincidencia. Se conserva aspirante_id para trazabilidad y revisión de recurrencia, fuera de los agrupadores de mercado.

La salida actual se identifica en reports/limpieza/ultima_revision_descriptiva.json; ultimo_cierre.json conserva el punto de control previo L09. El Excel incluye BaseUnificada_Revision y Principal_Analisis con 18 columnas, además de Alcance. También se exportan el consolidado en CSV y JSONL y la cohorte principal en CSV. Hay siete figuras en PNG y PDF y tablas de frecuencias, cruces, importes, puntajes, fechas, intervalos y calidad. El reporte está en reports/limpieza/revision_descriptiva_y_parciales.md. Los datos originales y las tablas Docker conservan su estado.

## 13. L11, estados y personas sin doble conteo

El usuario aclaró que Nuevo indica alguien que ya ingresó y comenzará estudios y preguntó si conviene agruparlo como Admitido o Matriculado. Se adopta Nuevo como Admitido para el análisis. El criterio incorpora esa definición y conserva Matriculado separado, pues los 560 Nuevo no tienen fecha de matrícula y los 1.079 Matriculado sí. Esto no acredita una equivalencia institucional por la sola ausencia de fecha. Los estados recibidos se guardan por fila en la auditoría. Hay 620 celdas reclasificadas entre las tres fuentes, sin retirar filas ni modificar los otros 17 atributos.

La cohorte principal mantiene 5.000 solicitudes y pasa a 1.665 Admitido y 1.079 Matriculado. La vista por aspirante tiene 2.924 códigos informados distintos, con 90 solicitudes sin identificador separadas. Un código puede tener solicitudes de varios programas, modalidades y periodos. Se observaron 1.363 códigos con varias solicitudes, 1.205 con varios estados originales, 1.210 con varios programas identificados y 966 con varios periodos. El conteo preliminar de 1.220 incluía el programa vacío como categoría adicional; se excluyó esa ausencia al contar programas distintos. Agrupar Nuevo deja 1.158 códigos con varios estados y no resuelve por sí solo el conteo de personas.

Las sumas de aspirantes distintos por estado son 4.474 antes y 4.371 después de agrupar Nuevo. Son pertenencias superpuestas, no personas únicas. Para una distribución aditiva se ofrece una clasificación excluyente por aspirante: alguna solicitud Matriculado, después alguna Admitido sin Matriculado y finalmente los demás. No es estado actual. Se conservan los estados observados y los códigos de todas las solicitudes.

La base no contiene fecha de actualización del estado. No se elige el último estado utilizando fecha de solicitud ni se elimina una solicitud por compartir aspirante. Los 48 grupos con el mismo aspirante, programa, modalidad y periodo se exportan para revisión; 39 presentan varios estados originales. Se mantienen sus 96 solicitudes porque no hay prueba de que todas sean versiones de una sola solicitud.

Las reglas se encuentran en config/limpieza/identidad_estados_v1.json. El resumen vigente es reports/limpieza/ultima_identidad_estados.json y el reporte es reports/limpieza/reporte_estados_personas_y_cierre.md. El Excel conserva BaseUnificada_Revision y Principal_Analisis con 18 columnas y añade las vistas auxiliares Aspirantes_Principal, Solicitudes_Sin_ID y Alcance. Se exportan el original de cada estado modificado, el destino de las 5.640 entradas, grupos de posible historial, frecuencias por solicitud y aspirante y un diccionario de indicadores y denominadores. L09 y L10 permanecen como puntos de control históricos.

## 14. Cierre integrado y entrega para revisión

El usuario autorizó completar el proceso y entregar una versión formal sin notas personales. L12 incorpora los 100 aportes CRM mediante registro_id, compatibilidad de 12 atributos y control de los identificadores informados. Se conservan 87 matrículas principales iguales a la base CRM y se recuperan las 13 ausentes desde esa base. Derechos administrativos y total CRM permanecen en el control económico. No se imputan promedios ni se modifican importes principales informados. La principal tiene 839 importes ausentes después de la recuperación.

L13 conserva las 500 filas Oracle dentro del conjunto integrado. Las 500 tienen candidatos por 11 atributos y 49 también por los dos atributos de fecha comparados. Las sondas utilizan igualdad numérica y las ausencias se identifican explícitamente; las coincidencias no prueban identidad. Se comparan contra el estado previo a recuperar importes para no perder candidatos por el enriquecimiento posterior. Los códigos Oracle y los datos de sus 500 filas se conservan.

Los periodos son semestres de ingreso y permanecen como llegaron tras su homologación. No se recalculan desde solicitud o matrícula. Las ventanas de octubre a enero y de mayo a julio son referencias descriptivas, sin afirmar calendario institucional ni excluir registros. Las fechas futuras y de orden inverso se señalan; los intervalos solo se calculan con ambas fechas sin las alertas aplicadas. No se crean fechas de actualización de estado.

La salida tiene 5.500 registros y 18 columnas: 5.000 principales enriquecidos y 500 Oracle. Cada una de las 5.640 entradas conserva su destino. Hay 26 programas sin identificar, 90 identificadores de aspirante ausentes, 246 puntajes ausentes y 920 importes ausentes. Hay 456 solicitudes con año posterior al periodo, 32 matrículas anteriores a solicitud y 28 fechas posteriores a la referencia del 26 de octubre. Las observaciones pueden superponerse y no se suman como registros nuevos. Se conservan 4.321 ausencias de fecha de matrícula; su ausencia en estados no matriculados no se declara error automáticamente.

Aspirantes_Origen incluye 2.924 identificadores principales y 500 Oracle: 3.424 códigos de origen y no personas globales únicas confirmadas. Los 90 casos sin identificador permanecen. Los gráficos integrados utilizan los 5.500 registros e identifican las limitaciones de independencia y cobertura por fuente.

L14 publica deliverables/BaseUnificada_Entregable.xlsx, su CSV, un informe formal PDF y Markdown, metadatos y BaseUnificada_Entregable.zip. La hoja BaseUnificada tiene 18 columnas. Diccionario_Datos, Origen_Registros, Control_Calidad, Resumen_Calidad, Aspirantes_Origen, Coincidencias_Oracle, Control_Economico, Registros_Sin_ID y Metodologia permiten revisión autónoma. El paquete contiene controles CSV y seis gráficos PNG y PDF. Se verifican contenido, hashes y ausencia de notas de conversación o rutas locales. La auditoría interna no se incorpora al paquete externo.

Pasaron 23 controles finales y la lectura completa de Excel, CSV y JSONL. Se conserva el inventario de las 5.640 entradas y se verifican los hashes de fuentes, archivo preparado y libro original. El resumen vigente es reports/limpieza/ultima_entrega.json. El informe interno es reports/limpieza/reporte_final_integracion_y_entrega.md. Las reglas están en config/limpieza/entrega_v1.json y el mismo notebook reproduce todo el proceso. Las tablas Docker no se modificaron.

La preparación técnica queda cerrada para revisión externa y análisis descriptivo de registros. La identidad global entre sistemas, las ausencias no recuperables, el calendario oficial y la falta de fecha de actualización de estado son límites declarados. Para indicadores que requieran esa validación se mantendrán los denominadores y alcances correspondientes; no se sustituyen por supuestos silenciosos.

## 15. Revisión de presentación 1.1 y guía de hojas

El usuario pidió aclarar el uso de las diez hojas, las decisiones aplicadas y el significado de la marca de coincidencia, y reducir punto y coma y guiones en la redacción. La revisión 1.1 conserva los 5.500 registros y las 18 columnas de BaseUnificada. Las listas usan comas y las oraciones puntos. Se mantienen los separadores técnicos de fecha y los códigos originales.

La marca coincidencia_oracle_pendiente se reemplaza por similitud_entre_fuentes_detectada. Se señala en ambos registros relacionados, de la principal y Oracle. Describe un resultado del control de atributos y no una transformación omitida. El cruce está ejecutado. La identidad del evento sigue sin confirmación, lo que se conserva como límite de la información. Los distintos códigos de origen no se declaran errores.

Metodologia incorpora decisiones aplicadas y aspectos no confirmados. Guia_Hojas.md y Guia_Hojas.csv explican las diez hojas, sus filas y función. La última celda del notebook conserva la validación y exportación, muestra la guía y los totales y no repite el informe completo. El Excel previo estaba abierto y bloqueó la sustitución, por lo que la actualización se publica en deliverables/v1_1, conservando la versión anterior.

La revisión añade el control de simetría, con 24 comprobaciones finales, y un control explícito de textos sin punto y coma en el paquete. Los estados antes y después se comparan sobre el mismo universo de 5.500 filas en reports/apoyo_informe_drive/homologacion_estados.png. La cobertura temporal también queda disponible como apoyo. La guía de ubicación distingue figuras de tratamiento y calidad de los gráficos descriptivos de programas, canales y estados resultantes.
