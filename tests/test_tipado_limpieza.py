"""Casos límite de interpretación que no deben resolverse por aproximación."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analitica_admisiones.tipado_limpieza import interpretar_fecha, interpretar_cop, interpretar_entero, mostrar_cop


class TipadoLimpiezaTest(unittest.TestCase):
    def test_fecha_iso_y_bisiesto(self):
        self.assertEqual(interpretar_fecha("2024-02-29").valor, date(2024, 2, 29))
        with self.assertRaises(ValueError):
            interpretar_fecha("2025-02-29")

    def test_convenciones_ambiguas_no_se_intercambian(self):
        a = interpretar_fecha("04/10/2025")
        b = interpretar_fecha("04-10-2025")
        self.assertEqual(a.valor, date(2025, 10, 4))
        self.assertEqual(b.valor, date(2025, 4, 10))
        self.assertTrue(a.dia_mes_ambiguo and b.dia_mes_ambiguo)

    def test_abreviatura_independiente_de_locale(self):
        self.assertEqual(interpretar_fecha("12-Apr-2026").valor, date(2026, 4, 12))
        with self.assertRaises(ValueError):
            interpretar_fecha("12-Ene-2026")

    def test_no_ambiguedad_espuria(self):
        self.assertFalse(interpretar_fecha("2025/02/12").dia_mes_ambiguo)
        self.assertFalse(interpretar_fecha("25/02/2025").dia_mes_ambiguo)
        self.assertFalse(interpretar_fecha("04/04/2025").dia_mes_ambiguo)

    def test_dinero_exacto_sin_float(self):
        self.assertEqual(interpretar_cop("2200000.1"), Decimal("2200000.10"))
        self.assertEqual(interpretar_cop("3807591"), Decimal("3807591.00"))

    def test_no_redondea_ni_adivina_separadores(self):
        for value in ["1.001", "2.200.000,00", "2,200,000.00", "NaN", "Infinity"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                interpretar_cop(value)

    def test_entero_no_trunca(self):
        self.assertEqual(interpretar_entero("2.0"), 2)
        with self.assertRaises(ValueError):
            interpretar_entero("2.5")

    def test_presentacion_colombiana_separada_del_valor(self):
        value = interpretar_cop("2200000.1")
        self.assertEqual(mostrar_cop(value), "COP 2.200.000,10")
        self.assertEqual(value, Decimal("2200000.10"))


if __name__ == "__main__":
    unittest.main()
