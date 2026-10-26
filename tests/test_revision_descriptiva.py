import unittest
from decimal import Decimal
from analitica_admisiones.revision_descriptiva import consolidar_parcial


class ParcialesTest(unittest.TestCase):
    def test_recupera_solo_ausencia(self):
        a={'registro_id':'R1','importe':None,'estado':'Retirado'}
        b={'registro_id':'R1','importe':Decimal('1800000.00'),'estado':'Retirado'}
        row,changes=consolidar_parcial([a,b],['importe'])
        self.assertEqual(row,b)
        self.assertIsNone(a['importe'])
        self.assertEqual(changes,[('importe',None,Decimal('1800000.00'))])

    def test_rechaza_dos_valores_informados(self):
        with self.assertRaises(ValueError):
            consolidar_parcial([{'id':'R','v':1},{'id':'R','v':2}],['v'])

    def test_rechaza_diferencia_fuera_de_alcance(self):
        with self.assertRaises(ValueError):
            consolidar_parcial([{'id':'R','v':None,'estado':'Nuevo'},
                                {'id':'R','v':2,'estado':'Admitido'}],['v'])

    def test_no_reemplaza_valor_informado_por_nulo(self):
        a={'id':'R','v':Decimal('2.00')}
        row,changes=consolidar_parcial([a,{'id':'R','v':None}],['v'])
        self.assertEqual(row,a)
        self.assertEqual(changes,[])
