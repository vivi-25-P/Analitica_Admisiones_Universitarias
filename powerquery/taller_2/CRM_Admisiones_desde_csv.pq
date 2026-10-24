// Corrección del origen CRM. Conserva los pasos existentes de preparación.
let
    OrigenCSV = Csv.Document(File.Contents("C:\Users\jdlos\Desktop\analitica_admisiones_universitaria\data\raw\taller_2\Caso2 CRM Admisiones.csv"), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Source = Table.PromoteHeaders(OrigenCSV, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"registro_aspirante_crm", type text}, {"fecha_solicitud", type text}, {"programa", type text}, {"modalidad", type text}, {"canal_captacion", type text}, {"estado_proceso", type text}, {"puntaje_admision", type text}, {"documentos_completos", type text}, {"matricula_base_cop", Int64.Type}, {"derechos_administrativos_cop", Int64.Type}, {"ciudad_residencia", type text}, {"asesor", type text}, {"fecha_matricula", type text}, {"correo", type text}, {"periodo_academico", type text}}),
    #"Split Column by Delimiter" = Table.SplitColumn(#"Changed Type", "registro_aspirante_crm", Splitter.SplitTextByDelimiter("|", QuoteStyle.Csv), {"registro_aspirante_crm.1", "registro_aspirante_crm.2"}),
    #"Changed Type1" = Table.TransformColumnTypes(#"Split Column by Delimiter",{{"registro_aspirante_crm.1", type text}, {"registro_aspirante_crm.2", type text}}),
    #"Added Custom" = Table.AddColumn(#"Changed Type1", "Calculada", each [matricula_base_cop] + [derechos_administrativos_cop]),
    #"Reordered Columns" = Table.ReorderColumns(#"Added Custom",{"registro_aspirante_crm.1", "registro_aspirante_crm.2", "fecha_solicitud", "programa", "modalidad", "canal_captacion", "estado_proceso", "puntaje_admision", "documentos_completos", "matricula_base_cop", "derechos_administrativos_cop", "Calculada", "ciudad_residencia", "asesor", "fecha_matricula", "correo", "periodo_academico"}),
    #"Renamed Columns" = Table.RenameColumns(#"Reordered Columns",{{"Calculada", "valor_matricula_cop"}}),
    #"Removed Columns" = Table.RemoveColumns(#"Renamed Columns",{"matricula_base_cop", "derechos_administrativos_cop"}),
    #"Renamed Columns1" = Table.RenameColumns(#"Removed Columns",{{"registro_aspirante_crm.2", "aspirante_id"}, {"registro_aspirante_crm.1", "registro_id"}}),
    #"Cleaned Text" = Table.TransformColumns(#"Renamed Columns1",{{"registro_id", Text.Clean, type text}, {"aspirante_id", Text.Clean, type text}}),
    #"Trimmed Text" = Table.TransformColumns(#"Cleaned Text",{{"registro_id", Text.Trim, type text}, {"aspirante_id", Text.Trim, type text}})
in
    #"Trimmed Text"
