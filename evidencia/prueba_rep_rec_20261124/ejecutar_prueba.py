from pathlib import Path
from datetime import datetime,timezone
import difflib, hashlib, json, os, re, shlex, statistics, subprocess, sys, time
p=Path(__file__).parent
repo=p/'Repositorio_Simple'
cfg=r'<carpeta local>\azure_cloud_20261025\.local\ssh_config'
env=dict(os.environ,SSH_CONFIG=cfg,PYTHONUTF8='1')
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','-F',cfg,'dme-master']
py=[sys.executable,'-B']
llevar=py+['coordinador/llevar.py']
red=py+['coordinador/red.py']
ctl=['pwsh','-NoProfile','-File',str(p/'Control-Cluster.ps1'),'-Action']
started=shaped=False
deadline=time.monotonic()+14400
rows=[]; recs=[]; errors=[]
def run(args, name, timeout=120, closing=False):
    print(name,flush=True)
    with (p/name).open('a',encoding='utf-8') as f:
        f.write('$ '+subprocess.list2cmdline(args)+'\n'); f.flush()
        if started and not closing:
            timeout=min(timeout,max(1,int(deadline-time.monotonic()-300)))
        r=subprocess.run(args,cwd=repo,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=timeout)
        f.write(r.stdout+r.stderr+'\n')
    if r.returncode: raise RuntimeError(f'{name}: {r.returncode}: {r.stderr[-800:]} {r.stdout[-800:]}')
    return r.stdout
def remote(cmd,log,timeout=120): return run(llevar+['correr',cmd],log,timeout)
def utc(): return datetime.now(timezone.utc).isoformat()+'\n'
def planpath(name,log):
    path=remote(f"find {name}/submit -name braindump.yml -printf '%h\\n'",log).strip()
    assert path.endswith('/run0001') and '\n' not in path,path
    return path
def verify_plan(folder, receipt):
    jobs={}
    for sub in folder.rglob('*.sub'):
        text=sub.read_text()
        if not re.search(r'(?im)^\+pegasus_job_class\s*=\s*1\s*$',text): continue
        tasks=re.findall(r'--task-id\s+([A-Z0-9]+)',sub.with_suffix('.in').read_text()) if sub.stem.startswith('merge_') else [sub.stem.removeprefix('campaign_task_')]
        req=re.search(r'(?im)^requirements\s*=\s*(.+)$',text)[1]
        host=set(re.findall(r'TARGET\.Machine\s*==\s*"(dme-worker[1-4])"',req,re.I))
        assert len(host)==1,(sub.name,req)
        jobs['+'.join(tasks)]=host.pop()
    receipt.write_text(json.dumps(jobs,indent=2))
    assert jobs=={'P+C1':'dme-worker1','C2':'dme-worker2','C3':'dme-worker3','C4':'dme-worker4'},jobs

f=repo/'coordinador/red.py'; old=f.read_text(encoding='utf-8')
if 'SSH_CONFIG' not in old:
    new=old.replace('import subprocess, sys','import os, subprocess, sys').replace('def ssh(nodo, orden):','SSH_CONFIG = os.environ.get("SSH_CONFIG")\nSSH_OPTIONS = ["-F", SSH_CONFIG] if SSH_CONFIG else []\n\n\ndef ssh(nodo, orden):').replace('["ssh", nodo, orden]','["ssh", *SSH_OPTIONS, nodo, orden]')
    assert next(x for x in old.splitlines() if x.startswith('NODOS'))==next(x for x in new.splitlines() if x.startswith('NODOS'))
    f.write_text(new,encoding='utf-8')
    with (p/'CAMBIOS.diff').open('a',encoding='utf-8') as stream:
        stream.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='coordinador/red.py',tofile='coordinador/red.py'))
seal=p/'HIPOTESIS_REC.md'
assert hashlib.sha256(seal.read_bytes()).hexdigest()==seal.with_suffix('.sha256').read_text().split()[0]
try:
    with (p/'INICIO_UTC_3.txt').open('x') as f: f.write(utc())
    started=True
    run(ctl+['Start','-Workers','4'],'ARRANQUE_3.txt',900)
    status=run(ssh+['condor_status -af Name State Activity Start && pegasus-version && condor_version'],'POOL_3.txt')
    slots=re.findall(r'(?m)^\S+@(dme-worker[1-4])\s+Unclaimed\s+Idle\s+(.+)$',status)
    assert len(slots)==4 and len({x[0] for x in slots})==4 and all(x[1].strip().lower() not in {'false','undefined','error'} for x in slots), 'Faltan slots disponibles o START es falso'
    run(ssh+['set -eu; mkdir -p ~/trabajo; sudo -n install -d -o "$(id -un)" -g "$(id -gn)" /mnt/prueba_rep_rec_20261124; if test -L ~/trabajo/prueba_rep_rec_20261124; then test "$(readlink ~/trabajo/prueba_rep_rec_20261124)" = /mnt/prueba_rep_rec_20261124; else ln -s /mnt/prueba_rep_rec_20261124 ~/trabajo/prueba_rep_rec_20261124; fi'],'DIRECTORIO_REMOTO_3.txt')
    remote('condor_status','POOL_LLEVAR_3.txt')
    run(llevar+['subir','flujos','analyzer'],'SUBIDA_3.txt')
    create='python3 flujos/crear_flujo.py flujos/especificaciones.json'
    assert json.loads((p/'PLAN_VERIFICADO.json').read_text())=={'P+C1':'dme-worker1','C2':'dme-worker2','C3':'dme-worker3','C4':'dme-worker4'}
    before=run(red+['ver'],'TC_ANTES_3.txt',300)
    assert len(re.findall(r'(?m)^== ',before))==5 and not re.search(r'(?m)^qdisc (prio|tbf)\b',before)
    shaped=True
    active=run(red+['limitar','100'],'TC_DURANTE_3.txt',600)
    assert len(re.findall(r'(?m)^qdisc tbf\b.*100Mbit',active))==5
    bandwidth="""set -eu
mkdir banda
cd banda
fallocate -l 1073741824 datos.bin
cat > banda.sub <<'SUB'
executable = /bin/true
transfer_executable = False
requirements = TARGET.Machine == "dme-worker2"
request_cpus = 1
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = datos.bin
transfer_output_files = ""
log = eventos.log
output = stdout.txt
error = stderr.txt
queue
SUB
id=$(condor_submit -terse banda.sub | cut -d. -f1)
condor_wait -wait 600 eventos.log
condor_history "$id" -json > history.json
python3 -c 'import json; a=json.load(open("history.json")); assert len(a)==1; a=a[0]; assert a["ExitCode"]==0; s=a["TransferInputStats"]["CedarSizeBytesTotal"]; assert s==2**30; d=a["TransferInFinished"]-a["TransferInStarted"]; assert d>0; print("MEDICION",json.dumps(dict(bytes=s,segundos=d,MB_s=s/d/1e6)))'
unlink datos.bin"""
    b=json.loads(re.search(r'(?m)^MEDICION (.+)$',remote('sh -c '+shlex.quote(bandwidth),'ANCHO_DE_BANDA.txt',650))[1])
    (p/'ANCHO_DE_BANDA.json').write_text(json.dumps(b,indent=2))
    run(llevar+['bajar','banda',str(p)],'ANCHO_DE_BANDA.txt')
    for i in range(1,4):
        for condition,prefix in [('REP','rep'),('REP-REC','reprec')]:
            assert deadline-time.monotonic()>3000,'Presupuesto insuficiente para otra corrida'
            name=f'{prefix}_r{i}'; log=name+'.txt'; dest=p/name
            remote(f'{create} {condition} {name}',log)
            remote(f'python3 flujos/ejecutar_flujo.py {name}',log,2750)
            dest.mkdir()
            run(llevar+['bajar',planpath(name,log),str(dest)],log,420)
            run(llevar+['bajar',f'{name}/history.long',str(dest)],log)
            if condition=='REP-REC': verify_plan(dest/'run0001',dest/'PLAN_VERIFICADO.json')
            args=[str(dest/'run0001'),str(dest/'history.long')]
            a=run(py+['analyzer/analyzer.py',*args,'-v'],log)
            t=run(py+['analyzer/tiempos.py',*args],log)
            required=int(re.search(r'(?m)^Requerido:\s+(\d+)',a)[1])
            observed=int(re.search(r'(?m)^(?:Contrato \(\.sub\)|Observado):\s+(\d+)',a)[1])
            duration=float(re.search(r'DAGMan\):\s*(\d+(?:\.\d+)?)',t)[1])
            times={k:int(v) for k,v in re.findall(r'(?m)^\s*(ejecucion|transferencia|auxiliares|cola|cierre|dagman)\s+(\d+) s',t)}
            assert len(times)==6
            rows.append(dict(repeticion=i,condicion=condition,requerido=required,observado=observed,DME=required/observed,duracion=duration,**times))
    for name in ('rep_r1','reprec_r1'):
        recs.append(run(py+['analyzer/recomendar.py',str(p/name/'run0001'),str(p/name/'history.long'),'--ancho',str(b['MB_s'])],f'RECOMENDAR_{name}.txt'))
except Exception as e:
    errors.append(str(e)); print(str(e),flush=True)
finally:
    if shaped:
        for action,log in [('quitar','TC_QUITAR_3.txt'),('ver','TC_FINAL_3.txt')]:
            try:
                text=run(red+[action],log,300,True)
                if action=='ver': assert len(re.findall(r'(?m)^== ',text))==5 and not re.search(r'(?m)^qdisc (prio|tbf)\b',text),'Queda una cola o falta un nodo'
            except Exception as e: errors.append(f'{log}: {e}')
    if started:
        try:
            run(ctl+['Deallocate'],'CIERRE_3.txt',650,True)
            status=json.loads((p/'.local/last-deallocation.json').read_text())
            assert len(status)==5 and all(x['powerState']=='VM deallocated' for x in status)
            (p/'ESTADO_FINAL_3.json').write_text(json.dumps(status,indent=2))
            (p/'CIERRE_UTC_3.txt').write_text(utc())
        except Exception as e: errors.append(f'Cierre pendiente: {e}')
    lines=['# Resultados REP-REC · 24 de noviembre de 2026','',
           'Versiones y slots en POOL_3.txt. Ventana en INICIO_UTC_3.txt y CIERRE_UTC_3.txt.',
           'Comandos en los registros por paso y corrida. Cambios en CAMBIOS.diff.']
    if shaped: lines.append('Estado de red en TC_ANTES_3.txt, TC_DURANTE_3.txt, TC_QUITAR_3.txt y TC_FINAL_3.txt.')
    if (p/'ANCHO_DE_BANDA.json').exists(): lines.append('Calibración HTCondor de entrada en ANCHO_DE_BANDA.json: '+(p/'ANCHO_DE_BANDA.json').read_text())
    if rows:
        keys=list(rows[0]); lines.extend(['','| '+' | '.join(keys)+' |','| '+' | '.join(['---']*len(keys))+' |'])
        lines.extend('| '+' | '.join(str(r[k]) for k in keys)+' |' for r in rows)
    if len(rows)==6:
        for condition in ('REP','REP-REC'):
            for k in list(rows[0])[2:]:
                v=[r[k] for r in rows if r['condicion']==condition]
                lines.append(f'- {condition} {k} {statistics.mean(v):.9g} ± {statistics.stdev(v):.9g}')
        d={k:[rows[i+1][k]-rows[i][k] for i in (0,2,4)] for k in ('transferencia','duracion')}
        for k,v in d.items(): lines.append(f'- REP-REC menos REP {k}: {v}, media ± desviación {statistics.mean(v):.3f} ± {statistics.stdev(v):.3f} s.')
        r1=all(r['requerido']==1887436800 for r in rows); r2=all(r['observado']==(2097152000 if r['condicion']=='REP' else 1887436800) for r in rows)
        r3=-27<=statistics.mean(d['transferencia'])<=-9
        lines.extend(['',f'R1 {r1}. R2 {r2}. R3 {r3} por el criterio de la media. Bajó en las tres: {all(v<0 for v in d["transferencia"])}. R4 reportada sin dirección esperada.'])
    else: lines.extend(['','R1–R4 pendientes de la matriz completa.'])
    for rec in recs: lines.extend(['','~~~text',rec,'~~~'])
    lines.extend(['','## Incidencia del intento 2','','El supervisor agotó su espera de 120 s durante red.py limitar. Se verificó la limpieza y la desasignación. Registro íntegro en INCIDENCIA_INTENTO_2.md.'])
    if errors: lines.extend(['','## Incidencias del intento 3','',*errors])
    (p/'RESULTADOS_REC.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if errors: sys.exit(1)

