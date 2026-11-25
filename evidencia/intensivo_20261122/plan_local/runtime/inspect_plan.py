from pathlib import Path
import hashlib,json,re,shlex
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def attrs(p):
 result={};buf=''
 for line in p.read_text().splitlines():
  line=buf+line.strip()
  if line.endswith('\\'):buf=line[:-1]+' ';continue
  buf=''
  if not line or line.startswith('#') or '=' not in line:continue
  k,v=line.split('=',1);v=v.strip();result[k.strip().lower()]=v[1:-1] if v.startswith('"') and v.endswith('"') else v
 return result

def inspect_plan(run,spec):
 files={f['file_id']:f for f in spec['files']};tasks={t['task_id']:t for t in spec['dag']['tasks']};seen={};jobs=[]
 for p in sorted(run.rglob('*.sub')):
  a=attrs(p)
  if a.get('+pegasus_job_class')!='1':continue
  node=a['+pegasus_wf_dag_job_id'];dax=a.get('+pegasus_wf_dax_job_id')
  if dax and dax.lower() not in {'null','undefined'}:members=[dax]
  else:
   text=p.with_suffix('.in').read_text();members=re.findall(r'^#@\s+\d+\s+\S+\s+(\S+)\s*$',text,re.M);commands=[]
   for line in text.splitlines():
    if not line.strip() or line.lstrip().startswith('#'):continue
    parts=shlex.split(line)
    if Path(parts[0]).name!='pegasus-kickstart' or parts.count('-N')!=1:raise ValueError('Formato agrupado inesperado')
    commands.append(parts[parts.index('-N')+1])
   if not members or members!=commands or int(a['+pegasus_cluster_size'])!=len(members):raise ValueError('Pertenencia no corroborada')
  if any(t not in tasks or t in seen for t in members):raise ValueError('Tarea desconocida o repetida')
  workers={tasks[t]['assigned_worker'] for t in members}
  if len(workers)!=1:raise ValueError('Grupo repartido entre maquinas')
  worker='dme-worker'+next(iter(workers))[1:]
  if a.get('requirements')!='TARGET.Machine == '+json.dumps(worker):raise ValueError('Asignacion distinta del diseno')
  if a.get('universe')!='vanilla' or a.get('should_transfer_files')!='YES' or a.get('when_to_transfer_output')!='ON_EXIT' or a.get('request_cpus')!='1' or a.get('request_memory')!='256':raise ValueError('Configuracion base modificada')
  scientific={d:sorted({Path(x.strip()).name for x in a.get('transfer_'+d+'_files','').split(',') if Path(x.strip()).name in files}) for d in ['input','output']}
  consumed={f for t in members for f in tasks[t]['input_files']};produced={f for t in members for f in tasks[t]['output_files']}
  needed={f for f in produced if files[f]['role']=='final' or any(t not in members for t in files[f]['consumer_tasks'])}
  if set(scientific['input'])!=consumed-produced or not needed<=set(scientific['output'])<=produced:raise ValueError('Contrato cientifico incompatible con dependencias')
  for f in produced:
   producer=files[f]['producer_task']
   for user in files[f]['consumer_tasks']:
    if user in members and members.index(producer)>=members.index(user):raise ValueError('Orden agrupado invalido')
  seen.update((t,node) for t in members);jobs.append({'node':node,'members':members,'worker':worker,'scientific_files':scientific,'submit_sha256':sha(p)})
 if set(seen)!=set(tasks) or {frozenset(j['members']) for j in jobs}!={frozenset(g) for g in spec['groups']}:raise ValueError('Mapa cientifico incompleto o distinto')
 return {'state':'NATIVE_PLAN_NOT_OBSERVATION','jobs':jobs,'task_to_job':seen,'planned_scientific_bytes':sum(files[f]['size_bytes'] for j in jobs for d in ['input','output'] for f in j['scientific_files'][d]),'submitted':False,'retry_policy':[s for p in run.glob('*.dag') for s in p.read_text().splitlines() if s.startswith('RETRY ')]}