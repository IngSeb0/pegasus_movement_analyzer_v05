"""Obtiene las entradas en el coordinador y conserva el diagnóstico si falla."""
from pathlib import Path
import subprocess
from acceso import ROOT,SESSION,REMOTE,ssh,scp


def main():
    archive=ROOT.parent/'pruebas_cierre_sin_cf_20261031/preparacion_montage'
    wheel=next(archive.glob('montagepy-2.3.0-*.whl'))
    ssh('dme-master',f'sudo install -d -o dmeadmin -g dmeadmin {REMOTE}')
    scp(ROOT/'descargar.py',f'dme-master:{REMOTE}/descargar.py')
    scp(wheel,f'dme-master:{REMOTE}/{wheel.name}')
    disk=ssh('dme-master','df -h /mnt; python3 -V')
    (ROOT/'RESULTADOS/DISCO_COORDINADOR.txt').write_text(disk,encoding='utf-8')
    command=f'cd {REMOTE} && timeout 180 python3 -u descargar.py 2.0 > descarga.log 2>&1'
    try:
        ssh('dme-master',command,200)
    finally:
        log=ssh('dme-master',f'cd {REMOTE}; cat descarga.log; if test -f entradas-2.0/DESCARGA.json; then cat entradas-2.0/DESCARGA.json; fi')
        (ROOT/'RESULTADOS/DESCARGA.log').write_text(log,encoding='utf-8')
    scp(f'dme-master:{REMOTE}/ENTRADAS.json',ROOT/'RESULTADOS/ENTRADAS.json')
    scp(f'dme-master:{REMOTE}/entradas-2.0/catalogo.tbl',ROOT/'RESULTADOS/catalogo.tbl')


if __name__=='__main__':
    main()
