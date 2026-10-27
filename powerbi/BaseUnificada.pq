// Consulta única. Elegir una fuente alternativa, sin anexar PostgreSQL y Excel.
// Editar estas cuatro variables antes de pegar en el editor avanzado.
let
    Origen = "PostgreSQL",
    Servidor = "localhost:5433",
    BaseDatos = "admisiones",
    RutaExcel = "C:\ruta\al\repositorio\deliverables\BaseUnificada_Entregable.xlsx",
    Datos =
        if Origen = "PostgreSQL" then
            PostgreSQL.Database(Servidor, BaseDatos){[Schema="analitica", Item="base_unificada"]}[Data]
        else if Origen = "Excel" then
            Table.PromoteHeaders(
                Excel.Workbook(File.Contents(RutaExcel), null, true){[Item="BaseUnificada", Kind="Sheet"]}[Data],
                [PromoteAllScalars=true])
        else
            error "Origen debe ser PostgreSQL o Excel",
    Tipos = {
        {"registro_id", type text}, {"aspirante_id", type text},
        {"fecha_solicitud", type date}, {"programa", type text},
        {"modalidad", type text}, {"canal_captacion", type text},
        {"estado_proceso", type text}, {"puntaje_admision", type number},
        {"documentos_completos", type text}, {"valor_matricula_cop", Currency.Type},
        {"ciudad_residencia", type text}, {"asesor", type text},
        {"fecha_matricula", type date}, {"correo", type text},
        {"periodo_academico", Int64.Type}, {"facultad", type text},
        {"duracion_semestres", Int64.Type}, {"nivel_formacion", type text}
    },
    Columnas = Table.SelectColumns(Datos, List.Transform(Tipos, each _{0})),
    Resultado = Table.TransformColumnTypes(Columnas, Tipos, "es-CO")
in
    Resultado
