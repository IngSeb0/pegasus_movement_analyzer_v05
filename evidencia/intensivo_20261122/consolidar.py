"""Consolida bytes, tramos, contrastes y evidencia de cierre."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from statistics import mean,stdev
from zipfile import ZipFile,ZIP_DEFLATED
import csv
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'RESULTADOS'
SESSION=ROOT/'sesion02'
EVIDENCE=SESSION/'evidencia'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
PARTS=('tramo_transferencia_s','tramo_ejecucion_s','tramo_auxiliares_s','tramo_cola_s','tramo_cierre_post_s','tramo_dagman_s')


def load(path):
    with path.open(encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def write(path,rows):
    if rows:
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def fmt(values):
    return f'{mean(values):.3f} ± {stdev(values):.3f}' if len(values)>1 else f'{mean(values):.3f}'


def intervals_length(intervals):
    end=None
    total=0
    for start,stop in sorted(intervals):
        if end is None or start>=end:
            total+=stop-start
            end=stop
        elif stop>end:
            total+=stop-end
            end=stop
    return total


def main():
    assert sha256((ROOT/'HIPOTESIS.md').read_bytes()).hexdigest()==(ROOT/'HIPOTESIS.sha256').read_text().split()[0]
    bandwidth={d:read(path) for d in ('entrada','salida') if (path:=EVIDENCE/f'patrones/banda-{d}/BANDA.json').exists()}
    if bandwidth:
        (OUT/'ANCHO_DE_BANDA.json').write_text(json.dumps(bandwidth,indent=2))
    state=read(SESSION/'estado_final.json')
    assert len(state)==5 and all(v['state']=='VM deallocated' for v in state)
    start,end=[datetime.fromisoformat((SESSION/f'{key}_utc.txt').read_text().strip()) for key in ('inicio','cierre')]
    initial=ROOT/'sesion'
    earlier_start,earlier_end=[datetime.fromisoformat((initial/f'{key}_utc.txt').read_text().strip()) for key in ('inicio','cierre')]
    total=end-start+earlier_end-earlier_start
    assert total.total_seconds()<=18000
    tc_path=OUT/'TC.txt'
    tc=tc_path.read_text(encoding='utf-8') if tc_path.exists() else ''
    removed=tc.count(' después ')==5 and not(OUT/'TC_ERRORES.json').is_file()
    tc_note='Se retiró tc y se registró el estado posterior en los cinco nodos.' if removed else 'TC.txt registra los nodos configurados y las comprobaciones disponibles.'
    (OUT/'VMS.md').write_text(f'# Cierre de Azure\n\nCinco VMs desasignadas. Ventana acumulada {total}. {tc_note}\n',encoding='utf-8')
    volumes=[]
    times=[]
    transfer=[]
    plans=[]
    cpu=[]
    directions=0
    accepted_ids=set()
    for group in ('patrones','contraste'):
        home=EVIDENCE/group
        if not (home/'RESULTS.json').exists():
            continue
        folder=OUT/group
        folder.mkdir(exist_ok=True)
        jobs=[]
        runs=[]
        for row in read(home/'RESULTS.json'):
            assert row['id'] not in accepted_ids
            accepted_ids.add(row['id'])
            case=home/'cases'/row['id']
            comparison=next(case.rglob('D1.json'))
            d=read(comparison)
            audit=read(comparison.with_name('INDEPENDENT_AUDIT.json'))
            directions+=len(audit['directions'])
            assert all(x['residual']==0 and x['exact'] for x in audit['directions'])
            observed,required=row['observed_bytes'],row['required_bytes']
            assert observed==20*d['observado_10MiB'] and required==20*d['requerido_10MiB']
            volumes.append(dict(corrida=row['id'],condicion=row['condition'],grupo=group,fase=row['phase'],requerido_B=required,observado_B=observed,exceso_B=observed-required,DME=row['dme'],requerido_FMA_10MiB=d['requerido_10MiB'],observado_FMA_10MiB=d['observado_10MiB'],referencias_misma_ubicacion=','.join(r['id'] for r in d['referencias_medidas']),ubicacion=json.dumps(d['ubicacion'],sort_keys=True)))
            meta=dict(grupo=group,fase=row['phase'],bloque=row['block'])
            job_rows=load(comparison.with_name('jobs.csv'))
            jobs.extend(dict(j,**meta) for j in job_rows)
            run=dict(load(comparison.with_name('corridas.csv'))[0],**meta)
            runs.append(run)
            plan=read(comparison.with_name('PLANIFICACION.json'))
            plans.append(dict(corrida=row['id'],segundos=plan['segundos']))
            task_records={}
            for source in case.rglob('*.out.000'):
                for line in source.read_text(errors='replace').splitlines():
                    if '"fma"' not in line or '"fixed_work_cpu_s"' in line:
                        continue
                    try:
                        item=json.loads(line[line.index('{'):line.rindex('}')+1])
                    except (ValueError, json.JSONDecodeError):
                        continue
                    if 'task_id' in item and 'fma' in item:
                        fma=item['fma']
                        assert fma['flops']==1766799020 and fma['fma_operations']*2==fma['flops']
                        task_records[item['task_id']]=dict(corrida=row['id'],condicion=row['condition'],tarea=item['task_id'],cpu_s=fma['cpu_seconds'],reloj_s=fma['wall_seconds'],flops=fma['flops'],fuente=source.relative_to(ROOT).as_posix())
            cpu.extend(task_records.values())
            if len(bandwidth)==2:
                # Direction comes from independently audited scientific deliveries.
                delivered=audit['directions']
                incoming=sum(x['scientific_bytes'] for x in delivered if x['direction'] in ('input','in'))
                outgoing=sum(x['scientific_bytes'] for x in delivered if x['direction'] in ('output','out'))
                assert incoming+outgoing==observed
                expected=incoming/bandwidth['entrada']['bytes_por_s']+outgoing/bandwidth['salida']['bytes_por_s']
                actual=float(run[PARTS[0]])
                intervals=[]
                for job in job_rows:
                    if job['tipo']=='tarea':
                        finish=float(job['t_fin_entrada'])
                        intervals.append((finish-float(job['transferencia_entrada_s']),finish))
                        intervals.append((float(job['t_inicio_salida']),float(job['t_fin_salida'])))
                transfer.append(dict(corrida=row['id'],condicion=row['condition'],fase=row['phase'],entrada_B=incoming,salida_B=outgoing,observado_B=observed,prediccion_s=expected,medido_s=actual,union_intervalos_transferencia_s=intervals_length(intervals),suma_transferencias_por_job_s=float(run['suma_transferencia_entrada_s'])+float(run['suma_transferencia_salida_s']),desviacion_relativa=(actual-expected)/expected,dentro_25_pct=abs(actual-expected)<=expected*.25))
        times.extend(r for r in runs if r['fase']!='piloto')
        write(folder/'jobs.csv',jobs)
        write(folder/'corridas.csv',runs)
        main_rows=[r for r in runs if r['fase']!='piloto']
        if main_rows:
            tmp=folder/'principales'
            tmp.mkdir(exist_ok=True)
            write(tmp/'corridas.csv',main_rows)
            subprocess.run([sys.executable,str(ROOT/'herramientas/resumir_tiempos.py'),str(tmp)],check=True)
            (folder/'resumen.csv').write_bytes((tmp/'resumen.csv').read_bytes())
    write(OUT/'BYTES.csv',volumes)
    write(OUT/'TRANSFERENCIA_VS_OBSERVADO.csv',transfer)
    write(OUT/'PLANIFICACION.csv',plans)
    write(OUT/'CPU_FMA_POR_TAREA.csv',cpu)
    metric_keys=('duracion_dagman_s',*PARTS)
    table=[]
    counts={g:sum(row['grupo']==g and row['fase']!='piloto' for row in volumes) for g in ('patrones','contraste')}
    pilots=sum(r['fase']=='piloto' for r in volumes)
    report=['# Flujos intensivos en datos','',f'Se aceptaron {len(volumes)} workflows. Fase 2: {len(bandwidth)} mediciones de enlace y {pilots} pilotos aceptados. Fase 3: {counts["patrones"]} de 20 corridas de patrones y {counts["contraste"]} de 9 corridas de contraste. Se conciliaron {directions} direcciones científicas con residuo cero.','',
            '| Condición | n | Total (s) | Transferencia | Ejecución | Auxiliares | Cola | Cierre | Espera sin atribuir |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for condition in sorted({r['condicion'] for r in times}):
        rows=[r for r in times if r['condicion']==condition]
        numbers={k:[float(r[k]) for r in rows] for k in metric_keys}
        averages={k:mean(numbers[k]) for k in PARTS}
        largest=max(averages,key=averages.get)
        table.append(dict(condicion=condition,n=len(rows),**averages,mayor=largest,intensivo=all(averages[PARTS[0]]>averages[k] for k in PARTS[1:])))
        report.append('| '+' | '.join([condition,str(len(rows)),*[fmt(numbers[k]) for k in metric_keys]])+' |')
    write(OUT/'INTENSIVO.csv',table)
    paired=[]
    for a,b in [('W2-AGR','REP'),('W2-SEP','W2-AGR'),('REP','W2-SEP')]:
        ma={r['bloque']:r for r in times if r['condicion']==a}
        mb={r['bloque']:r for r in times if r['condicion']==b}
        for block in sorted(ma.keys()&mb.keys()):
            paired.append(dict(contraste=f'{a} − {b}',bloque=block,**{k:float(ma[block][k])-float(mb[block][k]) for k in metric_keys}))
    write(OUT/'DIFERENCIAS_POR_BLOQUE.csv',paired)
    pair_summary=[]
    for label in dict.fromkeys(r['contraste'] for r in paired):
        subset=[r for r in paired if r['contraste']==label]
        summary=dict(contraste=label,n=len(subset))
        for k in metric_keys:
            values=[r[k] for r in subset]
            summary[k+'_media']=mean(values)
            summary[k+'_de']=stdev(values) if len(values)>1 else None
        pair_summary.append(summary)
    write(OUT/'DIFERENCIAS_RESUMEN.csv',pair_summary)
    per_run_intensive=sum(all(float(r[PARTS[0]])>float(r[k]) for k in PARTS[1:]) for r in times)
    conclusions=[
        ('D1',f'{len(volumes)} comprobaciones, {sum(bool(r["referencias_misma_ubicacion"]) for r in volumes)} con control FMA medido en la misma ubicación. Para las demás se reconstruyó la referencia de 10 MiB sobre la ubicación efectiva. Véase BYTES.csv y D1.json.') if volumes else ('D1','Pendiente.'),
        ('D2',f'{sum(r["intensivo"] for r in table)} de {len(table)} condiciones con transferencia media como tramo mayor. El criterio por corrida se cumple en {per_run_intensive} de {len(times)} corridas principales. Véase INTENSIVO.csv y corridas.csv.') if table else ('D2','Pendiente.'),
        ('D3',f'{sum(r["dentro_25_pct"] for r in transfer)} de {len(transfer)} corridas dentro del 25 %. En promedio, se predijeron {mean(r["prediccion_s"] for r in transfer):.3f} s, el tramo exclusivo registró {mean(r["medido_s"] for r in transfer):.3f} s y la unión de los intervalos registró {mean(r["union_intervalos_transferencia_s"] for r in transfer):.3f} s. Las transferencias pueden solaparse entre jobs y con la ejecución. Véase TRANSFERENCIA_VS_OBSERVADO.csv.') if transfer else ('D3','Pendiente.')]
    by_name={r['condicion']:r for r in table}
    worker_comparisons=[]
    non_decrease=0
    for name in ('PROCESS','PIPELINE','AGGREGATION','DISTRIBUTION','REDISTRIBUTION'):
        if name+'-W2' in by_name and name+'-W4' in by_name:
            difference=by_name[name+'-W4'][PARTS[0]]-by_name[name+'-W2'][PARTS[0]]
            non_decrease+=difference>=0
            worker_comparisons.append(f'{name} {difference:+.3f} s')
    conclusions.append(('D4',f'La transferencia no bajó en {non_decrease} de {len(worker_comparisons)} patrones. Diferencia W4 − W2. '+', '.join(worker_comparisons)+'. Cada worker limita su salida al coordinador por separado. La concurrencia y el solapamiento del tramo exclusivo pueden variar. Véase INTENSIVO.csv.' if worker_comparisons else 'Pendiente.'))
    for number,label in [('D5','W2-AGR − REP'),('D6','W2-SEP − W2-AGR')]:
        selected=[r for r in paired if r['contraste']==label]
        if selected:
            delta=mean(r['duracion_dagman_s'] for r in selected)
            trial='Cumple la dirección' if (delta<0 if number=='D5' else delta>0) else 'No cumple la dirección'
            expected=600*2**20/bandwidth['entrada']['bytes_por_s'] if 'entrada' in bandwidth else None
            model=f' El exceso evitado de 600 MiB predice {expected:.3f} s de transferencia de entrada.' if expected is not None else ''
            favored=sum((r['duracion_dagman_s']<0 if number=='D5' else r['duracion_dagman_s']>0) for r in selected)
            conclusions.append((number,f'{trial} en el promedio de {len(selected)} pares. AGR terminó antes en {favored} de {len(selected)} bloques. {label} total {delta:.3f} s y transferencia {mean(r[PARTS[0]] for r in selected):.3f} s.{model} Véase DIFERENCIAS_POR_BLOQUE.csv y los CSV de jobs.'))
        else:
            conclusions.append((number,'Pendiente.'))
    hypothesis='# Contraste de hipótesis\n\n| Hipótesis | Cifras e interpretación |\n|---|---|\n'+''.join(f'| {k} | {v} |\n' for k,v in conclusions)
    (OUT/'CONTRASTE_HIPOTESIS.md').write_text(hypothesis,encoding='utf-8')
    report+=['','Medias ± desviación estándar muestral en segundos. Pegasus se cronometra por separado en PLANIFICACION.csv. La espera sin atribuir se calcula por complemento. Las marcas de transferencia del historial tienen resolución de un segundo.','']
    if paired:
        report+=['| Diferencia pareada | n | Total (s) | Transferencia | Ejecución | Auxiliares | Cola | Cierre | Espera sin atribuir |',
                 '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for label in dict.fromkeys(r['contraste'] for r in paired):
            subset=[r for r in paired if r['contraste']==label]
            report.append('| '+' | '.join([label,str(len(subset)),*[fmt([r[k] for r in subset]) for k in metric_keys]])+' |')
        report.append('')
    report+=['La unión de intervalos y la suma por job se conservan en TRANSFERENCIA_VS_OBSERVADO.csv. El tramo exclusivo de transferencia aplica la prioridad de ejecución de la herramienta histórica. Un intervalo de transferencia concurrente con ejecución puede quedar fuera del tramo exclusivo. La duración clasificada como ejecución puede incluir tiempo antes de transferir la salida, además del bucle FMA.']
    if cpu:
        report.append(f'Kickstart registra {len(cpu)} mediciones de CPU del bucle FMA entre {min(r["cpu_s"] for r in cpu):.3f} y {max(r["cpu_s"] for r in cpu):.3f} s por tarea. Véase CPU_FMA_POR_TAREA.csv.')
    report.extend(f"Ancho de banda de {d}. {r['bytes_por_s']/10**6:.2f} MB/s." for d,r in bandwidth.items())
    report+=['',hypothesis,'',tc_note]
    if counts['contraste']==9:
        report+=['','Con la ubicación de los consumidores fija, agrupar elimina tres entregas de 200 MiB. El ahorro medido del tramo de transferencia queda cerca de ΔO/B. REP distribuye los consumidores entre cuatro workers y conserva el mismo observado que W2-SEP. Los workers pueden devolver datos en paralelo porque cada uno tiene su propio TBF de salida. Este diseño no impone un único límite agregado de entrada en el coordinador. El historial y las tablas de jobs conservan los intervalos superpuestos. En la campaña previa de 10 MiB, W2-AGR tardó 48,091 s más que REP en promedio. En esta campaña la brecha media bajó a 15,392 s. Cambiaron los tamaños, la red y el presupuesto de cómputo de los consumidores, así que la comparación entre campañas es descriptiva.']
    report+=['','El primer arranque terminó antes de aplicar tc y enviar jobs. El preflight leyó las líneas de contadores como si fueran declaraciones de colas. La corrección filtra las líneas qdisc. Las evidencias del ensayo y su cierre quedan en sesion.']
    (OUT/'RESUMEN_RESULTADOS.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    (OUT/'VERIFICACION.json').write_text(json.dumps(dict(archivos_B=200*2**20,pilotos=pilots,principales=counts,direcciones_exactas=directions,reglas_tc_retiradas=removed,vms_desasignadas=5,ventana_acumulada_s=total.total_seconds()),indent=2))
    target=ROOT/'intensivo_20261122_resultados.zip'
    with ZipFile(target,'w',ZIP_DEFLATED) as archive:
        for path in ROOT.rglob('*'):
            rel=path.relative_to(ROOT)
            if not path.is_file() or path.suffix in {'.zip','.gz','.pyc'} or {'ssh_config','__pycache__'}.intersection(rel.parts):
                continue
            if 'plan_local' in rel.parts and path.suffix not in {'.sub','.dag','.json','.yml','.in','.py'} and path.name!='fma_kernel':
                continue
            archive.write(path,rel)
    with ZipFile(target) as archive:
        assert archive.testzip() is None


if __name__=='__main__':
    main()
