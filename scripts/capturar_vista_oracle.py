"""Lee la vista y sus metadatos con SELECT y guarda evidencia para análisis."""

import csv
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from preparar_oracle import json_rows, PASSWORDS

ROOT = Path(__file__).resolve().parents[1]


def read_view():
    values = {}
    for line in (ROOT / ".env").read_text(encoding="utf8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip()
    password = values["ORACLE_CASO2_PASSWORD"]
    PASSWORDS.append(password)
    with (ROOT / "data/raw/Caso2_Admisiones_Universitarias.csv").open(encoding="utf-8-sig") as handle:
        headers = next(csv.reader(handle))
    fields = []
    for col in headers:
        expression = f"TO_CHAR({col}, 'YYYY-MM-DD')" if col.startswith("fecha_") else col
        fields.append(f"'{col}' VALUE {expression}")
    rows = json_rows(f"select json_object({', '.join(fields)} RETURNING CLOB) from CASO2.V_ADMISIONES_BASE;", password)
    meta = json_rows("select json_object('columna' value column_name, 'tipo' value data_type, 'orden' value column_id) from user_tab_columns where table_name='V_ADMISIONES_BASE' order by column_id;", password)
    assert rows and all(set(row) == set(headers) for row in rows)
    assert [col["columna"].lower() for col in meta] == headers
    rows = [{col: row[col] for col in headers} for row in rows]
    return {"consultado_en": datetime.now(ZoneInfo("America/Bogota")).isoformat(), "origen": "Consulta SELECT a CASO2.V_ADMISIONES_BASE; fechas serializadas como YYYY-MM-DD", "columnas": meta, "filas": rows}


def main():
    result = read_view()
    out = ROOT / "reports/taller_2/oracle_vista_lectura.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    temporary.replace(out)
    print(f"Vista consultada: {len(result['filas'])} filas y {len(result['columnas'])} columnas. Evidencia: {out.name}")


if __name__ == "__main__":
    main()
