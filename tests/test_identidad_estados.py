import unittest
from analitica_admisiones.identidad_estados import clasificar_aspirante


class ClasificacionAspiranteTest(unittest.TestCase):
    def test_matricula_en_alguna_solicitud_sin_inferir_actualidad(self):
        self.assertEqual(clasificar_aspirante(['Retirado','Matriculado','Admitido']),
                         'Matrícula registrada en alguna solicitud')

    def test_admitido_sin_matricula(self):
        self.assertEqual(clasificar_aspirante(['Admitido','Inscrito']),
                         'Admitido sin matrícula registrada')

    def test_no_inventa_admision_desde_otros_estados(self):
        self.assertEqual(clasificar_aspirante(['Retirado','No admitido','Inscrito']),
                         'Otros estados sin admisión o matrícula registrada')

    def test_repetir_un_estado_no_cambia_clasificacion(self):
        self.assertEqual(clasificar_aspirante(['Admitido']*4),clasificar_aspirante(['Admitido']))
