# Verificación del camino crítico (REP frente a REP-REC)

Generado por `camino_critico.py` a partir de `history.long` de cada corrida. Tiempos en segundos desde el primer job encolado.

## rep_r1

| job | encolado | inicio | entradas listas | fin |
|---|---:|---:|---:|---:|
| create_dir_flujo-rep_0_local | 0 | 4 | - | 6 |
| stage_in_local_local_0_0 | 20 | 22 | - | 26 |
| stage_in_remote_local_0_0 | 20 | 22 | - | 25 |
| campaign_task_P | 40 | 59 | 78 | 102 |
| campaign_task_C1 | 116 | 117 | 136 | 190 |
| campaign_task_C3 | 116 | 139 | 197 | 223 |
| campaign_task_C2 | 116 | 139 | 177 | 215 |
| campaign_task_C4 | 116 | 139 | 172 | 207 |
| stage_out_local_local_1_0 | 236 | 238 | - | 246 |

## reprec_r1

| job | encolado | inicio | entradas listas | fin |
|---|---:|---:|---:|---:|
| create_dir_flujo-rep-rec_0_local | 0 | 5 | - | 8 |
| stage_in_local_local_0_0 | 20 | 21 | - | 24 |
| stage_in_remote_local_0_0 | 20 | 21 | - | 23 |
| merge_group_1 | 35 | 39 | 58 | 105 |
| stage_out_local_local_0_0 | 120 | 124 | - | 128 |
| campaign_task_C3 | 120 | 139 | 197 | 221 |
| campaign_task_C2 | 120 | 139 | 190 | 215 |
| campaign_task_C4 | 120 | 139 | 167 | 192 |
| stage_out_local_local_1_0 | 235 | 238 | - | 243 |

## rep_r2

| job | encolado | inicio | entradas listas | fin |
|---|---:|---:|---:|---:|
| create_dir_flujo-rep_0_local | 0 | 4 | - | 6 |
| stage_in_local_local_0_0 | 20 | 22 | - | 26 |
| stage_in_remote_local_0_0 | 20 | 22 | - | 25 |
| campaign_task_P | 40 | 62 | 81 | 105 |
| campaign_task_C1 | 120 | 125 | 145 | 169 |
| campaign_task_C3 | 120 | 142 | 206 | 231 |
| campaign_task_C4 | 120 | 142 | 202 | 227 |
| campaign_task_C2 | 120 | 142 | 195 | 219 |
| stage_out_local_local_1_0 | 245 | 249 | - | 257 |

## reprec_r2

| job | encolado | inicio | entradas listas | fin |
|---|---:|---:|---:|---:|
| create_dir_flujo-rep-rec_0_local | 0 | 5 | - | 8 |
| stage_in_local_local_0_0 | 20 | 22 | - | 25 |
| stage_in_remote_local_0_0 | 20 | 22 | - | 24 |
| merge_group_1 | 35 | 45 | 64 | 111 |
| stage_out_local_local_0_0 | 125 | 130 | - | 133 |
| campaign_task_C4 | 125 | 146 | 204 | 229 |
| campaign_task_C3 | 125 | 146 | 185 | 211 |
| campaign_task_C2 | 125 | 146 | 185 | 209 |
| stage_out_local_local_1_0 | 240 | 243 | - | 249 |

## Lectura

- En REP, `campaign_task_C1` (W1) empieza antes que C2–C4 y termina de recibir `g` a los 136 s (r1) y 145 s (r2); C2–C4 empiezan a recibir `g` a los 139 s y 142 s. La copia de `g` hacia W1, que REP-REC evita, ocurre casi toda antes de que empiecen las otras tres.
- En REP y en REP-REC, el último consumidor termina de recibir `g` entre los 197 y los 206 s y el flujo termina con `stage_out` a los 243–257 s: lo que fija la duración son las tres copias de `g` hacia W2, W3 y W4, presentes en las dos variantes.
- Ejecución + transferencia (tiempos.py) suman 149, 148, 149 y 149 s en rep_r1, reprec_r1, rep_r2 y reprec_r2: lo que cambia entre variantes es cómo se reparte ese intervalo entre los dos tramos.
