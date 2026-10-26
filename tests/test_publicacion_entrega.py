import tempfile
import unittest
from pathlib import Path

from analitica_admisiones.publicacion_entrega import publicar_excel, huella


class PublicacionTest(unittest.TestCase):
    def test_conserva_respaldos_y_deja_un_solo_excel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'fuente.xlsx'
            source.write_bytes(b'excel vigente')
            delivery = root / 'deliverables'
            old = delivery / 'v1_1'
            old.mkdir(parents=True)
            (delivery / 'BaseUnificada_Entregable.xlsx').write_bytes(b'anterior')
            (old / 'BaseUnificada_Entregable.csv').write_bytes(b'csv anterior')
            result = publicar_excel(root, source, huella(source))
            self.assertEqual(list(delivery.iterdir()), [delivery / source.name.replace('fuente', 'BaseUnificada_Entregable')])
            self.assertEqual((delivery / 'BaseUnificada_Entregable.xlsx').read_bytes(), source.read_bytes())
            self.assertEqual(len(result['copias_anteriores_archivadas']), 2)
            for item in result['copias_anteriores_archivadas']:
                self.assertEqual(huella(root / item['archivo_interno']), item['sha256'])

    def test_rechaza_fuente_alterada_sin_tocar_entrega(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'fuente.xlsx'
            source.write_bytes(b'datos')
            with self.assertRaises(ValueError):
                publicar_excel(root, source, 'incorrecta')
            self.assertFalse((root / 'deliverables').exists())

    def test_no_retira_archivos_desconocidos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'fuente.xlsx'
            source.write_bytes(b'datos')
            old = root / 'deliverables/v1_1'
            old.mkdir(parents=True)
            (old / 'trabajo_personal.xlsx').write_bytes(b'conservar')
            with self.assertRaises(ValueError):
                publicar_excel(root, source, huella(source))
            self.assertEqual((old / 'trabajo_personal.xlsx').read_bytes(), b'conservar')
