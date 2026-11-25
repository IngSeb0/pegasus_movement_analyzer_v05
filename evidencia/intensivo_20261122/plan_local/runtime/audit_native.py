"""Auditoría independiente del par: no importa Analyzer ni ejecuta workflows."""
from pathlib import Path
from fractions import Fraction
import collections,hashlib,json,re,shlex,sys
sys.path[:0]=['/usr/lib/pegasus/python','/usr/lib/pegasus/externals/python']
import yaml
ROOT=Path('/srv/dme/campaign_cloud_20261026')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def attrs(p):
 d={};buf=''
 for raw in p.read_text().splitlines():
  line=buf+raw.strip()
  if line.endswith('\\'):buf=line[:-1]+' ';continue
  buf=''
  if not line or line.startswith('#') or '=' not in line:continue
  k,v=line.split('=',1);d[k.strip().lower()]=v.strip().strip('"')
 return d
def names(value):return [x.strip() for x in str(value or '').split(',') if x.strip()]
def stat(ad,key,field):
 v=ad.get(key,{})
 if isinstance(v,dict):return v.get(field)
 m=re.search(r'\b'+re.escape(field)+r'\s*=\s*(\d+)',str(v));return int(m[1]) if m else None
def resolve(path,run,case,ad,direction):
 p=Path(path);cand=[p] if p.is_absolute() else [Path(ad.get('Iwd','/'))/p,run/p,case/'bin'/p]
 if direction=='output':cand=[Path(str(x)+'.000') for x in cand]+cand
 for x in cand:
  if x.is_file():return x
 # The executable staged under transformation name has the original .py path.
 if Path(path).name=='campaign_task':
  x=case/'bin/campaign_task.py'
  if x.is_file():return x
 raise ValueError('No se puede resolver auxiliar '+path)
def audit(cid,spec):
 case=ROOT/'plans'/cid;ev=ROOT/'pilot'/cid
 state=json.loads((ev/'STATE.json').read_text());run=Path(state['run'])
 if state['status']!='ANALYZED_PENDING_INDEPENDENT_AUDIT':raise ValueError('Caso incompleto '+cid+': '+state['status'])
 wf=run/'workflow.yml';workflow=yaml.safe_load(wf.read_text());tasks={j['id']:j for j in workflow['jobs']}
 ads=json.loads((ev/'history.json').read_text());ads=[a for a in ads if a.get('pegasus_job_class')==1]
 bynode=collections.defaultdict(list)
 for a in ads:bynode[a['pegasus_wf_dag_job_id']].append(a)
 mapping={};jobs=[];errors=[];placement={};sources=[]
 for p in sorted(run.rglob('*.sub')):
  attr=attrs(p)
  if attr.get('+pegasus_job_class')!='1':continue
  node=attr['+pegasus_wf_dag_job_id'];dax=attr.get('+pegasus_wf_dax_job_id')
  if dax and dax.lower() not in {'null','undefined'}:members=[dax]
  else:
   native=p.with_suffix('.in');text=native.read_text()
   members=re.findall(r'^#@\s+\d+\s+\S+\s+(\S+)\s*$',text,re.M)
   commands=[]
   for line in text.splitlines():
    if not line.strip() or line.lstrip().startswith('#'):continue
    tokens=shlex.split(line)
    if Path(tokens[0]).name!='pegasus-kickstart' or tokens.count('-N')!=1:raise ValueError('Lista nativa inesperada')
    commands.append(tokens[tokens.index('-N')+1])
   if commands!=members or len(members)!=int(attr['+pegasus_cluster_size']):raise ValueError('Miembros no corroborados')
   sources.append({'path':str(native),'sha256':sha(native)})
  matches=bynode.pop(node,[])
  if len(matches)!=1:raise ValueError('Debe existir exactamente un historial para '+node)
  ad=matches[0]
  if ad.get('pegasus_root_wf_uuid')!=state['uuid']:raise ValueError('UUID distinto')
  if ad.get('JobStatus')!=4 or ad.get('ExitCode')!=0 or ad.get('ExitBySignal') is not False:raise ValueError('Terminación no satisfactoria')
  counts={k:ad.get(k) for k in ['JobRunCount','NumJobStarts','NumShadowStarts','NumInputTransferStarts','NumOutputTransferStarts']}
  if any(counts[k]!=1 for k in ['NumJobStarts','NumInputTransferStarts','NumOutputTransferStarts']):raise ValueError('Ejecución o transferencias repetidas: '+str(counts))
  if counts['JobRunCount'] is None or counts['JobRunCount']<1 or counts['NumShadowStarts']!=counts['JobRunCount']:raise ValueError('Alias de arranques contradictorio: '+str(counts))
  eventlogs=list(run.glob('*.dag.nodes.log'))
  if len(eventlogs)!=1:raise ValueError('Fuente de eventos de jobs ambigua')
  eventcounts=collections.Counter(code for code,cluster,proc in re.findall(r'(?m)^(\d{3}) \((\d+)\.(\d+)\.\d+\)',eventlogs[0].read_text()) if int(cluster)==ad['ClusterId'] and int(proc)==ad['ProcId'])
  if any(eventcounts[k]!=1 for k in ['000','001','005']) or any(eventcounts[k] for k in ['004','007','009']):raise ValueError('Eventos de ejecución incompletos o repetidos: '+str(eventcounts))
  sources.append({'path':str(eventlogs[0]),'sha256':sha(eventlogs[0])})
  host=ad.get('LastRemoteHost',ad.get('RemoteHost','')).split('@')[-1]
  expected_workers={t['task_id']:'dme-worker'+t['assigned_worker'][1:] for t in spec['dag']['tasks']}
  if any(host!=expected_workers.get(t) for t in members):raise ValueError('Asignacion observada distinta del diseno')
  for t in members:
   if t not in tasks or t in mapping:raise ValueError('Identidad ausente o repetida')
   mapping[t]=node;placement[t]=host
  sources.append({'path':str(p),'sha256':sha(p)})
  jobs.append({'node':node,'members':members,'worker':host,'global_job_id':ad['GlobalJobId'],'counts':counts,'event_counts':dict(eventcounts),'ad':ad,'submit':attr})
 if set(mapping)!=set(tasks) or bynode:raise ValueError('Cobertura de identidades incompleta')
 metadata=collections.defaultdict(list)
 for p in sorted(run.rglob('*.meta')):
  try:records=json.loads(p.read_text())
  except (ValueError,UnicodeError):continue
  if not isinstance(records,list):continue
  for m in records:
   if isinstance(m,dict) and m.get('_type')=='file' and 'size' in m.get('_attributes',{}):
    a=m['_attributes'];metadata[m['_id']].append({'bytes':int(a['size']),'checksum':a.get('checksum.value'),'path':str(p),'sha256':sha(p)})
 files={}
 for t,j in tasks.items():
  for u in j.get('uses',[]):
   f=files.setdefault(u['lfn'],{'producer':None,'consumers':[],'final':False})
   if u['type']=='output':
    if f['producer'] is not None:raise ValueError('Productor duplicado')
    f['producer']=t;f['final']=bool(u.get('stageOut',False))
   elif u['type']=='input':f['consumers'].append(t)
 for name,f in files.items():
  records=metadata[name]
  sizes={m['bytes'] for m in records};checksums={m['checksum'] for m in records if m['checksum']}
  if len(sizes)!=1 or len(checksums)!=1:raise ValueError('Metadatos ausentes o contradictorios: '+name)
  f['bytes']=next(iter(sizes));f['checksum']=next(iter(checksums));f['metadata']=records
  f['origin']=placement[f['producer']] if f['producer'] else 'dme-master'
  dest={placement[t] for t in f['consumers']}
  if f['final'] or (f['producer'] and any(d not in {f['origin'],'dme-master'} for d in dest)):dest.add('dme-master')
  f['destinations']=sorted(dest-{f['origin']});f['n_f']=len(f['destinations'])
  f['required_bytes']=f['bytes']*f['n_f']
 # Verificar el orden científico, además de la pertenencia declarada por el plan.
 for name,f in files.items():
  if f['producer'] is None:continue
  for consumer in f['consumers']:
   for job in jobs:
    members=job['members']
    if f['producer'] in members and consumer in members and members.index(f['producer'])>=members.index(consumer):raise ValueError('Orden interno viola dependencia '+name)
 for dep in workflow.get('jobDependencies',[]):
  for child in dep.get('children',[]):
   for job in jobs:
    members=job['members']
    if dep['id'] in members and child in members and members.index(dep['id'])>=members.index(child):raise ValueError('Orden interno viola dependencia explícita')
 if {frozenset(j['members']) for j in jobs}!={frozenset(g) for g in spec['groups']}:raise ValueError('Agrupacion distinta de la condicion')
 if set(tasks)!={t['task_id'] for t in spec['dag']['tasks']}:raise ValueError('Identidades cientificas distintas del diseno')
 if set(files)!={f['file_id'] for f in spec['files']}:raise ValueError('Archivos cientificos distintos del diseno')
 for declaration in spec['files']:
  actual=files[declaration['file_id']]
  if actual['bytes']!=declaration['size_bytes'] or actual['producer']!=declaration['producer_task'] or set(actual['consumers'])!=set(declaration['consumer_tasks']) or actual['final']!=(declaration['role']=='final'):raise ValueError('Fuente nativa contradice la condicion: '+declaration['file_id'])
 required=sum(f['required_bytes'] for f in files.values());deliveries=[];directions=[]
 for j in jobs:
  ad=j.pop('ad');attr=j.pop('submit')
  for direction,key,statskey in [('input','TransferInput','TransferInputStats'),('output','TransferOutput','TransferOutputStats')]:
   raw_contract=names(ad.get(key));planned=names(attr.get('transfer_'+direction+'_files'))
   if [Path(x).name for x in raw_contract]!=[Path(x).name for x in planned]:raise ValueError('Contrato nativo distinto del plan: '+j['node']+' '+direction)
   # Un token idéntico repetido en una misma lista no crea otra entrega.
   # No se deduplican jobs ni rutas diferentes que colisionen por basename.
   contract=list(dict.fromkeys(raw_contract))
   native_names=[Path(x).name for x in contract];planned_names=[Path(x).name for x in dict.fromkeys(planned)]
   if native_names!=planned_names:raise ValueError('Contrato nativo distinto del plan: '+j['node']+' '+direction)
   if len(native_names)!=len(set(native_names)):raise ValueError('Contrato con nombres repetidos')
   scientific=[n for n in native_names if n in files]
   for n in scientific:
    f=files[n]
    if direction=='input' and not any(mapping[t]==j['node'] for t in f['consumers']):raise ValueError('Entrada científica ajena al job')
    if direction=='output' and mapping.get(f['producer'])!=j['node']:raise ValueError('Salida científica ajena al job')
   aux=[p for p in contract if Path(p).name not in files]
   aux+= [ad['Cmd']] if direction=='input' else [ad['Out'],ad['Err']]
   auxrecords=[]
   for name in aux:
    p=resolve(name,run,case,ad,direction)
    auxrecords.append({'contract_path':name,'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
   sci=sum(files[n]['bytes'] for n in scientific);auxbytes=sum(a['bytes'] for a in auxrecords)
   total=stat(ad,statskey,'CedarSizeBytesTotal');last=stat(ad,statskey,'CedarSizeBytesLastRun')
   count=stat(ad,statskey,'CedarFilesCountTotal');lastcount=stat(ad,statskey,'CedarFilesCountLastRun')
   expected_count=len(contract)+(1 if direction=='input' else 2)
   exact=total is not None and total==last and total==sci+auxbytes and count==lastcount==expected_count
   if not exact:errors.append(j['node']+' '+direction+' no reconcilia exactamente')
   directions.append({'node':j['node'],'direction':direction,'raw_contract':raw_contract,'unique_contract':contract,'identical_duplicate_tokens':len(raw_contract)-len(contract),'scientific_files':scientific,'scientific_bytes':sci,'auxiliary_bytes':auxbytes,'native_bytes':total,'native_last_bytes':last,'native_count':count,'expected_count':expected_count,'exact':exact,'residual':None if total is None else total-sci-auxbytes,'auxiliaries':auxrecords})
   for n in scientific:deliveries.append({'node':j['node'],'global_job_id':j['global_job_id'],'direction':direction,'file':n,'bytes':files[n]['bytes'],'source':'dme-master' if direction=='input' else j['worker'],'destination':j['worker'] if direction=='input' else 'dme-master'})
 observed=sum(d['bytes'] for d in deliveries)
 required_counts=collections.Counter((n,d,f['bytes']) for n,f in files.items() for d in f['destinations'])
 delivered_counts=collections.Counter((d['file'],d['destination'],d['bytes']) for d in deliveries)
 if required_counts-delivered_counts:errors.append('Cobertura incompleta por archivo y destino')
 final=[]
 for name,f in files.items():
  if not f['final'] and f['producer']:continue
  p=case/('outputs' if f['final'] else 'inputs')/name
  rec={'file':name,'bytes':p.stat().st_size,'sha256':sha(p),'matches_native_metadata':p.stat().st_size==f['bytes'] and sha(p)==f['checksum']}
  if not rec['matches_native_metadata']:errors.append('Contenido preservado no coincide: '+name)
  if f['final']:final.append(rec)
 # Los valores del Analyzer solo se leen después de reconstruir los dos totales.
 report=json.loads(Path(state.get('report_file',str(ev/'reports/analysis.json'))).read_text());metrics=report['metrics']
 comparison={'required_match':required==metrics['required_movement_bytes'],'observed_match':observed==metrics['observed_movement_bytes'],'reported_dme':metrics['dme'],'reported_evidence_levels':metrics['evidence_levels']}
 if not comparison['required_match'] or not comparison['observed_match']:errors.append('Resultado Analyzer distinto de auditoría independiente')
 sources.extend({'path':str(p),'sha256':sha(p)} for p in [wf,ev/'history.long',ev/'history.json',case/'bin/campaign_task.py'])
 return {'condition':cid,'status':'CORROBORATED_BY_JOB_DIRECTION_CONTRACT' if not errors else 'NOT_ACCEPTED','errors':errors,'required_bytes':required,'observed_bytes':observed,'dme_exact':str(Fraction(required,observed)),'files':files,'task_to_node':mapping,'jobs':jobs,'directions':directions,'deliveries':deliveries,'final_files':final,'comparison_only_after_independent_reconstruction':comparison,'sources':sources,'replicas':1,'limit':'Native counters are aggregate by job and direction. Scientific deliveries corroborated under complete file contracts and exact auxiliary reconciliation, not independent per-file network or packet counters.'}
