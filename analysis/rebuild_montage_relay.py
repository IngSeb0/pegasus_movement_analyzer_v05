"""Recalculate preserved Montage breakdowns; does not rerun astronomy tasks."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import json,csv,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.rebuild_relay_dataset import calcular
def rebuild(root=ROOT):
 folder=root/'data/validation_montage_20261108'
 evidence=json.loads((folder/'DESGLOSE_MONTAGE.json').read_text(encoding='utf-8'))
 expected=list(csv.DictReader((folder/'MONTAGE_RELEVO.csv').open(encoding='utf-8')))
 rows=[]
 for item in evidence:
  files=item['files'];obligations=[]
  for name,f in files.items():
   dest=set(f['destinations']);origin=f['origin']
   if f['final'] or (f['producer'] and any(d not in {origin,'dme-master'} for d in dest)):dest.add('dme-master')
   obligations.extend((name,d,f['bytes']) for d in dest-{origin})
  req=sum(x[2] for x in obligations)
  core=calcular([[f['bytes'],f['origin'],f['destinations'],f['final']] for f in files.values()],'dme-master')
  assert core.total_bytes==req
  deliveries=item['deliveries'];assert not(Counter(obligations)-Counter((d['file'],d['destination'],d['bytes']) for d in deliveries))
  assert len({(d['global_job_id'],d['direction'],d['file'])for d in deliveries})==len(deliveries)
  obs=sum(d['bytes']for d in deliveries)
  for d in item['directions']:
   sci=sum(files[n]['bytes']for n in d['scientific_files']);aux=sum(a['bytes']for a in d['auxiliaries'])
   assert d['native_bytes']-sci-aux==d['residual']==0
   assert d['native_count']==d['expected_count']
  row=next(r for r in expected if r['caso']==item['case'])
  assert (int(row['requerido_bytes']),int(row['observado_bytes']),row['dme'],int(row['obligaciones']),int(row['entregas']))==(req,obs,str(Fraction(req,obs)),len(obligations),len(deliveries))
  rows.append(dict(caso=item['case'],requerido_bytes=req,observado_bytes=obs,dme=str(Fraction(req,obs)),obligaciones=len(obligations),entregas=len(deliveries)))
 assert len(rows)==4
 return rows
if __name__=='__main__':print(json.dumps(rebuild(),indent=2))
