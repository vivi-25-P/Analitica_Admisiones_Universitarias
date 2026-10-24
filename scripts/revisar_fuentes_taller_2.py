"""Inspección de archivos del Taller 2. No ejecuta SQL ni limpia las fuentes.

Usa únicamente la biblioteca estándar. Las claves normalizadas son sondas
de comparación en memoria y no constituyen reglas de integración aprobadas.
"""

import csv
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative):
    return list(csv.DictReader(io.StringIO((ROOT / relative).read_text(encoding="utf-8-sig"))))


def key(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.strip().upper()) if unicodedata.category(c) != "Mn")


def split_sql_values(text):
    """Separa literales y funciones del export recibido sin evaluarlos."""
    values, start, depth, quoted, i = [], 0, 0, False, 0
    while i < len(text):
        char = text[i]
        if char == "'":
            if quoted and i + 1 < len(text) and text[i + 1] == "'":
                i += 2
                continue
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                values.append(text[start:i].strip())
                start = i + 1
        i += 1
    assert not quoted and depth == 0
    values.append(text[start:].strip())
    return [None if v.lower() == "null" else v[1:-1].replace("''", "'") if v.startswith("'") and v.endswith("'") else v for v in values]


def main():
    manifest = json.loads((ROOT / "docs/referencias/taller_2/integridad.json").read_text(encoding="utf8"))
    for path, info in manifest.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == info["sha256"], path
    original = read_csv("data/raw/Caso2_Admisiones_Universitarias.csv")
    programs = read_csv("data/raw/taller_2/Caso2 Programas.csv")
    crm = read_csv("data/raw/taller_2/Caso2 CRM Admisiones.csv")
    sql = (ROOT / "sql/fuentes/taller_2/caso2.sql").read_text(encoding="cp1252")
    tables = defaultdict(list)
    for match in re.finditer(r"^Insert into CASO2\.(\w+) \(([^\n]+?)\) values \(([^\n]+)\);\s*$", sql, re.M | re.I):
        columns = [c.strip() for c in match[2].split(",")]
        values = split_sql_values(match[3])
        assert len(columns) == len(values)
        tables[match[1]].append(dict(zip(columns, values)))
    assert sum(map(len, tables.values())) == len(re.findall(r"^Insert into ", sql, re.M | re.I))
    by_id = defaultdict(list)
    for row in original:
        by_id[row["registro_id"]].append(row)
    common_columns = [c for c in original[0] if c not in {"registro_id", "aspirante_id", "valor_matricula_cop"}]
    crm_counts = Counter()
    differing = Counter()
    for row in crm:
        parts = row["registro_aspirante_crm"].split("|")
        if len(parts) != 2:
            crm_counts["clave_no_separable"] += 1
            continue
        reg, asp = [p.strip() for p in parts]
        crm_counts["aspirante_literal_nan"] += asp.lower() == "nan"
        candidates = by_id.get(reg, [])
        crm_counts["registro_id_en_principal" if candidates else "registro_id_nuevo"] += 1
        matches = [r for r in candidates if r["aspirante_id"] == asp]
        crm_counts["par_registro_aspirante_en_principal"] += bool(matches)
        crm_counts["coincide_con_una_fila_en_columnas_compartidas"] += any(all(r[c] == row[c] for c in common_columns) for r in matches)
        crm_counts["matricula_base_igual_a_valor_original"] += any(r["valor_matricula_cop"] == row["matricula_base_cop"] for r in matches)
        crm_counts["importe_principal_vacio_con_base_crm_disponible_en_pares_coincidentes"] += bool(matches) and all(not r["valor_matricula_cop"].strip() for r in matches) and bool(row["matricula_base_cop"].strip())
        if matches:
            for c in common_columns:
                differing[c] += all(r[c] != row[c] for r in matches)
    program_groups = defaultdict(list)
    for row in programs:
        program_groups[key(row["programa"])].append(row)
    normalized_counts = Counter(key(r["programa"]) for r in programs if key(r["programa"]))
    potential_join_rows = sum(max(1, normalized_counts[key(r["programa"])] if key(r["programa"]) else 0) for r in original)
    oracle_requests = tables["C2_SOLICITUDES"]
    oracle_people = tables["C2_ASPIRANTES"]
    original_emails = {r["correo"].strip().lower() for r in original if r["correo"].strip()}
    foreign_keys = {"ASPIRANTE_ID": "C2_ASPIRANTES", "PROGRAMA_ID": "C2_PROGRAMAS", "CANAL_ID": "C2_CANALES", "ASESOR_ID": "C2_ASESORES"}
    broken_fk = {col: sum(r[col] not in {d[col] for d in tables[table]} for r in oracle_requests) for col, table in foreign_keys.items()}
    result = {
        "alcance": "Inspección estática. Sin limpieza, cargas SQL, Oracle ni Power Query ejecutados.",
        "integridad_archivos": manifest,
        "fuentes": {
            "principal": {"filas": len(original), "columnas": len(original[0])},
            "programas": {"filas": len(programs), "columnas": len(programs[0]), "columnas_nombres": list(programs[0]), "filas_con_programa_en_blanco": sum(not r["programa"].strip() for r in programs), "claves_normalizadas_repetidas": {k: v for k, v in program_groups.items() if k and len(v) > 1}, "simulacion_left_merge_solo_programa_normalizado_sin_claves_vacias": potential_join_rows},
            "crm": {"filas": len(crm), "columnas": len(crm[0]), "columnas_nombres": list(crm[0]), "claves_compuestas_distintas": len({r["registro_aspirante_crm"] for r in crm}), "solapamiento": dict(crm_counts), "diferencias_en_columnas_compartidas": dict(differing), "vacios_o_espacios": {c: sum(not r[c].strip() for r in crm) for c in crm[0]}},
            "oracle_export": {"codificacion_lectura": "cp1252", "tablas": {t: {"filas_insertadas_en_script": len(rs), "columnas": len(rs[0]), "columnas_nombres": list(rs[0])} for t, rs in tables.items()}, "registros_id_solapados_principal": sum(r["REGISTRO_ID"] in by_id for r in oracle_requests), "aspirantes_con_correo_en_principal": sum(bool(r["CORREO"]) and r["CORREO"].strip().lower() in original_emails for r in oracle_people), "referencias_sin_correspondencia_en_export": broken_fk, "registro_id_distintos": len({r["REGISTRO_ID"] for r in oracle_requests}), "sentencias_to_date": len(re.findall(r"to_date\(", sql, re.I))}
        }
    }
    out = ROOT / "reports/taller_2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "revision_fuentes.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result["fuentes"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
