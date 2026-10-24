# Guía para el diagnóstico inicial de calidad por columna

## Propósito

Cumplir la actividad de examinar vacíos, posibles duplicados, formatos inconsistentes, variantes de categorías, valores negativos o inusuales y fechas que no se interpreten correctamente. Se conservan las 5.040 filas y las 15 columnas del archivo original. Las interpretaciones necesarias para revisar números y fechas se realizan en memoria, sin actualizar el CSV ni la tabla original.

Fuente principal: Calidad de datos.pptx, diapositivas 6–12 y 14–16. La organización del informe será por columna; las dimensiones de calidad sirven como criterios de revisión. No es necesario aplicar las seis dimensiones a todas las columnas.

## Estructura de cada apartado

1. **Qué se revisó:** controles pertinentes para la columna.
2. **Qué se encontró:** cantidades, porcentajes, variantes y ejemplos, con denominador explícito.
3. **Qué implica:** efecto posible sobre identificación, agrupación, cálculo o seguimiento.
4. **Qué queda por comprobar:** regla o fuente que falta para confirmar un error.

En esta fase no se presentan correcciones como realizadas ni se ordena eliminar registros, completar valores o unificar categorías. Los valores extremos se documentan como alertas, no como errores confirmados.

## Ruta de revisión por columna

| Columna | Controles de calidad | Evidencia inicial y revisión pendiente | Apoyo sugerido |
|---|---|---|---|
| registro_id | Vacíos, formato y repeticiones de clave | Sin vacíos; 5.000 identificadores distintos en 5.040 filas. Investigar dos claves con diferencias entre sus filas | Tabla breve de repeticiones y diferencias |
| aspirante_id | Vacíos, formato e identificación entre solicitudes | 92 vacíos. No confundir varias solicitudes con duplicación inválida de un aspirante | Tabla de completitud e identificación; sin gráfico propio |
| fecha_solicitud | Vacíos, patrones de fecha, interpretación y cobertura | Sin vacíos; cinco formatos. 723 valores usan formatos distintos a AAAA-MM-DD. Cobertura interpretada: 01/01/2025–12/09/2026 | Tabla de formatos; cronología solo si aporta al diagnóstico |
| programa | Espacios, vacíos y variantes de denominación | 25 valores con solo un espacio; variantes Derecho/DERECHO y Especializacion/Especialización en Data Analytics | Tabla de variantes con conteos |
| modalidad | Vacíos y variantes de escritura | Virtual/VIRTUAL y Presencial/presencial; conservar Híbrida | Tabla de variantes; barras opcionales para mostrar fragmentación |
| canal_captacion | Vacíos, espacios y categorías inesperadas | Se observan seis categorías sin vacíos; contrastar nombres con catálogo si está disponible | Fila en tabla resumen; gráfico de volumen corresponde a la sección descriptiva |
| estado_proceso | Vacíos y variantes; coherencia con fechas/documentación | Admitido/ADMITIDO y Matriculado/matriculado; cruces se informan en apartado conjunto | Tabla de variantes y tabla cruzada |
| puntaje_admision | Vacíos, texto, negativos, rango y atípicos | 179 vacíos; 50 Pendiente; 4.811 numéricos entre 40 y 100, sin negativos. Escala institucional pendiente | Tabla de disponibilidad; histograma opcional |
| documentos_completos | Vacíos, categorías y escritura | Sí/sí/SI, No y Pendiente; no convertir a booleano | Tabla de variantes; cruce con estado |
| valor_matricula_cop | Vacíos, texto, negativos, importes y atípicos | 826 vacíos; 35 por definir; 4.179 numéricos entre 1.800.000 y 3.500.000 COP, sin negativos. Tarifas y excepciones pendientes | Tabla de importes observados y frecuencias |
| ciudad_residencia | Espacios, vacíos y variantes de nombres | Cali/Cali con espacio final, Bogotá/BOGOTA y Popayán/Popayan | Tabla con valor entre comillas para mostrar espacios |
| asesor | Vacíos, variantes y estados de asignación | Asesor 1/asesor 1; Sin asignar es un valor explícito, no un vacío | Tabla de variantes y asignación |
| fecha_matricula | Vacíos, No aplica, formatos, interpretación y coherencia temporal | 2.612 vacíos; 1.343 No aplica; 1.085 fechas interpretables mediante cinco patrones. Verificar significado de fechas posteriores a una referencia confirmada | Tabla de disponibilidad y formatos; cruce con estado |
| correo | Vacíos, estructura, espacios y repeticiones | 120 vacíos. Falta aplicar y documentar una regla de estructura; el patrón no certifica entregabilidad ni identidad | Tabla de controles y ejemplos enmascarados |
| periodo_academico | Vacíos, variantes y coherencia con fechas | Cinco etiquetas: 2025-2, 2026-I, 2026-1, 2026 II y 2026-2. Equivalencias requieren catálogo | Tabla de variantes y cruce con fecha de solicitud |

## Hallazgos conjuntos para no repetir en varias columnas

- **Filas completas:** 38 duplicados exactos adicionales. No son necesariamente el número total de filas involucradas en los grupos repetidos. Verificar origen y regla de unicidad antes de decidir tratamientos.
- **Claves parciales:** REG004804 tiene discrepancia en programa; REG003600 en valor_matricula_cop. Son dos grupos de dos filas con diferencias.
- **Aspirante + programa + periodo:** la cifra depende de la clave y las equivalencias. Con valores originales y aspirante_id no vacío se encuentran 105 grupos repetidos, 212 filas involucradas y 107 repeticiones adicionales. No son duplicados confirmados. Si se incluyen los identificadores vacíos: 131 grupos, 291 filas y 160 adicionales; no conviene interpretar esos grupos vacíos como personas identificadas.
- **Estado + documentación:** al considerar Matriculado y matriculado como equivalentes solo para este control, hay 1.085 registros matriculados; 465 tienen No o Pendiente en documentación. Validar las reglas de admisión antes de calificarlos como inconsistentes.
- **Periodo + solicitud:** 410 registros con periodo 2025-2 tienen fecha de solicitud interpretada durante 2026. Requieren contraste con el calendario y las reglas de registro.
- **Matrícula + referencia temporal:** siete fechas posteriores al 17/10/2026. Esa fecha es una referencia propuesta en el borrador, no un corte institucional confirmado. Una fecha futura puede ser programada; no prueba inexactitud.
- **Cobertura de solicitudes:** septiembre de 2026 contiene 75 registros y la fecha máxima es el día 12. Describir cobertura parcial; no afirmar por ello retraso de actualización ni que todos los meses anteriores estén completos.

## Atípicos

La revisión exploratoria de puntaje y valor de matrícula no encontró valores fuera de Q1 − 1,5 × RIC y Q3 + 1,5 × RIC, con cuartiles por interpolación lineal. Esto no demuestra ausencia de errores de negocio. En categorías se revisan variantes, rareza y catálogo, no atípicos numéricos. Las tarifas deben contrastarse con una fuente institucional; que un programa tenga distintos importes no basta para afirmar un problema.

## Presentación administrativa

Usar una tabla general de calidad por columna y desarrollar los casos que afectan la lectura del informe. Conservar el detalle de las 15 columnas en anexo si la extensión supera las 2–4 páginas sugeridas.

No se necesita un gráfico por columna. Para calidad, priorizar una tabla de completitud (vacío exacto, solo espacios y valor de estado explícito por separado), una tabla de variantes y, si ayuda, un histograma del puntaje. Un gráfico de barras de vacíos puede resumir el conjunto, pero no debe equiparar No aplica con dato faltante ni presentar todos los vacíos como errores.

## Ajustes al borrador original

Los valores 1.079 matriculados y 462 con documentación No/Pendiente corresponden a quitar los 38 duplicados exactos, dejando 5.002 filas. La primera revisión usa 5.040: corresponden 1.085 y 465. También deben usarse 410 casos de periodo 2025-2 con solicitud de 2026 y 75 solicitudes en septiembre de 2026.

723 fechas en formatos alternativos no equivalen a 723 fechas inválidas. Exactitud requiere contraste con la realidad; oportunidad requiere información de extracción/actualización. Las variaciones de formato se describen principalmente bajo consistencia, y los incumplimientos de una regla confirmada bajo validez.

Evidencia complementaria: `reports/exploracion/revision_diagnostico_propuesto.json`. Los conteos se realizaron con el original; consultar allí las convenciones de interpretación y las equivalencias usadas en los controles conjuntos.
