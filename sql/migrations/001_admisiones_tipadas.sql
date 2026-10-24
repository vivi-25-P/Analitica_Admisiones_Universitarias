-- Estructura técnica, sin deduplicación ni estandarización de categorías.
-- Se aplica con scripts/preparar_tipos.py, que conserva y valida el origen.
CREATE TABLE IF NOT EXISTS public.admisiones_tipadas (
    fila_origen_csv INTEGER PRIMARY KEY CHECK (fila_origen_csv >= 2),
    origen_sha256 TEXT NOT NULL,
    registro_id TEXT,
    aspirante_id TEXT,
    fecha_solicitud DATE,
    programa TEXT,
    modalidad TEXT,
    canal_captacion TEXT,
    estado_proceso TEXT,
    puntaje_admision NUMERIC,
    documentos_completos TEXT,
    valor_matricula_cop NUMERIC,
    ciudad_residencia TEXT,
    asesor TEXT,
    fecha_matricula DATE,
    correo TEXT,
    periodo_academico TEXT,
    datos_originales JSONB NOT NULL,
    observaciones_tipado JSONB NOT NULL
);
COMMENT ON TABLE public.admisiones_tipadas IS
    'Proyección tipada sin limpieza: conserva cada fila y sus 15 valores originales en datos_originales.';
COMMENT ON COLUMN public.admisiones_tipadas.fila_origen_csv IS
    'Posición lógica en el CSV contando el encabezado como 1; no representa solicitud única.';
COMMENT ON COLUMN public.admisiones_tipadas.observaciones_tipado IS
    'Motivos de ausencia de representación numérica o de fecha; no son correcciones aplicadas.';
