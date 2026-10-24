"""Planificación de migraciones sin conexiones a Docker."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.sincronizar_bd import Migration, discover, plan


def migration(name, sql='SELECT 1;'):
    return Migration(name,int(name[:3]),hashlib.sha256(sql.encode()).hexdigest(),sql)


class MigracionesTest(unittest.TestCase):
    def test_solo_devuelve_pendientes(self):
        first,second=migration('001_inicial.sql'),migration('002_siguiente.sql')
        self.assertEqual(plan([first,second],{first.name:first.digest}),[second])
        self.assertEqual(plan([first,second],{first.name:first.digest,second.name:second.digest}),[])

    def test_rechaza_editar_una_migracion_aplicada(self):
        old=migration('001_inicial.sql');changed=migration('001_inicial.sql','SELECT 2;')
        with self.assertRaises(ValueError):plan([changed],{old.name:old.digest})

    def test_rechaza_migracion_desaparecida_y_orden_anterior(self):
        first,second=migration('001_inicial.sql'),migration('002_siguiente.sql')
        with self.assertRaises(ValueError):plan([second],{first.name:first.digest})
        with self.assertRaises(ValueError):plan([first,second],{second.name:second.digest})

    def test_rechaza_version_duplicada_y_nombre_invalido(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            (path/'001_uno.sql').write_text('SELECT 1;')
            (path/'001_dos.sql').write_text('SELECT 2;')
            with self.assertRaises(ValueError):discover(path)
            (path/'001_dos.sql').unlink()
            (path/'sin_version.sql').write_text('SELECT 1;')
            with self.assertRaises(ValueError):discover(path)
