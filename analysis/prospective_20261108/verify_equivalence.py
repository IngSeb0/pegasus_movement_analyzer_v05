"""Verify scientific endpoints from accepted records and archived FITS outputs."""
from pathlib import Path
import argparse,json,tarfile,struct,math,hashlib
def fits(raw):
 cards={};offset=None
 for i in range(0,len(raw),80):
  c=raw[i:i+80].decode('ascii');k=c[:8].strip()
  if k=='END':offset=((i+80+2879)//2880)*2880;break
  if c[8:10]=='= ':cards[k]=c[10:].split('/')[0].strip().strip("'")
 assert offset is not None and int(cards['NAXIS'])==2
 dims=(int(cards['NAXIS1']),int(cards['NAXIS2']));bit=int(cards['BITPIX']);fmt={-64:'d',-32:'f',16:'h',32:'i',8:'B'}[bit];size=struct.calcsize(fmt);n=dims[0]*dims[1]
 values=struct.unpack('>'+fmt*n,raw[offset:offset+n*size]);scale=float(cards.get('BSCALE','1'));zero=float(cards.get('BZERO','0'))
 return dims,[v*scale+zero for v in values]
def compare(a,b):
 da,va=a;db,vb=b;assert da==db and len(va)==len(vb)
 largest=0.;finite=0
 for x,y in zip(va,vb):
  assert math.isfinite(x)==math.isfinite(y)
  if math.isfinite(x):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12);largest=max(largest,abs(x-y));finite+=1
  else:assert(math.isnan(x)and math.isnan(y))or x==y
 assert finite>0
 return dict(dimensions=da,finite_pixels=finite,max_absolute_difference=largest,relative_tolerance=1e-12,absolute_tolerance=1e-12)
def main():
 p=argparse.ArgumentParser();p.add_argument('results',type=Path);p.add_argument('--require-pilots',action='store_true');a=p.parse_args();rows=json.loads(a.results.read_text());folder=a.results.parent;report={}
 if a.require_pilots:
  pilot=[r for r in rows if r['phase']=='pilot'];assert len(pilot)==12 and len({r['condition']for r in pilot})==12
 montage_payloads={};verified_files=0
 for row in rows:
  paths=[*folder.glob(row['id']+'.tar.gz'),*folder.glob(row['id']+'.tar.xz')];assert len(paths)==1
  with tarfile.open(paths[0])as t:
   for f in row['final_files']:
    raw=t.extractfile(f"plans/{row['condition']}/outputs/{f['file']}").read()
    assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']and f['matches_native_metadata']
    verified_files+=1
    if row['condition'].startswith('MONTAGE'):montage_payloads.setdefault(row['id'],{})[f['file']]=raw
 report['artifact_integrity']=dict(archives_checked=len(rows),final_files_verified=verified_files,all_sizes_and_sha256_match=True)
 for family,conditions in {'pipeline':{'L01','GL2','GL3','GL3_FINAL'},'compartido':{'AC1','AC2','AC4'},'particiones':{'D02','GD4'}}.items():
  members=[r for r in rows if r['condition']in conditions];signatures={tuple(sorted((f['file'],f['bytes'],f['sha256'])for f in r['final_files']))for r in members}
  assert len(signatures)<=1,(family,signatures)
  report[family]=dict(records=len(members),conditions=sorted({r['condition']for r in members}),final_signatures_identical=True,condition_set_complete={r['condition']for r in members}==conditions)
 refs={};checks=[]
 for row in rows:
  if not row['condition'].startswith('MONTAGE'):continue
  assert {f['file']for f in row['final_files']}=={'project_area.fits','reduced.fits'}
  for f in row['final_files']:
   raw=montage_payloads[row['id']][f['file']]
   data=fits(raw);expected=(256,256)if f['file']=='project_area.fits'else(128,128);assert data[0]==expected
   finite=[v for v in data[1]if math.isfinite(v)];assert finite and max(finite)>0
   if f['file']not in refs:refs[f['file']]=data
   check=compare(refs[f['file']],data);check.update(case=row['id'],file=f['file']);checks.append(check)
 report['montage']=dict(records=sum(r['condition'].startswith('MONTAGE')for r in rows),comparisons=checks)
 out=folder/'SCIENTIFIC_EQUIVALENCE.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
