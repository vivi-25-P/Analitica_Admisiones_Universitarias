"""Prepara y verifica el Oracle del Taller 2 sin tocar PostgreSQL ni los CSV."""

import csv
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
from zoneinfo import ZoneInfo

from revisar_fuentes_taller_2 import split_sql_values

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", "compose.oracle.yaml"]
PASSWORDS = []


def run(args, text=None):
    result = subprocess.run(args, cwd=ROOT, input=text, text=True, encoding="utf8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout
    for password in PASSWORDS:
        output = output.replace(password, "[credencial oculta]")
    if result.returncode:
        raise RuntimeError(output[-6000:])
    return output


def environment():
    path = ROOT / ".env"
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    additions = {}
    for name in ("ORACLE_PASSWORD", "ORACLE_CASO2_PASSWORD"):
        if name not in values:
            additions[name] = "Aa1" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(29))
        value = additions.get(name, values.get(name))
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{11,63}", value):
            raise ValueError(f"{name} debe tener de 12 a 64 caracteres alfanuméricos y empezar por letra. No se cambia una clave existente automáticamente.")
        PASSWORDS.append(value)
    if "ORACLE_PORT" not in values:
        additions["ORACLE_PORT"] = "1521"
    if additions:
        with path.open("a", encoding="utf8") as handle:
            handle.write("\n# Oracle local del Taller 2\n")
            handle.writelines(f"{k}={v}\n" for k, v in additions.items())
    values.update(additions)
    return values


def sqlplus(sql, admin=False, password=None):
    connection = "connect / as sysdba\nalter session set container = FREEPDB1;" if admin else f'connect CASO2/"{password}"@//localhost:1521/FREEPDB1'
    script = f"set echo off verify off feedback off heading off pagesize 0 linesize 32767 trimspool on long 100000 longchunksize 100000\nset define off\nwhenever oserror exit failure\nwhenever sqlerror exit failure rollback\n{connection}\n{sql}\nexit success\n"
    return run(COMPOSE + ["exec", "-T", "-e", "NLS_LANG=AMERICAN_AMERICA.AL32UTF8", "oracle", "sqlplus", "-s", "/nolog"], script)


def json_rows(sql, password):
    output = sqlplus(sql, password=password)
    return [json.loads(line) for line in output.splitlines() if line.strip().startswith("{")]


def source_tables(sql):
    tables = defaultdict(list)
    for m in re.finditer(r"^Insert into CASO2\.(\w+) \(([^\n]+?)\) values \(([^\n]+)\);\s*$", sql, re.M | re.I):
        cols = [c.strip() for c in m[2].split(",")]
        vals = split_sql_values(m[3])
        assert len(cols) == len(vals)
        tables[m[1]].append(dict(zip(cols, vals)))
    assert sum(map(len, tables.values())) == len(re.findall(r"^Insert into ", sql, re.M | re.I))
    return tables


def canonical(row, numeric):
    result = []
    for col, value in row.items():
        if isinstance(value, str) and value.lower().startswith("to_date("):
            m = re.fullmatch(r"to_date\('(\d{2})/(\d{2})/(\d{2})','DD/MM/RR'\)", value, re.I)
            if not m:
                raise ValueError("Formato de fecha del export no reconocido")
            day, month, year = map(int, m.groups())
            # El export actual contiene fechas de 2025 y 2026. No generalizar RR.
            if year not in (25, 26):
                raise ValueError("Revisar siglo del año RR antes de cargar")
            value = datetime(2000 + year, month, day).date().isoformat()
        if col in numeric and value is not None:
            value = Decimal(str(value))
        result.append(value)
    return tuple(result)


def main():
    env = environment()
    source = ROOT / "sql/fuentes/taller_2/caso2.sql"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = json.loads((ROOT / "docs/referencias/taller_2/integridad.json").read_text())
    assert digest == manifest["sql/fuentes/taller_2/caso2.sql"]["sha256"]
    export = source.read_text(encoding="cp1252")
    tables = source_tables(export)
    print("Iniciando Oracle y esperando disponibilidad. La primera descarga puede tardar varios minutos.", flush=True)
    run(COMPOSE + ["up", "-d", "--wait", "--wait-timeout", "1200", "oracle"])
    sqlplus("""DECLARE
      n NUMBER;
    BEGIN
      SELECT COUNT(*) INTO n FROM dba_tablespaces WHERE tablespace_name='USERS';
      IF n = 0 THEN
        EXECUTE IMMEDIATE 'CREATE TABLESPACE USERS DATAFILE ''/opt/oracle/oradata/FREE/FREEPDB1/users_taller2.dbf'' SIZE 100M AUTOEXTEND ON NEXT 25M MAXSIZE 1G';
      END IF;
    END;
    /""", admin=True)
    count = sqlplus("select count(*) from dba_users where username = 'CASO2';", admin=True).strip()
    if count == "0":
        sqlplus(f'CREATE USER CASO2 IDENTIFIED BY "{env["ORACLE_CASO2_PASSWORD"]}" DEFAULT TABLESPACE USERS TEMPORARY TABLESPACE TEMP QUOTA 100M ON USERS;\nGRANT CREATE SESSION, CREATE TABLE, CREATE VIEW TO CASO2;', admin=True)
        print("Esquema CASO2 creado.", flush=True)
    elif count != "1":
        raise RuntimeError("No se pudo comprobar el esquema CASO2")
    password = env["ORACLE_CASO2_PASSWORD"]
    existing = sqlplus("select count(*) from user_tables;", password=password).strip()
    if existing == "0":
        # Evita que la regla de siglo RR interprete un archivo futuro silenciosamente.
        for rows in tables.values():
            for row in rows:
                canonical(row, set())
        print("Cargando el export original, sin depuración.", flush=True)
        sqlplus(export + "\nCOMMIT;\n" + f"COMMENT ON TABLE CASO2.C2_SOLICITUDES IS 'Fuente SHA256={digest}';", password=password)
    else:
        markers = json_rows("select json_object('comentario' value comments) from user_tab_comments where table_name='C2_SOLICITUDES';", password)
        if not markers or markers[0]["comentario"] != f"Fuente SHA256={digest}":
            raise RuntimeError("El esquema contiene una carga distinta o incompleta. Se conserva para revisión; no se borra ni se vuelve a insertar.")
        print("La fuente ya está cargada. Se comprobará sin volver a insertar.", flush=True)
    verified = {}
    for table, expected in tables.items():
        numeric = {c for c in expected[0] if c in {"PROGRAMA_ID", "CANAL_ID", "ASESOR_ID", "PUNTAJE_ADMISION", "VALOR_MATRICULA_COP"}}
        fields = [f"'{c}' VALUE TO_CHAR({c}, 'YYYY-MM-DD')" if c.startswith("FECHA_") else f"'{c}' VALUE {c}" for c in expected[0]]
        actual = json_rows(f"select json_object({', '.join(fields)} RETURNING CLOB) from CASO2.{table};", password)
        if Counter(canonical(r, numeric) for r in actual) != Counter(canonical(r, numeric) for r in expected):
            raise RuntimeError(f"La tabla {table} no coincide con el export. No se altera su contenido.")
        verified[table] = len(actual)
    sqlplus((ROOT / "sql/oracle/01_vista_admisiones.sql").read_text(encoding="utf8"), password=password)
    view = json_rows("select json_object('filas' value count(*), 'ids_distintos' value count(distinct registro_id)) from CASO2.V_ADMISIONES_BASE;", password)[0]
    metadata = json_rows("select json_object('columna' value column_name, 'tipo' value data_type, 'orden' value column_id) from user_tab_columns where table_name='V_ADMISIONES_BASE' order by column_id;", password)
    with (ROOT / "data/raw/Caso2_Admisiones_Universitarias.csv").open(encoding="utf-8-sig") as handle:
        expected_columns = next(csv.reader(handle))
    assert [c["columna"].lower() for c in metadata] == expected_columns
    assert view == {"filas": len(tables["C2_SOLICITUDES"]), "ids_distintos": len(tables["C2_SOLICITUDES"])}
    verification = {
        "fecha": datetime.now(ZoneInfo("America/Bogota")).isoformat(),
        "origen_sha256": digest,
        "tablas_verificadas_contra_export": verified,
        "vista": {"nombre": "CASO2.V_ADMISIONES_BASE", **view, "columnas": metadata},
        "conexion": {"host": "localhost", "puerto": int(env["ORACLE_PORT"]), "servicio": "FREEPDB1", "usuario": "CASO2", "clave_en": "ORACLE_CASO2_PASSWORD en .env"},
        "imagen": run(COMPOSE + ["images", "--format", "json"]).strip(),
    }
    out = ROOT / "reports/taller_2/verificacion_oracle.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"tablas": verified, "vista": view, "columnas": len(metadata)}, ensure_ascii=False, indent=2), flush=True)
    print("Oracle listo. Consulta la conexión en docs/oracle_taller_2.md. Las claves quedan solo en .env.", flush=True)


if __name__ == "__main__":
    main()
