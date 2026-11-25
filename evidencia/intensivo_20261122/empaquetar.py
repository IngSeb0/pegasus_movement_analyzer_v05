"""Construye dos paquetes con los lanzadores FMA y los contratos escalados."""
from datetime import datetime,timedelta
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent
FMA=ROOT.parent/'fma_20261120'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def package(group):
    with ZipFile(FMA/(group+'.zip')) as z:
        files={n:z.read(n) for n in z.namelist() if n.startswith(('core/','runtime/'))}
    source=files['runtime/run_study.py'].decode()
    source=source.replace('time.time() + 600','time.time() + 1800').replace('time.time()+800','time.time()+1800')
    if group=='patrones':
        source=source.replace("    preserve_identical_files(case / 'inputs', evidence, specification, 'IDENTICAL_INPUT_LINKS.json')\n",'').replace('    preserve_identical_files(case, evidence, specification)\n','')
    files['runtime/run_study.py']=source.encode()
    specs=read(ROOT/'SPECS.json')
    predictions=read(ROOT/'RESULTADOS/PREDICCIONES.json')
    def put(name,obj):files[name]=json.dumps(obj,indent=2).encode()
    if group=='patrones':
        base=read(FMA/'especificaciones/matriz_tiempos.json')
        matrix=[dict(id=r['id'],condition=r['condition'],workers=r['workers'],pattern=r['pattern'],block=r['block'],phase='principal') for r in base if r['block']<=2]
        matrix.insert(0,dict(id='DISTRIBUTION-W2-PILOTO',condition='DISTRIBUTION-W2',workers=2,pattern='DISTRIBUTION',block=0,phase='piloto'))
        put('SPECS.json',{r['id']:specs[r['condition']] for r in matrix})
        put('PREDICTIONS.json',[dict(id=r['id'],expectedObservedBytes=predictions[r['condition']]['observado_B'],expectedDeliveries=predictions[r['condition']]['observado_B']//(200*2**20)) for r in matrix])
    else:
        base=read(FMA/'MATRIX_CONTRASTE_FMA.json')
        matrix=[r for r in base if 1<=r['block']<=3]
        put('SPECS.json',{r['condition']:specs[r['condition']] for r in matrix})
        put('PLAN_ACCOUNTS.json',{c:dict(required=p['referencias'][0]['requerido_escalado_B'],observed=p['observado_B']) for c,p in predictions.items() if c in {'REP','W2-SEP','W2-AGR'}})
    put('MATRIX.json',matrix)
    put('REFERENCIAS.json',predictions)
    end=datetime.fromisoformat((ROOT/'sesion02/limite_utc.txt').read_text().strip())
    put('SESSION_ACTIVE.json',dict(startedAtUtc=(ROOT/'sesion02/inicio_utc.txt').read_text().strip(),deadlineUtc=end.isoformat(),stopSubmissionsUtc=(end-timedelta(minutes=40)).isoformat(),maximumNewWorkflows=len(matrix)))
    for name,p in [('ejecutar.py',ROOT/'ejecutar.py'),('tabla_tiempos.py',ROOT/'herramientas/tabla_tiempos.py')]:
        files[name]=p.read_bytes().replace(b'\r\n',b'\n')
    put('HASHES.json',{n:sha256(v).hexdigest() for n,v in files.items()})
    target=ROOT/(group+'-carga.zip')
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for name,content in files.items():z.writestr(name,content)
    return target,matrix
