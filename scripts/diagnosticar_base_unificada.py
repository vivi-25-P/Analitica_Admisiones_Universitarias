"""Congela el diagnóstico y el inventario de entrada, sin limpiar la base."""

from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from analizar_relaciones_taller_2 import profile

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    path = ROOT / "data/prepared/taller_2/BaseUnificada.csv"
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    metadata = json.loads(path.with_suffix(".metadata.json").read_text(encoding="utf8"))
    assert digest == metadata["archivos"][path.name]["sha256"], "La entrada cambió: crear una nueva versión antes de continuar"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames
        rows = list(reader)
    assert len(rows) == metadata["filas_sin_encabezado"] and headers == metadata["encabezados"]
    result = profile(rows)
    hashes = [hashlib.sha256(json.dumps([r[c] for c in headers], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest() for r in rows]
    counts = Counter(hashes)
    by_id = defaultdict(list)
    for i, row in enumerate(rows, 1):
        by_id[row["registro_id"]].append(i)
    repeated = {key: ids for key, ids in by_id.items() if len(ids) > 1}
    result.update({"generado_en": datetime.now(ZoneInfo("America/Bogota")).isoformat(), "archivo_entrada": str(path.relative_to(ROOT)), "sha256_entrada": digest, "grupos_registro_id_repetido": len(repeated), "filas_en_grupos_registro_id_repetido": sum(map(len, repeated.values())), "repeticiones_adicionales_registro_id": len(rows) - len(by_id), "aspirante_literal_nan": sum(r["aspirante_id"].strip().lower() == "nan" for r in rows), "programa_sin_especificar": sum(r["programa"] == "Sin Especificar" for r in rows), "periodos_equivalentes_sonda": {"20252": sum(r["periodo_academico"] == "2025-2" for r in rows), "20261": sum(r["periodo_academico"] in {"2026-1", "2026-I"} for r in rows), "20262": sum(r["periodo_academico"] in {"2026 II", "2026-2"} for r in rows)}, "alcance": "Diagnóstico e inventario solamente. Las interpretaciones de fechas y equivalencias sirven al perfil; no se modifica la entrada ni se aplican correcciones, exclusiones o fusiones."})
    output = ROOT / "reports/limpieza"
    output.mkdir(parents=True, exist_ok=True)
    (output / "diagnostico_entrada.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    inventory = []
    for i, (row, row_hash) in enumerate(zip(rows, hashes), 1):
        inventory.append({"id_fila_entrada": f"BU{i:06d}", "fila_csv_incluye_encabezado": i + 1, "registro_id": row["registro_id"], "aspirante_id": row["aspirante_id"], "sha256_fila": row_hash, "apariciones_fila_exacta": counts[row_hash], "apariciones_registro_id": len(by_id[row["registro_id"]]), "sha256_archivo_entrada": digest})
    write_csv(output / "inventario_entrada.csv", inventory)
    write_csv(output / "identificadores_repetidos.csv", [{"registro_id": key, "filas_involucradas": len(ids), "id_filas_entrada": " | ".join(f"BU{i:06d}" for i in ids)} for key, ids in repeated.items()])
    assert len({r["id_fila_entrada"] for r in inventory}) == len(rows)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    print(f"Diagnóstico e inventario creados: {len(rows)} filas, {len(headers)} columnas; {len(repeated)} grupos de registro_id repetido. Base sin modificar.")


if __name__ == "__main__":
    main()
