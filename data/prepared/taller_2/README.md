# Base unificada de partida

BaseUnificada.xlsx contiene una hoja y una tabla llamadas BaseUnificada. BaseUnificada.csv contiene las mismas 5.640 filas y 18 columnas como texto delimitado por comas, con UTF8 y BOM. No se aplicó limpieza adicional al exportar.

El Excel conserva los valores y tipos de celda de la hoja guardada, incluidos los números que estaban almacenados como texto. Se preserva la distinción de texto vacío y celda ausente al serializarlo. El CSV representa ambos como celda vacía y no conserva tipos de Excel. Los distintos formatos de fechas de la hoja origen no se unifican durante esta exportación.

Para importar el CSV en Excel, usar Datos, Desde texto o CSV, codificación UTF8 y separador coma. Revisar los tipos antes de aceptar conversiones automáticas, especialmente periodo_academico y fechas.

La procedencia, fecha de exportación, conteos y hashes están en BaseUnificada.metadata.json. El libro de manejo con las consultas se conserva en data/BaseUnificada_Manejo.xlsx.

Para empezar en Power Query con el Excel nuevo, crear la consulta desde la tabla una sola vez. Para continuar editándola, utilizar Datos, Consultas y conexiones, Editar; volver a Desde tabla o rango crearía otra consulta.
