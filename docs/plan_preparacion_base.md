# Plan inicial de preparación de PostgreSQL

Actualización del 17 de octubre de 2026: este documento conserva la propuesta inicial. El usuario reservó la limpieza para otra actividad. La estructura ejecutada es `admisiones_tipadas`, descrita en [tipado sin limpieza](estructura_tipado_sin_limpieza.md); no se creó `admisiones_preparadas`. Las propuestas de tratamiento de este plan no se han aplicado.

## Situación de partida

PostgreSQL 17 funciona en Docker Desktop y dispone de un volumen persistente. La tabla public.admisiones_original conserva las 5.040 filas y las 15 columnas de texto que respaldan la primera exploración. El CSV se monta en modo de solo lectura y el servicio se publica en localhost:5433.

El trabajo siguiente consiste en preparar los datos dentro del PostgreSQL existente. No requiere instalar otro motor ni eliminar el contenedor o el volumen.

## Organización propuesta

| Componente | Función | Situación |
|---|---|---|
| public.admisiones_original | Referencia fiel del archivo recibido | Existente, verificada |
| public.admisiones_preparadas | Datos con tipos interpretables y reglas documentadas | Propuesta, todavía no creada |
| Registro de excepciones | Conservar motivos y valores que no puedan convertirse | Diseño pendiente |
| SQL de migraciones | Cambios de estructura versionados y aplicables al volumen existente | Pendiente |
| Bitácora | Decisiones, evidencia, validaciones y cambios aplicados | BITACORA.md |

## Tipos a revisar

Los identificadores y las categorías pueden seguir siendo TEXT. Las fechas interpretables usarán DATE y los puntajes e importes, NUMERIC con una precisión acordada. No se añadirá una escala obligatoria de puntajes ni una tarifa fija sin validación institucional.

Documentación debe conservar al menos Sí, No y Pendiente; no debe convertirse directamente a booleano. El periodo académico seguirá siendo una categoría con una denominación validada.

La nueva estructura necesita un identificador técnico y una referencia reproducible al archivo y su posición de origen. No debe utilizar registro_id como clave primaria ni depender del orden de filas devuelto por PostgreSQL.

## Reglas del proceso

El primer paso conservará todas las filas. Las conversiones se realizarán en la segunda tabla y sus excepciones se registrarán con el valor original y el motivo. Vacío, Pendiente, No aplica y por definir no se tratarán como situaciones equivalentes.

Las equivalencias de escritura del Anexo A son propuestas. Su aplicación debe tener una regla identificada. Las fechas con varias convenciones requieren patrones explícitos y un registro de ambigüedades.

Las 38 parejas exactas y los dos pares con discrepancias se tratarán en una decisión separada. No se eliminarán registros como consecuencia implícita de convertir tipos.

## Cambios sobre una base ya inicializada

Los archivos de docker/init solo se ejecutan al inicializar un volumen vacío. Editarlos no actualiza la base actual. Los cambios posteriores deberán realizarse mediante scripts de migración explícitos, con comprobaciones previas y dentro de transacciones cuando corresponda.

## Respaldo y verificación

Ejecutar desde la raíz con Docker disponible:

```bash
python3 scripts/respaldar_bd.py
```

El script genera un archivo de formato personalizado y sus metadatos en data/backups. Verifica cabecera e índice mediante pg_restore. No elimina datos ni restaura sobre la base activa. La lectura del índice no sustituye una restauración completa de prueba.

Cada etapa deberá terminar con conteos de filas, comparación de valores, resumen de excepciones y una entrada en BITACORA.md. Los respaldos permanecen locales y se excluyen de Git.
