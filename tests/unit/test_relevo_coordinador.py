"""Casos límite de la referencia por destino con relevo CondorIO."""
import unittest
from tests.unit.test_movement import scientific_file, task
from pegasus_movement.model import FileRole
from pegasus_movement.movement import build_required_movements
from pegasus_movement.metrics import calculate_metrics
from pegasus_movement.model import DeclaredMovementRecord, TransferDirection

class PruebasRelevo(unittest.TestCase):
    def test_no_calcula_dme_si_falta_entrega_al_coordinador(self):
        archivo = scientific_file(file_id="g",logical_name="g",size=10,
            roles={FileRole.INTERMEDIATE},producer="p",consumers=["c"])
        requerido = build_required_movements([archivo],
            [task("p","w1","1"),task("c","w2","2")],coordinator_location_id="m")
        entregas=[DeclaredMovementRecord(movement_id=str(i),job_id=str(i),file_id="g",attempt_context=None,
            direction=TransferDirection.INPUT,from_location_id="m",to_location_id="w2",
            size_bytes=10,confirmed=True) for i in range(2)]
        resultado=calculate_metrics(required_movements=requerido.records,declared_movements=entregas)
        self.assertIsNone(resultado.dme)
        self.assertEqual(resultado.coverage,1)

    def test_relevo_y_final_comparten_un_destino(self):
        archivo = scientific_file(file_id="g", logical_name="g", size=10,
            roles={FileRole.INTERMEDIATE,FileRole.FINAL_OUTPUT},
            producer="p", consumers=["a","b","c"], finals=["m"])
        resultado = build_required_movements([archivo],[
            task("p","w1","1"),task("a","w2","2"),
            task("b","w2","3"),task("c","w3","4")],coordinator_location_id="m")
        self.assertEqual(resultado.total_bytes,30)
        self.assertEqual({r.to_location_id for r in resultado.records},{"m","w2","w3"})
        self.assertEqual(len(resultado.records),3)

    def test_no_infiere_coordinador_para_intermedio_remoto(self):
        archivo = scientific_file(file_id="g",logical_name="g",size=10,
            roles={FileRole.INTERMEDIATE},producer="p",consumers=["c"])
        resultado = build_required_movements([archivo],[task("p","w1","1"),task("c","w2","2")])
        self.assertTrue(resultado.diagnostics)
        self.assertEqual(resultado.records,[])

    def test_archivo_cero_conserva_obligacion_de_relevo(self):
        archivo = scientific_file(file_id="g",logical_name="g",size=0,
            roles={FileRole.INTERMEDIATE},producer="p",consumers=["c"])
        resultado = build_required_movements([archivo],[task("p","w1","1"),task("c","w2","2")],
            coordinator_location_id="m")
        self.assertEqual(resultado.total_bytes,0)
        self.assertEqual(len(resultado.records),2)

if __name__ == '__main__': unittest.main()
