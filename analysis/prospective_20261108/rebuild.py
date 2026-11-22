"""Recalculate volumes from extracted audit records, not prediction values.

This portable calculation does not replace extraction from native capsules.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import argparse,csv,json

def calculate(a):
 assert not a['errors']
 files=a['files']; placement={t:j['worker']for j in a['jobs']for t in j['members']}
 workers={j['node']:j['worker']for j in a['jobs']}
 obligations=Counter();R=0
 for name,f in files.items():
  origin=placement[f['producer']]if f['producer']else'dme-master'
  destinations={placement[t]for t in f['consumers']}
  if f['final']or(f['producer']and any(d!=origin for d in destinations)):destinations.add('dme-master')
  destinations.discard(origin)
  for dest in destinations:obligations[(name,dest)]+=1;R+=f['bytes']
 deliveries=Counter();O=0;directions=0
 for d in a['directions']:
  contract=list(dict.fromkeys(d['raw_contract']));names=[Path(p).name for p in contract];assert len(names)==len(set(names))
  scientific=[n for n in names if n in files];assert scientific==d['scientific_files']
  volume=sum(files[n]['bytes']for n in scientific);aux=sum(x['bytes']for x in d['auxiliaries'])
  assert volume==d['scientific_bytes']and aux==d['auxiliary_bytes']
  assert d['native_bytes']==d['native_last_bytes']==volume+aux
  assert d['native_count']==len(contract)+(1 if d['direction']=='input'else 2)
  assert d['residual']==0 and d['exact']
  dest=workers[d['node']]if d['direction']=='input'else'dme-master'
  for n in scientific:deliveries[(n,dest)]+=1
  O+=volume;directions+=1
 assert not(obligations-deliveries)
 assert R<=O and O>0
 assert R==a['required_bytes']and O==a['observed_bytes']and Fraction(R,O)==Fraction(a['dme_exact'])
 assert O==sum(d['bytes']for d in a['deliveries'])
 return dict(required_bytes=R,observed_bytes=O,dme=str(Fraction(R,O)),obligations=sum(obligations.values()),deliveries=sum(deliveries.values()),directions=directions)

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=Path(__file__).resolve().parents[2]/'data/prospective_20261108');a=p.parse_args();folder=a.data
 rows=json.loads((folder/'RESULTS.json').read_text());audits=json.loads((folder/'AUDITS.json').read_text());matrix=json.loads((folder/'MATRIX.json').read_text())['rows']
 assert len({r['id']for r in rows})==len(rows)and len({r['uuid']for r in rows})==len(rows)
 assert {r['id']for r in rows}=={r['id']for r in matrix[:len(rows)]}==set(audits)
 output=[]
 for row in rows:
  values=calculate(audits[row['id']])
  assert all(row[k]==values[k]for k in values),(row['id'],values)
  output.append({k:row[k]for k in ['id','uuid','phase','condition','block']}|values)
 with(folder/'RECALCULATED.csv').open('w',newline='',encoding='utf-8')as stream:
  w=csv.DictWriter(stream,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
 print(json.dumps(dict(recalculated=len(output),phases=dict(Counter(r['phase']for r in rows)),directions=sum(r['directions']for r in output),all_residuals_zero=True,scope='Processed extracted records; native re-extraction requires capsules and shared static bundles.')))
if __name__=='__main__':main()
