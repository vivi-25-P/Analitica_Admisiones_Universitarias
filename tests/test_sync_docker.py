"""Pruebas reales reservadas a un proyecto Docker de validación aislado."""
import os
import subprocess
import unittest

from scripts.sincronizar_bd import Migration, apply_migration, psql
import hashlib


def version(name, sql):
    return Migration(name,int(name[:3]),hashlib.sha256(sql.encode()).hexdigest(),sql)


@unittest.skipUnless(
    os.environ.get('ADMISIONES_TEST_DOCKER')=='1'
    and os.environ.get('COMPOSE_PROJECT_NAME','').startswith('admisiones_validacion_'),
    'Requiere una base de validación aislada y activación explícita.',
)
class SincronizacionDockerTest(unittest.TestCase):
    def test_version_nueva_se_aplica_una_sola_vez(self):
        item=version('990_prueba_repetible.sql',
            'CREATE TABLE public.prueba_sincronizacion(id INTEGER PRIMARY KEY); '
            'INSERT INTO public.prueba_sincronizacion VALUES (1);')
        apply_migration(item)
        apply_migration(item)
        count=psql('COPY (SELECT COUNT(*) FROM public.prueba_sincronizacion) TO STDOUT;').strip()
        self.assertEqual(count,'1')

    def test_falla_y_revierte_si_altera_original(self):
        item=version('991_prueba_original.sql',
            'CREATE TABLE public.prueba_reversion_original(id INTEGER); '
            "UPDATE public.admisiones_original SET programa='ALTERADO' WHERE registro_id='REG004364';")
        with self.assertRaises(subprocess.CalledProcessError):apply_migration(item)
        result=psql("COPY (SELECT to_regclass('public.prueba_reversion_original') IS NULL) TO STDOUT;").strip()
        self.assertEqual(result,'t')
        applied=psql("COPY (SELECT COUNT(*) FROM public.migraciones_proyecto WHERE archivo='991_prueba_original.sql') TO STDOUT;").strip()
        self.assertEqual(applied,'0')

    def test_falla_y_revierte_si_altera_tipado(self):
        item=version('992_prueba_tipado.sql',
            'CREATE TABLE public.prueba_reversion_tipado(id INTEGER); '
            "UPDATE public.admisiones_tipadas SET programa='ALTERADO' WHERE fila_origen_csv=2;")
        with self.assertRaises(subprocess.CalledProcessError):apply_migration(item)
        result=psql("COPY (SELECT to_regclass('public.prueba_reversion_tipado') IS NULL) TO STDOUT;").strip()
        self.assertEqual(result,'t')
