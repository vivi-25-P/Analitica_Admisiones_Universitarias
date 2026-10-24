-- Consultas de solo lectura. No se eliminan ni normalizan los datos almacenados.
BEGIN READ ONLY;

SELECT COUNT(*) AS filas,
       COUNT(DISTINCT registro_id) AS registro_id_distintos,
       COUNT(*) - COUNT(DISTINCT registro_id) AS repeticiones_adicionales_registro_id,
       COUNT(DISTINCT NULLIF(aspirante_id, '')) AS aspirante_id_distintos_no_vacios
FROM public.admisiones_original;

-- Filas idénticas adicionales (no confundir con el total de filas involucradas).
SELECT COALESCE(SUM(cantidad - 1), 0) AS duplicados_exactos_adicionales
FROM (
    SELECT COUNT(*) AS cantidad
    FROM public.admisiones_original AS a
    GROUP BY to_jsonb(a)
    HAVING COUNT(*) > 1
) AS grupos;

-- Completitud por columna. "Solo espacios" se cuenta separado del vacío exacto.
SELECT campo,
       COUNT(*) FILTER (WHERE valor = '') AS vacios_exactos,
       COUNT(*) FILTER (WHERE valor <> '' AND BTRIM(valor) = '') AS solo_espacios,
       ROUND(100.0 * COUNT(*) FILTER (WHERE valor = '') / COUNT(*), 2) AS porcentaje_vacios
FROM public.admisiones_original AS a
CROSS JOIN LATERAL jsonb_each_text(to_jsonb(a)) AS campos(campo, valor)
GROUP BY campo
ORDER BY campo;

-- Categorías originales. El JSON hace visibles vacíos y espacios finales.
SELECT programa, to_json(programa) AS programa_visible,
       COUNT(*) AS registros,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS porcentaje_filas
FROM public.admisiones_original
GROUP BY programa
ORDER BY registros DESC, programa;

SELECT modalidad, estado_proceso, COUNT(*) AS registros
FROM public.admisiones_original
GROUP BY modalidad, estado_proceso
ORDER BY modalidad, registros DESC, estado_proceso;

SELECT canal_captacion, estado_proceso, COUNT(*) AS registros
FROM public.admisiones_original
GROUP BY canal_captacion, estado_proceso
ORDER BY canal_captacion, registros DESC, estado_proceso;

COMMIT;
