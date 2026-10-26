# Comprobación de calidad para iniciar el análisis

La revisión usa la entrega entrega_v1_6b14cc9ccf_716b06df_d0dca438_5cdda3c2, con 5.500 registros y 18 columnas.
No se imputaron valores, no se eliminaron filas y no se modificó el entregable.
El notebook 03 complementa la transformación documentada en el notebook 02.

## Disponibilidad de información

| columna | informados | ausentes | porcentaje_ausente |
| :--- | :--- | :--- | :--- |
| aspirante_id | 5410 | 90 | 1.6364 |
| programa | 5474 | 26 | 0.4727 |
| puntaje_admision | 5254 | 246 | 4.4727 |
| valor_matricula_cop | 4580 | 920 | 16.7273 |
| fecha_matricula | 1179 | 4321 | 78.5636 |
| correo | 5370 | 130 | 2.3636 |
| facultad | 5474 | 26 | 0.4727 |
| duracion_semestres | 5474 | 26 | 0.4727 |
| nivel_formacion | 5474 | 26 | 0.4727 |

No hay filas completamente vacías. El mínimo es 12 columnas informadas.
Los 90 registros sin código de aspirante conservan información útil para describir solicitudes.
Hay 0 matriculados sin fecha de matrícula y 4321 ausencias de esa fecha en otros estados.
Estas últimas no se tratan automáticamente como errores o fechas que deban imputarse.

## Concentración de faltantes

La siguiente tabla muestra el grupo con mayor porcentaje de ausencia en cada dimensión y variable.
Es una comparación descriptiva. No demuestra aleatoriedad, sesgo causal o significación estadística.
La tabla completa incluye modalidad y periodo en ausencias_por_grupo.csv.

| dimension | categoria | columna | registros_grupo | ausentes | porcentaje_ausente |
| :--- | :--- | :--- | :--- | :--- | :--- |
| programa | Sin información | valor_matricula_cop | 26 | 5 | 19.2308 |
| canal_captacion | Referido | valor_matricula_cop | 915 | 166 | 18.1421 |
| estado_proceso | Admitido | valor_matricula_cop | 1822 | 321 | 17.618 |
| fuente_origen | Principal | valor_matricula_cop | 5000 | 839 | 16.78 |
| programa | Sin información | puntaje_admision | 26 | 2 | 7.6923 |
| estado_proceso | Documentación pendiente | puntaje_admision | 638 | 39 | 6.1129 |
| canal_captacion | Referido | puntaje_admision | 915 | 53 | 5.7923 |
| fuente_origen | Principal | puntaje_admision | 5000 | 228 | 4.56 |

Los promedios y medianas se calcularán con los valores informados de cada grupo y mostrarán su cobertura.
No se estima el importe mediante programa y modalidad porque los datos no identifican una tarifa única.
No se reemplazan puntajes por la media ni por cero. Las diferencias de ausencia requieren prudencia al comparar grupos.

## Comprobación Oracle

Se revisaron 500 pares contra los valores finales, incluida la recuperación CRM.
La regla exploratoria exige correo, fecha de solicitud, programa, modalidad y periodo informados e iguales,
además de ausencia de contradicciones entre los demás atributos informados salvo identificadores de origen.
Cumplen 49 pares.

De los 49 candidatos previamente coincidentes en 13 atributos, 0 tienen fecha de matrícula informada en ambos.
En esos candidatos la igualdad de fecha de matrícula corresponde a un vacío compartido, no a una segunda fecha que confirme identidad.
Los códigos distintos tampoco demuestran por sí solos que sean solicitudes diferentes.

El escenario hipotético cuenta una vez los pares compatibles y contiene 5451 registros.
Frente a la entrega de 5.500 registros, el mayor cambio absoluto es 0.193 puntos porcentuales
entre las categorías de programa, modalidad, canal, estado y ciudad.
No se confirma identidad ni se reemplaza el archivo entregable. Las 500 filas Oracle permanecen disponibles.
La comparación solo principal es una vista de cobertura de fuente y no una propuesta de retirar Oracle.
El resultado de sensibilidad corresponde únicamente a los 49 pares compatibles y a las distribuciones generales.
No demuestra estabilidad de cada segmento pequeño ni resuelve los otros 451 pares con diferencias.

## Reglas de los indicadores

| indicador | registros_elegibles | registros_fuera_del_calculo | denominador | limite |
| :--- | :--- | :--- | :--- | :--- |
| Volumen por canal, modalidad y estado | 5500 | 0 | Todos los registros del grupo | Registros observados. Independencia de solicitudes entre fuentes sin confirmar |
| Distribución por programa | 5500 | 0 | Todos los registros, incluida la categoría Sin información | No asignar un programa a los 26 ausentes |
| Promedio y mediana de puntaje | 5254 | 246 | Puntajes informados dentro de cada grupo | Mostrar cobertura y no generalizar automáticamente a los ausentes |
| Promedio y mediana de importe | 4580 | 920 | Importes informados dentro de cada grupo | Importe registrado, no ingreso recaudado ni tarifa oficial |
| Serie de solicitudes con control de fecha | 5320 | 180 | Fechas de solicitud sin las alertas aplicadas | Conservar aparte los casos observados y evitar meses parciales como completos |
| Días entre solicitud y matrícula | 1035 | 4465 | Ambas fechas informadas y sin las alertas del intervalo | No representa tiempo de todos los aspirantes ni permanencia en cada estado |
| Códigos de aspirante por origen | 5410 | 90 | Códigos distintos de fuente y aspirante dentro del ámbito definido | No sumar códigos de ambos sistemas como personas globales confirmadas |

Los 5.410 registros con código contienen 3.424 códigos distintos por origen, no 5.410 personas.
Son 2.924 códigos de la principal y 500 de Oracle, cuya equivalencia entre sistemas no está confirmada.

Para explorar segmentos se usarán programa, modalidad, ciudad, canal y periodo con su volumen y cobertura.
Los segmentos pequeños se mostrarán con su cantidad para evitar interpretar porcentajes aislados.
El conjunto recoge solicitudes recibidas, no todo el mercado ni el gasto de las campañas.
No permite estimar rentabilidad de canales, causalidad o demanda no captada.

## Cierre

La base es utilizable para describir los registros integrados con los denominadores establecidos.
Se conservan los faltantes no recuperables. La imputación estadística no es necesaria para ese objetivo.
Siguen sin confirmación la identidad global entre fuentes y el historial de estados.
No se presentan tasas definitivas de conversión de personas o tiempos por etapa.
No se requiere completar artificialmente los datos para iniciar el análisis.
