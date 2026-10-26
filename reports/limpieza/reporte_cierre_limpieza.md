# Reporte de limpieza y decisiones pendientes

Fecha de revisión: 26 de octubre de 2026.

Se ejecutaron las etapas L05 a L09 sobre las 5.640 filas ya estandarizadas y tipadas. La salida conserva **5.602 registros y 18 columnas**, después de consolidar 38 repeticiones exactas de la misma fuente. Cada entrada mantiene su destino en la auditoría. No se completaron datos por suposición ni se fusionaron registros con diferencias.

| Etapa | Resultado |
| :--- | :--- |
| L05, catálogo | 5.613 correspondencias reproducibles y 27 sin programa identificado; 0 discrepancias en los atributos de trabajo. |
| L06, exactos | 38 grupos; 38 filas adicionales consolidadas. Representante por índice BU, sin atribuirle mayor actualidad. |
| L07, fuentes | 100 filas CRM con código en principal y 102 grupos de código repetido conservados. Oracle tiene 500 filas con candidatos por 11 atributos y 49 por 13; son sondas, no identidades confirmadas. |
| L08, coherencia | Se revisaron fechas, periodos, documentación, estados, identificadores, correos y valores numéricos; los casos pendientes se conservan. |
| L09, cierre técnico | 16 controles correctos; CSV, Excel y JSONL verificados íntegramente; frecuencias y completitud recalculadas. |

Las fechas usan año, mes y día. Los importes conservan precisión exacta en COP; la presentación colombiana se aplica en las tablas y según la configuración regional en Excel. Los periodos mantienen 20252, 20261 y 20262 como códigos. Los identificadores originales se conservan.

## Qué queda disponible para análisis

La base permite describir los 5.602 registros conservados por programa, modalidad, canal y estado, citando el denominador. Todavía no permite afirmar solicitudes o aspirantes únicos, ni tasas definitivas de conversión. Los importes se resumen por fuente porque CRM incluye derechos administrativos y el concepto de las otras fuentes está por confirmar.

L09 registra 2.110 incidencias en 1.766 filas de salida distintas. Los alcances se superponen y no deben sumarse como personas. La ausencia de alertas particulares tampoco acredita validación institucional.

## Hallazgos de revisión

Las modalidades de solicitud difieren de la modalidad única del catálogo en 3.385 entradas anteriores a la consolidación. Se conserva la modalidad de solicitud. Los tres atributos del catálogo coinciden con la reproducción por una clave normalizada única. El nombre asignado originalmente por fuzzy fue retirado del libro final: la reproducción actual no recupera esa evidencia histórica.

En CRM hay 13 filas con importe informado cuyo candidato principal no tiene importe. No se utiliza el total CRM para rellenarlas sin acordar antes el concepto y la precedencia. REG003600 conserva una diferencia de importe y REG004804 una diferencia de programa y atributos asociados.

Oracle presenta 16 filas candidatas compatibles con intercambio de día y mes en alguna fecha de solicitud principal. Esa compatibilidad no demuestra cuál fecha es correcta y no se aplica una corrección automática. Las sondas incluyen ausencias iguales; el detalle indica cuántos de los 11 atributos están informados.

De las 500 coincidencias Oracle por 11 atributos, 498 también tienen un programa original equivalente. Las otras 2 aparecen al homologar como ausencia Sin especificar y programa vacío. No representan nueva evidencia de identidad ni recuperan el programa: el detalle conserva ambos valores originales. Por eso el conteo de candidatos aumenta frente a los 498 del diagnóstico anterior.

| Alerta administrativa en representantes | Casos |
| :--- | ---: |
| solicitud posterior al anio del periodo | 466 |
| matriculado con documentacion no completa | 521 |
| identificador ausente o marcador | 95 |
| fecha posterior a referencia | 28 |
| matricula anterior a solicitud | 32 |

La referencia L08 es el 26 de octubre de 2026, fecha de revisión. L04 conserva su referencia histórica del día 24. Ninguna equivale a un corte institucional confirmado; los conteos de fechas posteriores no deben compararse sin indicar la referencia.

El control de correos registra {'estructura compatible': 5471, 'sin información': 131}. Se revisó estructura, sin comprobar existencia o entregabilidad. La evaluación numérica detectó 0 negativos y 0 valores fuera del criterio intercuartílico aplicado por variable y por fuente en los importes. Esto no acredita que todos los valores sean exactos.

## Decisiones necesarias para aprobar la versión final

| Decisión | Alcance en filas de salida | Qué resolver | Efecto |
| :--- | ---: | :--- | :--- |
| D01: Programas no identificados | 27 | Recuperar el programa desde la solicitud original o conservarlo ausente | Permite asignar facultad, duración y nivel; evita inventar el programa |
| D02: Catálogo institucional y modalidad | 5.575 | Confirmar los siete programas, sus atributos y la selección de Data Analytics Ingeniería; revisar diferencias de modalidad sin reemplazar la solicitud | Valida análisis por facultad y nivel. La reproducción de nombres no demuestra que el fuzzy histórico asignó el nombre correcto |
| D03: CRM y registros parciales | 204 | Definir la unidad solicitud y la precedencia por atributo para los 100 CRM; resolver REG003600 y REG004804 con evidencia | Determina qué filas consolidar y evita contar una misma solicitud dos veces |
| D04: Solapamiento Oracle | 500 | Confirmar si cada candidato es la misma solicitud o un evento distinto; conservar códigos propios y documentar equivalencias si se aprueban | Determina el volumen real; no fusionar por parecido de atributos |
| D05: Fechas y referencia temporal | 287 | Confirmar las convenciones de día y mes, fechas contradictorias y el corte institucional; definir si hay fechas programadas | Valida tendencias temporales y duraciones; no intercambiar fechas por conveniencia |
| D06: Periodos académicos | 466 | Validar solicitudes de 2026 asociadas a 20252 sin deducir la corrección del año | Valida comparaciones entre periodos; el código entero ya está aprobado |
| D07: Estados, documentación y matrícula | 521 | Confirmar excepciones documentales y significado de fecha de matrícula en cada estado; acordar qué acredita matrícula efectiva | Permite medir avance y después conversión con denominador definido |
| D08: Identidad y datos de contacto | 95 | Recuperar los ID vacíos y nan con fuente autorizada; validar correos sin asumir que correo equivale a persona | Permite contar aspirantes; conservar códigos Oracle. Un correo válido en estructura no acredita entregabilidad |
| D09: Importes y reglas numéricas | 5.602 | Acordar si el indicador económico es matrícula base o base más derechos y reconstruir una medida comparable; confirmar escala oficial de puntajes y tarifas si se quieren validar | Evita promediar conceptos diferentes y confundir matrícula con pago. Los extremos estadísticos no se eliminan automáticamente |
| D10: Ausencias y versión final | 4.672 | Definir qué vacíos son admisibles por estado, qué recuperar y quién valida cada excepción; aprobar la versión y el denominador final | Conserva motivos de ausencia; no imputar ceros o promedios para completar |

Los alcances indican filas que podrían verse afectadas por una decisión, no errores confirmados. Por ejemplo, validar el catálogo alcanza a todas sus asignaciones y acordar el concepto monetario afecta al diseño de indicadores de toda la base.

Las decisiones se aplicarán mediante reglas versionadas y un registro por celda o consolidación. Luego se recalcularán los destinos, controles y denominadores. La versión se denomina BaseUnificada_Revision para identificar que su preparación técnica está terminada y su conciliación administrativa sigue pendiente.

## Archivos y trazabilidad

Datos: `data/processed/taller_2/cierre_v1_b6b6136d80_d64d0a32_1ea4b71b_cd91e63a`.

Auditoría: `reports/limpieza/ejecuciones/cierre_v1_b6b6136d80_d64d0a32_1ea4b71b_cd91e63a`.

El archivo reports/limpieza/ultimo_cierre.json identifica esta ejecución y los hashes de las tres salidas. L09_disposicion_filas.csv enlaza las 5.640 entradas con su salida. L09_incidencias_pendientes.csv conserva los casos individuales y L09_decisiones_pendientes.csv resume las reglas por resolver. Los motivos de ausencia se mantienen en L03 y se recuperan mediante esa relación de entradas.

Los archivos originales y preparados permanecen intactos. Esta ejecución no carga ni reemplaza las tablas de Docker. El notebook 01 conserva la evidencia de la exploración inicial; el notebook 02 respalda la base consolidada y las etapas de limpieza.
