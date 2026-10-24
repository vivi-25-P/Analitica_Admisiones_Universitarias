# Lectura preliminar del perfil original

Evidencia generada por `uv run analitica-admisiones perfilar`, a partir del CSV cuyo SHA-256 está registrado en `perfil_inicial.json`. Esta nota prepara el diagnóstico; no sustituye el informe final ni las visualizaciones solicitadas.

## Estructura y unicidad

- 5.040 filas y 15 columnas. No se corrigieron ni eliminaron registros.
- 5.000 valores distintos de `registro_id`: hay 40 repeticiones adicionales de ese identificador.
- 38 filas idénticas adicionales, calculadas como filas totales menos combinaciones de fila distintas.
- Los dos indicadores anteriores miden cosas distintas. No asumir que toda repetición de clave es una fila idéntica ni que un aspirante repetido sea un duplicado inválido.

## Completitud

Todos los porcentajes siguientes usan 5.040 filas como denominador.

| Campo | Vacíos exactos | % de filas | Solo espacios |
|---|---:|---:|---:|
| aspirante_id | 92 | 1,83 % | 0 |
| programa | 0 | 0,00 % | 25 |
| puntaje_admision | 179 | 3,55 % | 0 |
| valor_matricula_cop | 826 | 16,39 % | 0 |
| fecha_matricula | 2.612 | 51,83 % | 0 |
| correo | 120 | 2,38 % | 0 |

En `programa`, los 25 campos con solo espacios representan 0,50 % de las filas: no están almacenados como cadenas vacías. En una revisión visual podrían pasar inadvertidos. La ausencia de fecha de matrícula no prueba un error: se necesita revisar el estado y definir cuándo el campo aplica.

## Interpretación numérica provisional

| Campo | Valores numéricos interpretables | Vacíos exactos | Texto no interpretable como número | Mínimo–máximo | Promedio aproximado | Mediana |
|---|---:|---:|---|---|---:|---:|
| puntaje_admision | 4.811 | 179 | 50 con `Pendiente` | 40–100 | 70,06 | 70 |
| valor_matricula_cop | 4.179 | 826 | 35 con `por definir` | 1.800.000–3.500.000 COP | 2.611.605,65 COP | 2.500.000 COP |

Las estadísticas usan únicamente los valores finitos interpretables de cada campo; los textos y vacíos no se convierten a cero. No se eliminaron atípicos ni se confirmó la escala o regla institucional. El valor de matrícula registrado no demuestra pago ni ingreso efectivo.

## Consistencia y límites

Las frecuencias originales permiten revisar variantes como `Virtual`/`VIRTUAL` y `Sí`/`sí`/`SI`. Las categorías se conservan separadas; no se ha validado un catálogo de equivalencias. Consultar `frecuencias_originales.csv`, que muestra los valores también en JSON para hacer visibles espacios.

El perfil automático todavía no resuelve fechas ni calcula cobertura cronológica. Tampoco certifica exactitud frente a una fuente real, oportunidad de actualización ni coherencia de negocio entre campos. Esos controles están detallados como pendientes en `docs/plan_informe_exploratorio.md`.

Estas observaciones siguen el enfoque de Calidad de datos: perfilar, cuantificar y documentar antes de decidir tratamientos. Para redactar los cinco hallazgos finales, combinar este diagnóstico con distribuciones por programa, modalidad, canal y estado.
