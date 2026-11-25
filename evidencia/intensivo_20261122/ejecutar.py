"""Ejecuta una fila o una medición de ancho de banda desde el coordinador."""
from fractions import Fraction
from pathlib import Path
import csv
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime'))
import run_study as runner
import tabla_tiempos


def bandwidth(direction):
    case=ROOT/('banda-'+direction)
    case.mkdir()
    size=2**30
    payload=case/'datos.bin'
    inbound=direction=='entrada'
    if inbound:
        subprocess.run(['fallocate','-l',str(size),payload],check=True)
    spec=case/'banda.sub'
    spec.write_text(f'''executable = {"/bin/true" if inbound else "/usr/bin/fallocate"}
arguments = {"" if inbound else "-l 1073741824 datos.bin"}
transfer_executable = False
requirements = TARGET.Machine == "dme-worker2"
request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {str(payload) if inbound else '""'}
transfer_output_files = {'""' if inbound else 'datos.bin'}
initialdir = {case}
log = {case/'eventos.log'}
output = {case/'stdout.txt'}
error = {case/'stderr.txt'}
queue
''')
    try:
        identifier=runner.command(['condor_submit','-terse',spec]).split()[0].split('.')[0]
        runner.command(['condor_wait','-wait','600',case/'eventos.log'],timeout=620)
        ads=json.loads(runner.command(['condor_history',identifier,'-json']))
        assert len(ads)==1 and ads[0]['ExitCode']==0
        ad=ads[0]
        kind='Input' if inbound else 'Output'
        assert ad[f'Transfer{kind}Stats']['CedarSizeBytesTotal']==size
        duration=ad[f'JobCurrentFinishTransfer{kind}Date']-ad[f'JobCurrentStartTransfer{kind}Date']
        assert duration>0
        runner.save(case/'BANDA.json',dict(direccion=direction,bytes=size,segundos=duration,bytes_por_s=size/duration,ad=ad))
    finally:
        payload.unlink(missing_ok=True)


def archive(case,evidence,row):
    base=case.parent.parent
    jobs,run=tabla_tiempos.analyze(row['id'],row['condition'],str(base))
    scientific=[j for j in jobs if j['tipo']=='tarea']
    assert scientific and all(j[k] is not None for j in scientific for k in ('transferencia_entrada_s','transferencia_salida_s','ejecucion_s'))
    audit=runner.read(evidence/'INDEPENDENT_AUDIT.json')
    historical=runner.read(ROOT/'REFERENCIAS.json')[row['condition']]
    placements={task:job['worker'] for job in audit['jobs'] for task in job['members']}
    refs=[r for r in historical['referencias'] if r['placement']==placements]
    if refs:
        required={r['requerido_escalado_B'] for r in refs}
        assert required=={audit['required_bytes']}
    else:
        # Reconstruct the 10 MiB control on this exact placement. No measured time is inferred.
        spec=runner.read(ROOT/'SPECS.json')
        spec=spec.get(row['id'],spec.get(row['condition']))
        required_units=0
        for file in spec['files']:
            producer=file['producer_task']
            origin=placements[producer] if producer else 'dme-master'
            destinations={placements[t] for t in file['consumer_tasks']}
            if file['role']=='final' or (producer and destinations-{origin,'dme-master'}):
                destinations.add('dme-master')
            required_units+=len(destinations-{origin})
        assert audit['required_bytes']==required_units*200*2**20
    assert audit['observed_bytes']==historical['observado_B']
    assert audit['comparison_only_after_independent_reconstruction']['required_match']
    assert audit['comparison_only_after_independent_reconstruction']['observed_match']
    assert all(item['exact'] and item['residual']==0 for item in audit['directions'])
    runner.save(evidence/'D1.json',dict(ubicacion=placements,referencias_medidas=refs,requerido_10MiB=audit['required_bytes']//20,observado_10MiB=audit['observed_bytes']//20,dme=str(Fraction(audit['required_bytes'],audit['observed_bytes']))))
    for name,records in [('jobs',jobs),('corridas',[run])]:
        with (evidence/(name+'.csv')).open('w',newline='') as out:
            writer=csv.DictWriter(out,fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)


def execute(identifier):
    row=next(r for r in runner.read(ROOT/'MATRIX.json') if r['id']==identifier)
    runner.archive=archive
    runner.archive_case=lambda case,ev,case_id:archive(case,ev,row)
    runner.execute(row)
    specs=runner.read(ROOT/'SPECS.json')
    spec=specs.get(identifier,specs.get(row['condition']))
    payloads={file['file_id'] for file in spec['files']}
    for path in (ROOT/'cases'/identifier).rglob('*'):
        if path.name.removesuffix('.000') in payloads and path.is_file() and path.stat().st_size==200*2**20:
            path.unlink()


if __name__=='__main__':
    if sys.argv[1] in ('entrada','salida'):
        bandwidth(sys.argv[1])
    else:
        execute(sys.argv[1])
