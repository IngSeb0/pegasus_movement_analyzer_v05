# Prompt para Codex: flujos intensivos en datos

Copia todo lo que está debajo de la línea en Codex, abierto en `C:\Users\Acer\Documents\ChatGPT\THESIS`.

---

## Contexto

Tesis DME (requerido / observado bajo CondorIO; Pegasus 5.1.2, HTCondor 26.0.1, Azure Chile Central; coordinador `dme-master`, workers de 1 núcleo). La tesis estudia el movimiento de datos en **flujos intensivos en datos**. En las campañas anteriores (`fma_20261120/`) los archivos eran de 10 MiB y la red de 134 MB/s, así que las transferencias tomaron menos de 2 s y el tiempo lo dominó la coordinación: esos flujos no eran intensivos en datos. En `transferencia_20261121/` (E4) se vio que con 100 Mbit/s y archivos grandes la transferencia sí domina.

Objetivo: repetir los cinco patrones y el contraste REP / W2-SEP / W2-AGR en un **régimen intensivo en datos**, definido así:

> Un flujo es intensivo en datos en este ambiente si **el tramo de transferencia es el mayor de su duración**, por encima de la ejecución y de cada tramo de coordinación (jobs auxiliares, espera de máquina, cierre y post-script, sin job activo).

Términos fijos: requerido, observado, exceso. Sin push, sin cambios de visibilidad, sin tocar evidencia preservada. Todo lo nuevo va en `intensivo_20261122/`. Reutiliza `campaign_task_fma.py`, `fma_kernel`, el generador FMA, Analyzer, el auditor y `herramientas/tabla_tiempos.py` + `resumir_tiempos.py` de `transferencia_20261121/`. Cualquier cambio a los scripts se anota en `CAMBIOS.md`.

## Régimen intensivo en datos

- **Archivos ×20**: todos los archivos científicos de 10 MiB pasan a 200 MiB (mismas especificaciones, mismos nombres, solo cambia el tamaño). Anota tamaños exactos.
- **Cómputo pequeño**: F_patrones (≈1,4 s de CPU) en **todas** las tareas, también en los consumidores del contraste.
- **Red limitada en ambos sentidos a 100 Mbit/s**: `tc ... tbf rate 100mbit` en la salida del coordinador hacia la red privada **y** en la salida de cada worker hacia el coordinador. Guarda `tc qdisc show` de cada nodo antes, durante y después en `TC.txt`. Al terminar, quítalo en todos los nodos antes de desasignar; si algo falla, quita `tc` antes de cualquier otra cosa.
- Revisa disco (`df -h`) en coordinador y workers antes de empezar (W2 tenía 26 GB libres). Borra los archivos grandes de cada corrida al terminarla (no la evidencia de logs).

## Fase 0: hipótesis antes de correr (sin nube)

Copia este archivo a `intensivo_20261122/HIPOTESIS.md` y guarda su SHA-256 en `HIPOTESIS.sha256` **antes de encender las VMs**. No lo edites después; si algo cambia, agrega un anexo fechado.

Sea B el ancho de banda medido con `tc` activo.

| # | Hipótesis | Cómo se comprueba |
|---|---|---|
| D1 | El requerido y el observado de cada corrida son exactamente 20 veces los de la campaña FMA con la misma ubicación; **DME es el mismo**: la métrica no depende del tamaño de los archivos | Analyzer, auditor y `BYTES.csv` frente a `fma_20261120` |
| D2 | En todos los patrones y variantes, el tramo de transferencia es el mayor (criterio de intensivo en datos) | `corridas.csv` |
| D3 | El tramo de transferencia ≈ observado / B, porque todo pasa por el enlace del coordinador (±25 %) | `TRANSFERENCIA_VS_OBSERVADO.csv` |
| D4 | Con 4 workers la transferencia no baja frente a 2, porque el observado no cambia y el enlace del coordinador es el mismo | tramos W2 frente a W4 |
| D5 | En el contraste, **W2-AGR ahora es más rápido que REP**: agrupar evita 600 MiB (≈ 600 MiB / B de transferencia) y la ejecución que se pierde en serie es pequeña (4 × 1,4 s). Es la inversión del resultado con archivos de 10 MiB (+48 s) | duración y diferencias por bloque de cada tramo |
| D6 | W2-AGR es más rápido que W2-SEP por ≈ 600 MiB / B, como en E4 | diferencias por bloque |

Valores de referencia (B ≈ 12 MB/s): 600 MiB evitados ≈ 50 s. Son estimaciones, no metas.

Al terminar escribe `CONTRASTE_HIPOTESIS.md`: hipótesis, se cumple sí/no, cifras y, si no se cumple, **por qué**, con el log que lo muestra.

## Fase 1: preparación (sin nube)

1. Genera las especificaciones ×20 de los cinco patrones (2 y 4 workers) y de REP / W2-SEP / W2-AGR.
2. Planifica en local: los `.sub` declaran los mismos archivos científicos que la campaña FMA; guarda en `PREDICCIONES.json` el requerido, el observado y DME esperados (20 × los de FMA con la misma ubicación).

## Fase 2: ambiente y piloto

1. Enciende (`Control-Cluster.ps1 -Action Start -Workers 4`).
2. Aplica `tc` en los cinco nodos y **mide B** con un job HTCondor que recibe 1 GiB y otro que devuelve 1 GiB. Guarda `ANCHO_DE_BANDA.json`.
3. Piloto: DISTRIBUTION con 2 workers. Corre Analyzer, el auditor y `tabla_tiempos.py`. Comprueba D1 y que la tabla tenga todos los tramos. Si D1 falla o la tabla sale incompleta: **detente**, quita `tc`, desasigna y reporta. Si está bien, sigue sin pedir más autorización.

## Fase 3: matrices (en este orden)

1. **Cinco patrones**: 5 patrones × 2 ambientes (2 y 4 workers) × 2 repeticiones = 20 corridas, orden alternado.
2. **Contraste**: REP, W2-SEP y W2-AGR × 3 repeticiones = 9 corridas, en bloques rotados.

Límite por corrida: 30 minutos. En cada corrida guarda `jobstate.log`, `history.long` y `history.json`, `*.dag.metrics`, `*.dag.nodes.log`, el `.dag`, los `.sub`, `braindump.yml`, las salidas de Kickstart y el tiempo de `pegasus-plan`. Montage no se repite.

Si el tiempo se acaba, prioriza: piloto → contraste completo → patrones con 2 workers → patrones con 4 workers.

Límite: 5 horas de VMs encendidas. Desasigna al terminar y confírmalo en `VMS.md`, junto con `tc qdisc show` final sin reglas en todos los nodos.

## Entregables en `intensivo_20261122/RESULTADOS/`

- `HIPOTESIS.md` y su `.sha256`, `PREDICCIONES.json`, `CONTRASTE_HIPOTESIS.md`, `ANCHO_DE_BANDA.json`, `TC.txt`, `CAMBIOS.md`, `VMS.md`.
- `BYTES.csv`: por corrida, requerido, observado, exceso, DME y comparación con FMA (×20).
- Por grupo (patrones, contraste): `jobs.csv`, `corridas.csv`, `resumen.csv`.
- `INTENSIVO.csv`: por condición, cada tramo promedio y cuál es el mayor (D2).
- `TRANSFERENCIA_VS_OBSERVADO.csv` (D3) y diferencias por bloque del contraste.
- `RESULTADOS_PARA_CLAUDE.md`: estado por fase, tabla de hipótesis (sí/no y por qué), tramos promedio ± desviación por condición, contraste con diferencias por tramo, ancho de banda y anomalías.
- Un zip con todo.