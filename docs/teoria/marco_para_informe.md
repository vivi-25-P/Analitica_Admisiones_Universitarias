# Base teórica para el primer informe exploratorio

## Fuentes y prioridad

1. **Calidad de datos.pptx**: referencia principal del diagnóstico. Las citas siguientes indican números de diapositiva del archivo original en `docs/referencias/`.
2. **Conceptos BI.pptx**: contexto del proyecto, decisiones y alcance descriptivo.
3. **Caso2_Admisiones_Universitarias_Analisis_Descriptivo.pdf**: requisitos de la actividad; páginas 2 y 3.

Se revisaron el texto editable y las notas de ambas presentaciones, además de las imágenes centrales de Conceptos BI sobre datos/información, arquitectura, CRISP-DM y tipos de análisis. Las extracciones de texto se conservan en esta carpeta como apoyo, no como sustituto de las presentaciones.

## Qué significa calidad en este caso

Calidad es la adecuación de los datos para responder una pregunta concreta, no la apariencia de orden ni la ausencia total de valores extraños (Calidad, diap. 4–5). Un cálculo correcto puede producir una conclusión equivocada si su base contiene duplicados, omisiones o categorías fragmentadas.

Pregunta de trabajo: ¿cómo se distribuyen las solicitudes por programa, modalidad y canal, y qué se observa en los estados del proceso de admisión? Primero describimos registros; la equivalencia entre una fila, una solicitud y un aspirante único requiere validación.

El primer informe corresponde al **perfilamiento**: comprender estructura, contenido y patrones antes de limpiar (Calidad, diap. 8). En el proceso recomendado, priorizamos comprender, perfilar y detectar; las decisiones de tratamiento se documentan como propuestas. Aplicar correcciones y validar el antes/después quedan para la etapa posterior (diap. 14).

## Las seis dimensiones aplicadas a admisiones

La definición procede de Calidad, diap. 6. Los controles de esta tabla son propuestas para nuestro caso; no son reglas institucionales confirmadas.

| Dimensión | Qué revisar en el CSV | Evidencia que necesitamos | Límite de interpretación |
|---|---|---|---|
| Completitud | Vacíos por columna; identificadores, puntajes, programa y matrícula | Cantidad y porcentaje sobre 5.040 filas; distinguir vacío de `No aplica` y `por definir` | La ausencia de fecha de matrícula puede ser esperable según el estado; falta definir campos obligatorios |
| Unicidad | Filas idénticas, `registro_id` repetidos y varios registros por `aspirante_id` | Conteos separados, ejemplos y definición de entidad/evento | Un aspirante repetido puede tener solicitudes legítimas; no deduplicar automáticamente |
| Validez | Fechas interpretables, formato del correo y valores numéricos | Formatos observados, resultados de interpretación y valores rechazados | La escala válida del puntaje y las reglas del correo deben explicitarse; formato válido no prueba exactitud |
| Consistencia | Variantes de programa, modalidad, ciudad, asesor y periodo; relaciones entre estado y fechas | Frecuencias sin normalizar y cruces entre campos; formatos de fecha documentados | Una matrícula anterior a la solicitud es una alerta solo cuando ambas fechas están interpretadas sin ambigüedad |
| Exactitud | Puntajes o importes inusuales y correspondencia con el hecho real | Contraste con el sistema fuente, reglas institucionales y responsable | Este CSV sintético permite detectar sospechas, pero no certificar que un dato refleja la realidad |
| Oportunidad | Disponibilidad y actualización de los registros para el análisis | Fecha de extracción, actualización, cierre y plazo esperado | Las fechas de solicitud por sí solas no permiten medir retrasos de actualización; dejar como no evaluable con la información disponible |

No sumar los porcentajes de problemas entre dimensiones: una fila puede presentar varios a la vez. No crear una nota global de calidad sin definir pesos, obligatoriedad y criterios.

## Principios para evitar conclusiones incorrectas

- **Faltantes con significado:** no mezclar vacío, desconocido y no aplicable. No reemplazar vacíos por cero; cambia los promedios y totales (Calidad, diap. 9).
- **Duplicados con contexto:** separar duplicado exacto, coincidencia parcial de clave y repetición legítima. Definir la unidad antes de eliminar (diap. 10).
- **Valor, tipo y significado:** conservar los campos como TEXT documenta el almacenamiento original. Para estadísticas, interpretar números/fechas en memoria o en SELECT y registrar los excluidos. No ordenar fechas como texto ni comparar puntajes lexicográficamente (diap. 11).
- **Atípico no equivale a error:** detectar, contrastar reglas y fuente, consultar contexto y documentar la decisión (diap. 7 y 12).
- **Limpieza y transformación:** tratar un error y adaptar la estructura son operaciones relacionadas, con propósitos diferentes; ambas exigen trazabilidad (diap. 13–16).
- **Trazabilidad:** conservar CSV, tabla original, hash, consultas, denominadores y limitaciones. Una categoría agrupada posteriormente debe tener su regla documentada (diap. 16–17).

## Qué aporta Conceptos BI

BI conecta datos con decisiones mediante procesos, métodos y herramientas; no se reduce a Power BI ni garantiza una decisión correcta (Conceptos BI, diap. 4–7 y 19).

La diapositiva 9 muestra el recorrido datos → información → conocimiento → decisión. Para admisiones, pasar de filas a una tabla de frecuencias genera información; interpretar su utilidad requiere contexto y calidad. No se debe saltar de una frecuencia a una recomendación de inversión sin costos, resultados validados y denominadores.

La arquitectura expuesta en las diapositivas 11–18 comprende fuentes, integración/ETL, almacenamiento/modelado, análisis/visualización y decisión/seguimiento. Nuestra organización inicial contiene una fuente CSV, una copia fiel en PostgreSQL y consultas exploratorias. No se necesita todavía un modelo estrella ni varias tablas de negocio.

La diapositiva 17 ubica CRISP-DM como proceso iterativo. Esta actividad se concentra en comprensión del negocio y de los datos. Las diapositivas 20–21 distinguen análisis descriptivo, diagnóstico, predictivo y prescriptivo. El informe responde **qué se observa**; las posibles explicaciones se presentan como hipótesis por validar.

## Alcance confirmado por la guía del caso

La página 2 exige reconocer la estructura, examinar calidad sin corregir el original, describir variables y construir visualizaciones pertinentes. También advierte que una solicitud no equivale necesariamente a un aspirante único ni a una matrícula efectiva.

La página 3 solicita un informe breve con cinco hallazgos descriptivos, al menos tres tablas o gráficos, diagnóstico inicial de calidad y tres preguntas posteriores. Extensión sugerida: 2–4 páginas sin anexos; adjuntar archivos o capturas de las visualizaciones.

## Qué queda para después

Validar catálogos y campos obligatorios, definir las claves de solicitud y aspirante, confirmar escala de puntajes, resolver fechas ambiguas y acordar reglas de matrícula. Solo después preparar limpieza/ETL en otra tabla y comparar resultados con el original.
