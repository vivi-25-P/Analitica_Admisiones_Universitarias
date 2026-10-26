import unittest
from decimal import Decimal
from datetime import date
from analitica_admisiones.entrega_base_unificada import conciliar_importe, en_ventana_orientativa


class EntregaTest(unittest.TestCase):
    def test_recupera_base_no_total(self):
        value,_=conciliar_importe(None,Decimal('2500000.00'),Decimal('209587.00'),Decimal('2709587.00'))
        self.assertEqual(value,Decimal('2500000.00'))

    def test_conserva_importe_principal_compatible(self):
        value,action=conciliar_importe(Decimal('2500000.00'),Decimal('2500000.00'),Decimal('50.00'),Decimal('2500050.00'))
        self.assertEqual(value,Decimal('2500000.00'))
        self.assertIn('conservado',action)

    def test_no_sobrescribe_conflicto(self):
        with self.assertRaises(ValueError):
            conciliar_importe(Decimal('2200000'),Decimal('2500000'),Decimal('50'),Decimal('2500050'))

    def test_rechaza_total_crm_inconsistente(self):
        with self.assertRaises(ValueError):
            conciliar_importe(None,Decimal('2500000'),Decimal('50'),Decimal('2500000'))

    def test_solicitud_anio_anterior_para_primer_periodo(self):
        self.assertTrue(en_ventana_orientativa(date(2025,10,1),20261))
        self.assertTrue(en_ventana_orientativa(date(2026,1,31),20261))
        self.assertFalse(en_ventana_orientativa(date(2026,5,1),20261))

    def test_solicitud_primer_semestre_para_segundo_periodo(self):
        self.assertTrue(en_ventana_orientativa(date(2026,5,1),20262))
        self.assertTrue(en_ventana_orientativa(date(2026,7,31),20262))
        self.assertFalse(en_ventana_orientativa(date(2026,8,1),20262))

    def test_ventana_no_recalcula_periodo(self):
        periodo=20252
        self.assertFalse(en_ventana_orientativa(date(2026,7,22),periodo))
        self.assertEqual(periodo,20252)
