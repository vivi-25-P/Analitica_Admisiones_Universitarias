# PostgreSQL para la exploración inicial

La preparación conserva las 15 columnas como TEXT y las 5.040 filas originales, incluidos los duplicados. No se agrega clave primaria ni se eliminan espacios, cambian categorías o convierten fechas/números. Los campos vacíos se guardan como cadenas vacías, no NULL, mediante FORCE_NOT_NULL. El CSV se monta en modo de solo lectura.

## Iniciar y verificar

Requisitos: Docker Engine disponible y Docker Compose v2. En Docker Desktop habilita la integración con tu distribución WSL.

Desde esta carpeta ejecuta:

```sh
uv run python iniciar_bd.py
```

El script descarga la imagen si hace falta, inicia PostgreSQL y verifica las columnas y todas las filas contra el CSV, contando también los duplicados. Comprueba además que el CSV conserva su SHA-256. PostgreSQL no garantiza el orden de las filas: la comparación respeta los valores y su cantidad, independientemente del orden.

## Conexión

- Servidor: localhost
- Puerto: 5433 (configurable en .env)
- Base de datos: admisiones
- Usuario: analista
- Contraseña: valor de POSTGRES_PASSWORD en el archivo local .env
- Tabla: public.admisiones_original

La contraseña se generó para esta instalación. No compartas ni subas .env a repositorios. El puerto se publica únicamente en la interfaz local.

## Consultas iniciales

```sh
docker compose exec postgres psql -U analista -d admisiones
```

```sql
SELECT COUNT(*) AS filas FROM public.admisiones_original;

SELECT programa, COUNT(*) AS solicitudes
FROM public.admisiones_original
GROUP BY programa
ORDER BY solicitudes DESC;

SELECT COUNT(*) AS puntajes_vacios
FROM public.admisiones_original
WHERE puntaje_admision = '';
```

## Persistencia

`docker compose stop` detiene la base sin borrar los datos. `uv run python iniciar_bd.py` vuelve a iniciarla y verifica su contenido. La importación automática solo ocurre al inicializar un volumen vacío; reiniciar no vuelve a insertar las filas. No elimines el volumen admisiones_data si quieres conservar la base. Cambiar las credenciales en .env después de inicializar no cambia la contraseña ya guardada en PostgreSQL.

Esta tabla es la copia original para explorar. Ejecuta consultas SELECT y realiza las transformaciones posteriores en otra tabla para conservar esta referencia.


## Estado verificado el 17 de octubre de 2026

PostgreSQL se inició mediante Docker Desktop para Windows. Se exportó la tabla y se compararon sus encabezados y todas sus filas contra el CSV, incluyendo la cantidad de repeticiones de cada fila. Resultado: 5.040 filas y 15 columnas idénticas. El hash del archivo original permanece intacto. Las consultas de `sql/exploracion/01_perfil_original.sql` se ejecutaron correctamente en una transacción de solo lectura.

La integración con Ubuntu ya está activa y el cliente de WSL se conecta al motor. El usuario `noovou` ya pertenece al grupo `docker`; las sesiones abiertas antes de esa asignación pueden mostrar `permission denied`. Ejecuta `newgrp docker` en esa terminal para actualizar sus grupos. Desde esta sesión se comprobó la conexión con `sg docker`, sin modificar permisos del socket.

Para administrar desde PowerShell de Windows, con Docker disponible en su PATH:

```powershell
cd C:\Users\jdlos\Desktop\analitica_admisiones_universitaria
docker compose ps
docker compose exec postgres psql -U analista -d admisiones
```

## Respaldo local y siguientes cambios

Ejecuta `python3 scripts/respaldar_bd.py` desde la raíz para generar un respaldo en data/backups. El script verifica cabecera e índice. La restauración completa de prueba sigue pendiente. Consulta [el plan de preparación](plan_preparacion_base.md) y [la bitácora](../BITACORA.md). La tabla original se conserva como referencia; todavía no se ha aplicado una migración para crear la segunda tabla.

## Actualización: tipos sin limpieza

La nueva tabla `public.admisiones_tipadas` ya está creada y cargada con 5.040 filas. La descripción anterior de una segunda tabla pendiente queda reemplazada por [la estructura tipada implementada](estructura_tipado_sin_limpieza.md). Cada valor original sigue disponible y la limpieza no se ha aplicado. La carga usa una migración explícita sobre el volumen existente.

## Sincronización de versiones compartidas

La entrada recomendada para una instalación nueva o una actualización es `python scripts/sincronizar_bd.py`, después de instalar las dependencias con uv o pip. Se registra cada versión SQL en public.migraciones_proyecto y se verifican las tablas de origen. La [guía compartida](trabajo_compartido.md) contiene los comandos de instalación y actualización. No basta con agregar nuevos archivos a docker/init sobre un volumen ya existente.
