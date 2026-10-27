"""Verifica carga repetible y detección de alteraciones en una base aislada."""

import os
import unittest

import psycopg
from dotenv import dotenv_values

from scripts.cargar_base_unificada import ROOT, cargar


@unittest.skipUnless(os.environ.get('ADMISIONES_TEST_DATABASE', '').startswith('admisiones_validacion_'),
                     'Requiere una base PostgreSQL de validación aislada explícita')
class CargaAnaliticaTest(unittest.TestCase):
    def test_repeticion_no_duplica_y_detecta_alteraciones(self):
        env = dotenv_values(ROOT / '.env')
        with psycopg.connect(host='127.0.0.1', port=env.get('POSTGRES_PORT', '5433'),
                             dbname=os.environ['ADMISIONES_TEST_DATABASE'], user='analista',
                             password=env['POSTGRES_PASSWORD']) as conn:
            with conn.transaction(force_rollback=True):
                first = cargar(connection=conn, guardar_reporte=False)
                second = cargar(connection=conn, guardar_reporte=False)
                self.assertEqual(first['carga_id'], second['carga_id'])
                self.assertIn('existente', second['accion'])
                self.assertTrue(all(second['controles'].values()))
                with conn.cursor() as cur:
                    cur.execute('SELECT count(*) FROM analitica.registros')
                    self.assertEqual(cur.fetchone(), (5500,))
                    cur.execute("UPDATE analitica.registros SET puntaje_admision=0 WHERE registro_id='REG004364'")
                with self.assertRaisesRegex(ValueError, '5500_filas_todos_los_valores_iguales'):
                    cargar(connection=conn, guardar_reporte=False)
