# Análisis administrativo y dashboard de admisiones

## Objetivo y punto de partida

Convertir los registros disponibles en hallazgos administrativos, oportunidades de captación y propuestas de seguimiento. El informe y el dashboard deben responder las mismas preguntas con cifras reconciliadas.

La base de trabajo es deliverables/BaseUnificada_Entregable.xlsx, hoja BaseUnificada, con 5.500 registros y 18 columnas. El otro entregable es el informe administrativo en Drive. El archivo Power BI será un producto de la siguiente fase solicitada, todavía no construido. No se cambia la limpieza para iniciar este análisis.

Una fila representa un registro de solicitud de origen. La independencia de eventos entre sistemas no está confirmada. Hay 3.424 códigos de aspirante por origen, no personas globales únicas. Las 500 filas Oracle se incluyen y se permite comparar fuentes sin retirarlas del conjunto.

## Secuencia de trabajo

1. Crear el notebook 04 de análisis administrativo, leyendo la entrega y comprobando su huella. Reutilizar los criterios de elegibilidad del notebook 03.
2. Calcular frecuencias, porcentajes, comparaciones por programa, modalidad, canal, ciudad y periodo, y estadísticas numéricas con cobertura por grupo.
3. Explorar segmentos y comprobar que sus patrones no dependan solo de pocos registros, diferencias de fuente o faltantes. No inferir crecimiento con periodos o meses de cobertura desigual.
4. Redactar cada hallazgo como hecho observado, interpretación administrativa, límite y acción propuesta. Separar las hipótesis de los hechos.
5. Construir el modelo y las medidas de Power BI con las mismas reglas. Verificar totales y filtros contra el notebook.
6. Incorporar resultados y gráficos seleccionados en Análisis descriptivo de la base integrada, después de limpieza y antes de las preguntas de seguimiento. Cerrar con recomendaciones y decisiones propuestas.

## Preguntas y evidencia

| Pregunta | Evidencia que se calculará | Uso administrativo y límite |
| :--- | :--- | :--- |
| ¿Cómo se distribuyen las solicitudes por programa, modalidad y canal, y qué se observa en los estados del proceso? | Conteos, participaciones y cruces de programas, modalidades, canales y estados. | Respuesta general sobre registros recibidos, sin afirmar personas únicas o conversión definitiva. |
| ¿Qué programas concentran registros y qué proporción tiene estado Matriculado por periodo? | Volumen y proporción de estado Matriculado dentro de cada grupo. | Interés registrado y seguimiento. Esa proporción no es tasa definitiva de conversión ni matrícula efectiva confirmada. |
| ¿Se mantienen las diferencias entre canales dentro de un mismo programa, modalidad y periodo? | Comparación de grupos equivalentes con numerador, denominador y tamaño visibles. | Identificar diferencias descriptivas. No medir eficacia causal, rentabilidad o costo de adquisición sin inversión y atribución. |
| ¿Cómo se distribuyen los estados según documentación y asesor? | Cruces por documentación, asignación de asesor, programa, modalidad y periodo. | Detectar grupos para revisar acompañamiento y contradicciones. No evaluar productividad causal del asesor ni tiempos por etapa. |
| ¿Dónde aparecen segmentos de interés para captar aspirantes? | Ciudad, programa y modalidad, complementados con canal y periodo. | Proponer campañas piloto donde existe interés observado. Pocas solicitudes no demuestran demanda insatisfecha ni ausencia de mercado. |

Las preguntas originales sobre solicitudes únicas y matrícula efectiva conservan sus condiciones pendientes. Se distingue la respuesta descriptiva posible ahora de la validación que necesitarían esas preguntas en sentido estricto.

## Indicadores compartidos

| Indicador | Regla |
| :--- | :--- |
| Registros | Conteo de filas del ámbito seleccionado. Base completa: 5.500. |
| Participación de una categoría | Registros de la categoría divididos por todos los registros del ámbito definido. Respetar los filtros y mostrar el denominador. |
| Registros con estado Matriculado | Contar el estado homologado. Total de control: 1.179. No llamarlos personas matriculadas únicas. |
| Proporción con estado Matriculado | Registros Matriculado divididos por registros del mismo grupo. Etiquetar como proporción observada, no conversión definitiva. |
| Puntaje promedio y mediano | Usar valores informados, 5.254 en la base completa. Mostrar ausencias y cobertura por grupo. |
| Importe promedio y mediano | Usar importes informados, 4.580 en la base completa. No llamarlo recaudo, ingreso o tarifa oficial. |
| Días entre solicitud y matrícula | Usar los 1.035 intervalos que cumplen los controles existentes, recalculando el tamaño bajo filtros. No atribuirlo a una etapa. |
| Serie con control de fecha | Usar las 5.320 fechas de solicitud aptas según los controles y mostrar por separado las observadas. No recalcular el periodo de ingreso. |
| Códigos de aspirante por origen | Contar combinaciones distintas de origen y código informado. Separar 90 registros sin código. No sumar códigos por programa como personas nuevas. |

La ausencia de programa se muestra como Sin información solo para presentar resultados. No se modifica el dato maestro. Los campos periodo, duración e identificadores no se suman como indicadores.

## Dashboard propuesto

| Página | Contenido | Decisión que puede orientar |
| :--- | :--- | :--- |
| Panorama de admisiones | Volumen, programas y modalidades, participación por canal y distribución de estados. | Prioridades de oferta y seguimiento. |
| Captación y segmentos | Matriz ciudad por programa, modalidad y canal, tamaño del segmento y comparación por periodo. | Campañas piloto y mensajes para segmentos con interés registrado. |
| Seguimiento del proceso | Estados por documentación y asesor, proporciones observadas y tamaños de grupo. | Revisión de casos y acompañamiento. Los estados no se dibujan como un embudo de transiciones reales. |
| Cobertura y condiciones | Faltantes, origen, fechas observadas, cobertura numérica y sensibilidad de correspondencias. | Interpretar los resultados con sus límites. |

Filtros comunes: periodo de ingreso, programa, modalidad, canal, ciudad y fuente. La fecha de solicitud se presenta separada del periodo académico. Los títulos deben reflejar los filtros activos y la unidad de registro.

## Modelo mínimo para Power BI

Se conserva el Excel maestro de 18 columnas. Dentro del modelo se puede preparar FactRegistrosAdmision, con una fila por registro y sus indicadores de control, junto con DimPrograma, DimCanal, DimPeriodo y DimFechaSolicitud. Modalidad, ciudad, documentación, asesor y estado pueden permanecer como atributos de la tabla de registros en la primera versión.

Las hojas Origen_Registros y Control_Calidad aportan controles mediante registro_id. Se comprueba que esa llave sea única antes de incorporarlas, evitando multiplicar filas. Las hojas de candidatos y aspirantes no se anexan a la tabla principal ni se suman como solicitudes adicionales.

La dimensión de programa conserva facultad, duración y nivel según el catálogo documentado. No sustituye la modalidad de cada solicitud por la modalidad del catálogo. El periodo de ingreso es una categoría ordenable y permanece independiente de la fecha de solicitud. Las relaciones tendrán claves únicas en dimensiones y filtrado hacia los registros.

El esquema y las fechas se diseñarán siguiendo [la guía oficial de esquema estrella](https://learn.microsoft.com/es-es/power-bi/guidance/star-schema) y [la guía de tablas de fechas](https://learn.microsoft.com/es-es/power-bi/guidance/model-date-tables). No es necesario crear un almacén dimensional en Docker para comenzar este modelo.

## Criterios para comunicar y decidir

Una recomendación debe identificar el hallazgo que la sustenta, el grupo al que aplica, una acción medible, un responsable propuesto y cómo evaluar el resultado. No se fijan metas numéricas sin calcular una línea de referencia.

Las oportunidades de captación se formulan como hipótesis para campañas piloto. No se imputan importes o programas para fabricar segmentos completos. La sensibilidad de 49 pares Oracle se comprueba en cada cruce relevante, porque la estabilidad de distribuciones generales no garantiza estabilidad en segmentos pequeños. Los otros 451 pares conservan sus diferencias e identidad no confirmada.

Se propondrán decisiones sobre comunicación por segmento, seguimiento documental, revisión de asignación y calidad del registro. No se recomendará eliminar programas, recortar presupuesto o atribuir fallas a asesores únicamente por estas asociaciones.

## Criterios de cierre de la fase

Notebook ejecutado y tablas reproducibles. Pregunta general respondida y alcance de las tres preguntas particulares explícito. Hallazgos con numeradores y denominadores, gráficos legibles y recomendaciones vinculadas con evidencia. Power BI conciliado contra los mismos resultados y filtros. Informe en Drive actualizado. Base maestra conservada e integridad comprobada. El dashboard permanece pendiente hasta realizar esa construcción y sus verificaciones.

## Actualización de infraestructura

La base final ya está disponible en PostgreSQL como analitica.base_unificada. El Excel entregable permanece idéntico como alternativa. No se creó todavía el modelo dimensional o dashboard. La selección de fuente y la preservación de trazabilidad están descritas en [la guía de conexión](postgresql_base_unificada_powerbi.md).
