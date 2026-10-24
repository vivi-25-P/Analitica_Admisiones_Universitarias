"""El tipado no normaliza categorías, redondea números ni inventa fechas."""
import unittest
from scripts.preparar_tipos import represent


class TipadoTest(unittest.TestCase):
    def test_categorias_y_espacios_no_se_modifican(self):
        for col, value in [('programa',' '),('programa','DERECHO'),('modalidad','presencial'),
                           ('ciudad_residencia','Cali '),('aspirante_id','')]:
            self.assertEqual(represent(col,value),(value,None))

    def test_numero_no_se_redondea(self):
        self.assertEqual(represent('puntaje_admision','70.123456'),('70.123456',None))
        self.assertEqual(represent('valor_matricula_cop','-100.00'),('-100.00',None))

    def test_textos_numericos_no_se_pierden(self):
        for value in ['', 'Pendiente', 'por definir', 'NaN', 'Infinity']:
            typed, note = represent('puntaje_admision',value)
            self.assertIsNone(typed)
            self.assertEqual(note['valor'],value)

    def test_fecha_imposible_no_se_corrige(self):
        typed, note = represent('fecha_solicitud','31/02/2026')
        self.assertIsNone(typed)
        self.assertEqual(note['valor'],'31/02/2026')

    def test_patrones_de_fecha_explicitos(self):
        for value in ['2026-07-28','2026/07/28','28/07/2026','07-28-2026','28-Jul-2026']:
            self.assertEqual(represent('fecha_solicitud',value),('2026-07-28',None))

    def test_no_aplica_no_equivale_a_vacio(self):
        _, empty = represent('fecha_matricula','')
        _, na = represent('fecha_matricula','No aplica')
        self.assertNotEqual(empty['motivo'],na['motivo'])
