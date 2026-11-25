"""Upload and preserve the dedicated M101 study using the new session."""

import json
from pathlib import Path
import shlex
import subprocess
import sys

BASE = Path(__file__).resolve().parent
SESSION = BASE / "session01"
SSH = ["ssh", "-F", str(SESSION / "ssh_config"), "dme-campaign"]
SCP = ["scp", "-F", str(SESSION / "ssh_config")]
location = SESSION / "DATA_ROOT.txt"
REMOTE = location.read_text().strip() if location.exists() else "/srv/dme/montage_m101_20261111"


def ssh(code, timeout):
    subprocess.run(SSH + ["python3 -"], input=code, text=True, timeout=timeout, check=True)


def upload():
    ssh(f"from pathlib import Path; Path({REMOTE!r}).mkdir()", 50)
    subprocess.run(SCP + [str(BASE / "payload.tar.gz"), "dme-campaign:" + REMOTE + "/"], check=True, timeout=210)
    subprocess.run(SCP + [str(SESSION / "SESSION_START.json"),
                          "dme-campaign:" + REMOTE + "/SESSION_ACTIVE.json"], check=True, timeout=60)
    ssh(f"""import json, tarfile, hashlib
from pathlib import Path
root=Path({REMOTE!r})
with tarfile.open(root/'payload.tar.gz') as archive:
    archive.extractall(root,filter='data')
for name,digest in json.loads((root/'HASHES.json').read_text()).items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print('Upload verified')
""", 60)


def storage():
    subprocess.run(SSH + ["df -h /srv/dme /mnt /dev/shm; lsblk -o NAME,SIZE,TYPE,MOUNTPOINT"], check=True, timeout=45)


def update_reference():
    ssh(f"""from pathlib import Path
p=Path({REMOTE!r})
assert not (p/'LEDGER.json').exists()
(p/'reference').rename(p/'reference_attempt01')
(p/'montage_assets/montage_task.py').rename(p/'montage_task_attempt01.py')
(p/'HASHES.json').rename(p/'HASHES_attempt01.json')
""", 40)
    for relative in ("montage_assets/montage_task.py", "HASHES.json"):
        subprocess.run(SCP + [str(BASE / "payload" / relative), "dme-campaign:" + REMOTE + "/" + relative],
                       check=True, timeout=150)
    ssh(f"""import json,hashlib
from pathlib import Path
p=Path({REMOTE!r})
for name,digest in json.loads((p/'HASHES.json').read_text()).items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
""", 40)

def task(script, *args, timeout):
    subprocess.run(SSH + [shlex.join(["python3", REMOTE + "/" + script, *args])], check=True, timeout=timeout)


def status():
    ssh(f"""from pathlib import Path
import json, subprocess
p=Path({REMOTE!r})
for name in ('PLAN_ACCOUNTS.json','RESULTS.json','COMPLETE.json','STOPPED.json'):
    f=p/name
    if f.exists():
        value=json.loads(f.read_text())
        if name=='PLAN_ACCOUNTS.json': value={{k:{{a:b for a,b in v.items() if a!='directions'}} for k,v in value.items()}}
        print(name,json.dumps(value))
subprocess.run(['condor_q','-allusers','-totals'],check=True)
""", 50)


def download():
    files = BASE / "evidence"
    files.mkdir(exist_ok=True)
    ssh(f"""from pathlib import Path
import tarfile
p=Path({REMOTE!r})
names=['SPECS.json','REFERENCE.json','PLAN_ACCOUNTS.json','FROZEN_DESIGN.json','FITS_EQUIVALENCE.json',
       'RESULTS.json','LEDGER.json','COMPLETE.json','STOPPED.json','PREFLIGHT.json','capsules']
if not (p/'evidence.tar').exists():
    with tarfile.open(p/'evidence.new.tar','w') as archive:
        for name in names:
            if (p/name).exists(): archive.add(p/name,arcname=name)
    (p/'evidence.new.tar').rename(p/'evidence.tar')
""", 160)
    sftp = ["sftp", "-B", "131072", "-R", "64", "-F", str(SESSION / "ssh_config"),
            "-b", "-", "dme-campaign"]
    local = (files / "evidence.tar").as_posix()
    subprocess.run(sftp, input=f'reget "{REMOTE}/evidence.tar" "{local}"\n', text=True,
                   check=True, timeout=950)
    import tarfile
    with tarfile.open(files / "evidence.tar") as archive:
        archive.extractall(files, filter="data")
    import hashlib
    for capsule in (files / "capsules").glob("*.tar.xz"):
        receipt = json.loads(capsule.with_suffix(".sha256.json").read_text())
        with capsule.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == receipt["sha256"]
    print("Capsules verified.")


def compact():
    files = BASE / "evidence"
    files.mkdir(exist_ok=True)
    ssh(f"""from pathlib import Path
import tarfile
p=Path({REMOTE!r})
with tarfile.open(p/'compact.tar.gz','w:gz') as archive:
    for name in ['RESULTS.json','FITS_EQUIVALENCE.json','COMPLETE.json','PLAN_ACCOUNTS.json','LEDGER.json']:
        archive.add(p/name,arcname=name)
    for cid in ['M101-BASE','M101-PROJ','M101-FINAL']:
        source=p/'cases'/cid/'pilot'/cid/'INDEPENDENT_AUDIT.json'
        archive.add(source,arcname=f'audits/{{cid}}.json')
""", 60)
    target = files / "compact.tar.gz"
    subprocess.run(SCP + ["dme-campaign:" + REMOTE + "/compact.tar.gz", str(target)],
                   check=True, timeout=140)
    import tarfile
    with tarfile.open(target) as archive:
        archive.extractall(files, filter="data")
    print("Verified result files and independent audits downloaded.")

def preflight():
    ssh(f"""import json,shutil,subprocess
from pathlib import Path
p=Path({REMOTE!r})
free=shutil.disk_usage(p).free
assert free>5*2**30,free
data=dict(freeBytes=free,pegasus=subprocess.check_output(['pegasus-version'],text=True).strip(),
          condor=subprocess.check_output(['condor_version'],text=True).splitlines()[0])
(p/'PREFLIGHT.json').write_text(json.dumps(data,indent=2))
print(data)
""", 50)
    task("design.py", timeout=720)


def preview():
    ssh(f"""import sys
import importlib.resources
from pathlib import Path
p=Path({REMOTE!r})
sys.path.insert(0,str(p/'reference_attempt01/.toolkit-P01'))
sys.modules.setdefault('importlib_resources',importlib.resources)
from MontagePy.main import mViewer
source=p/'cases/M101-BASE/plans/M101-BASE/outputs/m101.fits'
out=p/'m101_preview.png'
result=mViewer(f'-gray {{source}} 0% 100% gaussian-log',str(out),mode=2,outFmt='png')
assert int(result.get('status',-1))==0 and out.stat().st_size>1000,result
print('Preview from the measured baseline FITS:',result.get('nx'),result.get('ny'))
""", 60)
    subprocess.run(SCP + ["dme-campaign:" + REMOTE + "/m101_preview.png", str(BASE / "m101_preview.png")],
                   check=True, timeout=90)

if __name__ == "__main__":
    command = sys.argv[1]
    if command in {"upload", "preflight", "status", "download", "storage", "update_reference", "preview", "compact"}:
        globals()[command]()
    elif command in {"plan", "run"}:
        task("measure.py", command, timeout=2400)
    else:
        raise ValueError(command)
