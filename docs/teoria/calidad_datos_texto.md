# Texto de apoyo: Calidad de datos

Extracción del texto editable y notas. Las imágenes no se transcriben automáticamente; consulta la presentación original.

## Diapositiva 1

(Sin texto editable; consultar el original.)

## Diapositiva 2

INTELIGENCIA DE NEGOCIOS Especialización en Data  Analytics  para Marketing Digital

## Diapositiva 3

Calidad y limpieza de datos Propósito Identificar los fundamentos para convertir datos confiables en información útil para decidir.

## Diapositiva 4

TÍTULO ¿Por qué la calidad de los datos importa? Un análisis puede estar bien calculado y aun así conducir a una decisión equivocada si los datos de entrada son incompletos, incorrectos o inconsistentes. Una campaña puede parecer rentable si se duplican las conversiones. Una región puede parecer menos productiva si faltan ventas en su registro. Un indicador puede cambiar solo porque se modificó la forma de registrar los datos. Dato Representación registrada de un hecho, evento o entidad. Información Datos organizados e interpretados en un contexto. Decisión Acción elegida a partir de la información y los objetivos.

Notas: 4

## Diapositiva 5

TÍTULO Calidad de datos: concepto La calidad de los datos es el grado en que los datos son adecuados para el uso previsto y representan de forma confiable aquello que se necesita analizar. Depende del propósito Un dato puede ser suficiente para un informe general, pero insuficiente para una decisión operativa detallada. Se evalúa con evidencia No basta con afirmar que una base “se ve bien”: se revisan reglas, patrones, registros y excepciones. Es responsabilidad continua La calidad se debe controlar al capturar, integrar, transformar, almacenar y usar los datos. Calidad  de datos  no significa  que los datos sean perfectos, sino que sean confiables para la pregunta que se quiere responder.

Notas: 5

## Diapositiva 6

Seis dimensiones frecuentes de la calidad Exactitud ¿El valor  refleja  la  realidad ? Ejemplo :  Edad   registrada : 250  años . Completitud ¿ Están   presentes  los  datos   necesarios ? Ejemplo :  Pedidos  sin  fecha  o sin valor. Consistencia ¿Los  datos   concuerdan  entre  fuentes  o  reglas ? Ejemplo : Una  venta   figura   como   pagada  y  pendiente . Validez ¿ Cumple   el   formato  y las  reglas   definidas ? Ejemplo :  Correo  sin  estructura   válida . Unicidad ¿ Cada   entidad   aparece  una sola  vez   cuando   corresponde ? Ejemplo : El  mismo   cliente   aparece   duplicado . Oportunidad ¿ Está  disponible  cuando  se  necesita ? Ejemplo :  Reporte  de  ventas   entregado  con  semanas  de  retraso . Las  dimensiones  se  complementan : un  registro   puede  ser  completo ,  pero   incorrecto ;  válido   en   formato ,  pero   desactualizado .

Notas: 6

## Diapositiva 7

Cómo se manifiestan los problemas de calidad Campo Valor observado Posible   problema Qué   comprobar Fecha  de c o mpra 31/02/2026 Validez ¿La fecha existe en el calendario? Correo ana@ Validez ¿Cumple la regla de formato definida? ID cliente C104 repetido Unicidad ¿Es duplicado real o son compras distintas? Ventas -250.000 Exactitud / regla ¿Es devolución, ajuste o error? Ciudad Popayán / Popayan Consistencia ¿Son variantes equivalentes según el catálogo? Edad Vacío Completitud ¿Es  obligatorio  para  el   análisis ? Un valor inusual no demuestra por sí solo que exista un error: requiere contexto y verificación.

Notas: 7

## Diapositiva 8

TÍTULO Perfilamiento: conocer antes de limpiar El perfilamiento de datos es una revisión inicial de la estructura, contenido y patrones de una base para entender qué contiene y detectar posibles riesgos. Estructura Número de filas y columnas; nombres y tipos de campos; claves y relaciones. Contenido Valores mínimos y máximos; categorías; frecuencias; campos vacíos; formatos. Patrones Duplicados; categorías inesperadas; distribuciones extrañas; contradicciones entre campos. Ejemplo : antes de  analizar  la  conversión  por canal,  comprobar   cuántos   registros  hay,  si   cada   conversión   tiene  un  identificador  y  si  los  canales   están   escritos  de forma  uniforme .

Notas: 8

## Diapositiva 9

TÍTULO Datos faltantes: no todos significan lo mismo Un dato faltante ocurre cuando un campo no tiene un valor registrado. Su significado depende de por qué falta y de cómo se usará el campo. No aplica El campo no  corresponde  a ese  registro .  Ej .:  fecha  de  envío   en  una  compra  que no  requiere   envío . No se conoce El valor  existe   en  la  realidad ,  pero  no  fue   capturado  o no  está  disponible. Se perdió El  dato   pudo   existir ,  pero  se  omitió   durante  una  transferencia  o  integración . Opciones  de  tratamiento •   Investigar  y  recuperar   el  valor;  mantenerlo   como   faltante ;  marcar  “no  aplica ”; o  imputar  solo  si  hay  justificación   metodológica . No  reemplaces   automáticamente   todos  los  vacíos  por cero: cero es un valor real y  puede   alterar   promedios ,  totales  y  decisiones .

Notas: 9

## Diapositiva 10

TÍTULO Duplicados: identificar qué se está repitiendo Un duplicado aparece cuando dos o más filas representan la misma entidad o evento, según la regla de unicidad definida. La clave es establecer qué debe ser único. Duplicado exacto Todas  las  columnas   coinciden .  Puede   deberse  a una carga  repetida . Duplicado parcial Coinciden   campos  clave,  pero   otros   difieren .  Requiere   investigar   cuál   registro  es  válido . Repetición legítima Un  cliente   puede   realizar   varias   compras .  Repetir   su  ID no es  necesariamente  un error. Ejemplo  de  negocio :  contar   filas   como   si   fueran   pedidos   puede   inflar  las  ventas   cuando  un  pedido   aparece   repetido . Antes de  eliminar , define la  entidad  y la clave.

Notas: 10

## Diapositiva 11

TÍTULO Tipos de datos, formatos y estandarización La limpieza exige distinguir el valor almacenado de su tipo y su significado. Un campo numérico puede representar una cantidad, un código o una categoría. Tipo incorrecto La  fecha  '17/10/2026' se  almacena   como   texto  y no  puede   ordenarse   cronológicamente  con seguridad. Formato inconsistente ' Popayán ', 'POPAYAN' y 'Popayan '  pueden   fragmentar  una  agrupación  por ciudad. Unidad inconsistente Unas   ventas   están   en  pesos y  otras   en  miles de pesos;  sumarlas   directamente  produce un  resultado   incorrecto . Estandarizar   significa   aplicar  una  representación   común  sin  cambiar   el   significado :  normalizar   espacios  y  mayúsculas ,  unificar   catálogos  y  convertir   tipos  con  reglas   verificables .

Notas: 11

## Diapositiva 12

TÍTULO Valores atípicos: investigar antes de corregir Un valor atípico es una observación que se distancia de manera notable del patrón general. Puede ser un error, un evento excepcional o una señal importante del negocio. Procedimiento: detectar → contrastar con reglas y fuente → consultar contexto → documentar decisión. No elimines un valor solo porque es grande o pequeño. Posible error Una  venta  de $900.000.000  cuando   el   sistema   registra   ventas   habituales  de miles de pesos. Evento legítimo Una  compra   corporativa   extraordinaria  que  supera   ampliamente   el   promedio . Señal de negocio Un  pico  de  pedidos   durante  una  campaña   promocional   exitosa .

Notas: 12

## Diapositiva 13

Limpieza y transformación: relacionadas, pero distintas Ejemplo: corregir una fecha imposible es limpieza; convertir una fecha válida a tipo fecha para calcular meses es transformación. En la práctica, ambas pueden ocurrir en el mismo flujo ETL. Limpieza de datos Busca corregir o tratar problemas de calidad: • Duplicados confirmados • Valores inválidos o mal formados • Inconsistencias • Faltantes según reglas definidas Transformación  de  datos Adapta los datos a una estructura útil para análisis: • Cambiar tipos de datos • Crear columnas derivadas • Unificar tablas y campos • Agrupar o resumir información

Notas: 13

## Diapositiva 14

Proceso recomendado para limpiar datos 1 Comprender Definir   objetivo ,  unidad  de  análisis  y  reglas . 2 Perfilar Revisar estructura, tipos, rangos y patrones. 3 Detectar Identificar problemas potenciales y cuantificarlos. 4 Decidir Establecer reglas de tratamiento y justificar excepciones. 5 Aplicar Corregir, estandarizar, deduplicar o conservar según evidencia. 6 Validar Comparar antes y después; comprobar que no se alteró el sentido. 7 Documentar Registrar cambios, criterios, responsables y limitaciones. La  limpieza  no es  borrar   todo  lo  extraño : es  aplicar   reglas   explícitas  y  conservar   trazabilidad .

Notas: 14

## Diapositiva 15

Cómo la mala calidad distorsiona los indicadores Problema Efecto sobre el cálculo Riesgo de decisión Pedidos duplicados Sobrestima número de pedidos e ingresos Atribuir   éxito  a una  campaña  que no lo  tuvo Canal vacío Subestima o distorsiona resultados por canal Redistribuir mal el presupuesto publicitario Monedas/unidades mezcladas Total de ventas incorrecto Comparar   productos  o  periodos  de forma  errónea Fechas inconsistentes Ventas asignadas al periodo equivocado Tomar decisiones con tendencias falsas Clientes repetidos Sobreestima clientes únicos Calcular  mal  adquisición  y  retención Un  indicador   confiable   requiere  una  definición   clara ,  datos   adecuados  y un  cálculo  reproducible.

Notas: 15

## Diapositiva 16

Reglas, trazabilidad y responsabilidad Reglas de calidad Ej.: el identificador del pedido es obligatorio; el valor de venta no puede ser negativo salvo que represente una devolución documentada. Trazabilidad Registrar qué se cambió, por qué, cuándo y mediante qué regla. Conservar la base original cuando sea posible. Responsabilidad La herramienta puede automatizar controles, pero el área de negocio debe validar significados y excepciones. Una práctica profesional distingue entre dato original, dato transformado y decisión tomada. Esto permite explicar resultados, repetir procesos y auditar cambios.

Notas: 16

## Diapositiva 17

Conclusiones finales •  La  calidad  se  evalúa   según   el   uso   previsto , no por  apariencia . •  Un  dato   faltante , un  duplicado  o un valor  extremo   necesita   interpretación  contextual. •   Perfilar   permite   conocer  la base antes de  modificarla . •   Limpiar  y  transformar  son  actividades   relacionadas ,  pero  no  idénticas . •   Cada   tratamiento  debe  tener  una  regla ,  evidencia  y  justificación . •  La  validación  final debe  comprobar  que los  cambios   mejoraron  la  calidad  sin  distorsionar   el   significado .

Notas: 17

## Diapositiva 18

(Sin texto editable; consultar el original.)
