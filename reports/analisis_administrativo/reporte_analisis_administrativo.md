# Análisis administrativo de la base integrada

## Alcance y criterio

Se describen 5.500 registros y 18 columnas de la entrega validada. La unidad es registro de solicitud de origen.
No se confirman personas globales únicas ni independencia de solicitudes entre fuentes.
Se conservan los controles temporales de referencia del 26 de octubre de 2026, sin reinterpretarlos como una actualización de datos.
Los porcentajes de estados no son tasas definitivas de conversión. Se muestran tamaños, cobertura y diferencias observadas.
No se aplican pruebas de significación o intervalos de confianza automáticamente. No se presume independencia entre registros.
Los grupos con menos de 30 registros se marcan como pequeños y se conservan. Ese criterio visual no garantiza fiabilidad.
La existencia de distribuciones similares o la imposibilidad de recomendar una segmentación firme son resultados válidos.

## Respuesta general

Derecho y Especialización en Data Analytics reúnen 2.449 registros, equivalentes al 44,53 % del conjunto.
Presencial representa el 39,85 %, Virtual el 39,69 % e Híbrida el 20,45 %.
Los canales muestran volúmenes cercanos. El estado Matriculado aparece en 1.179 registros, el 21,44 %.
La distribución de estados es una fotografía del registro disponible, no un recorrido individual o embudo de transiciones.

## Tres preguntas específicas

### 1. Demanda registrada y matrícula por programa

La tabla programa_periodo_academico.csv presenta cantidades, participaciones y proporción Matriculado por programa y periodo.
En el periodo 20252, Especialización en Data Analytics reúne 231 registros y el 21,57 % de ese periodo. En el periodo 20261, Derecho reúne 518 registros y el 23,06 % de ese periodo. En el periodo 20262, Especialización en Data Analytics reúne 520 registros y el 23,82 % de ese periodo.
El periodo es semestre de ingreso, no semestre calculado desde la fecha de solicitud.
La respuesta actual describe registros. La pregunta original sobre solicitudes únicas y matrículas efectivas conserva su condición de validación.
Se mantienen 26 registros Sin información en programa, dentro del denominador general.

### 2. Diferencias entre canales

La proporción bruta observada va de 19,67 % a 23,86 %.
La amplitud es 4,18 puntos porcentuales en la base completa. En el soporte común es 4,03 puntos antes de ponderar y 3,20 con pesos comunes por programa, modalidad y periodo.
El soporte común incluye 5.474 de 5.500 registros y 63 estratos con presencia de todos los canales.
La tabla canales_comparables.csv informa cobertura, proporciones brutas y estandarizadas y celdas pequeñas por canal.
No se afirma que las diferencias desaparezcan. La estandarización descriptiva no demuestra causalidad, eficacia o rentabilidad.
No se ordenarán inversiones solo por estas proporciones.

### 3. Documentación, asesor y estado

La proporción Matriculado es 20,24 % con documentos Sí,
23,32 % con No y 23,10 % con Pendiente.
Estas cifras no indican que completar documentos reduzca la matrícula. Pueden reflejar diferencias de actualización o reglas no documentadas.
Hay 514 registros Matriculado con documentación No o Pendiente y 393 Documentación pendiente con documentos Sí.
Los cruces detallados por programa, modalidad y periodo permiten revisar composición, sin atribuir las diferencias al asesor.
Los intervalos por documentación se describen aparte con los 1.035 casos aptos. No se mide tiempo por etapa ni retiro posterior.
Sí: 33 días de mediana con 578 intervalos aptos. No: 34 días de mediana con 230 intervalos aptos. Pendiente: 33 días de mediana con 227 intervalos aptos.

## Hallazgos y decisiones propuestas

| codigo | hallazgo | hecho_observado | accion_propuesta | limite |
| :--- | :--- | :--- | :--- | :--- |
| H01 | Concentración de interés registrado | Derecho y Especialización en Data Analytics reúnen 2.449 registros, el 44,53 % del total. Presencial reúne 2.192 y Virtual 2.183. | Revisar capacidad, mensajes y atención para la oferta con mayor volumen registrado. | Las solicitudes no representan todo el mercado ni disponibilidad de cupos. |
| H02 | Diferencias observadas entre canales | Instagram presenta 23,86 % con estado Matriculado y Referido 19,67 %. En soporte común, la amplitud bruta es 4,03 puntos y con pesos comunes es 3,20 puntos. | Comparar campañas piloto dentro de programas, modalidades y periodos equivalentes antes de redistribuir presupuesto. | Las celdas pequeñas y la composición limitan la interpretación. No se mide eficacia o rentabilidad. |
| H03 | Coherencia documental por revisar | 514 de 1.179 registros Matriculado tienen documentos No o Pendiente. Hay 393 registros Documentación pendiente con documentos Sí. | Revisar las reglas y actualización coordinada de documentación y estado. | No se conoce la fecha de actualización de cada atributo. No se demuestra incumplimiento ni secuencia. |
| H04 | Puntajes y estados con información parcial | Promedio 70,21 en Admitido y 67,80 en No admitido. Se dispone de 5.254 puntajes. | Examinar distribución y reglas de admisión antes de proponer cambios en criterios. | Una diferencia de promedios no reconstruye la decisión ni valida un umbral institucional. |
| H05 | Asignación y recurrencia requieren dos unidades de lectura | 1.101 registros, 20,02 %, figuran Sin asignar. En la principal, 1.363 de 2.924 códigos tienen entre 2 y 7 solicitudes. | Revisar asignación y seguimiento por solicitud y código, evitando duplicar personas en los reportes. | La recurrencia puede ser legítima. No se atribuye desempeño a un asesor ni se fusionan personas por fuente. |
| H06 | Segmentos para validar, no nichos confirmados | La matriz ciudad, programa y modalidad identifica concentraciones de volumen. En segmentos con al menos 30 registros, el cambio máximo en la proporción Matriculado bajo el escenario de 49 pares es 2,37 puntos. | Seleccionar combinaciones con volumen suficiente para campañas piloto y registrar su respuesta. | La marca de 30 no prueba precisión. El escenario no resuelve los otros 451 pares ni mide mercado no captado. |
| H07 | Importes insuficientes para deducir tarifas por programa | Los siete programas identificados presentan cinco importes distintos y mediana de 2.500.000 COP. Hay 4.580 importes informados y 920 ausentes. | Mantener los importes como contexto y contrastar tarifas antes de presupuestar ingresos. | No acredita pagos, recaudo o tarifas oficiales. No se imputa por programa. |

| evidencia | decision_o_accion | responsable_propuesto | como_evaluar | estado |
| :--- | :--- | :--- | :--- | :--- |
| H03 | Revisar los 514 casos documentales de Matriculado y los 393 casos con estado documental discordante | Admisiones y gestión documental | Casos revisados, reglas aclaradas y registros actualizados con evidencia | Propuesta, sin ejecutar |
| H05 | Revisar los 1.101 registros Sin asignar y definir cómo registrar una asignación efectiva | Coordinación de admisiones | Registros con asignación validada y fecha de actualización | Propuesta, sin ejecutar |
| H01 y H06 | Seleccionar segmentos con volumen y capacidad disponible para una campaña piloto | Mercadeo y coordinación académica | Solicitudes identificadas por campaña, seguimiento, costos y matrícula validada | Hipótesis para evaluar |
| H02 | Comparar canales con igual oferta y seguimiento antes de modificar presupuesto | Mercadeo y admisiones | Resultados con denominadores comparables y gasto registrado | Propuesta, sin ejecutar |
| H04 | Contrastar puntajes y decisiones con las reglas institucionales | Comité de admisiones | Casos explicados por criterio, programa y periodo | Propuesta, sin ejecutar |
| H05 y H07 | Mejorar identificación entre fuentes, registro de eventos y catálogo de tarifas | Gestión de datos y responsables de sistemas | Correspondencias confirmadas, eventos con fecha y conceptos económicos definidos | Requiere registro futuro |

## Segmentos e incertidumbre entre fuentes

segmentos_completos.csv conserva todos los segmentos ciudad, programa y modalidad.
segmentos_volumen_priorizados_revision.csv muestra hasta 12 combinaciones con al menos 30 registros y programa identificado, ordenadas por volumen.
Son prioridades de revisión y pruebas de captación, no nichos de mercado confirmados ni mercados potenciales estimados.
segmentos_por_canal_periodo.csv mantiene los cruces finos, incluidos los pequeños, sin clasificarlos como ganadores.

El escenario hipotético cuenta una vez los 49 pares compatibles y contiene 5.451 registros.
La entrega no cambia. La comparación por fuente conserva Oracle y permite valorar su composición.
En segmentos con al menos 30 registros, el cambio máximo en proporción Matriculado es 2,37 puntos porcentuales.
No se deduce que los otros 451 pares sean independientes ni que el mercado completo esté representado.

## Qué cambió después de la limpieza y de incorporar fuentes

Se distinguen tres efectos en las tablas de antes y después. Primero se agrupan etiquetas sobre las mismas 5.040 filas originales.
Después se compara la fuente original alineada con la principal conciliada de 5.000 registros, enriquecida con CRM.
Finalmente se incorporan los 500 registros Oracle y se obtiene el conjunto de 5.500.
El aumento de 500 registros pertenece a incorporación de fuente, no a limpieza ni a crecimiento institucional.
No se sustituyen las cifras de la exploración inicial del informe por las del conjunto integrado.

## Siguiente uso

Estos resultados respaldan la sección administrativa y la construcción del dashboard con las mismas tablas y definiciones.
No se modifica Drive automáticamente. Las propuestas aún no son decisiones institucionales adoptadas.
El dashboard y su conexión en Power BI Desktop siguen pendientes.
