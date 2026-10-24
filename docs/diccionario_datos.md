# Diccionario inicial de datos

Significados inferidos a partir de los nombres, valores observados y guía del caso; requieren validación con el docente o responsable. No sustituyen un diccionario institucional.

Las 15 columnas se almacenan como TEXT para preservar los valores del CSV. El tipo analítico esperado no se impone durante la carga. El CSV utiliza coma y es legible como UTF-8; el lector admite BOM.

| Columna | Significado provisional | Tipo analítico esperado | Control inicial |
|---|---|---|---|
| `registro_id` | Identificador del registro | Identificador | Repeticiones de clave y duplicados de fila; no imponer unicidad todavía. |
| `aspirante_id` | Identificador del aspirante | Identificador | Vacíos y repetición entre solicitudes; no asumir que repetición equivale a error. |
| `fecha_solicitud` | Fecha registrada de la solicitud | Fecha | Inventariar formatos, fechas imposibles y ambigüedades antes de convertir. |
| `programa` | Programa académico solicitado | Categórica | Vacíos, mayúsculas, acentos y catálogo institucional. |
| `modalidad` | Modalidad del programa o solicitud | Categórica | Variantes de escritura y catálogo. |
| `canal_captacion` | Canal registrado de captación | Categórica | Frecuencias y relación con estado; falta validar atribución. |
| `estado_proceso` | Estado registrado del proceso de admisión | Categórica | Variantes y reglas de coherencia con documentación/matrícula. |
| `puntaje_admision` | Puntaje registrado de admisión | Numérica | Vacíos, interpretación y valores inusuales; escala institucional pendiente. |
| `documentos_completos` | Indicador o estado de documentación | Categórica | Conservar Sí/sí/SI/No/Pendiente; no convertir todavía a booleano. |
| `valor_matricula_cop` | Valor de matrícula expresado en pesos colombianos | Numérica monetaria | Vacíos y texto por definir; no asumir recaudo ni ingreso realizado. |
| `ciudad_residencia` | Ciudad registrada de residencia | Categórica | Espacios, acentos y mayúsculas; catálogo pendiente. |
| `asesor` | Asesor registrado o estado de asignación | Categórica | Variantes y Sin asignar; no equivale necesariamente a vacío. |
| `fecha_matricula` | Fecha registrada de matrícula | Fecha | Distinguir vacío y No aplica; revisar formatos y coherencia temporal. |
| `correo` | Correo electrónico registrado | Texto de contacto | Vacíos y estructura; no prueba identidad ni entregabilidad. |
| `periodo_academico` | Periodo académico registrado | Categórica temporal | Variantes de notación y coherencia con calendario institucional. |

## Unidad de análisis y faltantes

Una fila es un registro de origen. Su equivalencia con una solicitud única se debe verificar; tampoco equivale automáticamente a un aspirante único. No hay clave primaria ni restricciones que impidan cargar las repeticiones.

Un campo vacío se conserva como cadena vacía (`''`) en PostgreSQL mediante `FORCE_NOT_NULL`. Las cadenas `No aplica`, `por definir` y `Sin asignar` permanecen como texto. No se transforman automáticamente a NULL, cero o falso.

Al usar pandas, leer con `dtype=str, keep_default_na=False, na_filter=False` para evitar conversiones implícitas. No aplicar `.strip()`, normalización de categorías o eliminación de duplicados a la referencia original.

## Pendientes de validación

Clave de solicitud, obligatoriedad de campos, rango de puntajes, catálogos oficiales, formatos de fecha, significado de matrícula efectiva y calendario académico. La exactitud frente al hecho real y la oportunidad requieren fuentes o metadatos adicionales.
