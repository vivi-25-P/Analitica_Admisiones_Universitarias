# Reporte descriptivo y comparativo de las fuentes del Taller 2

Fecha: 24 de octubre de 2026.

## 1. Resultado general

La vista CASO2.V_ADMISIONES_BASE contiene 15 columnas y 500 registros. Las columnas tienen el mismo significado general y el mismo orden que las 15 columnas de negocio de la base inicial. Por estructura, puede prepararse para su integración en Power Query. Sin embargo, la compatibilidad de estructura no demuestra que sus registros sean nuevos ni autoriza a anexarlos directamente.

Las tres fuentes nuevas cumplen funciones diferentes. Programas aporta atributos de la oferta académica, pero presenta un conflicto de catálogo. CRM aporta información económica para solicitudes que ya existen en la base principal. Oracle presenta solicitudes con identificadores propios, aunque existe un solapamiento importante de sus atributos con la base inicial y diferencias temporales que requieren validación.

La recomendación es evaluar Programas y CRM como enriquecimientos mediante Merge. La incorporación de Oracle mediante Append queda condicionada a determinar si sus filas corresponden a eventos nuevos, versiones de solicitudes existentes u otra situación administrativa. Ninguna de estas operaciones se ha aplicado en esta revisión.

## 2. Alcance y evidencia

Se consultaron mediante SELECT los datos y metadatos de la vista Oracle. Para la base principal se utilizó el CSV original de 5.040 filas, cuyo hash continúa coincidiendo con el registrado. PostgreSQL estaba detenido al revisar su estado; no se presenta esta comparación como una consulta nueva a sus tablas. La equivalencia histórica del CSV con admisiones_original está documentada en las verificaciones previas.

Los CSV y el SQL originales se mantuvieron intactos. Para buscar correspondencias se construyeron sondas en memoria: espacios externos recortados, categorías en mayúsculas sin tildes, correo en minúsculas, equivalencias explícitas de periodos y representación de fechas y números. Las fechas se interpretaron mediante las convenciones del proyecto, incluidas las barras para día, mes y año y los guiones con año al final para mes, día y año. Las convenciones ambiguas requieren confirmación institucional.

Estas sondas no son una limpieza aplicada ni una regla definitiva de identidad. En las comparaciones tipadas, vacíos, fechas No aplica y números no interpretables pueden compartir ausencia de representación; sus significados originales siguen disponibles en las fuentes. Por ello, una coincidencia tipada debe revisarse antes de consolidar registros.

Todos los porcentajes descriptivos usan el total de filas de su propia fuente. Las estadísticas numéricas excluyen valores no interpretables, sin sustituirlos por cero. Los promedios no representan personas únicas ni pagos confirmados.

## 3. Compatibilidad de las columnas

| Columna de negocio | Naturaleza esperada | Base original PostgreSQL | Proyección tipada PostgreSQL | Vista Oracle |
| :--- | :--- | :--- | :--- | :--- |
| registro_id | Identificador de registro | TEXT | TEXT | VARCHAR2 |
| aspirante_id | Identificador de aspirante | TEXT | TEXT | VARCHAR2 |
| fecha_solicitud | Fecha de solicitud | TEXT | DATE | DATE |
| programa | Programa solicitado | TEXT | TEXT | VARCHAR2 |
| modalidad | Modalidad de la solicitud | TEXT | TEXT | VARCHAR2 |
| canal_captacion | Canal registrado | TEXT | TEXT | VARCHAR2 |
| estado_proceso | Situación de admisión | TEXT | TEXT | VARCHAR2 |
| puntaje_admision | Puntaje numérico | TEXT | NUMERIC | NUMBER |
| documentos_completos | Condición documental | TEXT | TEXT | VARCHAR2 |
| valor_matricula_cop | Importe registrado en COP | TEXT | NUMERIC | NUMBER |
| ciudad_residencia | Ciudad registrada | TEXT | TEXT | VARCHAR2 |
| asesor | Asesor asignado | TEXT | TEXT | VARCHAR2 |
| fecha_matricula | Fecha consignada de matrícula | TEXT | DATE | DATE |
| correo | Correo de contacto | TEXT | TEXT | VARCHAR2 |
| periodo_academico | Periodo asociado | TEXT | TEXT | VARCHAR2 |

La tabla admisiones_original tiene 15 columnas. Admisiones_tipadas tiene 19: las mismas 15 de negocio y cuatro técnicas, fila_origen_csv, origen_sha256, datos_originales y observaciones_tipado. La vista no necesita incorporar esas cuatro columnas para ser compatible con la fuente inicial. La trazabilidad de una integración posterior deberá contemplar cada origen por separado.

En Oracle los encabezados se muestran en mayúsculas porque los alias se crearon sin comillas. Power Query puede ajustar sus nombres a minúsculas. Los tipos DATE y NUMBER tienen correspondencias con fecha y número en Power Query; el CSV inicial necesita interpretación de tipos. Que una columna sea DATE no demuestra que su fecha sea exacta.

La vista fue creada para el ejercicio y no venía incluida en el export recibido. Une C2_SOLICITUDES con las tablas de aspirantes, programas, canales y asesores. No incorpora las otras fuentes ni depura categorías.

## 4. Inventario de las fuentes

| Fuente | Filas | Columnas | Qué representa cada fila | Aporte |
| :--- | ---: | ---: | :--- | :--- |
| Base inicial | 5.040 | 15 | Registro recibido de solicitud | Referencia del análisis anterior |
| Programas | 9 | 6 | Fila de catálogo, pendiente de validar su grano | Facultad, duración, nivel y modalidad de oferta |
| CRM | 100 | 15 | Registro CRM asociado a una solicitud | Matrícula base y derechos administrativos |
| Vista Oracle | 500 | 15 | Solicitud expuesta por la fuente Oracle | Otra representación de solicitudes y sus atributos |

No deben sumarse las cuatro cantidades. Las nueve filas de Programas no representan solicitudes y el CRM se solapa con la base principal. Tampoco está confirmado que las 500 filas Oracle sean solicitudes adicionales.

## 5. Descripción de la base inicial

El archivo contiene 5.040 filas, 5.000 registro_id distintos y 2.924 aspirante_id distintos no vacíos. Hay 92 filas sin aspirante_id. Estos resultados no acreditan un número definitivo de personas o solicitudes únicas.

Se identifican 38 repeticiones exactas adicionales y dos pares con el mismo registro_id y una discrepancia. Hay 25 programas con un espacio como único contenido, 120 correos vacíos y variantes de escritura en programas, modalidades, estados, documentación, ciudades, asesores y periodos.

Las solicitudes abarcan del 1 de enero de 2025 al 12 de septiembre de 2026. Las 5.040 fechas se interpretan con las reglas actuales, aunque hay cinco formatos. Existen 410 solicitudes de 2026 asociadas al segundo periodo de 2025, pendientes de validación institucional.

| Variable numérica | Valores numéricos | Mínimo | Máximo | Promedio | Mediana |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Puntaje | 4.811 | 40 | 100 | 70,06 | 70 |
| Matrícula en COP | 4.179 | 1.800.000 | 3.500.000 | 2.611.605,65 | 2.500.000 |

En puntaje hay 179 vacíos y 50 Pendiente. En matrícula hay 826 vacíos y 35 por definir. No se encontraron negativos ni atípicos con el criterio de 1,5 veces el rango intercuartílico. Esta comprobación no sustituye la escala de admisión ni las tarifas oficiales.

Los seis canales tienen participaciones entre 16,19 % y 17,08 %. Feria universitaria registra 861 filas e Instagram 859. La distribución por programas, modalidades y estados está fragmentada por diferencias de escritura, como se documentó en el primer informe.

## 6. Fuente complementaria: Programas

### 6.1. Descripción

Contiene 9 filas y las columnas programa, programa_clave, facultad, duracion_semestres, nivel_formacion y modalidad. Hay ocho nombres no vacíos y una fila cuyo programa es un espacio y cuya programa_clave está vacía. Al considerar equivalencias de escritura aparecen siete nombres de programa no vacíos, pero esa equivalencia no resuelve sus atributos.

| Atributo del catálogo | Distribución observada |
| :--- | :--- |
| Facultad | Ciencias Sociales: 3; Ciencias Económicas: 2; Ingeniería: 2; Educación: 2 |
| Modalidad | Presencial: 5; Virtual: 4 |
| Nivel de formación | Pregrado: 6; Posgrado: 3 |
| Duración | Entre 8 y 12 semestres; mediana de 10 y promedio de 9,78 |

Estas frecuencias describen filas de catálogo, incluida la fila sin programa identificado. No representan demanda por facultad ni duración efectiva de los estudios.

### 6.2. Problemas de calidad

Las dos denominaciones de Data Analytics presentan atributos distintos:

| Denominación | Facultad | Semestres | Nivel | Modalidad |
| :--- | :--- | ---: | :--- | :--- |
| Especializacion en Data Analytics | Ciencias Económicas | 12 | Pregrado | Virtual |
| Especialización en Data Analytics | Ingeniería | 8 | Pregrado | Presencial |

El catálogo también clasifica Derecho y Psicología como Posgrado, y las especializaciones como Pregrado. Estos son contenidos por verificar con la fuente; no se cambiaron con base en el nombre del programa. Tampoco se asume que las facultades y duraciones observadas sean correctas.

### 6.3. Relación con la base principal

Se simularon tres formas de Left Merge, excluyendo programas vacíos como llaves válidas:

| Sonda de relación | Filas principales con correspondencia | Sin correspondencia | Filas resultantes simuladas |
| :--- | ---: | ---: | ---: |
| Programa en mayúsculas, conservando tildes | 5.015 | 25 | 5.040 |
| Programa en mayúsculas, sin tildes | 5.015 | 25 | 6.176 |
| Programa sin tildes y modalidad | 2.403 | 2.637 | 5.040 |

La segunda sonda encuentra dos filas de catálogo para 1.136 solicitudes de Data Analytics y genera esa misma cantidad de filas adicionales. La tercera evita multiplicación, pero solo cubre el 47,68 % de las filas principales; no demuestra que la llave sea correcta. El catálogo solo declara determinadas modalidades y la base contiene otras combinaciones.

La primera sonda mantiene el número de filas, pero conserva la separación entre las variantes de Data Analytics y les atribuye características diferentes. Un conteo estable no garantiza una integración semánticamente válida.

Decisión recomendada: confirmar si el catálogo representa programas u ofertas por programa y modalidad, resolver sus atributos contradictorios y excluir las llaves vacías de la combinación. Después realizar un Merge con cardinalidad controlada. No anexar estas filas como solicitudes.

## 7. Fuente CRM

### 7.1. Estructura y distribución

El CRM contiene 100 filas y 15 columnas. Comparte 12 columnas con el esquema principal. Reúne registro_id y aspirante_id en registro_aspirante_crm y sustituye la columna económica original por matricula_base_cop y derechos_administrativos_cop. Por tanto, tener también 15 columnas no significa que su estructura sea directamente equivalente.

| Aspecto | Distribución original |
| :--- | :--- |
| Programas | Especializacion en Data Analytics: 14; Contaduría Pública: 14; Psicología: 13; Ingeniería de Sistemas: 13; Especialización en Data Analytics: 11; Derecho: 9; Especialización en Gerencia: 9; Administración de Empresas: 9; DERECHO: 8 |
| Modalidades | Presencial: 25; presencial: 17; VIRTUAL: 21; Virtual: 19; Híbrida: 18 |
| Canales | Web institucional: 22; Landing page: 20; Instagram: 17; Feria universitaria: 16; Correo: 13; Referido: 12 |
| Estados | No admitido: 16; Admitido: 15; Retirado: 14; Documentación pendiente: 12; matriculado: 11; Matriculado: 10; Nuevo: 9; Inscrito: 9; ADMITIDO: 4 |
| Documentación | Sí: 22; SI: 21; sí: 21; Pendiente: 19; No: 17 |

Con 100 filas, cada cantidad de la tabla equivale al mismo porcentaje dentro de esta fuente. Para describir conjuntamente las variantes, 42 filas corresponden a las etiquetas presenciales, 40 a las virtuales y 18 a Híbrida. Las dos escrituras de Matriculado suman 21. Estas sumas son lecturas exploratorias, no cambios aplicados.

Las fechas de solicitud van del 9 de enero de 2025 al 11 de septiembre de 2026. Hay 21 fechas interpretables de matrícula, 53 vacíos y 26 No aplica. El correo está vacío en una fila. El puntaje tiene tres vacíos y un Pendiente. Cuatro claves compuestas contienen el texto nan como aspirante. No se detectan filas completamente idénticas.

| Variable | Valores numéricos | Mínimo | Máximo | Promedio | Mediana |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Puntaje | 96 | 40 | 100 | 69,95 | 71 |
| Matrícula base en COP | 100 | 1.800.000 | 3.500.000 | 2.537.000 | 2.500.000 |
| Derechos administrativos en COP | 100 | 55.220 | 307.591 | 158.490,88 | 152.929 |

No aparecen negativos ni atípicos mediante el criterio aplicado. Siete registros con etiquetas de matrícula tienen documentos No o Pendiente. Diez solicitudes de 2026 están asociadas al segundo periodo de 2025. Se mantienen como condiciones por verificar.

### 7.2. Relación con la base principal

| Comprobación | Resultado |
| :--- | ---: |
| Códigos de solicitud CRM presentes en la principal | 100 de 100 |
| Códigos de solicitud nuevos por registro_id | 0 |
| Coincidencia del par registro y aspirante sin interpretar nan | 96 |
| Coincidencia de las otras 12 columnas compartidas por registro_id | 100 |
| Importe principal numéricamente igual a matrícula base CRM | 87 |
| Importe principal vacío con matrícula base disponible en CRM | 13 |
| Filas de la principal que reciben correspondencia CRM | 101 |

El último resultado se debe a que REG002361 aparece dos veces en la principal y una vez en CRM. El CRM tiene 100 códigos distintos: un Left Merge por registro_id conservaría las 5.040 filas principales y enriquecería 101 de ellas. No solucionaría sus duplicados.

En los cuatro casos con nan, la principal tiene aspirante vacío. No se interpreta ese texto como una identidad real. El conteo económico 87 y 13 se calcula sobre las 100 correspondencias por registro_id; amplía la revisión inicial de 96 pares completos, donde se observaron 84 coincidencias y 12 importes ausentes. Son universos distintos.

Ejemplo: REG001725 tiene importe vacío en la principal; CRM registra matrícula base de 2.200.000 COP y derechos administrativos de 78.059 COP. Es un candidato a enriquecimiento, pero no se deben trasladar ni sumar los importes hasta confirmar qué representa cada concepto y cuál fuente tiene autoridad.

Decisión recomendada: separar la clave compuesta, documentar los cuatro nan y evaluar un Merge por registro_id con controles de identidad. Mantener los conceptos económicos separados y su fuente. No hacer Append del CRM como si aportara 100 solicitudes adicionales.

## 8. Fuente Oracle

### 8.1. Estructura y calidad

La vista contiene 500 filas, 500 registro_id distintos y 500 aspirante_id distintos. Los identificadores utilizan otro espacio de códigos respecto de la principal. No existen duplicados exactos dentro de la vista.

Sin embargo, hay 463 correos distintos no vacíos y 10 filas con correo nulo. Que existan 500 aspirante_id no acredita que existan 500 personas distintas. Los identificadores deben interpretarse dentro del sistema de origen.

| Condición | Cantidad | Porcentaje sobre Oracle |
| :--- | ---: | ---: |
| Puntaje nulo | 18 | 3,60 % |
| Valor de matrícula nulo | 81 | 16,20 % |
| Fecha de matrícula nula | 400 | 80,00 % |
| Correo nulo | 10 | 2,00 % |
| Programa Sin especificar | 2 | 0,40 % |

Oracle tiene categorías más uniformes en su escritura. Esto facilita agruparlas, pero no demuestra que se haya realizado una limpieza correcta ni permite conocer por qué cada dato terminó nulo. La vista no conserva una columna equivalente al JSON de valores originales de nuestra tabla tipada.

### 8.2. Distribución descriptiva

| Programa | Cantidad | Porcentaje |
| :--- | ---: | ---: |
| Derecho | 120 | 24,00 % |
| Especialización en Data Analytics | 89 | 17,80 % |
| Administración de Empresas | 62 | 12,40 % |
| Ingeniería de Sistemas | 61 | 12,20 % |
| Contaduría Pública | 59 | 11,80 % |
| Especialización en Gerencia | 56 | 11,20 % |
| Psicología | 51 | 10,20 % |
| Sin especificar | 2 | 0,40 % |

| Modalidad | Cantidad | Porcentaje |
| :--- | ---: | ---: |
| Presencial | 212 | 42,40 % |
| Virtual | 202 | 40,40 % |
| Híbrida | 86 | 17,20 % |

| Canal | Cantidad | Porcentaje |
| :--- | ---: | ---: |
| Referido | 90 | 18,00 % |
| Correo | 88 | 17,60 % |
| Feria universitaria | 86 | 17,20 % |
| Instagram | 86 | 17,20 % |
| Web institucional | 84 | 16,80 % |
| Landing page | 66 | 13,20 % |

| Estado | Cantidad | Porcentaje |
| :--- | ---: | ---: |
| Admitido | 106 | 21,20 % |
| Matriculado | 100 | 20,00 % |
| Documentación pendiente | 68 | 13,60 % |
| No admitido | 67 | 13,40 % |
| Inscrito | 58 | 11,60 % |
| Nuevo | 51 | 10,20 % |
| Retirado | 50 | 10,00 % |

La documentación figura como Sí en 284 filas, Pendiente en 108 y No en 108. Hay 52 matriculados con documentos No o Pendiente, equivalentes al 52 % de los 100 matriculados de esta fuente. Esta combinación requiere confirmar si se permiten matrículas condicionadas.

Los periodos se distribuyen en 2026-1 con 226 filas, 2026-2 con 174 y 2025-2 con 100. Hay 50 solicitudes de 2026 asociadas al segundo periodo de 2025. Las ciudades más frecuentes son Cali con 117, Bogotá con 116 y Popayán con 109. Asesor 1 reúne 198 registros; Sin asignar aparece en 99.

| Variable | Valores numéricos | Mínimo | Máximo | Promedio | Mediana |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Puntaje | 482 | 40 | 100 | 70,24 | 70 |
| Matrícula en COP | 419 | 1.800.000 | 3.500.000 | 2.637.708,83 | 2.500.000 |

No se detectan negativos ni atípicos con el criterio de 1,5 veces el rango intercuartílico. Los promedios son cercanos a los de la principal, pero esa similitud no demuestra que las fuentes sean independientes o representativas de la misma población.

### 8.3. Fechas y correspondencias con la principal

Las fechas de solicitud Oracle van del 2 de enero de 2025 al 10 de diciembre de 2026, mientras que las de la principal terminan el 12 de septiembre de 2026. Hay 15 solicitudes posteriores al 24 de octubre de 2026. Esta referencia es la fecha de revisión, no un corte institucional validado; no se clasifican como errores automáticamente.

Las 100 fechas de matrícula van del 6 de enero de 2025 al 11 de diciembre de 2026. Los DATE del servidor se consultaron con formato explícito de año, mes y día, de modo que la presentación regional de DBeaver no explica por sí sola las diferencias observadas.

| Sonda de comparación | Filas Oracle con alguna coincidencia en la principal |
| :--- | ---: |
| Mismo registro_id | 0 |
| Correo no vacío normalizado | 490 |
| Correo y fecha de solicitud | 61 |
| Correo, fecha de solicitud, programa, modalidad y periodo | 60 |
| Trece columnas comparables, excluyendo los dos identificadores | 49 |
| Once columnas comparables, excluyendo identificadores y ambas fechas | 498 |

Las sondas compuestas exigen llaves no vacías. En las sondas de 11 y 13 atributos se permite comparar ausencias tipadas, con la limitación explicada al inicio. Las 498 coincidencias no presentan más de un registro_id principal candidato por fila, aunque puede repetirse una fila con el mismo identificador. Las dos filas restantes tienen programa Sin especificar.

Dentro de esas 498 correspondencias exploratorias, 60 conservan la fecha de solicitud y 399 conservan la fecha de matrícula, incluyendo ausencias. La cifra 399 no significa 399 matrículas con fecha confirmada. Solo 49 filas coinciden en ambas fechas y en los demás atributos comparados.

Se identificaron 16 correspondencias exploratorias cuya fecha de solicitud es compatible con un intercambio entre día y mes. No explican todas las diferencias. Ejemplos:

| Candidato en la principal | Fecha original | Interpretación actual | Registro Oracle | Fecha Oracle |
| :--- | :--- | :--- | :--- | :--- |
| REG003093 | 04-10-2025 | 10 de abril de 2025 | ANX2_00041 | 4 de octubre de 2025 |
| REG001364 | 2025/02/12 | 12 de febrero de 2025 | ANX2_00275 | 2 de diciembre de 2025 |
| REG004068 | 2025-10-19 | 19 de octubre de 2025 | ANX2_00001 | 19 de noviembre de 2025 |

El último ejemplo muestra una diferencia que no corresponde a intercambiar día y mes. Estos pares son candidatos seleccionados por otros atributos, no equivalencias de solicitud confirmadas. Puede haber actualizaciones, nuevas solicitudes similares, problemas de interpretación de fechas u otras transformaciones en origen. Los datos disponibles no permiten elegir una explicación definitiva.

Usar solo correo también es insuficiente: 332 filas Oracle encuentran más de un registro_id distinto en la principal. Las 10 filas sin coincidencia por correo tienen ese dato nulo; no acreditan diez personas nuevas. Una sonda de correo, fecha, programa, modalidad y periodo también encuentra una fila Oracle coincidente con CRM, que a su vez ya corresponde a la principal.

Decisión recomendada: revisar la procedencia de Oracle y las reglas de sus fechas e identificadores antes de anexar. Las 440 filas sin coincidencia por la sonda de evento no son automáticamente nuevas, porque cambiar una fecha puede impedir el reconocimiento de una solicitud existente. Tampoco se deben eliminar las 498 por similitud de atributos.

## 9. Estrategia de integración propuesta

| Fuente | Relación candidata | Operación a evaluar | Condición previa |
| :--- | :--- | :--- | :--- |
| Programas | Atributos de programa u oferta | Merge | Confirmar grano, llave, modalidades y atributos contradictorios |
| CRM | Solicitudes ya presentes por registro_id | Merge | Separar identificadores, revisar nan, validar autoridad y conceptos económicos |
| Oracle | Solicitudes con códigos propios y alto solapamiento de atributos | Append o conciliación, según el resultado | Resolver identidad de evento, discrepancias temporales y precedencia de fuentes |

La base inicial se conserva como referencia. Las cuatro consultas se mantienen separadas en Power Query durante el perfilamiento. Antes de integrar se documentan los catálogos, la política de duplicados, el significado de una solicitud única y las condiciones para completar o reemplazar un dato.

En las combinaciones, debe comprobarse que la llave derecha sea única con el significado acordado. En las anexiones, debe existir una definición común de evento y de columnas. Conviene conservar en el resultado o en un control asociado la fuente, el identificador de origen y la decisión de conciliación. Para Excel pueden utilizarse nombres de encabezado homogéneos y tipos consistentes, conservando separadas las observaciones de calidad.

Después de cada operación se verifican filas iniciales y finales, coincidencias, exclusiones, duplicados, faltantes y errores. No se fija todavía un número esperado final de solicitudes. El objetivo de Base_unificada será reunir información justificada, no alcanzar la suma de archivos.

## 10. Decisiones que deben resolverse primero

1. Confirmar si dos versiones de Data Analytics representan el mismo programa o distintas ofertas y cuál es su información válida.
2. Confirmar qué representa modalidad en el catálogo y si debe formar parte de su llave.
3. Definir cómo tratar los cuatro nan del CRM sin crear identidades ficticias.
4. Confirmar si valor_matricula_cop equivale a matrícula base, total u otro concepto, y cuándo pueden incorporarse los 13 importes disponibles en CRM.
5. Establecer qué representan los identificadores ANX2 y si las fechas Oracle son fechas nuevas, actualizadas o transformadas.
6. Definir una solicitud única y una política de precedencia para datos diferentes entre fuentes.
7. Confirmar el corte temporal y las reglas de periodo, documentación y matrícula.

## 11. Entregables de esta revisión

El respaldo está en reports/taller_2/comparacion:

| Archivo | Contenido |
| :--- | :--- |
| analisis_completo.json | Perfiles, metadatos, metodología y resultados de correspondencia |
| frecuencias_por_fuente.csv | Frecuencias y porcentajes de las categorías originales |
| calidad_por_fuente.csv | Vacíos, nulos, espacios y valores distintos por columna |
| estadisticas_numericas.csv | Mínimo, máximo, promedio, mediana y controles numéricos |
| relacion_crm_principal.csv | Detalle de los 100 registros CRM frente a la principal |
| cobertura_catalogo_programas.csv | Correspondencias candidatas del catálogo |
| relacion_oracle_principal.csv | Sondas y candidatos para las 500 filas Oracle |
| fechas_oracle_candidatos_revision.csv | Fechas originales e interpretadas de los candidatos Oracle |

La lectura de Oracle se conserva en reports/taller_2/oracle_vista_lectura.json. Se puede actualizar con python scripts/capturar_vista_oracle.py si Docker está activo y el usuario tiene acceso a su motor. La captura solo ejecuta consultas y requiere las credenciales locales existentes. Después se reproduce el análisis con python scripts/analizar_relaciones_taller_2.py. Los scripts verifican las fuentes y no aplican la integración.

El notebook anterior continúa respaldando la primera exploración. Esta revisión nueva se respalda mediante los scripts y archivos de esta sección; todavía no se incorporó al notebook anterior ni se ejecutó en Power Query.
