# Organización de los datos

| Ubicación | Contenido | Uso |
| :--- | :--- | :--- |
| raw/ | CSV inicial y CSV de Programas y CRM recibidos | Fuentes originales conservadas |
| exports/taller_2/ | Exportación plana de la vista Oracle y sus metadatos | Consulta compartida de la fuente Oracle |
| prepared/taller_2/ | BaseUnificada.csv, BaseUnificada.xlsx y metadatos | Punto de partida del trabajo posterior de limpieza, con 18 columnas |
| BaseUnificada_Manejo.xlsx | Libro del usuario con fuentes, consultas Power Query y Merge | Respaldo del proceso de preparación y consolidación |
| workbooks/recibidos/ | Libros recibidos desde Git, separados de la versión de manejo | Conservar aportes sin sobrescribir el trabajo actual |
| backups/ | Respaldos locales de PostgreSQL y temporales apartados | No se comparten por Git |

BaseUnificada_Manejo.xlsx permanece en la raíz de data para conservar la ruta del libro que el usuario tiene abierto. No se guardaron sobre él las exportaciones. El libro traído por el pull del commit 37986c7 se trasladó desde Nueva carpeta a workbooks/recibidos, sin cambiar sus bytes. El archivo de bloqueo recibido se apartó en backups/temporales_excel; los bloqueos nuevos de Office se excluyen mediante .gitignore.

La nueva base de partida es prepared/taller_2/BaseUnificada.xlsx. Contiene una sola hoja y una tabla llamadas BaseUnificada, con 5.640 registros y 18 columnas. Es una copia de valores de la hoja BaseUnificada_ConProgramas_Merg del libro de manejo; no contiene conexiones o consultas y no aplica nuevas correcciones. El CSV ofrece los mismos registros serializados para herramientas de texto.

No confundir esta exportación con una limpieza terminada. Los duplicados, ausencias, periodos, fechas y decisiones sobre importes y atributos del catálogo permanecen tal como están en el libro guardado. La información original y el procedimiento de preparación siguen disponibles en las otras carpetas.

Para reproducir la exportación desde la raíz del proyecto:

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group excel python scripts/exportar_base_unificada.py
```

El script verifica todos los valores del Excel y todas las filas serializadas del CSV antes de publicar los archivos y registra sus hashes en BaseUnificada.metadata.json. Si el libro origen cambia durante la exportación, se detiene para no mezclar versiones.
