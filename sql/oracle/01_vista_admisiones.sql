-- Proyección de la fuente Oracle. No depura ni fusiona con los CSV.
CREATE OR REPLACE VIEW CASO2.V_ADMISIONES_BASE AS
SELECT
    s.REGISTRO_ID AS registro_id,
    s.ASPIRANTE_ID AS aspirante_id,
    s.FECHA_SOLICITUD AS fecha_solicitud,
    p.NOMBRE_PROGRAMA AS programa,
    s.MODALIDAD AS modalidad,
    c.NOMBRE_CANAL AS canal_captacion,
    s.ESTADO_PROCESO AS estado_proceso,
    s.PUNTAJE_ADMISION AS puntaje_admision,
    s.DOCUMENTOS_COMPLETOS AS documentos_completos,
    s.VALOR_MATRICULA_COP AS valor_matricula_cop,
    a.CIUDAD_RESIDENCIA AS ciudad_residencia,
    t.NOMBRE_ASESOR AS asesor,
    s.FECHA_MATRICULA AS fecha_matricula,
    a.CORREO AS correo,
    s.PERIODO_ACADEMICO AS periodo_academico
FROM CASO2.C2_SOLICITUDES s
LEFT JOIN CASO2.C2_ASPIRANTES a ON a.ASPIRANTE_ID = s.ASPIRANTE_ID
LEFT JOIN CASO2.C2_PROGRAMAS p ON p.PROGRAMA_ID = s.PROGRAMA_ID
LEFT JOIN CASO2.C2_CANALES c ON c.CANAL_ID = s.CANAL_ID
LEFT JOIN CASO2.C2_ASESORES t ON t.ASESOR_ID = s.ASESOR_ID;
