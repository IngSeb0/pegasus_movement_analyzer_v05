"""Compila y prueba FMA en los nodos autorizados, conservando cada medición."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parent
SESSION = ROOT / 'sesion'
REMOTE = '/mnt/montage_intensivo_20261122'


def call(args, timeout=180):
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stderr[-3500:] + p.stdout[-1000:])
    return p.stdout


def ssh(host, command, timeout=180):
    for attempt in range(4):
        try:
            return call(['ssh', '-F', str(SESSION/'ssh_config'), host, command], timeout)
        except (RuntimeError,subprocess.TimeoutExpired) as error:
            message=str(error).lower()
            transient=isinstance(error,subprocess.TimeoutExpired)or any(word in message for word in ('timed out','connection reset','connection closed','broken pipe','connection refused','kex_exchange'))
            if not transient or attempt==3:
                raise
            with (SESSION/'REINTENTOS_SSH.log').open('a',encoding='utf-8')as log:
                log.write(host+' '+str(error)+'\n')
            time.sleep(5)


def scp(source, target):
    return call(['scp', '-F', str(SESSION/'ssh_config'), str(source), str(target)])


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding='utf-8')


