# BaseUnificada Entregable

## Informe de preparación e integración de datos

Instituto Universitario Horizonte. Fecha de preparación: 26 de octubre de 2026.

## 1. Resultado y alcance

**La base entregada contiene 5.500 registros y 18 columnas.** Integra información principal, CRM y Oracle. Se conservan los 500 registros Oracle y se incorpora el aporte de los 100 registros CRM a sus solicitudes correspondientes. El archivo está preparado para revisión externa y análisis descriptivo de registros, con procedencia y observaciones de calidad identificadas.

Un registro es una solicitud identificada por su código de origen. La unicidad de ese código en el entregable no confirma que los sistemas describan eventos independientes. Las coincidencias Oracle permanecen visibles y no se eliminan por semejanza. Tampoco se presenta el número de códigos de aspirante por origen como una cantidad global de personas civiles únicas.

| Componente | Cantidad | Interpretación |
| :--- | ---: | :--- |
| Registros principales | 5.000 | Incluyen el enriquecimiento CRM cuando corresponde. |
| Aportes CRM incorporados | 100 | Información integrada a los registros principales, sin filas adicionales. |
| Registros Oracle | 500 | Incluidos en la tabla principal y en los gráficos integrados. |
| Total de filas entregadas | 5.500 | No sumar nuevamente los aportes CRM. |

## 2. Preparación realizada

| Operación | Resultado |
| :--- | :--- |
| Conservación del origen | Las 5.640 entradas consolidadas inicialmente mantienen un destino documentado. |
| Estandarización | Homologación de espacios, tildes, categorías, formatos y tipos. |
| Ausencias | Separación de valores desconocidos y marcadores. Los identificadores vacíos y nan se representan como ausencia real. |
| Repeticiones exactas | 38 filas adicionales consolidadas con evidencia de igualdad. |
| Registros parciales | Dos filas complementarias consolidadas; cinco valores recuperados para REG003600 y REG004804. |
| Estados | Nuevo agrupado analíticamente como Admitido; Matriculado conservado y estado recibido disponible en Control_Calidad. |
| CRM | 100 aportes incorporados mediante correspondencia por código y 12 atributos; 13 importes recuperados. |
| Oracle | 500 registros conservados; sus coincidencias y diferencias se exportan para revisión. |
| Periodos | Códigos 20252, 20261 y 20262 conservados como semestres de ingreso, sin recalcularlos desde las fechas. |
| Exportación | Excel con datos y controles, CSV, JSONL, informe y gráficos. |

La conciliación de cantidades es: 5.640 entradas, menos 38 repeticiones exactas, menos dos parciales y menos 100 aportes CRM integrados, igual a 5.500 registros. No se retiran registros por ser Oracle, tener información faltante o estar fuera de una ventana temporal orientativa.

## 3. Conceptos económicos y recuperación CRM

En los 100 cruces CRM, los códigos y 12 atributos comparados son compatibles. En 87 casos la matrícula principal coincide con la matrícula base CRM y se conserva. En 13 casos el principal está ausente y se recupera la matrícula base desde el CRM. Los derechos administrativos y el total CRM se mantienen en Control_Economico. No se suman silenciosamente al importe de matrícula.

La principal conserva 839 importes ausentes. El conjunto integrado tiene 920 ausencias de importe. No se completaron por programa, modalidad, promedio, mediana o moda. El importe reportado no acredita un pago ni una tarifa institucional oficial.

## 4. Revisión Oracle y procedencia

Los 500 registros Oracle se conservaron. 500 presentan candidatos al comparar 11 atributos excluyendo identificadores y fechas; 49 coinciden también en los dos atributos de fecha comparados. Las reglas utilizan igualdad numérica y mantienen explícitas las ausencias. Una ausencia compartida no constituye evidencia independiente de identidad.

Las sondas se documentan sobre el punto previo a recuperar importes CRM, para no perder candidatos por una recuperación posterior. Coincidencias_Oracle muestra las fechas y los importes finales disponibles. No se cambian los códigos Oracle ni se fusionan personas o solicitudes únicamente por la coincidencia de atributos.

Origen_Registros tiene una fila por registro final y distingue la fuente de origen y las fuentes asociadas. Sus filas se relacionan con BaseUnificada por registro_id y no se anexan como registros nuevos.

## 5. Fechas, periodos y oportunidad

El periodo académico representa el semestre de ingreso reportado. Una solicitud de octubre de 2025 puede corresponder al primer periodo de 2026. Una matrícula realizada antes del inicio de clases no determina por sí sola un periodo distinto. Los códigos recibidos se conservan y no se hacen coincidir automáticamente con las fechas.

Se utiliza una ventana descriptiva de octubre a enero para el primer periodo y de mayo a julio para el segundo. Esta referencia no acredita el calendario oficial. Estar fuera de esa ventana solo genera una observación; no provoca exclusión o reasignación del periodo.

Hay 456 registros cuya solicitud tiene un año posterior al periodo reportado. Se mantienen para revisión, sin inventar cuál dato debe cambiarse. Hay 32 matrículas anteriores a la solicitud. Las fechas posteriores al 26 de octubre de 2026 se identifican como posteriores a la referencia de preparación, sin afirmar que sean errores o actividades ya realizadas.

Los intervalos entre solicitud y matrícula se calculan para 1.035 registros con ambas fechas y sin las alertas definidas. El periodo académico no se exige igual al semestre de las fechas. No existe fecha de actualización de estado y no se reconstruyen transiciones ni un último estado por persona.

## 6. Identidad y prevención del doble conteo

Se registran 2.924 códigos de aspirante informados en la principal y 500 en Oracle: 3.424 identificadores por origen. La vista Aspirantes_Origen incluye ambos sistemas. Esta suma no confirma personas únicas entre sistemas, porque las correspondencias de identidad siguen siendo candidatas.

Se conservan 90 registros sin código de aspirante. No se interpretan como ese mismo número de personas ni se agrupan como una sola persona. Un código de aspirante puede tener varias solicitudes de distintos programas o periodos. La clasificación por código se basa en cualquier solicitud con matrícula, después admisión sin matrícula y finalmente otros estados; no representa el estado actual.

Para medir registros se cuenta registro_id. Para describir identificadores de aspirante se utiliza la clave de origen de Aspirantes_Origen. Los conteos de aspirantes por programa, canal o estado pueden solaparse y no deben sumarse como nuevas personas. No se presentan tasas definitivas de conversión de personas entre sistemas.

## 7. Perfil descriptivo integrado

Las siguientes frecuencias y gráficos utilizan los 5.500 registros integrados, incluidos los 500 Oracle. Describen registros, sin afirmar personas únicas o independencia confirmada de todos los eventos.

| Variable | Categoría | Registros | Porcentaje |
| :--- | :--- | ---: | ---: |
| programa | Derecho | 1.233 | 22.42 % |
| programa | Especialización en Data Analytics | 1.216 | 22.11 % |
| programa | Ingeniería de Sistemas | 630 | 11.45 % |
| programa | Contaduría Pública | 613 | 11.15 % |
| programa | Especialización en Gerencia | 605 | 11.00 % |
| programa | Psicología | 595 | 10.82 % |
| programa | Administración de Empresas | 582 | 10.58 % |
| programa | Sin información | 26 | 0.47 % |
| modalidad | Presencial | 2.192 | 39.85 % |
| modalidad | Virtual | 2.183 | 39.69 % |
| modalidad | Híbrida | 1.125 | 20.45 % |
| canal_captacion | Feria universitaria | 941 | 17.11 % |
| canal_captacion | Instagram | 939 | 17.07 % |
| canal_captacion | Correo | 926 | 16.84 % |
| canal_captacion | Referido | 915 | 16.64 % |
| canal_captacion | Web institucional | 891 | 16.20 % |
| canal_captacion | Landing page | 888 | 16.15 % |
| estado_proceso | Admitido | 1.822 | 33.13 % |
| estado_proceso | Matriculado | 1.179 | 21.44 % |
| estado_proceso | Documentación pendiente | 638 | 11.60 % |
| estado_proceso | Inscrito | 630 | 11.45 % |
| estado_proceso | No admitido | 617 | 11.22 % |
| estado_proceso | Retirado | 614 | 11.16 % |

| Variable numérica | Informados | Ausentes | Mínimo | Máximo | Promedio | Mediana |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| puntaje_admision | 5.254 | 246 | 40.0 | 100.0 | 70.07 | 70.0 |
| valor_matricula_cop | 4.580 | 920 | 1800000.00 | 3500000.00 | 2612532.75 | 2500000.00 |
| duracion_semestres | 5.474 | 26 | 2 | 10 | 6.66 | 8 |

Los importes de la tabla se expresan en COP y los puntajes en su unidad reportada. La presencia de concentraciones por programa, ciudad o canal identifica patrones del registro disponible. No demuestra causalidad comercial, capacidad de oferta o rentabilidad. Para evaluar oportunidad de mercado se debe mantener esta distinción.

## 8. Observaciones que acompañan la revisión

| Observación | Registros |
| :--- | ---: |
| programa ausente | 26 |
| aspirante id ausente | 90 |
| puntaje ausente | 246 |
| importe ausente | 920 |
| fecha matricula ausente | 4.321 |
| fecha solicitud ambigua | 165 |
| fecha matricula ambigua | 64 |
| matricula anterior a solicitud | 32 |
| solicitud posterior al anio periodo | 456 |
| solicitud posterior referencia | 15 |
| matricula posterior referencia | 13 |
| matriculado documentos no completos | 514 |
| documentacion pendiente con documentos si | 393 |

Las observaciones pueden superponerse en una misma fila y no deben sumarse como solicitudes diferentes. Una ausencia puede ser pertinente para un estado y limitar otro indicador; la falta de fecha de matrícula en una solicitud no matriculada no se declara automáticamente error.

## 9. Estado de cierre y condiciones de uso

La preparación técnica y la conciliación CRM están completadas. Pasaron 23 controles finales, con lectura completa de Excel, CSV y JSONL y conservación de fuentes. El archivo puede entregarse para revisión y utilizarse en análisis descriptivo de registros con su procedencia y sus alertas.

Para afirmar cantidades globales de personas únicas o conversiones entre sistemas sería necesario validar las correspondencias de identidad. Para presentar tarifas, ingresos cobrados o un calendario institucional oficial se requeriría una validación de esos conceptos. Estas limitaciones no provocan la eliminación de registros ni impiden revisar el conjunto integrado.

El criterio Nuevo a Admitido y el catálogo de programas son decisiones analíticas documentadas. Su eventual ajuste deberá conservar los valores recibidos y repetir los controles. La versión entregada no presupone que todas las observaciones de negocio estén resueltas o que la información refleje sin error cada hecho real.

## 10. Contenido del paquete

BaseUnificada_Entregable.xlsx contiene BaseUnificada, Diccionario_Datos, Origen_Registros, Control_Calidad, Resumen_Calidad, Aspirantes_Origen, Coincidencias_Oracle, Control_Economico, Registros_Sin_ID y Metodologia. Las hojas auxiliares se relacionan con la principal y no se suman como nuevos registros.

Se incluyen CSV y JSONL del conjunto, controles CSV, tablas descriptivas, seis gráficos y este informe. Los metadatos contienen versión, cantidades, formatos y huellas de integridad de los archivos. El conjunto no contiene consultas dependientes de rutas locales ni conexiones a bases de datos.
