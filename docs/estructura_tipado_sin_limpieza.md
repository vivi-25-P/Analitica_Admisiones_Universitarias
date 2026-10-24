# Estructura de tipos sin limpieza

## Alcance acordado

La limpieza corresponde a la actividad siguiente. En esta etapa solo se habilita una representación técnica de fechas y números, manteniendo cada fila y cada valor recibido. No se eliminan duplicados, recortan espacios, homologan categorías, rellenan ausencias ni corrigen discrepancias.

## Tablas actuales

| Tabla | Uso |
|---|---|
| public.admisiones_original | Las 5.040 filas y 15 columnas TEXT del archivo original. No se modifica. |
| public.admisiones_tipadas | Las mismas 5.040 filas con representación DATE y NUMERIC cuando es posible. Cada fila conserva también los 15 valores originales completos. |

En admisiones_tipadas las dos fechas usan DATE; puntaje_admision y valor_matricula_cop usan NUMERIC sin una precisión que obligue a redondear. Identificadores, categorías, documentación, correo y periodo siguen siendo TEXT. No se impone un catálogo, rango académico o unicidad de solicitud pendiente de validación.

## Por qué se conservan representaciones paralelas

Un número no puede almacenar literalmente Pendiente, y una fecha no puede almacenar No aplica. El valor tipado se presenta como NULL cuando no existe una representación válida, pero su contenido se conserva en datos_originales y su motivo se registra en observaciones_tipado. Esto permite distinguir vacío, No aplica, Pendiente y por definir durante la actividad de limpieza. No equivale a resolver ni descartar esos casos.

La columna datos_originales es JSONB y contiene los nombres y valores TEXT de las 15 columnas de origen, incluidos espacios y cadenas vacías. Su orden de claves no es significativo; cada valor y cada fila se verifican por reconstrucción contra el CSV. La sintaxis y codificación originales del archivo permanecen además en data/raw.

fila_origen_csv identifica la posición lógica del registro en el CSV, contando el encabezado como 1. No representa una solicitud única. origen_sha256 permite identificar el archivo exacto. Estos controles técnicos no cambian los identificadores institucionales.

## Fechas: convenciones de representación

Se usan los cinco patrones documentados en el notebook: año mes día con guiones o barras; día mes año con barras; mes día año con guiones y año al final; día y mes abreviado en inglés con año al final. Las convenciones deben verificarse con la fuente si su significado es ambiguo. El texto original siempre se conserva y no se corrigen fechas.

## Carga y validación

La migración está en sql/migrations/001_admisiones_tipadas.sql. El script scripts/preparar_tipos.py verifica el hash y la igualdad del CSV con la tabla original antes de cargar. Usa una transacción, conserva todas las filas y evita añadirlas de nuevo en ejecuciones repetidas. Si la tabla existente difiere de la representación esperada, la operación falla en vez de sobrescribirla.

```bash
uv run --group notebooks python scripts/preparar_tipos.py
```

No ejecutarlo sobre datos ya limpiados esperando que los reemplace. La limpieza posterior debe tener su propio procedimiento documentado.

## Consultas de ejemplo

```sql
SELECT registro_id, programa, puntaje_admision,
       datos_originales ->> 'puntaje_admision' AS puntaje_original,
       observaciones_tipado
FROM public.admisiones_tipadas
WHERE puntaje_admision IS NULL;

SELECT registro_id, fecha_matricula,
       datos_originales ->> 'fecha_matricula' AS fecha_matricula_original
FROM public.admisiones_tipadas
WHERE fecha_matricula IS NULL;
```

## Verificaciones realizadas

Se conservaron 5.040 filas en cada tabla. Los 15 valores originales se reconstruyeron por posición y coincidieron con el CSV. La comparación de multiplicidades comprobó que admisiones_original sigue representando el mismo origen. Se representaron 5.040 fechas de solicitud, 1.085 fechas de matrícula, 4.811 puntajes y 4.179 importes. Las categorías y los espacios no se normalizaron.

El respaldo previo a esta estructura está en data/backups/admisiones_20261017_134557_186521.dump. El detalle reproducible se guarda en reports/estructura/verificacion_tipado.json.
