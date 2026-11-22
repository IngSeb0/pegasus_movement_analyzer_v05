"""Recalcula con el núcleo vigente; distingue modelos y desgloses nativos extraídos."""
import csv,json,sys
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pegasus_movement.model import ScientificFile,FileRole,TaskExecution,DeclaredMovementRecord,TransferDirection
from pegasus_movement.movement import build_required_movements
from pegasus_movement.metrics import calculate_metrics

def calcular(archivos,coordinador):
    objetos=[]; tareas=[]
    for i,(tamano,origen,destinos,final) in enumerate(archivos):
        productor=None
        if origen!=coordinador:
            productor=f'p{i}'
            tareas.append(TaskExecution(task_id=productor,pegasus_node_id=productor,worker_location_id=origen))
        consumidores=[]
        for j,destino in enumerate(destinos):
            if destino==coordinador:continue
            identidad=f'c{i}_{j}'; consumidores.append(identidad)
            tareas.append(TaskExecution(task_id=identidad,pegasus_node_id=identidad,worker_location_id=destino))
        objetos.append(ScientificFile(file_id=str(i),logical_name=str(i),size_bytes=int(tamano),
            roles={FileRole.INTERMEDIATE} if productor else {FileRole.EXTERNAL_INPUT},
            producer_task_id=productor,consumer_task_ids=consumidores,
            origin_location_id=origen,final_destination_ids=[coordinador] if final else []))
    resultado=build_required_movements(objetos,tareas,coordinator_location_id=coordinador)
    assert not resultado.diagnostics,resultado.diagnostics
    return resultado

def main():
    modelos=json.loads((ROOT/'data/source/relevo/configuraciones.json').read_text(encoding='utf-8'))
    historicos=list(csv.DictReader((ROOT/'data/derived/workflows_113.csv').open(encoding='utf-8')))
    filas=[]
    for caso in historicos:
        nombre={'B01':'AC1','B02':'AC2','B04':'AC4'}.get(caso['condition'],caso['condition'])
        if caso['block']!='A' or nombre not in modelos:continue
        modelo=modelos[nombre]
        calculo=calcular([[int(s*2**20),o,d,f] for s,o,d,f in modelo['archivos']],'m')
        requerido=calculo.total_bytes
        observado=int(caso['observed_bytes'])
        assert observado==int(modelo['observado_mib']*2**20)
        filas.append(dict(caso=caso['case'],condicion=nombre,uuid=caso['uuid'],
            requerido_bytes=requerido,observado_bytes=observado,dme=str(Fraction(requerido,observado)),
            duracion_s=caso['dag_duration_s'],obligaciones=len(calculo.records),procedencia='configuracion_documentada_y_observado_historico'))
    assert len(filas)==45
    nativos=json.loads((ROOT/'data/validation_free_20261107/DESGLOSE_NATIVO.json').read_text(encoding='utf-8'))
    libres=list(csv.DictReader((ROOT/'data/validation_free_20261107/RESULTADOS_VALIDACION_LIBRE.csv').open(encoding='utf-8')))
    for caso in libres:
        desglose=next(d for d in nativos if d['case']==caso['case'])
        assert all(d['exact'] and d['residual']==0 for d in desglose['directions'])
        archivos=[[f['bytes'],f['origin'],f['destinations'],f['final']] for f in desglose['files'].values()]
        calculo=calcular(archivos,'dme-master')
        requerido=calculo.total_bytes
        observado=sum(d['bytes'] for d in desglose['deliveries'])
        identidades={nombre:str(i) for i,nombre in enumerate(desglose['files'])}
        entregas=[DeclaredMovementRecord(movement_id=str(i),job_id=d['global_job_id'],
            attempt_context=None,file_id=identidades[d['file']],direction=TransferDirection(d['direction']),
            from_location_id=d['source'],to_location_id=d['destination'],size_bytes=d['bytes'],confirmed=True)
            for i,d in enumerate(desglose['deliveries'])]
        metrica=calculate_metrics(required_movements=calculo.records,declared_movements=entregas)
        assert metrica.observed_movement_bytes==observado
        assert metrica.dme==requerido/observado
        assert observado==int(caso['observed_mib'])*2**20
        filas.append(dict(caso=caso['case'],condicion=caso['condition'],uuid=caso['uuid'],
            requerido_bytes=requerido,observado_bytes=observado,dme=str(Fraction(requerido,observado)),
            duracion_s=caso['duration_s'],obligaciones=len(calculo.records),procedencia='desglose_nativo_extraido'))
    assert len(filas)==55 and len({f['uuid'] for f in filas})==55
    destino=ROOT/'data/derived/dme_relevo_55.csv'
    with destino.open('w',encoding='utf-8',newline='') as archivo:
        escritor=csv.DictWriter(archivo,fieldnames=list(filas[0])); escritor.writeheader(); escritor.writerows(filas)
    print(f'{len(filas)} casos recalculados con build_required_movements; datos originales conservados.')

if __name__=='__main__':main()
