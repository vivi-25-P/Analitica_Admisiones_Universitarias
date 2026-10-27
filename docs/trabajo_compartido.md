# Trabajo compartido con Git, Docker y Python

## Qué se sincroniza

Git distribuye el CSV original, las versiones SQL, los scripts y las dependencias. Cada computador mantiene su propio PostgreSQL y volumen de datos. Un pull descarga los cambios; el comando de sincronización los aplica a la base local. No se copian volúmenes de Docker entre computadores.

La configuración utiliza rutas relativas. La base se levanta con PostgreSQL 17 y el CSV recibido. Se conserva la tabla original y se reproduce la proyección tipada. .gitattributes evita convertir los finales de línea del CSV y fija LF para scripts y migraciones, manteniendo los hashes entre plataformas.

## Primera instalación con uv

Instalar Git, Docker con Compose y uv. Clonar el repositorio y entrar en su carpeta. Mantener Docker en ejecución.

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group notebooks --group excel python scripts/sincronizar_bd.py
```

Si .env no existe, el sincronizador lo crea con una contraseña aleatoria local. Si se copió .env.example manualmente, reemplazar la contraseña de ejemplo antes de ejecutar. No se cambia ni se imprime una contraseña ya existente.

El primer arranque crea admisiones_original; el sincronizador verifica sus 5.040 filas, prepara admisiones_tipadas y registra las migraciones. Cada equipo puede tener una contraseña diferente y obtener los mismos datos.

## Primera instalación con pip

Usar Python 3.12. Desde la carpeta del repositorio, en Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirement.pip
python scripts/sincronizar_bd.py
```

En Windows, activar con `.venv\Scripts\Activate.ps1` desde PowerShell. También funciona `python -m pip install -r requirements.txt`; este archivo remite a requirement.pip. La exportación incluye las herramientas de notebooks y se genera desde uv.lock, sin rutas de esta máquina ni la .venv de origen.

Los comandos directos de scripts y notebooks funcionan sin instalar el proyecto como paquete. Para usar además el comando analitica-admisiones en un entorno pip, instalar el proyecto con `python -m pip install -e .`.

## Actualizaciones con uv

```bash
git pull --ff-only
uv sync --locked --group notebooks --group excel
uv run --locked --group notebooks --group excel python scripts/sincronizar_bd.py
```

## Actualizaciones con pip

Con el entorno virtual activado:

```bash
git pull --ff-only
python -m pip install -r requirement.pip
python scripts/sincronizar_bd.py
```

No se configuran hooks que ejecuten SQL de forma silenciosa al hacer pull. El comando explícito permite ver los pendientes y el resultado.

## Cómo se aplican los cambios

Las versiones SQL se guardan en sql/migrations con nombres como 001_admisiones_tipadas.sql. En el futuro se agregará una versión posterior para la actividad de limpieza; no se creó ni ejecutó esa limpieza ahora.

Cada versión aplicada se registra en public.migraciones_proyecto con nombre, SHA256 y fecha. Al ejecutar de nuevo el sincronizador, se omiten las ya registradas. Si se modifica o desaparece una versión aplicada, la sincronización se detiene; se debe publicar una nueva versión, no reescribir la anterior.

Antes de aplicar versiones pendientes se crea un respaldo local. Cada versión SQL se ejecuta en una transacción y se revierte si falla o altera las tablas original o tipada. La limpieza posterior deberá escribir en otra tabla. El orden se controla mediante los números de versión.

Los archivos de docker/init solo inicializan un volumen vacío. Agregar un archivo ahí no actualiza las bases existentes; por eso los cambios posteriores van en sql/migrations.

Para consultar el estado:

```bash
python scripts/sincronizar_bd.py --estado
```

Este modo levanta y verifica el servicio y crea el registro de versiones si falta, pero no aplica las migraciones pendientes.

## Qué compartir al desarrollar la siguiente actividad

Compartir el procedimiento reproducible, no únicamente una modificación manual realizada dentro de PostgreSQL. Una migración SQL nueva puede crear o poblar la tabla limpia a partir del origen conservado.

Si la limpieza se implementa en Python, su ejecución versionada deberá incorporarse explícitamente al flujo de sincronización al desarrollar esa actividad. La presencia de un archivo Python nuevo en Git no hace que se ejecute automáticamente. El sincronizador actual aplica versiones SQL y reproduce la estructura tipada conocida.

Los cambios manuales en tablas futuras de trabajo tampoco se propagan por Git. Las migraciones y los procesos compartidos deben permitir reconstruir su resultado en otra computadora.

## Mantener la exportación para pip

Después de cambiar dependencias con uv, actualizar y subir estos archivos juntos: pyproject.toml, uv.lock y requirement.pip.

```bash
uv export --frozen --all-groups --no-emit-project --format requirements-txt --output-file requirement.pip
```

requirements.txt permanece como entrada alternativa al mismo archivo. Cada equipo reconstruye su entorno; .venv, .env y data/backups continúan excluidos de Git.

## Alcance de las pruebas

Las pruebas verifican planificación, versiones inmutables, orden y preservación de datos. Las ejecuciones con Docker se documentan en BITACORA.md. La portabilidad de configuración no sustituye una ejecución real en Linux o macOS; esa validación debe registrarse al realizarse.

## Capa integrada vigente

El sincronizador ya incorpora la entrega final y sus controles mediante la migración 002 y scripts/cargar_base_unificada.py. No basta con aplicar el SQL para poblar las tablas. La carga compara todos los datos con el Excel, conserva fuentes y reglas, registra los 5.640 destinos y publica una sola vista vigente. Consulta [la guía de PostgreSQL y Excel para Power BI](postgresql_base_unificada_powerbi.md). Instala también el grupo excel de uv. Los comandos anteriores que describen únicamente las tablas original y tipada corresponden a la etapa inicial.
