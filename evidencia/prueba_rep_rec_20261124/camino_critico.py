"""Orden de los jobs de REP y REP-REC desde history.long (segundos desde el primer QDate).
start = JobStartDate (inicio del job, incluye recibir entradas); exec = JobCurrentStartExecutingDate
(entradas ya recibidas, empieza a ejecutar); end = CompletionDate."""
import re, sys
out=["# Verificación del camino crítico (REP frente a REP-REC)","",
     "Generado por `camino_critico.py` a partir de `history.long` de cada corrida. Tiempos en segundos desde el primer job encolado.",""]
for r in ['rep_r1','reprec_r1','rep_r2','reprec_r2']:
    txt=open(f'{r}/history.long',errors='replace').read()
    rows=[]
    for a in re.split(r'\n\s*\n',txt):
        d=dict(re.findall(r'^(\w+) = (.*)$',a,re.M)); n=d.get('DAGNodeName','').strip('"')
        if not n: continue
        g=lambda k: int(d[k]) if d.get(k,'').isdigit() else None
        rows.append((n,g('QDate'),g('JobStartDate'),g('JobCurrentStartExecutingDate'),g('CompletionDate')))
    t0=min(x[1] for x in rows)
    out+=[f"## {r}","","| job | encolado | inicio | entradas listas | fin |","|---|---:|---:|---:|---:|"]
    for n,q,s,e,c in sorted(rows,key=lambda x:(x[1],x[2] or 0)):
        f=lambda v:'-' if v is None else str(v-t0)
        out.append(f"| {n} | {f(q)} | {f(s)} | {f(e)} | {f(c)} |")
    out.append("")
out+=["## Lectura","",
"- En REP, `campaign_task_C1` (W1) empieza antes que C2–C4 y termina de recibir `g` a los 136 s (r1) y 145 s (r2); C2–C4 empiezan a recibir `g` a los 139 s y 142 s. La copia de `g` hacia W1, que REP-REC evita, ocurre casi toda antes de que empiecen las otras tres.",
"- En REP y en REP-REC, el último consumidor termina de recibir `g` entre los 197 y los 206 s y el flujo termina con `stage_out` a los 243–257 s: lo que fija la duración son las tres copias de `g` hacia W2, W3 y W4, presentes en las dos variantes.",
"- Ejecución + transferencia (tiempos.py) suman 149, 148, 149 y 149 s en rep_r1, reprec_r1, rep_r2 y reprec_r2: lo que cambia entre variantes es cómo se reparte ese intervalo entre los dos tramos.",""]
open('CAMINO_CRITICO.md','w',encoding='utf-8').write("\n".join(out))
