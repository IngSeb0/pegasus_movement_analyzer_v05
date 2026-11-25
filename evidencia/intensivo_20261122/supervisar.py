"""Controla el piloto y la matriz, restaura la red y cierra Azure."""
from datetime import datetime
from pathlib import Path
import json
import shlex
import subprocess
import tarfile
import time
from acceso import ROOT,SESSION,REMOTE,ssh,scp
from configurar_pool import ensure_aliases,pool,restore
from empaquetar import package

HOSTS=['dme-master',*[f'dme-worker{i}' for i in range(1,5)]]
OUT=ROOT/'RESULTADOS'


def run(group,row):
    label=row['id'].lower()
    command=f'python3 -u ejecutar.py {shlex.quote(row["id"])} > {label}.log 2>&1; status=$?; echo "$status" > {label}.exit; exit "$status"'
    prefix=f'cd {REMOTE}/{group}; '
    ssh('dme-master',f'sudo systemd-run --unit=intensivo-{label} --uid=dmeadmin --working-directory={REMOTE}/{group} --property=RuntimeMaxSec=2050 /bin/bash -c '+shlex.quote(command))
    deadline=time.monotonic()+2100
    while time.monotonic()<deadline:
        try:
            state=ssh('dme-master',prefix+f'if test -f {label}.exit; then cat {label}.exit; else systemctl is-active intensivo-{label} || true; fi',45).strip()
        except (RuntimeError,subprocess.SubprocessError):
            time.sleep(10)
            continue
        if state=='0':
            print(row['id'],'aceptada',flush=True)
            return
        if state not in ('active','activating'):
            raise RuntimeError(ssh('dme-master',prefix+f'tail -20 {label}.log'))
        time.sleep(15)
    raise RuntimeError('Tiempo de supervisión superado para '+row['id'])


def network(host,when,iface):
    saved=ssh(host,f'tc -s qdisc show dev {iface}; tc filter show dev {iface} parent 1: 2>/dev/null || true')
    with (OUT/'TC.txt').open('a',encoding='utf-8') as f:
        f.write(f'\n{host} {when} {iface}\n{saved}')
    return saved


def export():
    code="""from pathlib import Path
import tarfile
with tarfile.open('evidencia.tar.gz','w:gz') as z:
 for f in Path('.').rglob('*'):
  if f.is_file() and (f.suffix in {'.json','.log','.yml','.yaml','.sub','.in','.metrics','.dag','.long','.csv','.stdout','.stderr','.out','.exit','.xml','.tsv','.meta'} or '.out.' in f.name or '.err.' in f.name):
   z.add(f,arcname=str(f))
"""
    ssh('dme-master',f'cd {REMOTE}; python3 -c '+shlex.quote(code),300)
    target=SESSION/'evidencia.tar.gz'
    scp(f'dme-master:{REMOTE}/evidencia.tar.gz',target)
    with tarfile.open(target) as archive:
        archive.extractall(SESSION/'evidencia',filter='data')


def main():
    shaped={}
    ready=False
    pool_changed=False
    deadline=datetime.fromisoformat((SESSION/'limite_utc.txt').read_text().strip())
    try:
        ensure_aliases()
        disks={}
        for host in HOSTS:
            path='/mnt' if host=='dme-master' else '$(condor_config_val EXECUTE)'
            value=ssh(host,f'df -PB1 "{path}"; df -h "{path}"')
            disks[host]=value
            assert int(value.splitlines()[1].split()[3])>=8*2**30,(host,value)
        (OUT/'DISCO.json').write_text(json.dumps(disks,indent=2))
        ssh('dme-master',f'sudo install -d -o dmeadmin -g dmeadmin {REMOTE}')
        ready=True
        matrices={}
        for group in ('patrones','contraste'):
            payload,matrices[group]=package(group)
            ssh('dme-master',f'mkdir {REMOTE}/{group}')
            scp(payload,f'dme-master:{REMOTE}/{group}/carga.zip')
            ssh('dme-master',f'cd {REMOTE}/{group} && python3 -m zipfile -e carga.zip .')
        for host in HOSTS:
            central=host=='dme-master'
            peer='10.42.1.5' if central else '10.42.0.4'
            destination='10.42.1.0/24' if central else '10.42.0.4/32'
            route=ssh(host,f'ip -o route get {peer}').split()
            iface=route[route.index('dev')+1]
            original=network(host,'antes',iface)
            queues=[line for line in original.splitlines() if line.startswith('qdisc ')]
            assert queues and all(line.split()[1] in {'noqueue','mq','fq_codel'} for line in queues),original
            delay=max(1,int(deadline.timestamp()-time.time()-25*60))
            ssh(host,f'sudo tc qdisc add dev {iface} root handle 1: prio bands 2 priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0')
            shaped[host]=iface
            ssh(host,f'sudo systemd-run --unit=intensivo-quitar-tc --on-active={delay}s /usr/sbin/tc qdisc del dev {iface} root')
            ssh(host,f'sudo tc qdisc add dev {iface} parent 1:2 handle 20: tbf rate 100mbit burst 256kbit latency 400ms && sudo tc filter add dev {iface} parent 1: protocol ip prio 1 u32 match ip dst {destination} flowid 1:2')
            network(host,'durante',iface)
        for direction in ('entrada','salida'):
            run('patrones',dict(id=direction))
        pool_changed=True
        pool(2)
        run('patrones',matrices['patrones'][0])
        active_workers=2
        rows=list(matrices['patrones'][1:])
        contrast=list(matrices['contraste'])
        while rows or contrast:
            remaining=deadline.timestamp()-time.time()
            if remaining<40*60:
                print('Reserva del cierre de cinco horas',flush=True)
                break
            # Keep the requested order while enough time remains for the contrast.
            if contrast and (not rows or remaining<40*60+(len(contrast)+len(rows))*350):
                group='contraste'
                row=contrast.pop(0)
            elif rows:
                group='patrones'
                row=rows.pop(0)
            else:
                break
            if active_workers!=row['workers']:
                pool(row['workers'])
                active_workers=row['workers']
            run(group,row)
    finally:
        failures=[]
        for host,iface in shaped.items():
            try:
                state=ssh(host,f'tc qdisc show dev {iface}')
                if 'qdisc prio 1:' in state:
                    ssh(host,f'sudo tc qdisc del dev {iface} root')
                ssh(host,'sudo systemctl stop intensivo-quitar-tc.timer')
                assert ' tbf ' not in network(host,'después',iface)
            except Exception as error:
                failures.append(f'{host}: {error}')
        if failures:
            (OUT/'TC_ERRORES.json').write_text(json.dumps(failures,indent=2))
        try:
            if pool_changed:
                restore()
            if ready:
                export()
        finally:
            subprocess.run(['pwsh','-NoProfile','-File',str(ROOT/'control.ps1'),'close'],check=True,timeout=720)
        if failures:
            raise RuntimeError('No se verificó tc en todos los nodos')


if __name__=='__main__':
    main()
