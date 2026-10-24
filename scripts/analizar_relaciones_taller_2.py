"""Perfil y comparación reproducible. No limpia ni integra las fuentes.

La vista Oracle se lee de oracle_vista_lectura.json, capturado mediante SELECT.
Las normalizaciones se usan solo como sondas documentadas de correspondencia.
"""

from collections import Counter, defaultdict
from datetime import datetime
from datetime import date as Date
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json
from pathlib import Path
from statistics import median, quantiles
from zoneinfo import ZoneInfo

from revisar_fuentes_taller_2 import read_csv, key
from preparar_tipos import represent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/taller_2/comparacion"
CATEGORIES = ["programa", "modalidad", "canal_captacion", "estado_proceso", "documentos_completos", "ciudad_residencia", "asesor", "periodo_academico", "facultad", "nivel_formacion"]
NUMBERS = {"puntaje_admision", "valor_matricula_cop", "matricula_base_cop", "derechos_administrativos_cop", "duracion_semestres"}


def text(value):
    return "" if value is None else str(value)


def number(value):
    if value is None or not str(value).strip():
        return None
    try:
        value = Decimal(str(value))
        return value if value.is_finite() else None
    except InvalidOperation:
        return None


def date(value, column="fecha_solicitud"):
    if not value:
        return None
    return represent(column, str(value))[0]


def period(value):
    mapping = {"2025-2": "20252", "2026-I": "20261", "2026-1": "20261", "2026 II": "20262", "2026-2": "20262"}
    return mapping.get(text(value).strip(), text(value).strip())


def normalize(value, column):
    if column.startswith("fecha_"):
        return date(value, column)
    if column in NUMBERS:
        return number(value)
    if column == "correo":
        return text(value).strip().lower()
    if column == "periodo_academico":
        return period(value)
    return key(text(value))


def signature(row, columns):
    values = tuple(normalize(row.get(c), c) for c in columns)
    return values if all(v is not None and v != "" for v in values) else None


def profile(rows):
    columns = list(rows[0])
    n = len(rows)
    result = {"filas": n, "columnas": len(columns), "nombres": columns}
    result["duplicados_exactos_adicionales"] = n - len({tuple(text(r[c]) for c in columns) for r in rows})
    result["calidad"] = {c: {"vacios_o_null": sum(r[c] is None or r[c] == "" for r in rows), "solo_espacios": sum(bool(text(r[c])) and not text(r[c]).strip() for r in rows), "distintos_no_vacios": len({text(r[c]) for r in rows if text(r[c]).strip()})} for c in columns}
    result["frecuencias"] = {c: dict(Counter(text(r[c]) for r in rows).most_common()) for c in CATEGORIES if c in columns}
    result["numericas"] = {}
    for c in columns:
        if c not in NUMBERS:
            continue
        nums = [v for r in rows if (v := number(r[c])) is not None]
        invalid = Counter(text(r[c]) for r in rows if text(r[c]).strip() and number(r[c]) is None)
        if nums:
            q1, _, q3 = quantiles(nums, n=4, method="inclusive")
            low, high = q1 - Decimal("1.5") * (q3 - q1), q3 + Decimal("1.5") * (q3 - q1)
            result["numericas"][c] = {"validos_numericos": len(nums), "minimo": str(min(nums)), "maximo": str(max(nums)), "promedio": str(sum(nums) / len(nums)), "mediana": str(median(nums)), "negativos": sum(v < 0 for v in nums), "atipicos_1_5_RIC": sum(v < low or v > high for v in nums), "q1": str(q1), "q3": str(q3), "no_interpretables": dict(invalid)}
    result["fechas"] = {}
    for c in [c for c in columns if c.startswith("fecha_")]:
        parsed = [d for r in rows if (d := date(r[c], c)) is not None]
        result["fechas"][c] = {"interpretables": len(parsed), "minimo": min(parsed) if parsed else None, "maximo": max(parsed) if parsed else None, "no_aplica": sum(text(r[c]) == "No aplica" for r in rows), "no_interpretables_no_vacios_ni_no_aplica": sum(bool(text(r[c]).strip()) and text(r[c]) != "No aplica" and date(r[c], c) is None for r in rows)}
    for c in ["registro_id", "aspirante_id", "correo", "programa_clave", "registro_aspirante_crm"]:
        if c in columns:
            vals = [text(r[c]) for r in rows if text(r[c]).strip()]
            result[c + "_distintos_no_vacios"] = len(set(vals))
    if "estado_proceso" in columns:
        result["matriculados_con_documentacion_no_o_pendiente"] = sum(key(text(r["estado_proceso"])) == "MATRICULADO" and key(text(r["documentos_completos"])) in {"NO", "PENDIENTE"} for r in rows)
        result["periodo_20252_solicitud_2026"] = sum(period(r["periodo_academico"]) == "20252" and text(date(r["fecha_solicitud"])).startswith("2026") for r in rows)
    return result


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {
        "principal": read_csv("data/raw/Caso2_Admisiones_Universitarias.csv"),
        "programas": read_csv("data/raw/taller_2/Caso2 Programas.csv"),
        "crm": read_csv("data/raw/taller_2/Caso2 CRM Admisiones.csv"),
    }
    snapshot_path = ROOT / "reports/taller_2/oracle_vista_lectura.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf8"))
    sources["oracle"] = snapshot["filas"]
    base, programs, crm, oracle = (sources[k] for k in ["principal", "programas", "crm", "oracle"])
    expected = list(base[0])
    assert [c["columna"].lower() for c in snapshot["columnas"]] == expected
    assert list(oracle[0]) == expected
    for manifest in ["docs/referencias/integridad.json", "docs/referencias/taller_2/integridad.json"]:
        for path, item in json.loads((ROOT / manifest).read_text(encoding="utf8")).items():
            digest = item if isinstance(item, str) else item["sha256"]
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    profiles = {name: profile(rows) for name, rows in sources.items()}
    by_id = defaultdict(list)
    for i, row in enumerate(base, start=2):
        by_id[row["registro_id"]].append((i, row))
    crm_detail = []
    crm_index = Counter()
    core = [c for c in expected if c not in {"registro_id", "aspirante_id", "valor_matricula_cop"}]
    for row in crm:
        reg, asp = [part.strip() for part in row["registro_aspirante_crm"].split("|")]
        candidates = by_id[reg]
        crm_index[reg] += 1
        crm_detail.append({"registro_id": reg, "aspirante_crm": asp, "filas_origen_csv": ", ".join(str(i) for i, r in candidates), "aspirantes_principal": json.dumps(sorted({r["aspirante_id"] for _, r in candidates}), ensure_ascii=False), "coinciden_12_columnas_compartidas": any(all(text(r[c]) == row[c] for c in core) for _, r in candidates), "importe_principal": json.dumps(sorted({r["valor_matricula_cop"] for _, r in candidates})), "matricula_base_crm": row["matricula_base_cop"], "derechos_administrativos_crm": row["derechos_administrativos_cop"], "importe_igual": any(number(r["valor_matricula_cop"]) == number(row["matricula_base_cop"]) for _, r in candidates), "importe_principal_ausente": all(not r["valor_matricula_cop"].strip() for _, r in candidates)})
    write_csv(OUT / "relacion_crm_principal.csv", crm_detail)
    crm_relation = {"ids_en_principal": sum(bool(by_id[d["registro_id"]]) for d in crm_detail), "ids_nuevos": sum(not by_id[d["registro_id"]] for d in crm_detail), "aspirante_literal_nan": sum(d["aspirante_crm"] == "nan" for d in crm_detail), "coinciden_12_columnas_compartidas": sum(d["coinciden_12_columnas_compartidas"] for d in crm_detail), "importes_iguales": sum(d["importe_igual"] for d in crm_detail), "importe_principal_ausente_con_base_crm": sum(d["importe_principal_ausente"] for d in crm_detail), "filas_principales_con_match": sum(bool(crm_index[r["registro_id"]]) for r in base), "filas_left_merge_por_registro_id": sum(max(1, crm_index[r["registro_id"]]) for r in base)}
    program_relations = {}
    for name, cols, norm in [("programa_con_tilde", ["programa"], lambda v: text(v).strip().upper()), ("programa_sin_tilde", ["programa"], lambda v: key(text(v))), ("programa_y_modalidad", ["programa", "modalidad"], lambda v: key(text(v)))]:
        index = Counter(tuple(norm(r[c]) for c in cols) for r in programs if text(r["programa"]).strip())
        sizes = [index.get(tuple(norm(r[c]) for c in cols), 0) if r["programa"].strip() else 0 for r in base]
        program_relations[name] = {"filas_con_match": sum(v > 0 for v in sizes), "filas_sin_match": sum(v == 0 for v in sizes), "filas_con_match_multiple": sum(v > 1 for v in sizes), "filas_resultantes_left_merge": sum(max(1, v) for v in sizes)}
    programs_detail = []
    for r in programs:
        programs_detail.append({**r, "registros_principal_nombre_normalizado": sum(bool(r["programa"].strip()) and key(s["programa"]) == key(r["programa"]) for s in base), "registros_principal_nombre_y_modalidad": sum(bool(r["programa"].strip()) and key(s["programa"]) == key(r["programa"]) and key(s["modalidad"]) == key(r["modalidad"]) for s in base)})
    write_csv(OUT / "cobertura_catalogo_programas.csv", programs_detail)
    probes = {
        "correo": ["correo"],
        "correo_fecha": ["correo", "fecha_solicitud"],
        "correo_fecha_programa_modalidad_periodo": ["correo", "fecha_solicitud", "programa", "modalidad", "periodo_academico"],
    }
    indices = {}
    for name, cols in probes.items():
        idx = defaultdict(list)
        for i, r in enumerate(base, start=2):
            sig = signature(r, cols)
            if sig is not None:
                idx[sig].append((i, r))
        indices[name] = idx
    payload_cols = [c for c in expected if c not in {"registro_id", "aspirante_id"}]
    # La representación tipada de ausencias se compara; los motivos de origen
    # siguen en las fuentes. Esta igualdad no define identidad de solicitud.
    payload_index = defaultdict(list)
    no_dates_index = defaultdict(list)
    no_dates_cols = [c for c in payload_cols if not c.startswith("fecha_")]
    for i, r in enumerate(base, start=2):
        payload_index[tuple(normalize(r[c], c) for c in payload_cols)].append((i, r))
        no_dates_index[tuple(normalize(r[c], c) for c in no_dates_cols)].append((i, r))
    oracle_detail = []
    date_details = []
    for row in oracle:
        detail = {"registro_id_oracle": row["registro_id"], "aspirante_id_oracle": row["aspirante_id"], "correo": row["correo"], "fecha_solicitud": row["fecha_solicitud"], "programa": row["programa"]}
        for name, cols in probes.items():
            sig = signature(row, cols)
            matches = indices[name].get(sig, []) if sig is not None else []
            detail[name + "_filas"] = len(matches)
            detail[name + "_ids_distintos"] = len({r["registro_id"] for _, r in matches})
            if name == "correo_fecha_programa_modalidad_periodo":
                detail["candidatos_registro_id_principal"] = ", ".join(sorted({r["registro_id"] for _, r in matches}))
        payload_matches = payload_index.get(tuple(normalize(row[c], c) for c in payload_cols), [])
        detail["coincidencias_13_columnas_sin_ids"] = len(payload_matches)
        detail["ids_con_coincidencia_13_columnas"] = ", ".join(sorted({r["registro_id"] for _, r in payload_matches}))
        no_dates_matches = no_dates_index.get(tuple(normalize(row[c], c) for c in no_dates_cols), [])
        detail["coincidencias_11_columnas_sin_ids_ni_fechas"] = len(no_dates_matches)
        detail["ids_distintos_coincidencia_11_columnas"] = len({r["registro_id"] for _, r in no_dates_matches})
        detail["fecha_solicitud_igual_entre_candidatos_11"] = any(date(r["fecha_solicitud"]) == row["fecha_solicitud"] for _, r in no_dates_matches)
        detail["fecha_matricula_igual_entre_candidatos_11"] = any(date(r["fecha_matricula"], "fecha_matricula") == row["fecha_matricula"] for _, r in no_dates_matches)
        detail["posible_intercambio_dia_mes_solicitud"] = False
        for pos, r in no_dates_matches:
            source_date = date(r["fecha_solicitud"])
            swapped = False
            if source_date and source_date != row["fecha_solicitud"]:
                x, y = Date.fromisoformat(source_date), Date.fromisoformat(row["fecha_solicitud"])
                swapped = x.day <= 12 and x.year == y.year and x.day == y.month and x.month == y.day
            detail["posible_intercambio_dia_mes_solicitud"] |= swapped
            date_details.append({"registro_id_oracle": row["registro_id"], "registro_id_candidato_principal": r["registro_id"], "fila_csv": pos, "fecha_solicitud_original": r["fecha_solicitud"], "fecha_solicitud_interpretada": source_date, "fecha_solicitud_oracle": row["fecha_solicitud"], "fecha_matricula_original": r["fecha_matricula"], "fecha_matricula_oracle": row["fecha_matricula"], "compatible_intercambio_dia_mes": swapped})
        oracle_detail.append(detail)
    write_csv(OUT / "relacion_oracle_principal.csv", oracle_detail)
    write_csv(OUT / "fechas_oracle_candidatos_revision.csv", date_details)
    oracle_relation = {name: {"filas_oracle_con_match": sum(d[name + "_filas"] > 0 for d in oracle_detail), "filas_oracle_sin_match": sum(d[name + "_filas"] == 0 for d in oracle_detail), "filas_oracle_multiples_filas_principal": sum(d[name + "_filas"] > 1 for d in oracle_detail), "filas_oracle_multiples_registro_id": sum(d[name + "_ids_distintos"] > 1 for d in oracle_detail)} for name in probes}
    oracle_relation["ids_iguales_principal"] = sum(r["registro_id"] in by_id for r in oracle)
    oracle_relation["filas_coinciden_13_columnas_sin_ids"] = sum(d["coincidencias_13_columnas_sin_ids"] > 0 for d in oracle_detail)
    oracle_relation["filas_coinciden_11_columnas_sin_ids_ni_fechas"] = sum(d["coincidencias_11_columnas_sin_ids_ni_fechas"] > 0 for d in oracle_detail)
    oracle_relation["multiples_ids_principal_en_sonda_11_columnas"] = sum(d["ids_distintos_coincidencia_11_columnas"] > 1 for d in oracle_detail)
    oracle_relation["coinciden_fecha_solicitud_entre_candidatos_11"] = sum(d["fecha_solicitud_igual_entre_candidatos_11"] for d in oracle_detail)
    oracle_relation["coinciden_fecha_matricula_entre_candidatos_11"] = sum(d["fecha_matricula_igual_entre_candidatos_11"] for d in oracle_detail)
    oracle_relation["solicitud_compatible_intercambio_dia_mes_entre_candidatos_11"] = sum(d["posible_intercambio_dia_mes_solicitud"] for d in oracle_detail)
    oracle_relation["solicitudes_posteriores_a_referencia_2026_10_24"] = sum(r["fecha_solicitud"] > "2026-10-24" for r in oracle)
    oracle_relation["programas_sin_especificar"] = sum(r["programa"] == "Sin especificar" for r in oracle)
    oracle_relation["filas_oracle_y_crm_coinciden_sonda_evento"] = sum(signature(r, probes["correo_fecha_programa_modalidad_periodo"]) in {signature(c, probes["correo_fecha_programa_modalidad_periodo"]) for c in crm} for r in oracle if signature(r, probes["correo_fecha_programa_modalidad_periodo"]) is not None)
    all_frequencies, all_quality, all_numeric = [], [], []
    for source, p in profiles.items():
        for col, counts in p["frecuencias"].items():
            all_frequencies.extend({"fuente": source, "columna": col, "valor_original": v, "cantidad": n, "porcentaje": round(100 * n / p["filas"], 2)} for v, n in counts.items())
        all_quality.extend({"fuente": source, "columna": col, **stats} for col, stats in p["calidad"].items())
        all_numeric.extend({"fuente": source, "columna": col, **{k: v for k, v in stats.items() if k != "no_interpretables"}, "no_interpretables": json.dumps(stats["no_interpretables"], ensure_ascii=False)} for col, stats in p["numericas"].items())
    write_csv(OUT / "frecuencias_por_fuente.csv", all_frequencies)
    write_csv(OUT / "calidad_por_fuente.csv", all_quality)
    write_csv(OUT / "estadisticas_numericas.csv", all_numeric)
    result = {"generado_en": datetime.now(ZoneInfo("America/Bogota")).isoformat(), "oracle_consultado_en": snapshot["consultado_en"], "oracle_lectura_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(), "alcance": "SELECT Oracle y archivos originales; PostgreSQL estaba detenido al consultar su estado. Sin limpieza ni integración aplicada.", "metodo_sondas": "Recorte y mayúsculas sin tildes para categorías; correo recortado en minúsculas; periodos con equivalencias explícitas; fechas y números interpretables. Los faltantes tipados se comparan como ausencia, sin resolver su motivo. Coincidencias no acreditan identidad ni autorizan fusiones.", "perfiles": profiles, "relaciones": {"crm_principal": crm_relation, "programas_principal": program_relations, "oracle_principal": oracle_relation}, "compatibilidad_vista": {"mismas_15_columnas_y_orden": True, "metadatos_oracle": snapshot["columnas"], "columnas_tecnicas_postgresql_excluidas": ["fila_origen_csv", "origen_sha256", "datos_originales", "observaciones_tipado"]}}
    (OUT / "analisis_completo.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result["relaciones"], ensure_ascii=False, indent=2))
    print("PERFILES RESUMIDOS")
    print(json.dumps({k: {c: v for c, v in p.items() if c not in {"calidad", "frecuencias", "nombres"}} for k, p in profiles.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
