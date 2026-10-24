// Plantilla de conexión. Las credenciales se introducen en Excel.
let
    Origen = Oracle.Database(
        "localhost:1521/FREEPDB1",
        [Query = "SELECT * FROM CASO2.V_ADMISIONES_BASE", HierarchicalNavigation = true]
    ),
    EncabezadosCompatibles = Table.TransformColumnNames(Origen, Text.Lower)
in
    EncabezadosCompatibles
