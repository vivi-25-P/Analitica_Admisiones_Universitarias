# Migraciones compartidas

Usar nombres con tres dígitos y descripción: 001_admisiones_tipadas.sql, seguido de versiones nuevas con número mayor. No editar una versión ya registrada en una base compartida.

El sincronizador aplica el SQL dentro de una transacción y registra nombre, SHA256 y fecha en public.migraciones_proyecto. No incluir comandos psql, COPY desde STDIN, BEGIN, COMMIT ni operaciones que necesiten ejecutarse fuera de una transacción. Los archivos son SQL de PostgreSQL, no scripts de terminal.

La carga tipada base se reproduce con scripts/preparar_tipos.py. Las siguientes versiones pueden crear tablas limpias o analíticas, pero deben preservar admisiones_original y admisiones_tipadas. Una modificación de esas bases produce una reversión de la migración.

Antes de publicar una migración, probarla sobre una base nueva y sobre otra con versiones anteriores. Comprobar sus cantidades y el significado de los indicadores. El sincronizador registra cada versión solo una vez.

La migración 002 crea los esquemas fuentes, trazabilidad y analitica. La carga se realiza después del SQL mediante scripts/cargar_base_unificada.py y forma parte del sincronizador. Conserva la preparación ya validada en Python y no vuelve a limpiar. La vista vigente tiene 5.500 registros y 18 columnas. Ver docs/postgresql_base_unificada_powerbi.md.
