"""Independent, offline relay oracle. Does not import Analyzer or parse raw capsules.

45 rows use documented configurations, 10 use extracted native breakdowns.
Historic inputs are read-only. Results are compared only after reconstruction.
"""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def obligations(files, coordinator):
    if not coordinator:
        raise ValueError('Coordinador ausente')
    result = []
    for name, f in files.items():
        size, origin = f['bytes'], f['origin']
        if not isinstance(size, int) or size < 0 or not origin:
            raise ValueError('Tamaño u origen inválido')
        destinations = set(f['destinations']) - {origin}
        remote_workers = destinations - {coordinator}
        if f['final'] or (origin != coordinator and remote_workers):
            destinations.add(coordinator)
        for destination in sorted(destinations - {origin}):
            result.append((name, destination, size))
    return result


def check_coverage(required, deliveries):
    available = Counter((d['file'], d['destination'], d['bytes']) for d in deliveries)
    missing = Counter(required) - available
    if missing:
        raise ValueError(f'Obligaciones sin entrega: {dict(missing)}')
    return len(required) == len(deliveries)


def reconstruct(root=ROOT):
    models = json.loads((root/'data/source/relevo/configuraciones.json').read_text(encoding='utf-8'))
    historic = list(csv.DictReader((root/'data/derived/workflows_113.csv').open(encoding='utf-8')))
    output = []
    for row in historic:
        condition = {'B01':'AC1','B02':'AC2','B04':'AC4'}.get(row['condition'], row['condition'])
        if row['block'] != 'A' or condition not in models:
            continue
        files = {str(i):dict(bytes=int(Fraction(str(s))*2**20),origin=o,destinations=d,final=f)
                 for i,(s,o,d,f) in enumerate(models[condition]['archivos'])}
        req = obligations(files, 'm')
        obs = int(row['observed_bytes'])
        output.append(dict(caso=row['case'],condicion=condition,uuid=row['uuid'],
            requerido_bytes=sum(x[2] for x in req),observado_bytes=obs,obligaciones=len(req),
            cobertura_por_entrega='no_evaluada_configuracion',
            procedencia='configuracion_documentada_y_observado_historico'))
    assert len(output) == 45
    native = json.loads((root/'data/validation_free_20261107/DESGLOSE_NATIVO.json').read_text(encoding='utf-8'))
    rows = {r['case']:r for r in csv.DictReader((root/'data/validation_free_20261107/RESULTADOS_VALIDACION_LIBRE.csv').open(encoding='utf-8'))}
    for item in native:
        row = rows[item['case']]
        req = obligations(item['files'], 'dme-master')
        for direction in item['directions']:
            assert direction['exact'] and direction['residual'] == 0
            scientific = sum(item['files'][name]['bytes'] for name in direction['scientific_files'])
            auxiliary = sum(a['bytes'] for a in direction['auxiliaries'])
            assert scientific == direction['scientific_bytes']
            assert auxiliary == direction['auxiliary_bytes']
            assert direction['native_bytes'] - scientific - auxiliary == 0
            assert direction['native_count'] == direction['expected_count']
        deliveries = item['deliveries']
        identifiers = [(d['global_job_id'],d['direction'],d['file']) for d in deliveries]
        assert len(identifiers) == len(set(identifiers))
        bijective = check_coverage(req, deliveries)
        output.append(dict(caso=row['case'],condicion=row['condition'],uuid=row['uuid'],
            requerido_bytes=sum(x[2] for x in req),observado_bytes=sum(d['bytes'] for d in deliveries),
            obligaciones=len(req),cobertura_por_entrega='biyectiva' if bijective else 'inyectiva',
            procedencia='desglose_nativo_extraido'))
    assert len(output) == len({r['uuid'] for r in output}) == 55
    for row in output:
        row['dme'] = str(Fraction(row['requerido_bytes'],row['observado_bytes']))
    return output


def main():
    reconstructed = reconstruct()
    analyzer = {r['uuid']:r for r in csv.DictReader((ROOT/'data/derived/dme_relevo_55.csv').open(encoding='utf-8'))}
    assert len(analyzer) == 55
    for row in reconstructed:
        other = analyzer[row['uuid']]
        for key in ['requerido_bytes','observado_bytes','obligaciones','dme']:
            assert str(row[key]) == other[key], (row['caso'],key,row[key],other[key])
    out = ROOT/'data/derived/auditoria_relevo_55.csv'
    with out.open('w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(reconstructed[0]))
        writer.writeheader();writer.writerows(reconstructed)
    report = dict(definicion='condorio_coordinator_relay_v1',casos=55,
        configuraciones_documentadas=45,desgloses_nativos_extraidos=10,direcciones_extraidas=40,
        discrepancias=0,importa_analyzer=False,reaudita_capsulas=False,
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'reproducibility/AUDITORIA_RELEVO.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
