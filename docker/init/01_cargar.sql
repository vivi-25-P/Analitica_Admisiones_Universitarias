BEGIN;

CREATE TABLE public.admisiones_original (
    registro_id TEXT,
    aspirante_id TEXT,
    fecha_solicitud TEXT,
    programa TEXT,
    modalidad TEXT,
    canal_captacion TEXT,
    estado_proceso TEXT,
    puntaje_admision TEXT,
    documentos_completos TEXT,
    valor_matricula_cop TEXT,
    ciudad_residencia TEXT,
    asesor TEXT,
    fecha_matricula TEXT,
    correo TEXT,
    periodo_academico TEXT
);

COPY public.admisiones_original
FROM '/datos/admisiones.csv'
WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', FORCE_NOT_NULL *);

DO $$
BEGIN
    IF (SELECT COUNT(*) FROM public.admisiones_original) <> 5040 THEN
        RAISE EXCEPTION 'La carga debe conservar las 5040 filas originales';
    END IF;
END $$;

COMMIT;
