"""Verifica una comparación conocida de canales con composición desequilibrada."""

import unittest
import pandas as pd

from analitica_admisiones.analisis_administrativo import AnalisisAdministrativo


class CanalHarness(AnalisisAdministrativo):
    def __init__(self, rows):
        self.df = pd.DataFrame(rows)
        self.rules = {'grupos_pequenos_menores_de':30}
        self.tables = {}

    def save(self, name, frame):
        self.tables[name] = frame.copy()
        return frame


def example():
    rows = []
    for channel, program, amount, enrolled in [
        ('A','Programa 1',8,1), ('A','Programa 2',2,0),
        ('B','Programa 1',2,1), ('B','Programa 2',8,0)]:
        rows.extend({'canal_captacion':channel,'programa':program,'modalidad':'Virtual',
                     'periodo_academico':20261,'matriculado':enrolled} for _ in range(amount))
    return rows


class ComparacionCanalesTest(unittest.TestCase):
    def test_misma_proporcion_en_estratos_no_inventa_ventaja_ajustada(self):
        analysis = CanalHarness(example())
        result = analysis.canales_comparables().set_index('canal_captacion')
        self.assertEqual(result.loc['A','proporcion_bruta_pct'],80)
        self.assertEqual(result.loc['B','proporcion_bruta_pct'],20)
        self.assertEqual(result.loc['A','proporcion_estandarizada_descriptiva_pct'],50)
        self.assertEqual(result.loc['B','proporcion_estandarizada_descriptiva_pct'],50)
        self.assertEqual(analysis.tables['pesos_estratos_comunes'].peso_comun.sum(),1)

    def test_estrato_sin_todos_los_canales_queda_fuera_solo_del_soporte(self):
        rows = example() + [{'canal_captacion':'A','programa':'Solo A','modalidad':'Virtual',
                             'periodo_academico':20261,'matriculado':0}]
        analysis = CanalHarness(rows)
        result = analysis.canales_comparables().set_index('canal_captacion')
        self.assertEqual(len(analysis.df),21)
        self.assertEqual(result.loc['A','registros_totales'],11)
        self.assertEqual(result.loc['A','registros_soporte_comun'],10)
        self.assertEqual(result.loc['A','proporcion_estandarizada_descriptiva_pct'],50)
        self.assertEqual(result.loc['A','estratos_comunes'],2)
