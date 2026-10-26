# Organización de los datos

| Ubicación | Contenido | Uso |
| :--- | :--- | :--- |
| raw/ | CSV inicial y CSV de Programas y CRM recibidos | Fuentes originales conservadas |
| exports/taller_2/ | Exportación plana de la vista Oracle y sus metadatos | Consulta compartida de la fuente Oracle |
| prepared/taller_2/ | BaseUnificada.csv, BaseUnificada.xlsx y metadatos | Punto de partida del trabajo posterior de limpieza, con 18 columnas |
| interim/taller_2/ | Estados intermedios de estandarización, identificados por versión y hashes | Resultado por etapas del notebook; todavía no es una limpieza final |
| processed/taller_2/ | Versiones de preparación e integración y carpeta entregable bajo una ejecución | Salida final: 5.500 registros y 18 columnas, con CRM incorporado y 500 registros Oracle incluidos |
| BaseUnificada_Manejo.xlsx | Libro del usuario con fuentes, consultas Power Query y Merge | Respaldo del proceso de preparación y consolidación |
| workbooks/recibidos/ | Libros recibidos desde Git, separados de la versión de manejo | Conservar aportes sin sobrescribir el trabajo actual |
| backups/ | Respaldos locales de PostgreSQL y temporales apartados | No se comparten por Git |

BaseUnificada_Manejo.xlsx permanece en la raíz de data para conservar la ruta del libro que el usuario tiene abierto. No se guardaron sobre él las exportaciones. El libro traído por el pull del commit 37986c7 se trasladó desde Nueva carpeta a workbooks/recibidos, sin cambiar sus bytes. El archivo de bloqueo recibido se apartó en backups/temporales_excel; los bloqueos nuevos de Office se excluyen mediante .gitignore.

La nueva base de partida es prepared/taller_2/BaseUnificada.xlsx. Contiene una sola hoja y una tabla llamadas BaseUnificada, con 5.640 registros y 18 columnas. Es una copia de valores de la hoja BaseUnificada_ConProgramas_Merg del libro de manejo; no contiene conexiones o consultas y no aplica nuevas correcciones. El CSV ofrece los mismos registros serializados para herramientas de texto.

No confundir esta exportación con una limpieza terminada. Los duplicados, ausencias, periodos, fechas y decisiones sobre importes y atributos del catálogo permanecen tal como están en el libro guardado. La información original y el procedimiento de preparación siguen disponibles en las otras carpetas.

La salida actual del notebook se identifica en reports/limpieza/ultima_entrega.json y tiene una copia de revisión en deliverables/BaseUnificada_Entregable.xlsx. El paquete ZIP y los otros formatos se conservan únicamente como respaldo interno. Contiene 5.500 registros: 5.000 principales, con los 100 aportes CRM incorporados, y 500 Oracle conservados. Se recuperaron 13 importes desde matrícula base CRM. Los derechos y el total anterior están en Control_Economico. Los periodos académicos se conservan como semestres de ingreso y no se hacen coincidir con las fechas. La entrada preparada y todas las fuentes mantienen sus bytes.

La versión interna queda bajo processed/taller_2 en la carpeta de ejecución y su subcarpeta entregable conserva el contenido del paquete externo. Los CSV de origen, calidad, aspirantes por origen y coincidencias Oracle se incluyen en el ZIP. El Excel tiene una sola tabla administrativa BaseUnificada con 18 columnas; las hojas restantes son controles y resúmenes relacionados mediante registro_id y no se suman como nuevas fuentes.

Los resúmenes ultima_identidad_estados.json, ultima_revision_descriptiva.json y ultimo_cierre.json conservan los puntos previos L11, L10 y L09. La revisión L11 tenía 5.600 registros antes de incorporar CRM y agrupó Nuevo como Admitido con el original en auditoría.

La vista final Aspirantes_Origen incluye 2.924 identificadores principales y 500 Oracle. Sus 3.424 filas son códigos por sistema y no personas globales únicas confirmadas. Registros_Sin_ID conserva 90 registros cuya cantidad de personas es desconocida. Las coincidencias entre sistemas se identifican, sin borrar Oracle por semejanza ni crear equivalencias civiles. Los conteos por programa o estado pueden solaparse.

La versión 1.1 conserva exactamente los mismos datos de BaseUnificada y mejora su presentación auxiliar. Se sustituyen puntos y coma por comas en listas y puntos en las explicaciones. La marca similitud_entre_fuentes_detectada se informa en ambas fuentes relacionadas. El cruce está ejecutado y la marca no significa que falte una transformación técnica. Guia_Hojas.md explica las diez hojas. Los archivos anteriores de la raíz de deliverables se conservan porque el Excel estaba abierto durante la revisión.

reports/limpieza/ultimo_cierre.json conserva el punto de control L09 anterior, con 5.602 registros, y la exploración L10 está en reports/limpieza/revision_descriptiva_y_parciales.md. La entrega final ya incorpora CRM y conserva los candidatos Oracle dentro de sus 5.500 registros. Su auditoría enlaza las 5.640 entradas originales. Los archivos preparados permanecen como referencia y no se afirma un total global de personas o eventos independientes confirmados entre sistemas.

Para reproducir la exportación desde la raíz del proyecto:

```bash
uv sync --locked --group notebooks --group excel
uv run --locked --group excel python scripts/exportar_base_unificada.py
```

El script verifica todos los valores del Excel y todas las filas serializadas del CSV antes de publicar los archivos y registra sus hashes en BaseUnificada.metadata.json. Si el libro origen cambia durante la exportación, se detiene para no mezclar versiones.
