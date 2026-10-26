section Section1;

shared Caso2_Oracle_Admisiones = let
    Source = Csv.Document(File.Contents("C:\Users\jdlos\Desktop\analitica_admisiones_universitaria\data\exports\taller_2\Caso2_Oracle_Admisiones.csv"),[Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    #"Promoted Headers";

shared Caso2_Admisiones_Universitarias_Principal = let
    Source = Excel.CurrentWorkbook(){[Name="Caso2_Admisiones_Universitarias"]}[Content],
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"registro_id", type text}, {"aspirante_id", type text}, {"fecha_solicitud", type text}, {"programa", type text}, {"modalidad", type text}, {"canal_captacion", type text}, {"estado_proceso", type text}, {"puntaje_admision", type text}, {"documentos_completos", type text}, {"valor_matricula_cop", type text}, {"ciudad_residencia", type text}, {"asesor", type text}, {"fecha_matricula", type text}, {"correo", type text}, {"periodo_academico", type text}}),
    #"Cleaned Text" = Table.TransformColumns(#"Changed Type",{{"registro_id", Text.Clean, type text}, {"aspirante_id", Text.Clean, type text}}),
    #"Trimmed Text" = Table.TransformColumns(#"Cleaned Text",{{"registro_id", Text.Trim, type text}, {"aspirante_id", Text.Trim, type text}})
in
    #"Trimmed Text";

shared Caso2_CRM_Admisiones = // Corrección del origen CRM. Conserva los pasos existentes de preparación.
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
;

shared BaseUnificada = let
    Source = Table.Combine({Caso2_Admisiones_Universitarias_Principal, Caso2_CRM_Admisiones, Caso2_Oracle_Admisiones}),
    #"Capitalized Each Word" = Table.TransformColumns(Source,{{"programa", Text.Proper, type text}, {"modalidad", Text.Proper, type text}, {"canal_captacion", Text.Proper, type text}, {"estado_proceso", Text.Proper, type text}, {"ciudad_residencia", Text.Proper, type text}, {"asesor", Text.Proper, type text}}),
    #"Cleaned Text" = Table.TransformColumns(#"Capitalized Each Word",{{"programa", Text.Clean, type text}, {"modalidad", Text.Clean, type text}, {"canal_captacion", Text.Clean, type text}, {"estado_proceso", Text.Clean, type text}, {"ciudad_residencia", Text.Clean, type text}, {"asesor", Text.Clean, type text}}),
    #"Trimmed Text" = Table.TransformColumns(#"Cleaned Text",{{"programa", Text.Trim, type text}, {"modalidad", Text.Trim, type text}, {"canal_captacion", Text.Trim, type text}, {"estado_proceso", Text.Trim, type text}, {"ciudad_residencia", Text.Trim, type text}, {"asesor", Text.Trim, type text}})
in
    #"Trimmed Text";

shared Caso2_Programas = let
    Source = Excel.CurrentWorkbook(){[Name="Caso2_Programas"]}[Content],
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"programa", type text}, {"programa_clave", type text}, {"facultad", type text}, {"duracion_semestres", Int64.Type}, {"nivel_formacion", type text}, {"modalidad", type text}}),
    #"Removed Columns" = Table.RemoveColumns(#"Changed Type",{"programa_clave"}),
    #"Filtered Rows" = Table.SelectRows(#"Removed Columns", each ([programa] <> "Especializacion en Data Analytics")),
    #"Cleaned Text" = Table.TransformColumns(#"Filtered Rows",{{"programa", Text.Clean, type text}, {"facultad", Text.Clean, type text}, {"nivel_formacion", Text.Clean, type text}, {"modalidad", Text.Clean, type text}}),
    #"Trimmed Text" = Table.TransformColumns(#"Cleaned Text",{{"programa", Text.Trim, type text}, {"facultad", Text.Trim, type text}, {"nivel_formacion", Text.Trim, type text}, {"modalidad", Text.Trim, type text}}),
    #"Capitalized Each Word" = Table.TransformColumns(#"Trimmed Text",{{"programa", Text.Proper, type text}, {"facultad", Text.Proper, type text}, {"nivel_formacion", Text.Proper, type text}, {"modalidad", Text.Proper, type text}})
in
    #"Capitalized Each Word";

shared BaseUnificada_ConProgramas_Merge = let
    Source = Table.FuzzyNestedJoin(BaseUnificada, {"programa"}, Caso2_Programas, {"programa"}, "Caso2_Programas", JoinKind.LeftOuter, [IgnoreCase=true, IgnoreSpace=true]),
    #"Expanded Caso2_Programas" = Table.ExpandTableColumn(Source, "Caso2_Programas", {"programa", "facultad", "duracion_semestres", "nivel_formacion", "modalidad"}, {"Caso2_Programas.programa", "Caso2_Programas.facultad", "Caso2_Programas.duracion_semestres", "Caso2_Programas.nivel_formacion", "Caso2_Programas.modalidad"}),
    #"Removed Columns" = Table.RemoveColumns(#"Expanded Caso2_Programas",{"Caso2_Programas.programa"}),
    #"Renamed Columns" = Table.RenameColumns(#"Removed Columns",{{"Caso2_Programas.facultad", "facultad"}, {"Caso2_Programas.duracion_semestres", "duracion_semestres"}, {"Caso2_Programas.nivel_formacion", "nivel_formacion"}, {"Caso2_Programas.modalidad", "modalidad1"}}),
    #"Removed Columns1" = Table.RemoveColumns(#"Renamed Columns",{"modalidad1"})
in
    #"Removed Columns1";