# Texto extraído del Taller 2

Extracción de las tres páginas del PDF para consulta. El PDF original es la referencia.

PÁGINA 1
Análisis de múltiples fuentes de datos con Oracle y Power
Query
Propósito del taller
Analizar, preparar, depurar e integrar información proveniente de diferentes fuentes, utilizando una
vista de Oracle y herramientas de Power Query, para construir una base unificada consistente y
lista para su análisis.
Contexto del caso
Con el pasar de los días, la empresa consultora ha encontrado nuevas fuentes de datos que
complementan la información analizada inicialmente. El equipo debe reconocer qué aporta cada
fuente, revisar su calidad, determinar cómo se relaciona con las demás y realizar la integración de
forma justificada, evitando duplicidades y conservando la trazabilidad de las transformaciones.
Fuentes disponibles
• 1. Base principal: Archivo u tilizado y explorado durante la sesión anterior. Sirve como
referencia para identificar la estructura y el significado de los datos iniciales.
• 2. Fuente complementaria: Archivo o tabla que incorpora atributos adicionales relacionados
con registros existent es. Se debe evaluar su llave de relación y definir si corresponde
combinarla mediante Merge.
• 3. CRM: Fuente procedente del sistema de gestión de relaciones con clientes. Se debe
establecer si aporta registros nuevos, atributos adicionales o información que  se solapa con
las fuentes existentes. Append solo aplica si son registros del mismo tipo y la estructura es
compatible.
• 4. Oracle: Información disponible en Oracle. Se debe construir una vista SQL con las
columnas requeridas y una estructura compatible co n la base principal. La vista se importa a
Power Query como una consulta independiente y se integra según el resultado del análisis.
Organización del equipo
Cada integrante explora una fuente y registra sus características, calidad, campos relevantes,
posibles llaves y problemas encontrados. En equipos de tres integrantes, una persona puede
asumir la fuente de Oracle y la complementaria. En equipos de cuatro, se puede asignar una fuente
a cada integrante. Antes de integrar, el equipo debe compartir los hallazgos y acordar la estrategia
de unificación.
Instrucciones de trabajo
1. Construyan en Oracle una vista SQL que seleccione los campos necesarios y presente una
estructura compatible con la base principal. Verifiquen los nombres, significados y tipos de
datos.
2. Importen las cuatro fuentes a Power Query como consultas separadas.

PÁGINA 2
3. Exploren cada fuente: columnas, tipos de datos, cantidad de filas, valores vacíos, errores,
frecuencias y posibles llaves.
4. Depuren las fuentes según los problemas identificados. Justifiq uen las transformaciones y
eviten eliminar información sin sustento.
5. Determinen cómo se relacionan las fuentes antes de integrarlas. Utilicen Merge para
incorporar atributos mediante una llave común y Append únicamente cuando se agreguen
registros del mismo tipo con estructuras compatibles.
6. Integren todas las fuentes disponibles, revisen duplicados y validen que las operaciones no
hayan multiplicado o eliminado registros de manera injustificada.
7. Documenten las decisiones, transformaciones y validaciones realizadas.
8. Al final deben tener una sola base de datos que deben llamar Base_unificada
Criterios para integrar correctamente
• Merge se utiliza para incorporar columnas o atributos de otra fuente a partir de una llave
común. Antes de aplicarlo, verificar que la llave tenga el mismo significado y que su
cardinalidad no multiplique registros inesperadamente.
• Append se utiliza para agregar filas de fuentes que representan el mismo tipo de entidad o
evento y tienen campos equivalentes. Revisar solapamientos y duplicados antes de anexar.
• La fuente complementaria normalmente se evalúa para M erge, pero la decisión depende de
su estructura real.
• La información de CRM no debe anexarse automáticamente: primero se debe establecer si
contiene nuevos registros o si complementa registros ya existentes.
• La vista de Oracle debe exponer los campos reque ridos con nombres y tipos compatibles. La
limpieza y las transformaciones analíticas se realizan en Power Query.
• No eliminar registros ni valores sin una justificación. Las reglas de depuración deben ser
coherentes con el contexto de los datos y quedar documentadas.
• Después de cada operación, verificar el número de filas, la unicidad de las llaves cuando
corresponda, los valores nulos, los errores y la consistencia de los campos.
Producto entregable
Cada equipo debe entregar dos archivos:
• Documento integrado  (mismo de la clase anterior ) del proceso realizado, que explique las
fuentes utilizadas, el análisis de calidad, las decisiones de depuración, las transformaciones
aplicadas, las operaciones de integración y las validaciones realizadas. Debe incluir evidencia
suficiente para comprender y reproducir el proceso.

• Archivo Excel con la base unificada final  (Base_unificada), que integre todas las fuentes
disponibles y esté depurada, con nombres de campos claros, tipos de datos consistentes,
duplicados revisados y resultados vali dados. Si alguna fuente no puede integrarse de forma
responsable por falta de una llave, incompatibilidad o riesgo de duplicación, el equipo debe
justificarlo explícitamente y proponer cómo resolverlo.
Criterios de evaluación
Puntaje total: 100 puntos.

PÁGINA 3
Criterio Desempeño esperado Puntos
Análisis y comprensión de
las fuentes
Identifica el origen, estructura, significado, aporte y
limitaciones de cada fuente.
15
Construcción de la vista
Oracle
La vista consulta los campos necesarios y presenta
nombres, sign ificados y tipos compatibles con el
esquema esperado.
15
Depuración y calidad de
datos
Trata valores nulos, errores, formatos, tipos y
duplicados con reglas justificadas; evita eliminar
información sin sustento.
20
Integración de todas las
fuentes
Aplica correctamente Merge y/o Append según la
naturaleza de los datos; controla llaves, relaciones,
duplicidades y cobertura.
25
Validación de la base
unificada
Comprueba cantidades de registros, consistencia de
columnas, llaves, duplicados, nulos y coherencia entre
fuentes.
15
Documento del proceso y
presentación del archivo
Documenta decisiones y transformaciones de forma
clara; entrega un Excel organizado y reproducible.
10

Nota de evaluación: no se calificará únicamente que exista una base final . Se evaluará que la
integración sea técnicamente correcta, que las decisiones de depuración estén justificadas y que
el resultado no pierda información ni introduzca duplicados por errores de relación.

