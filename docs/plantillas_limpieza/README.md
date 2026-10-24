# Controles para la limpieza

Son plantillas vacías. No acreditan acciones de limpieza ejecutadas.

registro_pasos.csv registra cantidades antes y después, reglas, versión, cambios de valor y cambios de tipo por separado. Cada fila corresponde a un paso realmente aplicado en una ejecución.

cambios_por_celda.csv conserva el valor, tipo y motivo de ausencia anterior y posterior. Diferenciar texto vacío, dato no informado, Pendiente y No aplica cuando la fuente permita recuperar su significado.

disposicion_filas.csv registra el destino de cada una de las entradas del inventario. Las consolidaciones conservan las relaciones de todas sus filas originales con una misma salida. Una fila excluida necesita motivo; una fila con incidencias puede seguir conservada en la salida.

incidencias_pendientes.csv permite mantener los casos no resueltos y su efecto en los indicadores. El mismo registro puede presentar varias incidencias; no sumar esas filas de control como si fueran registros de negocio diferentes.

El inventario inicial ya generado está en reports/limpieza/inventario_entrada.csv. Los controles de una ejecución real se guardarán en reports/limpieza/ejecuciones con su identificador, sin sobrescribir estas plantillas ni la base de entrada.
