# Oracle en Docker para el Taller 2

## Diseño

Se utiliza la imagen oficial container-registry.oracle.com/database/free:23.26.0.0-lite. El archivo compose.oracle.yaml define un proyecto independiente llamado admisiones_oracle, con un volumen oracle_taller2_data y puerto publicado solo en localhost. La base usa FREEPDB1 y caracteres AL32UTF8. PostgreSQL conserva su Compose y volumen anteriores.

Oracle permite trabajar el requisito de la vista del taller. DBeaver sirve para explorar y desarrollar SQL; Excel con Power Query sirve para importar la vista, depurar e integrar las fuentes y entregar Base_unificada. Una exportación CSV desde DBeaver no acredita por sí sola una conexión Oracle desde Power Query.

## Preparación reproducible

Con Docker Desktop abierto y la integración WSL activa, desde la raíz:

```bash
python scripts/preparar_oracle.py
```

El script solo usa la biblioteca estándar. Genera ORACLE_PASSWORD y ORACLE_CASO2_PASSWORD en .env si faltan, inicia Oracle, espera disponibilidad, crea el usuario local CASO2 con permisos de sesión, tablas y vistas, y cuota de 100 MB en USERS. No muestra las claves en su salida.

Oracle Lite no incluye USERS por defecto. El script lo crea si falta en FREEPDB1, con un archivo inicial de 100 MB, crecimiento de 25 MB y máximo de 1 GB, dentro del mismo volumen persistente. Esto permite ejecutar las cláusulas TABLESPACE del export sin editarlo.

Carga el export original leyendo cp1252 y enviando UTF8 al cliente SQL*Plus. Los INSERT y los valores no se depuran. Las cinco tablas se comparan fila por fila con las sentencias del export, respetando tipos numéricos y fechas. Se registra el hash de origen como comentario de C2_SOLICITUDES.

En ejecuciones posteriores, si la fuente coincide, no vuelve a insertar datos: verifica su contenido y recrea la vista de ejemplo. Una carga parcial o diferente se conserva y requiere revisión; el script no borra el esquema automáticamente. Los DDL de Oracle hacen commits implícitos, por lo que una importación fallida no equivale a una transacción totalmente reversible.

Las credenciales existentes no se rotan al editar .env. Conservarlas junto al volumen. El script admite claves alfanuméricas de 12 a 64 caracteres que empiecen por letra. Cambiar una contraseña requiere hacerlo también en Oracle.

## Conexión desde DBeaver en este PC

| Opción | Valor |
| :--- | :--- |
| Motor | Oracle |
| Host | localhost |
| Puerto | 1521, o el ORACLE_PORT local |
| Identificación | Service name |
| Servicio | FREEPDB1 |
| Usuario | CASO2 |
| Contraseña | ORACLE_CASO2_PASSWORD del archivo local .env |
| Rol | Normal |
| URL JDBC | jdbc:oracle:thin:@//localhost:1521/FREEPDB1 |

Permitir la descarga del controlador Oracle cuando DBeaver la solicite. No elegir SID FREE ni el rol SYSDBA para esta conexión de trabajo. El puerto se publica en Docker Desktop para que Windows pueda acceder por localhost; la conexión desde las aplicaciones debe probarse en este PC.

Las tablas esperadas son C2_SOLICITUDES con 500 filas, C2_ASPIRANTES con 500, C2_PROGRAMAS con 8, C2_CANALES con 6 y C2_ASESORES con 4. Los conteos efectivos y la verificación quedan en reports/taller_2/verificacion_oracle.json cuando el script termina correctamente.

## Vista para el ejercicio

El archivo sql/oracle/01_vista_admisiones.sql crea CASO2.V_ADMISIONES_BASE. Une solicitudes con los cuatro catálogos y expone las 15 columnas compatibles con la base inicial. Los LEFT JOIN conservan las solicitudes y las claves primarias evitan correspondencias múltiples. El script comprueba 500 filas, 500 identificadores distintos y las 15 columnas en el orden esperado.

```sql
SELECT COUNT(*) AS filas,
       COUNT(DISTINCT registro_id) AS registros_distintos
FROM CASO2.V_ADMISIONES_BASE;

SELECT *
FROM CASO2.V_ADMISIONES_BASE
FETCH FIRST 10 ROWS ONLY;
```

La vista no elimina duplicados, no unifica categorías, no cambia periodos y no incorpora los CSV. Proyecta la fuente Oracle para su evaluación posterior. Sus columnas Oracle aparecen en mayúsculas porque los alias no están entre comillas. En Power Query se pueden ajustar los encabezados a minúsculas para compatibilizarlos sin alterar valores.

## Conexión desde Excel y Power Query

En Excel de Windows, usar Datos, Obtener datos, Desde una base de datos, Desde una base de datos Oracle. Indicar localhost:1521/FREEPDB1, autenticación de base de datos y el usuario CASO2 con su clave local. Seleccionar V_ADMISIONES_BASE y Transformar datos. Mantener la consulta separada de las otras tres fuentes.

Si aparece un mensaje de proveedor ausente, revisar Oracle Client for Microsoft Tools, con arquitectura compatible con la instalación de Excel. La documentación sobre el controlador integrado de Power BI Desktop no garantiza que el mismo controlador esté disponible en Excel. No se ha instalado OCMT ni verificado una conexión Excel o DBeaver durante la preparación del servidor.

Se incluye una consulta de ejemplo en powerquery/taller_2/Oracle_Admisiones.pq. Su servidor debe ajustarse si se cambia el puerto. Las credenciales se introducen en el administrador de origen de datos de Excel, no en el código M.

## Operación y persistencia

```bash
docker compose -f compose.oracle.yaml ps
docker compose -f compose.oracle.yaml stop
docker compose -f compose.oracle.yaml up -d --wait
```

El volumen conserva los datos después de detener el servicio. No usar down con eliminación de volúmenes para detenerlo. El sincronizador PostgreSQL actual no inicia este proyecto Oracle; cada equipo debe ejecutar también preparar_oracle.py. La imagen declara soporte para amd64 y arm64, pero la ejecución de este proyecto en Mac no está probada.

## Verificación realizada el 24 de octubre de 2026

El servidor quedó iniciado y saludable. Se cargaron las cinco tablas y se comprobó la igualdad de todas sus filas contra los INSERT del archivo, incluidos acentos, números y fechas. La vista devolvió 500 filas, 500 identificadores distintos y 15 columnas. También se comprobó una conexión TCP desde Windows a 127.0.0.1:1521. Esta prueba confirma accesibilidad del puerto; no equivale a una conexión de DBeaver o Excel autenticada.

El digest publicado al descargar la imagen fue sha256:ec92fdc8d687c12d6501d5ad1a5827838f1ef5026c997ac878009491b167b2a1. El SQL original permanece sin cambios. No se ejecutó limpieza ni integración con las otras fuentes.

## Referencias

Oracle, ejecución local y persistencia: https://docs.oracle.com/en/database/oracle/agent-memory/26.6/guide/run-locally.html

Microsoft, conector Oracle y OCMT: https://learn.microsoft.com/en-us/power-query/connectors/oracle-database

Microsoft, importación desde Excel: https://support.microsoft.com/en-us/excel/import-data-from-data-sources-power-query
