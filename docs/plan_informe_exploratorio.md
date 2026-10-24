# Plan del primer informe exploratorio

## Objetivo y alcance

Describir el conjunto de admisiones e identificar riesgos de calidad usando las seis dimensiones de la clase. Conservar el CSV y `public.admisiones_original` sin correcciones, conversiones permanentes ni eliminación de registros. El informe es descriptivo; no certifica exactitud frente a una fuente real.

## Secuencia de trabajo

1. **Reconocer el conjunto:** 5.040 filas, 15 columnas; revisar diccionario y significado de registro, solicitud y aspirante. Inventariar periodos y formatos de fecha antes de determinar cobertura temporal.
2. **Perfilar sin limpiar:** ejecutar `uv run analitica-admisiones perfilar`. Revisar vacíos exactos y campos con solo espacios, filas idénticas adicionales, repetición de identificadores, categorías originales y resumen numérico con denominadores.
3. **Completar diagnóstico:** inventariar formatos de fechas y ambigüedades; probar coherencia entre campos solo con interpretaciones documentadas. Contrastar posibles errores con reglas institucionales. Separar dimensiones evaluadas, parcialmente evaluadas y no evaluables.
4. **Explorar distribuciones:** cantidades y porcentajes por programa, modalidad, canal y estado. Los porcentajes iniciales usan todas las filas, con vacíos visibles. Las variantes se mantienen separadas y se advierte su efecto.
5. **Comunicar:** escoger cinco hallazgos que combinen descripción del negocio y calidad, mostrar al menos tres tablas/gráficos, indicar evidencia y limitaciones, y formular tres preguntas posteriores a la limpieza.

## Propuesta de visualizaciones

| Salida | Pregunta | Denominador y precaución |
|---|---|---|
| Barras por programa | ¿Dónde se concentra el volumen registrado? | 5.040 filas; incluir vacíos y variantes originales |
| Tabla de modalidad y estado | ¿Cómo se distribuyen los estados entre modalidades? | Conteos; si se usan porcentajes, indicar si son del total o dentro de modalidad |
| Tabla o barras de canal y estado | ¿Qué estados aparecen por canal? | Conteos de registros; no presentar como tasa definitiva de conversión |
| Tabla de calidad por campo | ¿Qué ausencias pueden limitar el análisis? | Vacíos/5.040; no equiparar ausencia con error confirmado |

La guía pide como mínimo tres tablas o gráficos, no necesariamente tres gráficos. Los títulos deben indicar que se trata de registros originales sin depurar.

## Estructura sugerida: 2–4 páginas más anexos

- **Página 1:** contexto, objetivo, unidad provisional de análisis, estructura y cobertura temporal con límites.
- **Página 2:** diagnóstico de calidad, evidencia y posibles efectos sobre indicadores.
- **Página 3:** visualizaciones y explicación de los cinco hallazgos; ajustar el espacio si se usan cuatro páginas.
- **Cierre:** límites, tres preguntas futuras y breve respuesta a la discusión de la guía.
- **Anexos:** tablas completas, consultas, resumen numérico, formatos observados y matriz de controles.

## Matriz mínima de controles a completar

| ID | Dimensión | Control propuesto | Estado inicial |
|---|---|---|---|
| C01 | Completitud | Vacíos exactos y espacios por columna | Automatizado en perfil |
| C02 | Unicidad | Duplicados de fila y repeticiones de registro_id | Automatizado; no elimina |
| C03 | Consistencia | Frecuencias de categorías originales | Automatizado; equivalencias pendientes |
| C04 | Validez | Interpretación numérica y valores rechazados | Automatizado; rangos de negocio pendientes |
| C05 | Validez | Fechas, formatos ambiguos y estructura del correo | Pendiente de implementación y reglas |
| C06 | Consistencia | Estado frente a documentación, fechas y periodo | Pendiente de interpretación y reglas |
| C07 | Exactitud | Comparar posibles anomalías con la fuente | Requiere evidencia externa |
| C08 | Oportunidad | Evaluar actualidad y demora de registro | Requiere metadatos de actualización |

Registrar para cada control: regla, fuente teórica, campo, conteo, denominador, ejemplos, impacto posible, decisión propuesta y evidencia pendiente. El perfil automático no sustituye esta matriz ni completa por sí solo el informe.

## Tres preguntas sugeridas para la siguiente etapa

1. Una vez confirmadas las claves y repeticiones, ¿cuántas solicitudes y cuántos aspirantes únicos existen por periodo?
2. Tras validar categorías y estados, ¿qué proporción de las solicitudes llega a matrícula por canal y modalidad, con qué denominador y dentro de qué ventana temporal?
3. Después de validar fechas y documentación, ¿cómo se relaciona la documentación completa con el tiempo entre solicitud y matrícula, sin atribuir causalidad?

## Criterios de entrega

- Cinco hallazgos, cada uno con cifra, referencia a evidencia, interpretación y límite.
- Al menos tres tablas o gráficos con títulos, etiquetas, unidades y pregunta explícita.
- Diagnóstico de calidad y dimensiones que no se pueden evaluar.
- Tres preguntas posteriores a la limpieza.
- Archivo/capturas de visualizaciones y método reproducible.
- CSV original intacto y tabla original sin modificaciones.
