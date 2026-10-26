"""Verifica límites de consolidación y conservación de orígenes."""
from pathlib import Path
import json
import tempfile
import unittest
import pandas as pd
from analitica_admisiones.cierre_limpieza import CierreLimpieza


class CierreLimpiezaTest(unittest.TestCase):
    def context(self, raw, typed, sources, ids):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root/'config/limpieza').mkdir(parents=True)
        (root/'config/limpieza/cierre_v1.json').write_text(json.dumps({
            'version':'test', 'fecha_referencia_revision':'2026-10-26'}))
        origen = pd.DataFrame([{'id_fila_entrada':ident,'origen_sistema':source} for ident,source in zip(ids,sources)])
        return CierreLimpieza(root,pd.DataFrame(typed,dtype=object),pd.DataFrame(raw,dtype=object),ids,
                             origen,pd.DataFrame(),{'archivos_datos':{'BaseUnificada_Tipada.jsonl':'a'*64}},'b'*64)

    def test_consolida_exactos_con_representante_estable(self):
        rows = [{'registro_id':'R1','valor':'10'}]*2
        c = self.context(rows,rows,['Principal']*2,['BU000002','BU000001'])
        result = c.l06()
        self.assertEqual(result['repeticiones_consolidadas'],1)
        self.assertEqual(c.mapping,{'BU000002':'BU000001','BU000001':'BU000001'})
        self.assertEqual(c.kept,['BU000001'])
        self.assertEqual(len(c.rows),2)

    def test_no_consolida_entre_fuentes(self):
        rows = [{'registro_id':'R1','valor':'10'}]*2
        c = self.context(rows,rows,['Principal','CRM'],['BU000001','BU000002'])
        self.assertEqual(c.l06()['repeticiones_consolidadas'],0)

    def test_no_pierde_diferencias_originales_tras_tipado(self):
        raw = [{'registro_id':'R1','valor':'Pendiente'},{'registro_id':'R1','valor':''}]
        typed = [{'registro_id':'R1','valor':None}]*2
        c = self.context(raw,typed,['Principal']*2,['BU000001','BU000002'])
        self.assertEqual(c.l06()['repeticiones_consolidadas'],0)

    def test_no_fusiona_por_identificador_compartido(self):
        rows = [{'registro_id':'R1','valor':'10'},{'registro_id':'R1','valor':'20'}]
        c = self.context(rows,rows,['Principal']*2,['BU000001','BU000002'])
        self.assertEqual(c.l06()['repeticiones_consolidadas'],0)

    def test_incidencias_conservan_entrada_y_actualizan_destino(self):
        rows = [{'registro_id':'R1','valor':'10'}]*2
        c = self.context(rows,rows,['Principal']*2,['BU000001','BU000002'])
        c.issue('BU000002','valor','revisar','detalle','D01')
        c.l06()
        self.assertEqual(c.issues[0]['id_fila_entrada'],'BU000002')
        self.assertEqual(c.issues[0]['id_registro_salida'],'BU000001')
