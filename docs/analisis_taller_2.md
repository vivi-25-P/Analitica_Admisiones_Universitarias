# Análisis y ruta de trabajo del Taller 2

Fecha de revisión: 24 de octubre de 2026.

Estado: archivos organizados e inspección estática realizada. No se ejecutó el SQL, no se modificó PostgreSQL, no se limpiaron las fuentes y no se construyó todavía Base_unificada. Este documento interpreta el enunciado y propone una ruta; no sustituye el entregable.

## 1. Qué pide el taller

El PDF tiene tres páginas. El propósito es analizar, depurar e integrar cuatro fuentes mediante una vista de Oracle y Power Query. La base principal del taller anterior sirve de referencia, pero ahora deben justificarse las transformaciones y las relaciones entre fuentes.

La vista Oracle debe presentar nombres, significados y tipos compatibles con la base principal. Después se importan las cuatro fuentes como consultas independientes en Power Query. La limpieza y las transformaciones analíticas se realizan allí. Python puede respaldar las verificaciones, pero el procedimiento Python y PostgreSQL actual no sustituye los requisitos explícitos de Oracle y Power Query.

## 2. Organización de los archivos recibidos

| Archivo | Ubicación dentro del proyecto | Función |
| :--- | :--- | :--- |
| Taller 2do fin de semana.pdf | docs/referencias/taller_2/ | Enunciado original |
| Caso2 Programas.csv | data/raw/taller_2/ | Fuente complementaria de atributos de programas |
| Caso2 CRM Admisiones.csv | data/raw/taller_2/ | Fuente CRM con información solapada y atributos económicos |
| caso2.sql | sql/fuentes/taller_2/ | Export de estructura y datos de Oracle |

Los cuatro archivos conservan sus bytes originales. Sus hashes y tamaños están registrados en docs/referencias/taller_2/integridad.json. El SQL se guarda fuera de sql/migrations y docker/init para evitar que el sincronizador o la inicialización de PostgreSQL lo intenten ejecutar.

El archivo original de la primera actividad permanece en data/raw/Caso2_Admisiones_Universitarias.csv.

## 3. Qué contiene cada fuente

| Fuente | Tamaño observado | Aporte y cautela principal |
| :--- | :--- | :--- |
| Base principal | 5.040 filas y 15 columnas | Referencia inicial de solicitudes. Conserva duplicados, ausencias y variantes de escritura ya documentados. |
| Programas | 9 filas y 6 columnas | Incluye programa, programa_clave, facultad, duracion_semestres, nivel_formacion y modalidad. No debe asumirse como catálogo validado. |
| CRM | 100 filas y 15 columnas | Combina registro y aspirante en registro_aspirante_crm; separa matricula_base_cop y derechos_administrativos_cop. |
| Export de Oracle | Cinco tablas | Contiene 500 solicitudes, 500 aspirantes, 8 programas, 6 canales y 4 asesores. Son conteos de INSERT del archivo, no de una instancia Oracle consultada. |

Los dos CSV nuevos son legibles como UTF8 con BOM. El SQL no se interpreta como UTF8 y se leyó con cp1252, conservando correctamente sus acentos. Se debe respetar esa codificación al importarlo; no guardar sobre el archivo original con otra codificación.

## 4. Riesgos concretos encontrados

### 4.1. El catálogo de programas requiere validación antes de Merge

Las dos escrituras de Data Analytics no solo difieren en la tilde:

| Denominación original | Facultad | Duración | Nivel | Modalidad del catálogo |
| :--- | :--- | :--- | :--- | :--- |
| Especializacion en Data Analytics | Ciencias Económicas | 12 semestres | Pregrado | Virtual |
| Especialización en Data Analytics | Ingeniería | 8 semestres | Pregrado | Presencial |

Si se eliminan las diferencias de escritura para crear una llave por programa, ambas filas quedan con la misma llave y atributos distintos. Una simulación de Left Merge sobre la base principal, usando solo ese nombre normalizado y excluyendo llaves vacías, pasaría de 5.040 a 6.176 filas: 1.136 filas adicionales por multiplicación de correspondencias. La simulación es una alerta, no una integración aplicada.

También hay una fila de catálogo con un espacio en programa y programa_clave vacía. No debe utilizarse para asignar facultad, duración o nivel a las 25 solicitudes sin programa identificado.

Derecho y Psicología figuran como Posgrado y las especializaciones como Pregrado. Son atributos por contrastar con la fuente, no correcciones para realizar por intuición. Debe aclararse si la modalidad del catálogo identifica una oferta específica o si es un atributo general; no reemplazar la modalidad de la solicitud.

Decisión propuesta: verificar el grano del catálogo, su clave y los atributos en conflicto. Programa y modalidad podrían formar una llave solo si la fuente confirma esa definición y se comprueba su cobertura. No elegirla únicamente para evitar duplicados.

### 4.2. El CRM no representa automáticamente 100 solicitudes nuevas

Los 100 registro_id extraídos del CRM ya existen en la base principal. En 96 casos también coincide el aspirante y coinciden exactamente las otras 12 columnas compartidas comparadas, excluyendo los identificadores y el importe.

En cuatro filas, el aspirante dentro de la clave compuesta es el texto literal nan, mientras que en la base principal el aspirante está vacío. Estos cuatro casos requieren una regla explícita; nan no debe convertirse en un identificador real. Ejemplos: REG002324, REG000591, REG002690 y REG002248.

Dentro de los 96 pares de identificadores coincidentes, 84 valores de matricula_base_cop son textualmente iguales al valor de matrícula original y otros 12 aportan un importe donde la base original está vacía. Esto describe coincidencias; no acredita que ambos conceptos económicos sean intercambiables.

El CRM tiene tres puntajes vacíos, 53 fechas de matrícula vacías y un correo vacío. Además, conserva categorías y fechas que deben perfilarse en Power Query.

Decisión propuesta: evaluar CRM como enriquecimiento por Merge tras validar la llave y la cardinalidad de ambas fuentes. Antes de completar importes, confirmar el significado de matrícula base frente al valor original. Mantener separados matrícula base y derechos administrativos; una eventual suma requiere confirmar que corresponde al importe total solicitado. No anexar las 100 filas por defecto.

### 4.3. Oracle usa otra estructura y otros identificadores

El archivo define C2_SOLICITUDES, C2_ASPIRANTES, C2_PROGRAMAS, C2_CANALES y C2_ASESORES. Solicitudes referencia las otras cuatro tablas mediante identificadores. El script declara claves primarias y foráneas; en su contenido estático no se encontraron referencias de solicitudes sin correspondencia en esos catálogos.

Las 500 solicitudes tienen 500 registro_id distintos y ninguno coincide con los registro_id originales. Sin embargo, 490 de las 500 filas de aspirantes tienen un correo que aparece en la base principal. Este control usa espacios externos recortados y minúsculas solo como sonda de comparación, sin cambiar archivos.

Un identificador distinto no demuestra una solicitud nueva. Un correo coincidente tampoco demuestra que sea el mismo evento de solicitud. Se necesita revisar otras columnas y acordar una regla de correspondencia antes de decidir Append.

El SQL contiene tipos y cláusulas específicos de Oracle, incluidos NUMBER, VARCHAR2, TABLESPACE y almacenamiento. No es una migración de PostgreSQL. Tampoco contiene ya la vista compatible que exige el taller; construirla y probarla sigue pendiente.

Decisión propuesta: disponer de Oracle o confirmar el acceso institucional; cargar el export en un entorno destinado a esta actividad, construir una vista que una las cinco tablas y exponga las 15 columnas compatibles. Conservar sus identificadores de origen y evaluar solapamiento antes de anexar solicitudes.

## 5. Ruta de trabajo propuesta

| Paso | Trabajo | Evidencia que debe quedar |
| :--- | :--- | :--- |
| 1. Reconocer las fuentes | Importar por separado y comprobar codificación, filas, columnas, tipos, faltantes y llaves. | Inventario y perfil de cada fuente. |
| 2. Preparar Oracle | Crear y verificar la vista con solicitudes y sus cuatro tablas relacionadas. | SQL de la vista, conteos y captura del resultado. |
| 3. Acordar reglas | Revisar conflictos de catálogo, identificadores, importes y criterio de solicitud única. | Matriz de decisiones con motivo y responsable de validación. |
| 4. Depurar en Power Query | Aplicar tipos, equivalencias, tratamiento de ausencias y revisión de duplicados. | Pasos aplicados, código M y controles de errores. |
| 5. Incorporar atributos | Evaluar Merge con programas y CRM, conservando el origen de los valores. | Llaves, cardinalidad, coincidencias, ausencias y filas antes y después. |
| 6. Incorporar solicitudes | Evaluar Append desde la vista Oracle únicamente para eventos cuya incorporación esté justificada. | Comparación de solapamientos y conciliación de registros. |
| 7. Validar | Revisar cantidad de filas, identificadores, errores, faltantes, tipos y coherencia entre fuentes. | Tabla de controles y listado de excepciones. |
| 8. Entregar | Cargar el resultado como Base_unificada en Excel y ampliar el mismo informe anterior. | Excel final y documento integrado con evidencias. |

No es responsable fijar todavía el número final de filas ni asumir una suma de 5.040, 100 y 500. El conteo dependerá de duplicados confirmados, eventos realmente nuevos y decisiones de conciliación.

## 6. Cómo continuar el informe existente

Conservar el análisis descriptivo inicial y su respuesta preliminar como evidencia de la primera actividad. Añadir después un bloque de preparación e integración de fuentes con los siguientes apartados:

1. Propósito de la integración y descripción de las nuevas fuentes.
2. Diagnóstico de calidad por fuente y relación con la base principal.
3. Decisiones y reglas de depuración.
4. Construcción y validación de la vista Oracle.
5. Transformaciones realizadas en Power Query.
6. Integración mediante Merge y Append, con sus justificaciones.
7. Validación y descripción de Base_unificada.
8. Resultados actualizados frente a la primera exploración y limitaciones pendientes.

Los scripts, consultas completas, capturas y listados extensos pueden ir en anexos. No presentar como ejecutado lo que todavía sea una propuesta. El taller no establece en este PDF una nueva extensión de páginas para el documento integrado.

## 7. Entregables y evaluación

Se entregan dos archivos: el documento integrado, continuando el de la clase anterior, y un Excel con la base final llamada Base_unificada. Si alguna fuente no puede integrarse responsablemente, el enunciado permite justificarlo expresamente y proponer cómo resolverlo.

| Criterio | Puntos |
| :--- | ---: |
| Análisis y comprensión de las fuentes | 15 |
| Construcción de la vista Oracle | 15 |
| Depuración y calidad de datos | 20 |
| Integración de todas las fuentes | 25 |
| Validación de la base unificada | 15 |
| Documento del proceso y presentación del archivo | 10 |
| Total | 100 |

La existencia de una tabla final por sí sola no satisface la evaluación: debe poder explicarse y reproducirse el proceso sin pérdidas o duplicaciones injustificadas.

## 8. Respaldo de esta revisión

La inspección se reproduce desde la raíz con:

```bash
python scripts/revisar_fuentes_taller_2.py
```

Solo requiere la biblioteca estándar. Verifica los hashes de los cuatro archivos y genera reports/taller_2/revision_fuentes.json. El lector de INSERT es específico para la forma del export recibido, no un intérprete SQL general. No conecta a bases ni ejecuta sus sentencias.

El texto de las tres páginas se conserva para consulta en docs/teoria/taller_2_texto.md. El PDF original mantiene la autoridad del enunciado. Los resultados sobre Oracle son inspecciones del export; no se ha comprobado su carga ni la ejecución de la vista.
