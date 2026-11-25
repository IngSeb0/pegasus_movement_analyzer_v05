"""New bounded VM session manager. Uses existing resources only."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,os,json,time,urllib.request,argparse
ROOT=Path(__file__).resolve().parents[1];BASE=Path(__file__).parent
CFG=json.loads((ROOT/'azure_cloud_20261025/cluster.json').read_text())
AZ=Path(r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe')
ENV=dict(os.environ,AZURE_CONFIG_DIR=str(ROOT/'.azure-cli-session'))
def now():return datetime.now(timezone.utc)
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2),encoding='utf-8')
def az(*args):
 p=subprocess.run([str(AZ),'-IBm','azure.cli',*args,'--subscription',CFG['subscriptionId'],'--only-show-errors','-o','json'],env=ENV,text=True,capture_output=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr[-2000:])
 return json.loads(p.stdout)if p.stdout.strip()else None
def inventory():
 vms=az('vm','list','-g',CFG['resourceGroup'],'--show-details')
 assert len(vms)==5 and {v['name']for v in vms}=={'dme-master',*[f'dme-worker{i}'for i in range(1,5)]}
 assert all(v['tags'].get('managedBy')=='dme-azure-20261025'for v in vms)
 return vms
def close(folder,reason):
 save(folder/'STOP_NEW_SUBMISSIONS.json',dict(reason=reason,atUtc=now().isoformat()))
 vms=inventory()
 names=[v['name']for v in vms if v['name']in ['dme-master','dme-worker1','dme-worker2']and v['powerState']!='VM deallocated']
 with ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(lambda n:az('vm','deallocate','-g',CFG['resourceGroup'],'--name',n,'--no-wait'),names))
 for _ in range(60):
  vms=inventory()
  if all(v['powerState']=='VM deallocated'for v in vms):break
  time.sleep(4)
 save(folder/'VM_FINAL_SESSION.json',[dict(name=v['name'],powerState=v['powerState'])for v in vms])
 assert all(v['powerState']=='VM deallocated'for v in vms)
 before=folder/'SSH_RULE_BEFORE.json'
 if before.exists():
  rule=json.loads(before.read_text());changed=az('network','nsg','rule','update','-g',CFG['resourceGroup'],'--nsg-name',rule['nsg'],'--name',rule['name'],'--source-address-prefixes',*rule['prefixes'])
  actual=changed.get('sourceAddressPrefixes')or[changed.get('sourceAddressPrefix')]
  assert actual==rule['prefixes'];save(folder/'SSH_RULE_RESTORED.json',dict(restored=True))
 save(folder/'SESSION_CLOSED.json',dict(closedAtUtc=now().isoformat(),reason=reason,allFiveDeallocated=True,disksAndIpsPreserved=True))
def start(folder):
 assert not(folder/'SESSION_START.json').exists(),'New session directory required'
 ready=json.loads((BASE/'PREPARATION.json').read_text());assert ready['offlineChecksPassed']
 import hashlib
 assert hashlib.sha256((BASE/'payload.tar.gz').read_bytes()).hexdigest()==ready['payloadSha256']
 assert all(v['powerState']=='VM deallocated'for v in inventory())
 candidates=[]
 for nsg in az('network','nsg','list','-g',CFG['resourceGroup']):
  for r in nsg.get('securityRules',[]):
   if r.get('destinationPortRange')=='22'and r['access']=='Allow'and r['direction']=='Inbound':
    candidates.append(dict(nsg=nsg['name'],name=r['name'],prefixes=r.get('sourceAddressPrefixes')or[r['sourceAddressPrefix']]))
 assert len(candidates)==1 and all(candidates[0]['prefixes']);save(folder/'SSH_RULE_BEFORE.json',candidates[0])
 began=now();deadline=began+timedelta(minutes=90)
 save(folder/'SESSION_START.json',dict(startedAtUtc=began.isoformat(),deadlineUtc=deadline.isoformat(),stopSubmissionsUtc=(began+timedelta(minutes=60)).isoformat(),maximumNewWorkflows=3,resources=['dme-master','dme-worker1','dme-worker2'],authorization='Montage M101 complete workflow requested on 2026-11-11; scope in PROTOCOLO.md.'))
 try:
  for guard in ['primary','backup']:
   with (folder/f'guard_{guard}.log').open('w')as log:
    proc=subprocess.Popen([sys.executable,str(Path(__file__)), 'guard','--session',folder.name,'--guard-id',guard],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   for _ in range(30):
    if(folder/f'GUARD_READY_{guard}.json').exists():break
    assert proc.poll()is None;time.sleep(.25)
   assert(folder/f'GUARD_READY_{guard}.json').exists()
  with ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(lambda n:az('vm','start','-g',CFG['resourceGroup'],'--name',n),['dme-master','dme-worker1','dme-worker2']))
  address=urllib.request.urlopen('https://api.ipify.org',timeout=20).read().decode().strip()
  import ipaddress;assert ipaddress.ip_address(address).version==4
  rule=candidates[0];changed=az('network','nsg','rule','update','-g',CFG['resourceGroup'],'--nsg-name',rule['nsg'],'--name',rule['name'],'--source-address-prefixes',address+'/32')
  vms=inventory();master=next(v for v in vms if v['name']=='dme-master');assert master['publicIps']
  key=ROOT/'azure_cloud_20261025/.local/id_ed25519_dme';assert key.is_file()
  (folder/'ssh_config').write_text(f'Host dme-campaign\n  HostName {master["publicIps"]}\n  User dmeadmin\n  IdentityFile {key.as_posix()}\n  StrictHostKeyChecking accept-new\n  BatchMode yes\n  ConnectTimeout 15\n  ServerAliveInterval 15\n',encoding='ascii')
  save(folder/'STARTED.json',dict(atUtc=now().isoformat(),deadlineUtc=deadline.isoformat()))
  print('Session started; deadline '+deadline.isoformat(),flush=True)
 except Exception:
  close(folder,'start_failure');raise
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['status','start','close','guard']);p.add_argument('--session',default='session01');p.add_argument('--guard-id');a=p.parse_args();folder=BASE/a.session;assert a.session in ['session01','session02','session03'];folder.mkdir(exist_ok=True)
 if a.action=='status':print(json.dumps([dict(name=v['name'],powerState=v['powerState'],location=v['location'],size=v['hardwareProfile']['vmSize'])for v in inventory()],indent=2));return
 if a.action=='start':start(folder)
 elif a.action=='close':close(folder,'normal_close')
 else:
  session=json.loads((folder/'SESSION_START.json').read_text());stop=datetime.fromisoformat(session['deadlineUtc'])-timedelta(minutes=10)
  save(folder/f'GUARD_READY_{a.guard_id}.json',dict(pid=os.getpid(),closeAtUtc=stop.isoformat()))
  while now()<stop:
   if(folder/'SESSION_CLOSED.json').exists():return
   time.sleep(5)
  close(folder,'deadline_'+a.guard_id)
if __name__=='__main__':main()
