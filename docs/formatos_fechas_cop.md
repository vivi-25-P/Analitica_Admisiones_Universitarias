# Fechas y valores monetarios de L04

## Fechas

La representación de intercambio es AAAA-MM-DD, por ejemplo 2026-10-24. En memoria se utilizan objetos date y Excel contiene fechas reales con formato yyyy-mm-dd. Los textos de origen y la convención aplicada se conservan en la auditoría de conversiones.

Se aplican las cinco reglas documentadas: año primero con guiones o barras, día primero con barras y año al final, mes primero con guiones y año al final, y día con abreviatura inglesa del mes. No se utiliza la detección automática de pandas ni la configuración regional del equipo para adivinar el orden. Las abreviaturas se interpretan con un catálogo explícito independiente del idioma del sistema.

Una fecha como 04/10/2025 se representa como 2025-10-04 según la regla de barras, pero queda señalada porque admite dos lecturas si no se confirma la convención. La interpretación no demuestra exactitud institucional. No se intercambian fechas para aumentar coincidencias entre fuentes.

## Valores en pesos colombianos

La moneda es COP. En Python se utiliza Decimal con dos decimales exactos para el importe; no se calcula mediante float ni se redondean fracciones de centavo sin una decisión. Un valor informado 2200000.1 se representa exactamente como 2200000.10. Un dato 1.001 requiere revisión por su precisión y no se redondea a 1.00.

| Medio | Representación |
| :--- | :--- |
| Tabla de lectura del notebook | COP 2.200.000,00 |
| Excel | Valor numérico con formato monetario y dos decimales, identificado como COP |
| CSV | 2200000.00, con punto decimal, sin símbolo y sin separadores de miles |
| JSONL | Literal decimal 2200000.00; leer con Decimal para preservar exactitud |

En Excel los separadores visibles dependen de la configuración regional, aunque el dato siga siendo el mismo número. El formato no cambia su valor. Microsoft explica la relación entre formatos y presentación en [Format Cells](https://learn.microsoft.com/en-us/troubleshoot/microsoft-365-apps/excel/format-cells-settings) y el uso de [separadores regionales](https://learn.microsoft.com/en-us/troubleshoot/microsoft-365-apps/excel/formula-errors).

El CSV mantiene coma como delimitador y punto decimal para facilitar el intercambio del proyecto. En Excel se importa desde Datos, Desde texto o CSV; si se requiere, se indica una configuración de lectura compatible con punto decimal y se trata periodo_academico como entero. No se incluyen COP ni separadores de miles dentro del dato porque dificultarían su conversión numérica. No se sobrescriben fuentes desde Excel al cambiar separadores.

La entrada actual ya tiene números con punto decimal y sin separadores de miles. Un texto como 2.200.000,00 en esa entrada no se convierte por suposición: se registra como excepción hasta definir una regla para su procedencia.

## Periodo, puntaje y duración

El periodo se representa como entero identificador: 20252, 20261 y 20262. No se presenta como fecha ni se suma como medida. La duración es un entero exacto; no se truncan fracciones. El puntaje utiliza Decimal, con validación de valores informados sin imponer una escala institucional todavía no confirmada.

## Ausencias y validaciones

Las 5.866 ausencias de L03 conservan sus motivos en la auditoría. Los identificadores, incluidos sus vacíos y nan, siguen como llegaron. No se eliminan filas ni se completan valores por cero o promedios.

L04 registra formatos de día y mes ambiguos, fechas posteriores a la referencia de revisión, matrícula anterior a solicitud, periodos dispares y matrícula con documentación no completa. Estas alertas no son errores confirmados ni autorizan correcciones o exclusiones automáticas.

COP identifica la unidad monetaria, pero no acredita equivalencia entre matrícula base, total CRM e importes de otras fuentes, ni prueba un pago. Esa conciliación continúa pendiente.

El estado actual y las rutas de datos y controles están en reports/limpieza/ultima_tipificacion.json. El notebook conserva la explicación y los resultados de las etapas previas.
