# Fuente Oracle exportada

Caso2_Oracle_Admisiones.csv es una copia de CASO2.V_ADMISIONES_BASE consultada en vivo. Incluye las 15 columnas de negocio, sin limpieza ni integración con las otras fuentes. Puede utilizarse sin instalar Oracle para explorar esta fuente y compartir sus datos. El conteo, la fecha de extracción, los tipos Oracle y el SHA256 están en Caso2_Oracle_Admisiones.metadata.json.

En Excel utilizar Datos, Obtener datos, Desde texto o CSV. Seleccionar UTF8 y separador coma. Después revisar los tipos en Power Query: identificadores como texto, fechas con orden año, mes y día y números con punto decimal. No abrir y guardar sobre el original para evitar cambios de formato. Las celdas vacías representan los NULL exportados; el CSV no conserva tipos de base de datos.

La copia no se actualiza al refrescar Excel como lo haría una conexión Oracle. Para regenerarla desde la raíz del proyecto, con Oracle activo y las credenciales locales configuradas:

```bash
python scripts/exportar_vista_oracle.py
```

El exportador consulta la vista, ordena por registro_id y verifica la lectura completa del CSV contra todas las filas serializadas. No altera datos en el servidor.

Esta copia facilita el trabajo compartido, pero el taller pide evidenciar la vista y su importación desde Oracle a Power Query. Usar el CSV no demuestra esa conexión.
