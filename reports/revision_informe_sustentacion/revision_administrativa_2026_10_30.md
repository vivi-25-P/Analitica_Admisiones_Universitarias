# Revisión del informe y propuesta de sustentación administrativa

Revisión del 30 de octubre de 2026. Se leyó la versión actual del informe de Drive, con modificación registrada a las 18:49 de Colombia, y el contenido y notas de las quince diapositivas de la sustentación v2. Se consultaron las evidencias de auditoría del dashboard y los resultados del análisis administrativo. Esta revisión no modifica el informe ni las presentaciones.

## Informe en Drive

El orden Oportunidades de captación y seguimiento, Dashboard en Power BI y Recomendaciones para la gestión es adecuado. Primero se presenta el conocimiento obtenido, luego cómo consultarlo y finalmente las acciones propuestas. El tono de las recomendaciones resulta administrativo y distingue observaciones de explicaciones no comprobadas.

### Ajustes del apartado Dashboard en Power BI

1. Sustituir la afirmación de que el dashboard lee Excel o PostgreSQL por una descripción de la conexión actual. El proyecto utiliza el Excel entregable y seis CSV de resultados. PostgreSQL conserva la base equivalente y constituye una alternativa de conexión. No se implementó en este proyecto una sustitución completa de todas las fuentes por PostgreSQL.
2. Actualizar el número de páginas: seis de análisis y una portada Inicio. Las cuatro primeras páginas del análisis tienen filtros. Comparaciones controladas y Respuestas y decisiones utilizan resultados de la base completa y no responden a esos filtros.
3. Escribir una fila por registro de solicitud, evitando sugerir solicitudes independientes confirmadas.
4. Precisar que los 33 días corresponden a la mediana de 1.035 registros aptos para comparar fechas. No equivalen a duración de atención ni a tiempos de cada etapa.
5. Sustituir la validación general por su alcance comprobado. Las 22 medidas en sus valores generales, los 28 grupos, los 395 segmentos y las nueve dimensiones coinciden con las referencias. Se corrigieron y comprobaron los contextos de dos porcentajes. Esto no certifica todas las interacciones por clic ni implica que los diez indicadores de referencia ya tengan medidas dinámicas explícitas.
6. Simplificar el detalle técnico del modelo. Para el cuerpo administrativo basta explicar que permite consultar las solicitudes por programa, modalidad, canal, ciudad, periodo y fuente. El esquema estrella y DAX pueden quedar como una oración breve o en un anexo.
7. Mantener la Figura 10 de Panorama con una captura posterior a los ajustes. Una captura legible y su explicación son suficientes para esta sección, sin incorporar imágenes de todas las páginas.

Texto sugerido para el inicio:

Los resultados se organizaron en un tablero de Power BI para consultar el volumen de solicitudes, su distribución y las situaciones que requieren seguimiento. El proyecto actual utiliza el Excel entregable de 5.500 registros y seis archivos de resultados del análisis, sin repetir la limpieza. La misma base está disponible en PostgreSQL como alternativa de conexión.

El tablero incluye una portada y seis páginas de análisis. Las cuatro primeras permiten consultar la información por periodo, programa, modalidad, canal, ciudad y fuente. Las dos últimas presentan comparaciones y respuestas calculadas sobre la base completa y no cambian con los filtros.

Texto sugerido para sustituir la frase final de validación:

Los cálculos generales y las agrupaciones revisadas coinciden con el análisis de referencia. La revisión final de presentación e interacciones continúa antes del cierre de la entrega.

## Recomendaciones para la gestión

Conservar los cuatro párrafos actuales. Mejorar tres puntos:

1. Cambiar atender la concentración por revisar la capacidad de atención en Derecho y Especialización en Data Analytics. La concentración describe el volumen, pero no constituye por sí misma un problema.
2. Añadir responsables propuestos y seguimiento de las tres prioridades. No inventar plazos, metas o recursos aprobados.
3. Cambiar el futuro reunirá por el presente permite consultar. El tablero ya está construido, aunque su cierre visual y algunos indicadores siguen pendientes.

Cierre sugerido:

Para dar continuidad a estas recomendaciones, se propone que admisiones y gestión documental revisen los casos señalados, que la coordinación de admisiones compruebe la asignación de responsables y que mercadeo, junto con coordinación académica, evalúe los pilotos de captación. El tablero permite consultar la situación registrada por programa, modalidad, canal y periodo de ingreso. La institución deberá acordar plazos y metas y registrar el resultado de las acciones para evaluar su evolución.

Seguimiento propuesto:

| Prioridad | Responsable propuesto | Referencia actual | Cómo revisar el avance |
| :--- | :--- | :--- | :--- |
| Coherencia documental | Admisiones y gestión documental | 514 Matriculado con documentos No o Pendiente y 393 Documentación pendiente con Sí | Casos revisados, explicación documentada y actualización respaldada. K04 y K05 contextualizados con sus denominadores. |
| Asignación | Coordinación de admisiones | 1.101 registros Sin asignar, el 20,02 % | Comprobar responsable, fecha, contacto y siguiente acción. K02 como cobertura de asignación registrada. |
| Pilotos de captación | Mercadeo y coordinación académica | Administración virtual en Cali y Bogotá | Validar capacidad y comparar oferta, periodo y seguimiento. Registrar inversión y resultados antes de estimar costos o retorno. |

No utilizar la reducción de inconsistencias como una mejora operativa demostrada si solo se actualizó la información. No presentar los segmentos como mercados rentables confirmados.

Corrección menor fuera de las nuevas secciones: en la comprobación final de la limpieza está duplicado el fragmento con los valores disponibles, indicando su cobertura. Debe aparecer una sola vez.

## Sustentación actual

La v2 tiene quince diapositivas y una identidad visual consistente con la teoría. El flujo de conciliación está explicado correctamente como preparación de información, no como conversión. Los hallazgos conservan límites de interpretación.

Para una junta administrativa, el problema es la distribución del tiempo: la necesidad institucional no aparece suficientemente explícita antes del diagnóstico y hay tres láminas centradas en las etapas, la conciliación y ejemplos de limpieza. Los códigos L00 a L14, JSON y SHA corresponden a respaldo técnico. En cambio, las oportunidades territoriales concretas no tienen una diapositiva propia y el cierre no formula claramente qué se propone acordar.

Cambios propuestos sobre las diapositivas existentes:

| Diapositiva actual | Tratamiento propuesto |
| :--- | :--- |
| 1. Portada | Conservar y abrir con el propósito institucional. |
| 2. Ruta | Sustituir por necesidad del negocio, pregunta general y decisiones que se busca apoyar. |
| 3. Diagnóstico | Resumir riesgos que impedían comparar y contar correctamente. Evitar detenerse en etiquetas originales. |
| 4. Integración | Conservar como esquema visual de fuentes, junto con el diagnóstico resumido. |
| 5. Quince etapas | Pasar al anexo técnico. |
| 6. Conciliación | Conservar como explicación central de preparación y confianza. |
| 7. Antes y después | Pasar al anexo. Usar solo un ejemplo oral si hace falta. |
| 8. Matrícula registrada | Ampliar con concentración por programa y modalidades para responder la pregunta general y H1. |
| 9. Canales | Conservar el resultado y simplificar pesos comunes como comparación de grupos equivalentes. |
| 10. Respuestas | Distribuir sus respuestas entre programas, seguimiento y canales, conservando el alcance de las preguntas originales. |
| 11. Cinco hallazgos | Priorizar documentación y asignación con sus denominadores. Pasar puntajes e importes a apoyo. |
| 12. Modelo estrella | Pasar al anexo técnico. Explicar el beneficio del modelo en una oración al mostrar el tablero. |
| 13. Dashboard | Actualizar a seis páginas de análisis más Inicio y renovar capturas. Mostrar una sola consulta guiada. |
| 14. Recomendaciones | Conservar y convertir en tres acuerdos propuestos con responsables e indicadores. Añadir los pilotos territoriales concretos en una lámina previa. |
| 15. Preguntas | Dejar como respaldo para preguntas, después del cierre con las acciones propuestas. |

Las diapositivas 12 y 13 contienen advertencias previas a la auditoría de hoy. Deben actualizarse sin afirmar validación total. Las 22 medidas basales y los contextos examinados ya se verificaron. Permanecen pendientes medidas explícitas de varios indicadores, completar la presentación de H3 y las pruebas finales de interacción y entrega.

La pregunta formal H3 trata la distribución de los seis estados, no solo la suma Documentación pendiente o Retirado. Si se utiliza ese contraste binario al exponer, presentarlo como una síntesis de la exploración, con el perfil completo disponible en el respaldo. Las preguntas sobre conversión definitiva siguen condicionadas: describimos registros y no identidad única ni un seguimiento uniforme confirmado.

## Guion propuesto de trece minutos

Diez diapositivas principales. Reservar dos minutos para preguntas si el límite total de quince minutos las incluye. La duración es una estimación de planificación y requiere ensayo.

| Orden | Título propuesto | Mensaje o evidencia | Minutos |
| :--- | :--- | :--- | :--- |
| 1 | Información para fortalecer las admisiones | Propósito y resultado del proyecto, sin enumerar herramientas | 0,5 |
| 2 | Qué necesitaba conocer la institución | Demanda registrada, captación y seguimiento. Pregunta general | 1 |
| 3 | Qué impedía una lectura confiable | Fuentes dispersas, categorías distintas y repeticiones. Alcance de la integración | 1 |
| 4 | Cómo construimos una base comparable | 5.640 entradas a 5.500 registros. Recuperación CRM, conservación de Oracle y controles | 1,5 |
| 5 | Dónde se concentra el interés registrado | Derecho y Data Analytics 44,53 %. Presencial y Virtual cercanas al 40 %. Matriculado 21,44 %. Respuesta general y H1 | 1,5 |
| 6 | Qué requiere revisión administrativa | 514 de 1.179, 393 de 638 y 1.101 Sin asignar. H3 sin atribuir causas o desempeño | 1,5 |
| 7 | Qué sabemos de los canales | Diferencias de 4,03 a 3,20 puntos en grupos comunes. Respuesta H2 y límites para mover presupuesto | 1,5 |
| 8 | Qué oportunidades conviene probar | Administración virtual: Cali 19 de 44 y Bogotá 22 de 66. Derecho: revisión de seguimiento antes de ampliar inversión | 1,5 |
| 9 | Cómo consultar y seguir los resultados | Una demostración de Panorama y un segmento, con periodo definido. Distinguir comparaciones estáticas | 1,5 |
| 10 | Qué proponemos acordar | Revisión documental, asignación y pilotos. Responsables propuestos, indicadores y metas por acordar | 1 |

Total de exposición: trece minutos. Con preguntas: quince. Los cambios de expositor deben estar incluidos dentro del tiempo de cada bloque. Si participan tres personas, el primer bloque puede cubrir las diapositivas 1 a 4, el segundo 5 a 7 y el tercero 8 a 10. Ajustar el reparto después de ensayar.

No recorrer las siete páginas de Power BI en directo. Preparar una secuencia de selección y capturas de respaldo. El modelo estrella, las quince etapas, la tabla de estandarización, las respuestas completas y los controles detallados deben quedar después del cierre como material para preguntas.

La intervención final debe pedir acuerdos concretos sin presentarlos como aprobados. Por ejemplo: proponemos iniciar la revisión documental, comprobar responsables de seguimiento y diseñar dos pilotos comparables. El retorno de inversión y la eficacia causal de los canales no se estiman con esta información.
