"""Azure Run Command fallback when the local network drops SSH handshakes."""

import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import sys

import cloud


BASE = Path(__file__).resolve().parent
REMOTE = "/mnt/montage_m101_20261111"


def invoke(*scripts):
    reply = cloud.az("vm", "run-command", "invoke", "-g", cloud.CFG["resourceGroup"],
                     "-n", "dme-master", "--command-id", "RunShellScript", "--scripts", *scripts)
    for row in reply["value"]:
        print(row["message"])


def bootstrap():
    payload = BASE / "payload"
    names = ["design.py", "measure.py", "runtime/run_study.py"]
    texts = {name: (payload / name).read_text(encoding="utf-8") for name in names}
    texts["mosaic_task.py"] = (BASE / "mosaic_task.py").read_text(encoding="utf-8")
    setup = {
        "files": texts,
        "session": json.loads((BASE / "session01/SESSION_START.json").read_text()),
        "hashes": json.loads((payload / "HASHES.json").read_text()),
        "tutorial": json.loads((BASE / "PREPARATION.json").read_text())["tutorialSha256"],
    }
    packed = base64.b64encode(gzip.compress(json.dumps(setup).encode())).decode()
    code = f"""import ast,base64,gzip,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
root=Path({REMOTE!r})
old=Path('/srv/dme/campana_dme_20261108')
setup=json.loads(gzip.decompress(base64.b64decode({packed!r})))
assets=root/'montage_assets'
assets.mkdir(exist_ok=True)
archive=root/'tutorial.tar.gz'
subprocess.run(['curl','-fsSL','--max-time','55',
    'https://irsa.ipac.caltech.edu/Montage/docs/m101Example/tutorial-initial.tar.gz','-o',str(archive)],check=True)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==setup['tutorial']
with tarfile.open(archive) as t:
    for m in t:
        if m.isfile() and m.name.endswith(('.fits','template.hdr')):
            with t.extractfile(m) as a,(assets/Path(m.name).name).open('wb') as b:
                shutil.copyfileobj(a,b)
for name in setup['hashes']:
    if name.startswith('core/') or (name.startswith('runtime/') and name not in setup['files']):
        dest=root/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((old/name).read_bytes().replace(b'\\r\\n',b'\\n') if name.startswith('runtime/') else (old/name).read_bytes())
for name,content in setup['files'].items():
    if name=='mosaic_task.py':
        line=next(line for line in (old/'montage_assets/montage_task.py').read_text().splitlines() if line.startswith('WHEEL='))
        encoded=ast.literal_eval(line.split('=',1)[1])
        if isinstance(encoded,str): encoded=encoded.encode('ascii')
        content+='\\nWHEEL = '+repr(encoded)+"\\n\\nif __name__ == '__main__':\\n    main()\\n"
        name='montage_assets/montage_task.py'
    (root/name).write_text(content)
for name,digest in setup['hashes'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
(root/'HASHES.json').write_text(json.dumps(setup['hashes']))
(root/'SESSION_ACTIVE.json').write_text(json.dumps(setup['session']))
print('All M101 inputs and program hashes verified.')
"""
    command = shlex.join(["runuser", "-u", "dmeadmin", "--", "python3", "-c", code])
    invoke(command)


def start(action):
    commands = {"reference": ("design.py",), "plan": ("measure.py", "plan"), "run": ("measure.py", "run")}
    script, *args = commands[action]
    invoke(shlex.join(["systemd-run", "--unit", f"dme-m101-{action}", "--uid", "dmeadmin",
                       "--property", "RuntimeMaxSec=2300", "--working-directory", REMOTE,
                       "/usr/bin/python3", REMOTE + "/" + script, *args]))


def status():
    action = sys.argv[2]
    if action not in {"reference", "plan", "run"}:
        raise ValueError(action)
    invoke("journalctl -u dme-m101-" + action + " -n 18 --no-pager",
           "ls -1 " + REMOTE + " | tail -25")


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "bootstrap":
        bootstrap()
    elif action == "status":
        status()
    else:
        start(action)
