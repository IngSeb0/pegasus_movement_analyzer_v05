"""Prospective bounded execution; native evidence is independent of predictions."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
import argparse,copy,fcntl,hashlib,json,os,re,shutil,subprocess,sys,tarfile,time,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'runtime'),str(ROOT/'core'),'/usr/lib/pegasus/python','/usr/lib/pegasus/externals/python']
import yaml
from generate_workflow import prepare_run
from inspect_plan import inspect_plan,attrs
import audit_native
from pegasus_movement.analyzer_v1 import analyze_run_v1,overall_status
from pegasus_movement.reporting import write_reports
def read(p):return json.loads(Path(p).read_text())
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def command(args,cwd=None,timeout=120,prefix=None):
 p=subprocess.run([str(x)for x in args],cwd=cwd,text=True,capture_output=True,timeout=timeout)
 if prefix:
  Path(str(prefix)+'.stdout').write_text(p.stdout);Path(str(prefix)+'.stderr').write_text(p.stderr)
 if p.returncode:raise RuntimeError(str(args[0])+' failed: '+p.stderr[-2500:])
 return p.stdout
def frozen():
 for path,digest in read(ROOT/'HASHES.json').items():assert sha(ROOT/path)==digest,path
def session():return read(ROOT/'SESSION_ACTIVE.json')
def admission():
 s=session();stop=datetime.fromisoformat(s['stopSubmissionsUtc']).timestamp();hard=datetime.fromisoformat(s['deadlineUtc']).timestamp()
 assert time.time()<stop and hard-time.time()>600,'Window expired'
 assert not(ROOT/'STOP_NEW_SUBMISSIONS').exists()
 ledger=read(ROOT/'LEDGER.json')if(ROOT/'LEDGER.json').exists()else[]
 assert len(ledger)<s['maximumNewWorkflows']
 assert shutil.disk_usage(ROOT).free>3*2**30+200*2**20,'Storage reserve'
 return s,ledger
def idle():
 for _ in range(40):
  admission();q=json.loads(command(['condor_q','-allusers','-json'],timeout=30)or'[]');slots=json.loads(command(['condor_status','-json'],timeout=30)or'[]')
  assert {s['Machine']for s in slots}=={'dme-worker1','dme-worker2'}
  parents=[s for s in slots if s.get('PartitionableSlot')]
  if not q and len(parents)==2 and all(s.get('State')=='Unclaimed'and s.get('Cpus')==1 for s in parents):return
  time.sleep(3)
 raise RuntimeError('Pool not idle')
def prepare(row):
 cid=row['condition'];base=ROOT/'cases'/row['id'];case=base/'plans'/cid;ev=base/'pilot'/cid
 if(ev/'STATE.json').exists():
  state=read(ev/'STATE.json');assert state['status']=='PREPARED';return base,case,ev,state,read(ev/'SPEC.json'),Path(state['run'])
 ev.mkdir(parents=True,exist_ok=False);spec=copy.deepcopy(read(ROOT/'SPECS.json')[cid]);save(ev/'STATE.json',dict(status='PREPARING',submitted=False))
 prepare_run(spec,case,{'master':'dme-master','W1':'dme-worker1','W2':'dme-worker2'},row['block'],ROOT/'SPECS.json')
 if spec.get('application')=='montage':
  program=(ROOT/'montage_assets/montage_task.py').read_bytes().replace(b'\r\n',b'\n');assert program.split(b'\n',1)[0]==b'#!/usr/bin/env python3'
  (case/'bin/campaign_task.py').write_bytes(program);(case/'bin/campaign_task.py').chmod(0o755)
  for n in spec['dag']['external_inputs']:shutil.copyfile(ROOT/'montage_assets'/n,case/'inputs'/n)
  meta=read(case/'meta.json');meta['program_version']='MontagePy2.3.0';meta['input_artifacts']=[dict(file=n,bytes=(case/'inputs'/n).stat().st_size,sha256=sha(case/'inputs'/n))for n in spec['dag']['external_inputs']];save(case/'meta.json',meta)
 props=case/'pegasus.properties';props.write_text(props.read_text()+'dagman.retry=0\n')
 wf=yaml.safe_load((case/'workflow.yml').read_text());grouped=any(len(g)>1 for g in spec['groups'])
 if grouped:
  wf['transformationCatalog']['transformations'].append({'namespace':'pegasus','name':'seqexec','sites':[{'name':'condorpool','pfn':'/usr/bin/pegasus-cluster','type':'installed','arch':'x86_64','os.type':'linux'}]})
  labels={t:'group_'+str(i+1)for i,g in enumerate(spec['groups'])if len(g)>1 for t in g}
  for j in wf['jobs']:
   if j['id']in labels:j.setdefault('profiles',{}).setdefault('pegasus',{})['label']=labels[j['id']]
 wf.setdefault('metadata',{}).update(prospective_study='montage-m101-20261111',study_case=row['id'])
 source=case/'workflow_for_plan.yml';source.write_text(yaml.safe_dump(wf,sort_keys=False))
 args=['pegasus-plan','--conf',props,'--dir',case/'submit','--sites','condorpool','--output-sites','local','--cleanup','none']
 if grouped:args+=['--cluster','label']
 args+=['-Xms16m','-Xmx128m','--json',source]
 command(args,cwd=case,timeout=180,prefix=ev/'plan')
 runs=list((case/'submit').rglob('braindump.yml'));assert len(runs)==1;run=runs[0].parent
 patch=[]
 if spec.get('return_policy')=='finals_only':
  for p in run.rglob('*.sub'):
   a=attrs(p)
   if a.get('+pegasus_job_class')!='1':continue
   before=p.read_text();old=a.get('transfer_output_files','');tokens=old.split(',');omitted=set(spec['omit_returns']);keep=[n for n in tokens if Path(n.strip()).name not in omitted]
   assert {Path(n.strip()).name for n in tokens}- {Path(n.strip()).name for n in keep}==omitted
   after=re.sub(r'(?m)^(transfer_output_files\s*=\s*).*$',lambda m:m[1]+','.join(keep),before,flags=re.I)
   assert after!=before;p.write_text(after);patch.append(dict(file=str(p),before=before,after=after,only_contract=True))
  assert len(patch)==1;save(ev/'CONTRACT_PATCH.json',patch)
 review=inspect_plan(run,spec);assert all(int(line.split()[2])==0 for line in review['retry_policy'])
 if not(run/'workflow.yml').exists():shutil.copyfile(source,run/'workflow.yml')
 state=dict(status='PREPARED',uuid=yaml.safe_load(runs[0].read_text())['root_wf_uuid'],run=str(run),submitted=False,program_sha256=sha(case/'bin/campaign_task.py'))
 save(ev/'SPEC.json',spec);save(ev/'PLAN_REVIEW.json',review);save(ev/'STATE.json',state)
 return base,case,ev,state,spec,run
def archive(case,ev,row):
 out=ROOT/'capsules'/(row['id']+'.tar.xz');out.parent.mkdir(exist_ok=True);excluded=[]
 def filt(m):
  if Path(m.name).name.startswith('pegasus-worker-')and m.name.endswith('.tar.gz'):
   path=case/Path(m.name).relative_to(Path('plans')/case.name);excluded.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path)));return None
  return m
 with tarfile.open(out,'w:xz',preset=1)as t:t.add(case,arcname='plans/'+case.name,filter=filt);t.add(ev,arcname='pilot/'+ev.name)
 save(out.with_suffix('.sha256.json'),dict(bytes=out.stat().st_size,sha256=sha(out),excluded_static_bundles=excluded,scope='Native administrative sources, scientific inputs/finals and task outputs; excludes only static Pegasus worker archives, preserved on remote filesystem.'))
def share_static(case,ev):
 # Only immutable new Pegasus worker packages; no scientific files or historical paths.
 cache=ROOT/'static_worker_bundles';cache.mkdir(exist_ok=True)
 receipt=read(ev/'STATIC_PACKAGE_LINKS.json')if(ev/'STATIC_PACKAGE_LINKS.json').exists()else[]
 for p in case.rglob('pegasus-worker-*.tar.gz'):
  assert p.resolve().is_relative_to((ROOT/'cases').resolve())
  digest=sha(p);canonical=cache/(digest+'.tar.gz');before=p.stat()
  if not canonical.exists():os.link(p,canonical)
  else:
   assert sha(canonical)==digest and canonical.stat().st_size==before.st_size
   if p.stat().st_ino==canonical.stat().st_ino:continue
   tmp=p.with_name(p.name+'.shared');assert not tmp.exists();os.link(canonical,tmp);os.replace(tmp,p)
  assert sha(p)==digest
  receipt.append(dict(path=str(p),canonical=str(canonical),sha256=digest,bytes=before.st_size,prior_mtime_ns=before.st_mtime_ns,scope='new immutable static worker package only; bytes and logical paths preserved'))
 save(ev/'STATIC_PACKAGE_LINKS.json',receipt)
def execute(row):
 frozen();idle();base,case,ev,state,spec,run=prepare(row);share_static(case,ev);idle();s,ledger=admission()
 assert not any(r['id']==row['id']or r['uuid']==state['uuid']for r in ledger)
 ledger.append(dict(id=row['id'],uuid=state['uuid'],condition=row['condition'],phase=row['phase'],block=row['block'],submittedAtUtc=utc(),sessionStart=s['startedAtUtc']));save(ROOT/'LEDGER.json',ledger)
 state.update(status='SUBMITTED',submitted=True);save(ev/'STATE.json',state)
 command(['pegasus-run',run],timeout=60,prefix=ev/'submission')
 deadline=min(time.time()+800,datetime.fromisoformat(s['deadlineUtc']).timestamp()-300)
 while True:
  exits=[int(n)for p in run.glob('*.dag.dagman.out')for n in re.findall(r'EXITING WITH STATUS\s+(\d+)',p.read_text(errors='replace'))]
  if exits:assert exits[-1]==0,'Workflow failed';break
  assert time.time()<deadline and not(ROOT/'STOP_NEW_SUBMISSIONS').exists(),'Workflow time limit'
  time.sleep(1)
 constraint='pegasus_root_wf_uuid == '+json.dumps(state['uuid'])
 for flag,name in [('-json','history.json'),('-long','history.long')]:
  (ev/name).write_text(command(['condor_history',flag,'-constraint',constraint],timeout=40))
 analyzed=analyze_run_v1(run,history_file=ev/'history.long');write_reports(analyzed,ev/'reports')
 state.update(status='ANALYZED_PENDING_INDEPENDENT_AUDIT',report_file=str(ev/'reports/analysis.json'));save(ev/'STATE.json',state)
 share_static(case,ev)
 audit_native.ROOT=base;audit=audit_native.audit(row['condition'],spec);save(ev/'INDEPENDENT_AUDIT.json',audit)
 assert not audit['errors'],audit['errors'];assert str(overall_status(analyzed))=='VALID'
 expected=read(ROOT/'PLAN_ACCOUNTS.json')[row['condition']]
 matches=audit['required_bytes']==expected['required']and audit['observed_bytes']==expected['observed']
 metrics=list(run.glob('*.dag.metrics'));assert len(metrics)==1;dag=read(metrics[0]);assert dag['exitcode']==0
 result=dict(**row,uuid=state['uuid'],required_bytes=audit['required_bytes'],observed_bytes=audit['observed_bytes'],dme=audit['dme_exact'],predictions_match=matches,duration_s=dag['end_time']-dag['start_time'],obligations=sum(f['n_f']for f in audit['files'].values()),deliveries=len(audit['deliveries']),directions=len(audit['directions']),all_exact=all(d['exact']for d in audit['directions']),final_files=audit['final_files'],placement={t:j['worker']for j in audit['jobs']for t in j['members']},acceptedAtUtc=utc())
 state.update(status='ACCEPTED',accepted=True);save(ev/'STATE.json',state);save(ev/'ACCEPTANCE.json',result)
 archive(case,ev,row)
 accepted=read(ROOT/'RESULTS.json')if(ROOT/'RESULTS.json').exists()else[];accepted.append(result);save(ROOT/'RESULTS.json',accepted)
 print(json.dumps(dict(accepted=len(accepted),last=result)),flush=True)
 # Discrepancies are preserved and stop advance; they are not excluded as scientific results.
 assert matches,'Observed prediction discrepancy; retained, inspect before advance'
 frozen()
