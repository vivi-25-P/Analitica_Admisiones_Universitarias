"""Interpretación explícita de fechas y números para L04, sin imputación."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re


@dataclass(frozen=True)
class FechaInterpretada:
    valor: date
    formato: str
    dia_mes_ambiguo: bool = False


def interpretar_fecha(texto):
    """Aplica las cinco convenciones documentadas, sin heurística regional."""
    texto = str(texto).strip()
    if match := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texto):
        year, month, day = map(int, match.groups())
        return FechaInterpretada(date(year, month, day), "AAAA-MM-DD")
    if match := re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", texto):
        year, month, day = map(int, match.groups())
        return FechaInterpretada(date(year, month, day), "AAAA/MM/DD")
    if match := re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", texto):
        day, month, year = map(int, match.groups())
        return FechaInterpretada(date(year, month, day), "DD/MM/AAAA", day <= 12 and day != month)
    if match := re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", texto):
        month, day, year = map(int, match.groups())
        return FechaInterpretada(date(year, month, day), "MM-DD-AAAA", day <= 12 and day != month)
    if match := re.fullmatch(r"(\d{2})-([A-Za-z]{3})-(\d{4})", texto):
        months = {name: i for i, name in enumerate(
            ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
        day, name, year = match.groups()
        if name.lower() not in months:
            raise ValueError("Abreviatura de mes no reconocida en la convención de origen")
        return FechaInterpretada(date(int(year), months[name.lower()], int(day)), "DD-Mmm-AAAA")
    raise ValueError("Formato de fecha sin regla de interpretación")


def interpretar_decimal(texto):
    """El formato de intercambio usa punto decimal y no separadores de miles."""
    texto = str(texto).strip()
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", texto):
        raise ValueError("Se esperaba número con punto decimal y sin separadores de miles")
    value = Decimal(texto)
    if not value.is_finite():
        raise ValueError("El número no es finito")
    return value


def interpretar_cop(texto):
    value = interpretar_decimal(texto)
    try:
        scaled = value.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError("Importe fuera de la precisión admitida") from exc
    if scaled != value:
        raise ValueError("Importe con fracción inferior a un centavo; requiere decisión, no redondeo automático")
    return scaled


def interpretar_entero(texto):
    value = interpretar_decimal(texto)
    if value != value.to_integral_value():
        raise ValueError("El valor no representa un entero exacto")
    return int(value)


def mostrar_cop(value):
    """Presentación colombiana para tablas, sin transformar la medida en texto."""
    if value is None:
        return "Sin importe"
    return "COP " + format(value, ",.2f").translate(str.maketrans({",": ".", ".": ","}))
