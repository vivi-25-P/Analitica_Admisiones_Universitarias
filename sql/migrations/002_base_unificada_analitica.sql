CREATE SCHEMA fuentes;
CREATE SCHEMA trazabilidad;
CREATE SCHEMA analitica;

CREATE TABLE fuentes.archivos (
    sha256 TEXT PRIMARY KEY CHECK (length(sha256) = 64),
    contenido BYTEA NOT NULL
);
CREATE TABLE fuentes.filas (
    archivo_sha256 TEXT NOT NULL REFERENCES fuentes.archivos,
    numero_fila INTEGER NOT NULL CHECK (numero_fila >= 2),
    valores_originales JSONB NOT NULL,
    PRIMARY KEY (archivo_sha256, numero_fila)
);
CREATE TABLE trazabilidad.ejecuciones (
    carga_id TEXT PRIMARY KEY,
    ejecucion_limpieza TEXT NOT NULL,
    excel_sha256 TEXT NOT NULL REFERENCES fuentes.archivos,
    csv_sha256 TEXT NOT NULL REFERENCES fuentes.archivos,
    manifiesto JSONB NOT NULL,
    cargado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE trazabilidad.archivos_ejecucion (
    carga_id TEXT NOT NULL REFERENCES trazabilidad.ejecuciones,
    ruta TEXT NOT NULL,
    archivo_sha256 TEXT NOT NULL REFERENCES fuentes.archivos,
    PRIMARY KEY (carga_id, ruta)
);
CREATE TABLE analitica.registros (
    carga_id TEXT NOT NULL REFERENCES trazabilidad.ejecuciones,
    registro_id TEXT NOT NULL,
    aspirante_id TEXT,
    fecha_solicitud DATE NOT NULL,
    programa TEXT,
    modalidad TEXT NOT NULL,
    canal_captacion TEXT NOT NULL,
    estado_proceso TEXT NOT NULL,
    puntaje_admision NUMERIC,
    documentos_completos TEXT NOT NULL,
    valor_matricula_cop NUMERIC(18,2),
    ciudad_residencia TEXT NOT NULL,
    asesor TEXT NOT NULL,
    fecha_matricula DATE,
    correo TEXT,
    periodo_academico INTEGER NOT NULL,
    facultad TEXT,
    duracion_semestres INTEGER,
    nivel_formacion TEXT,
    PRIMARY KEY (carga_id, registro_id)
);
CREATE TABLE trazabilidad.hojas (
    carga_id TEXT NOT NULL REFERENCES trazabilidad.ejecuciones,
    hoja TEXT NOT NULL,
    posicion INTEGER NOT NULL,
    valores JSONB NOT NULL,
    PRIMARY KEY (carga_id, hoja, posicion)
);
CREATE TABLE trazabilidad.destinos (
    carga_id TEXT NOT NULL,
    id_fila_entrada TEXT NOT NULL,
    archivo_entrada_sha256 TEXT NOT NULL,
    numero_fila_entrada INTEGER NOT NULL,
    registro_id_salida TEXT NOT NULL,
    fuente TEXT NOT NULL,
    detalle JSONB NOT NULL,
    PRIMARY KEY (carga_id, id_fila_entrada),
    FOREIGN KEY (carga_id, registro_id_salida) REFERENCES analitica.registros,
    FOREIGN KEY (archivo_entrada_sha256, numero_fila_entrada)
        REFERENCES fuentes.filas (archivo_sha256, numero_fila)
);
CREATE TABLE trazabilidad.publicacion_actual (
    unico BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (unico),
    carga_id TEXT NOT NULL REFERENCES trazabilidad.ejecuciones
);

CREATE VIEW analitica.base_unificada AS
SELECT r.registro_id, r.aspirante_id, r.fecha_solicitud, r.programa,
       r.modalidad, r.canal_captacion, r.estado_proceso, r.puntaje_admision,
       r.documentos_completos, r.valor_matricula_cop, r.ciudad_residencia,
       r.asesor, r.fecha_matricula, r.correo, r.periodo_academico,
       r.facultad, r.duracion_semestres, r.nivel_formacion
FROM analitica.registros r
JOIN trazabilidad.publicacion_actual a USING (carga_id);

CREATE VIEW analitica.origen_registros AS
SELECT v.* FROM trazabilidad.hojas h
JOIN trazabilidad.publicacion_actual a USING (carga_id)
CROSS JOIN LATERAL jsonb_to_record(h.valores) AS v(
    registro_id TEXT, fuente_origen TEXT, fuentes_asociadas TEXT,
    crm_incorporado BOOLEAN, importe_recuperado_crm BOOLEAN,
    similitud_entre_fuentes_detectada BOOLEAN, unidad TEXT)
WHERE h.hoja = 'Origen_Registros';

CREATE VIEW analitica.control_calidad AS
SELECT v.* FROM trazabilidad.hojas h
JOIN trazabilidad.publicacion_actual a USING (carga_id)
CROSS JOIN LATERAL jsonb_to_record(h.valores) AS v(
    registro_id TEXT, fuente_origen TEXT, programa_ausente BOOLEAN,
    aspirante_id_ausente BOOLEAN, puntaje_ausente BOOLEAN, importe_ausente BOOLEAN,
    fecha_matricula_ausente BOOLEAN, fecha_solicitud_ambigua BOOLEAN,
    fecha_matricula_ambigua BOOLEAN, matricula_anterior_a_solicitud BOOLEAN,
    solicitud_posterior_al_anio_periodo BOOLEAN, fuera_ventana_orientativa BOOLEAN,
    solicitud_posterior_referencia BOOLEAN, matricula_posterior_referencia BOOLEAN,
    matriculado_documentos_no_completos BOOLEAN, documentacion_pendiente_con_documentos_si BOOLEAN,
    estado_recibido TEXT, estado_analitico TEXT, intervalo_dias_apto_reglas_aplicadas BOOLEAN,
    dias_solicitud_matricula INTEGER, fecha_solicitud_apta_reglas_aplicadas BOOLEAN,
    referencia_revision DATE)
WHERE h.hoja = 'Control_Calidad';

CREATE VIEW analitica.control_economico AS
SELECT v.* FROM trazabilidad.hojas h
JOIN trazabilidad.publicacion_actual a USING (carga_id)
CROSS JOIN LATERAL jsonb_to_record(h.valores) AS v(
    registro_id TEXT, "importe_principal_anterior_COP" NUMERIC(18,2),
    "matricula_base_CRM_COP" NUMERIC(18,2), "derechos_administrativos_CRM_COP" NUMERIC(18,2),
    "total_reportado_CRM_COP" NUMERIC(18,2), "importe_final_COP" NUMERIC(18,2), tratamiento TEXT)
WHERE h.hoja = 'Control_Economico';

COMMENT ON VIEW analitica.base_unificada IS
'Mismos 18 atributos y registros que el Excel vigente. No sumar con otra copia Excel ni afirmar identidad global de personas.';
COMMENT ON TABLE trazabilidad.destinos IS
'Destino de cada una de las 5.640 entradas conservando sus valores de integración y vínculo con la salida.';
