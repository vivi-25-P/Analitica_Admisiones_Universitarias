"""Controles de fidelidad del lector y del perfil, sin acceso a Docker."""

import csv
from pathlib import Path
import tempfile
import unittest

from analitica_admisiones.profiling import numeric_summary, read_original, summarize


class PreservacionTest(unittest.TestCase):
    def test_preserva_espacios_vacios_comas_y_duplicados(self):
        rows = [['R1', 'Cali ', '', 'texto, con coma'],
                ['R1', 'Cali ', '', 'texto, con coma'],
                ['R2', 'CALI', ' ', 'No aplica']]
        headers = ['registro_id', 'ciudad', 'fecha', 'nota']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'origen.csv'
            with path.open('w', encoding='utf-8-sig', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(headers)
                writer.writerows(rows)
            loaded_headers, loaded = read_original(path)
        self.assertEqual(loaded_headers, headers)
        self.assertEqual(loaded, rows)
        profile = summarize(headers, loaded)
        self.assertEqual(profile['duplicados_exactos_adicionales'], 1)
        self.assertEqual(profile['campos'][2]['vacios_exactos'], 2)
        self.assertEqual(profile['campos'][2]['solo_espacios'], 1)

    def test_no_interpretables_no_se_convierten_a_cero(self):
        profile = numeric_summary(['', 'por definir', '10', '20', 'NaN', 'Infinity'])
        self.assertEqual(profile['interpretables'], 2)
        self.assertEqual(profile['promedio'], '15')
        self.assertEqual(profile['vacios'], 1)
        self.assertEqual(sum(profile['no_interpretables'].values()), 3)

    def test_rechaza_filas_incompletas(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'malformado.csv'
            path.write_text('registro_id,valor\nR1\n')
            with self.assertRaises(ValueError):
                read_original(path)
