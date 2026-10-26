# Organización de los datos

| Ubicación | Contenido | Uso |
| :--- | :--- | :--- |
| raw/ | CSV inicial y CSV de Programas y CRM recibidos | Fuentes originales conservadas |
| exports/taller_2/ | Exportación plana de la vista Oracle y sus metadatos | Consulta compartida de la fuente Oracle |
| prepared/taller_2/ | BaseUnificada.csv, BaseUnificada.xlsx y metadatos | Punto de partida del trabajo posterior de limpieza, con 18 columnas |
| interim/taller_2/ | Estados intermedios de estandarización, identificados por versión y hashes | Resultado por etapas del notebook; todavía no es una limpieza final |
| processed/taller_2/ | BaseUnificada_Revision en CSV, Excel y JSONL bajo una carpeta de ejecución | Salida L11: consolidado de 5.600 registros y 18 columnas, 5.000 solicitudes principales y vistas auxiliares de 2.924 códigos de aspirante y 90 solicitudes sin ID |
| BaseUnificada_Manejo.xlsx | Libro del usuario con fuentes, consultas Power Query y Merge | Respaldo del proceso de preparación y consolidación |
| workbooks/recibidos/ | Libros recibidos desde Git, separados de la versión de manejo | Conservar aportes sin sobrescribir el trabajo actual |
| backups/ | Respaldos locales de PostgreSQL y temporales apartados | No se comparten por Git |

BaseUnificada_Manejo.xlsx permanece en la raíz de data para conservar la ruta del libro que el usuario tiene abierto. No se guardaron sobre él las exportaciones. El libro traído por el pull del commit 37986c7 se trasladó desde Nueva carpeta a workbooks/recibidos, sin cambiar sus bytes. El archivo de bloqueo recibido se apartó en backups/temporales_excel; los bloqueos nuevos de Office se excluyen mediante .gitignore.

La nueva base de partida es prepared/taller_2/BaseUnificada.xlsx. Contiene una sola hoja y una tabla llamadas BaseUnificada, con 5.640 registros y 18 columnas. Es una copia de valores de la hoja BaseUnificada_ConProgramas_Merg del libro de manejo; no contiene conexiones o consultas y no aplica nuevas correcciones. El CSV ofrece los mismos registros serializados para herramientas de texto.

No confundir esta exportación con una limpieza terminada. Los duplicados, ausencias, periodos, fechas y decisiones sobre importes y atributos del catálogo permanecen tal como están en el libro guardado. La información original y el procedimiento de preparación siguen disponibles en las otras carpetas.

La salida actual del notebook de limpieza está en processed/taller_2 y se identifica en reports/limpieza/ultima_identidad_estados.json. El punto previo L10 se identifica en ultima_revision_descriptiva.json: complementó dos parciales y homologó identificadores no informados como null. L11 mantiene 5.600 registros y agrupa Nuevo con Admitido según el contexto del usuario, conservando los estados recibidos en auditoría. El Excel incluye BaseUnificada_Revision, Principal_Analisis, Aspirantes_Principal, Solicitudes_Sin_ID y Alcance. Las dos primeras conservan las 18 columnas de negocio; las restantes son vistas auxiliares y no se suman al consolidado.

Principal_Analisis contiene 5.000 códigos de solicitud distintos. Aspirantes_Principal contiene 2.924 códigos de aspirante informados y una clasificación excluyente basada en cualquiera de sus solicitudes; no es estado actual. Solicitudes_Sin_ID conserva 90 solicitudes cuya cantidad de personas es desconocida. Los conteos de personas por programa o estado no son aditivos. Las vistas se ofrecen también como CSV y se documentan en reports/limpieza/reporte_estados_personas_y_cierre.md.

reports/limpieza/ultimo_cierre.json conserva el punto de control L09 anterior, con 5.602 registros. La auditoría L10 enlaza las 5.640 entradas originales con las salidas actuales. reports/limpieza/revision_descriptiva_y_parciales.md presenta la exploración, sus gráficos y las limitaciones. Los archivos preparados se conservan como referencia. El consolidado todavía contiene solapamientos CRM y candidatos Oracle y no acredita un total global de solicitudes únicas.

Para reproducir la exportación desde la raíz del proyecto:

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group excel python scripts/exportar_base_unificada.py
```

El script verifica todos los valores del Excel y todas las filas serializadas del CSV antes de publicar los archivos y registra sus hashes en BaseUnificada.metadata.json. Si el libro origen cambia durante la exportación, se detiene para no mezclar versiones.
