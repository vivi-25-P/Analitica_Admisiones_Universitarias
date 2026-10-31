# Revisión del dashboard de admisiones

Revisión del 30 de octubre de 2026. Se consultó el modelo abierto DashboardAdmisiones mediante el MCP de Power BI en modo de solo lectura. Se compararon los resultados con el Excel entregable y las tablas calculadas del notebook 04. La imagen proporcionada se utilizó para revisar la franja superior. La captura automática de la aplicación no está disponible por un error de inicialización del control de Windows desde WSL.

## Corrección aplicada posteriormente

Con autorización del usuario se corrigieron % Matriculado y % sin asesor asignado en el modelo abierto mediante una sesión temporal de escritura. Se respaldaron las medidas anteriores y se actualizaron únicamente sus expresiones. Las mismas fórmulas quedaron guardadas en FactRegistros.tmdl y en el generador. La configuración general del MCP permanece en solo lectura.

Las 22 referencias generales, los 28 grupos, los 395 segmentos y las nueve dimensiones siguen correctos. Los siete casos de prueba por estado y asesor pasan ahora sin errores de contexto. Se comprobaron adicionalmente filtros combinados de programa, modalidad, canal, ciudad y periodo. Los datos permanecen intactos. Los apartados que reproducen los errores conservan los valores anteriores como evidencia histórica.

## Resultado general

El proyecto auditado contenía seis páginas de análisis. Posteriormente se añadió Inicio, una portada con navegación, sin alterar los cálculos. El modelo conserva una tabla de hechos, nueve dimensiones y seis tablas de referencia independientes. Las diez relaciones están listas, con cardinalidad de varios a uno y una sola dirección de filtro. Nueve están activas y la de fecha de matrícula está inactiva. Las nueve dimensiones tienen claves únicas y no se detectaron claves informadas de la tabla de registros sin correspondencia.

Las veintidós medidas reproducen sus valores de referencia sin filtros. Coinciden veintiocho grupos por programa, canal, ciudad, periodo, modalidad y fuente. Coinciden también las 395 combinaciones observadas de ciudad, programa, modalidad y periodo. Se verificaron 115 referencias de campos de los visuales sin encontrar referencias a columnas o medidas inexistentes.

Estos resultados validan los cálculos y los cruces consultados, pero no equivalen a una certificación de todas las interacciones por clic ni de la apariencia de las seis páginas.

## Cobertura por página

| Página | Contenido existente | Ajuste o complemento |
| :--- | :--- | :--- |
| Panorama de admisiones | Registros, Matriculado, proporción observada, códigos por origen y distribución de programas, canales, estados y modalidades. | El denominador de la proporción Matriculado ya fue corregido y validado. |
| Captación y segmentos | Matriz de programas y ciudades, proporción por canal y combinaciones de ciudad, programa y modalidad. | Señalar expresamente los grupos pequeños y las oportunidades de piloto. No tratar treinta registros como una garantía de fiabilidad. |
| Seguimiento del proceso | Documentos y asesores por estado, puntajes, intervalos aptos y clasificación de recurrencia en la base completa. | Porcentaje Sin asignar corregido. Falta completar indicadores documentales dinámicos. |
| Cobertura y condiciones | Serie de fechas aptas, fuentes, puntajes e importes disponibles. | Complementar las cantidades con porcentajes de cobertura y disponibilidad de correo. Mostrar la referencia temporal de los controles. |
| Comparaciones controladas | Canales con pesos comunes, contraste binario de H3 y sensibilidad de los 49 pares Oracle. | Para cubrir H3 con todo el detalle acordado, incorporar los perfiles condicionados de los seis estados. |
| Respuestas y decisiones | Respuestas a las preguntas, diez indicadores de referencia y seis propuestas de acción. | Los valores son de la base completa. Conservar la advertencia de que estas tablas no cambian con los filtros. |

## Errores reproducidos con filtros

La medida % Matriculado utiliza un numerador que sustituye el estado seleccionado, mientras el denominador conserva esa selección. Esto compara grupos distintos.

| Selección de estado | Resultado antes de corregir | Criterio previsto en el plan |
| :--- | ---: | :--- |
| Matriculado | 100,00 % | Mantener la proporción sobre todos los estados del mismo ámbito. |
| Admitido | 64,71 % | Mantener la proporción sobre todos los estados del mismo ámbito. |
| Documentación pendiente | 184,80 % | Mantener la proporción sobre todos los estados del mismo ámbito. |

Sin otros filtros, ese ámbito contiene 5.500 registros y la proporción correcta según el criterio acordado es 21,44 %. No se propone fijar este valor como constante. Debe seguir cambiando con programa, modalidad, canal, periodo, ciudad y fuente, conservando el denominador adecuado.

La medida % sin asesor asignado sustituye el filtro de asesor solo en el numerador. Al seleccionar Asesor 2 devuelve 100,55 % y con Asesor 3, 101,38 %. Para una cobertura calculada dentro del grupo seleccionado, una selección compuesta exclusivamente por un asesor informado debe tener cero registros Sin asignar. La propuesta usa la intersección con el grupo seleccionado.

Ambas fórmulas alternativas se comprobaron inicialmente como medidas temporales dentro de consultas DAX. Posteriormente se aplicaron con autorización del usuario al modelo y al generador. La proporción Matriculado conserva todos los estados del mismo ámbito, mientras Sin asignar utiliza la intersección con el grupo de asesor seleccionado. Los resultados actuales figuran en auditoria_modelo.json y en validacion_filtros_combinados.json. La evidencia anterior está en auditoria_modelo_antes_correccion.json.

## Indicadores y alcance pendiente

| Indicador del análisis | Situación actual |
| :--- | :--- |
| K01. Proporción Matriculado | Medida dinámica corregida y validada al seleccionar estados y combinar otros filtros. |
| K02. Cobertura de asignación | El porcentaje complementario Sin asignar ya está corregido. Falta una medida explícita de cobertura de asignación. |
| K03. Documentación completa | Disponible como distribución y referencia global. Falta el indicador dinámico explícito de cantidad y porcentaje. |
| K04. Matriculado con documentos No o Pendiente | Existe la cantidad de 514. Falta la proporción explícita sobre Matriculado, con referencia global de 43,60 %. |
| K05. Documentación pendiente con documentos Sí | Visible en el cruce y en la referencia. Falta el indicador explícito de 393 y su proporción de 61,60 %. |
| K06. Estado Retirado | Visible en la distribución de estados. Falta una medida explícita de proporción para seguimiento. No llamarla tasa de abandono. |
| K07. Disponibilidad de correo | Figura como referencia global. Falta una medida de cobertura dinámica. |
| K08. Cobertura de puntaje | La cantidad está implementada. Falta la proporción explícita. |
| K09. Cobertura de importe | La cantidad está implementada. Falta la proporción explícita. No es recaudo. |
| K10. Recurrencia de códigos de la Principal | Existe la clasificación por número de solicitudes en toda la base. Falta una medida explícita con el ámbito de códigos informados de la fuente Principal y su denominador. No confundirla con retención. |

No es necesario convertir los diez indicadores en tarjetas de la portada. Los principales pueden quedar en Panorama y Seguimiento y los de calidad en Cobertura. No se incorporan ROI, ROAS o costo de adquisición sin las fuentes necesarias.

## Ajuste visual aplicado

Los veinticuatro segmentadores de las primeras cuatro páginas tenían una altura de 58 unidades y comenzaban en y=82. Se amplió su altura a 76 y se desplazaron a y=90. Las tarjetas y gráficos se redistribuyeron debajo de la franja, manteniendo el lienzo de 1.280 por 720. Se comprobó que las posiciones internas y externas coinciden, que no se sale ningún objeto del lienzo y que la franja de filtros no invade el contenido inferior.

Se conservó una copia exacta del diseño anterior en respaldo_diseno_anterior.json. El generador se ajustó con la misma regla para que no se pierda al reconstruir. No se ejecutó el generador sobre el proyecto principal, ya que esa operación elimina la caché local y reemplaza más archivos. La comprobación del generador se hizo en una carpeta temporal.

El cambio está guardado en report.json. La instancia abierta de Power BI no vuelve a leer automáticamente ese archivo. Se necesita reabrir el proyecto para comprobar la apariencia posterior. No se debe sobrescribir el ajuste guardando sobre él el diseño anterior que siga en memoria. Si hay otros cambios sin guardar, deben conservarse primero en una copia.

## Orden recomendado para terminar

1. Reabrir el proyecto y comprobar visualmente los filtros ampliados.
2. Completado: dos porcentajes corregidos con respaldo previo y validación posterior.
3. Completar las medidas de los indicadores acordados y verificar sus denominadores bajo filtros combinados.
4. Completar H3 y facilitar la lectura de segmentos, con tamaño del grupo y advertencias visibles.
5. Revisar sincronización de filtros entre páginas, restablecimiento de selecciones, formatos COP y porcentajes y lectura de textos extensos.
6. Confirmar las cifras de referencia y exportar un PBIX con los datos cargados para la entrega de consulta.

No se modificaron el Excel, PostgreSQL o los datos del modelo. Solo se corrigieron las dos expresiones autorizadas. No se realizó commit ni push.
