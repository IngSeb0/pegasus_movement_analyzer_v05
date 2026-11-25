# Diseño e hipótesis: Montage intensivo en datos

---

## Contexto

Tesis DME (requerido / observado bajo CondorIO; Pegasus 5.1.2, HTCondor 26.0.1, Azure Chile Central; coordinador `dme-master`, workers W1–W4 de 1 núcleo). La tesis estudia **flujos intensivos en datos**. Las pruebas sintéticas ya se hicieron en ese régimen (`intensivo_20261122/`: archivos de 200 MiB, red limitada a 100 Mbit/s con `tc tbf`, transferencia como tramo mayor en 29 de 29 corridas).

El Montage actual (M101, 10 fotos, ~311 MB, red sin límite) **no es intensivo en datos**: ejecución 126 s, transferencias ~4 s. La literatura clasifica Montage como limitado por E/S en mosaicos grandes (Juve et al. 2013: 8 grados², 10 429 jobs, CPU 31 %). Objetivo: repetir la comparación **M101-BASE frente a M101-FINAL** (agrupar `mImgtbl` con `mAdd`) en un mosaico grande y en el mismo régimen de red, y comprobar si el exceso que evita agrupar se vuelve tiempo.

Criterio de intensivo en datos (igual que en `intensivo_20261122/`): **el tramo de transferencia es el mayor de la duración**, por encima de la ejecución y de cada tramo de coordinación.

Términos fijos: requerido, observado, exceso. Sin push, sin cambios de visibilidad, sin tocar evidencia preservada. Todo lo nuevo va en `montage_intensivo_20261122/`. Reutiliza el generador de Montage (`generate_workflow_montage.py`, MontagePy 2.3.0 empaquetado), Analyzer, el auditor, `herramientas/tabla_tiempos.py` + `resumir_tiempos.py` y el procedimiento de `tc` de `intensivo_20261122/`. Todo cambio va en `CAMBIOS.md`.

## Diseño

- **Mosaico**: 2MASS banda J centrado en M101, **2,0° × 2,0°** (si el disco o el tiempo no alcanzan, 1,5° × 1,5°; anótalo). Descarga las imágenes en el coordinador con `mArchiveList` + `mArchiveDownload` de MontagePy, guarda la lista, el número de imágenes y el SHA-256 de cada archivo en `ENTRADAS.json`.
- **Reproyección**: `mProjectPP` (la reproyección plano a plano que usan los flujos de Montage en Pegasus; Juve et al. 2013). Igual en todas las variantes.
- **Ubicación fija**: las alineaciones repartidas en round-robin fijo entre **W2, W3 y W4**; `mImgtbl` y `mAdd` en **W1**. Se fija en el plan y se comprueba en el historial.
- **Variantes** (lo único que cambia es qué tareas comparten job):
  - `MG-BASE`: una tarea por job.
  - `MG-FINAL`: `mImgtbl` y `mAdd` en el mismo job en W1.
- **Red**: `tc tbf rate 100mbit` en ambos sentidos, igual que en `intensivo_20261122/` (salida del coordinador y salida de cada worker). Mide el ancho de banda con un job HTCondor de 1 GiB antes de empezar. Guarda `tc qdisc show` antes, durante y después en `TC.txt`; quítalo al terminar en todos los nodos; si algo falla, quita `tc` antes de cualquier otra cosa.
- **Repeticiones**: 3 por variante, en bloques con orden rotado, un flujo a la vez.

## Fase 0: hipótesis antes de correr (sin nube)

Copia este archivo a `montage_intensivo_20261122/HIPOTESIS.md` y guarda su SHA-256 en `HIPOTESIS.sha256` **antes de encender las VMs**. No lo edites después; si algo cambia, anexo fechado.

Sea N el número de imágenes, A el tamaño total de las imágenes alineadas más sus mapas de área, ΔO = observado(BASE) − observado(FINAL) y B el ancho de banda medido.

| # | Hipótesis | Cómo se comprueba |
|---|---|---|
| M1 | El requerido es igual en BASE y FINAL (misma ubicación); el observado de FINAL es menor; ΔO ≈ tamaño de las imágenes alineadas más la tabla (la segunda copia que llegaba al job de `mImgtbl`), como en M101 | Analyzer, auditor, `PLAN_ACCOUNTS.json` |
| M2 | El mosaico y su cobertura son idénticos byte a byte entre BASE y FINAL | SHA-256 de los FITS finales |
| M3 | El flujo es intensivo en datos: la transferencia es el tramo mayor en todas las corridas | `corridas.csv` |
| M4 | El tramo de transferencia baja ≈ ΔO / B al agrupar (±25 %) | diferencias por bloque |
| M5 | La duración total baja al agrupar, en todos los bloques | `.dag.metrics` |

Escribe en `PREDICCIONES.json`, antes de correr y desde los planes: requerido, observado, DME y ΔO esperados por variante.

## Fase 1: preparación

1. Enciende (`Control-Cluster.ps1 -Action Start -Workers 4`). Revisa disco (`df -h`) en coordinador y workers: estima N × (foto + alineada + área) × 3 + mosaico × 4 y deja margen 2×. Si no cabe 2,0°, usa 1,5°.
2. Descarga las imágenes en el coordinador y registra `ENTRADAS.json`.
3. Genera y planifica BASE y FINAL; guarda `PLAN_ACCOUNTS.json` y `PREDICCIONES.json`.

## Fase 2: piloto

1. Aplica `tc` y mide B (`ANCHO_DE_BANDA.json`).
2. Ejecuta **una corrida de BASE**. Corre Analyzer, el auditor y `tabla_tiempos.py`.
3. Si la transferencia **no** es el tramo mayor: detente, quita `tc`, desasigna y reporta los tramos (no cambies la red para forzarlo). Si Analyzer y el auditor no coinciden: detente y reporta. Si todo está bien, sigue sin pedir más autorización.

## Fase 3: matriz

3 bloques × (BASE, FINAL) en orden rotado. Límite por corrida: 45 minutos. Guarda por corrida: `jobstate.log`, `history.long` y `history.json`, `*.dag.metrics`, `*.dag.nodes.log`, el `.dag`, los `.sub`, `braindump.yml`, salidas de Kickstart, tiempo de `pegasus-plan` y SHA-256 de los FITS finales. Borra archivos grandes de los workers al terminar cada corrida (no los logs).

Límite: 5 horas de VMs encendidas. Desasigna al terminar y confírmalo en `VMS.md` con `tc qdisc show` final sin reglas.

## Entregables en `montage_intensivo_20261122/RESULTADOS/`

- `HIPOTESIS.md` y `.sha256`, `PREDICCIONES.json`, `ENTRADAS.json`, `PLAN_ACCOUNTS.json`, `ANCHO_DE_BANDA.json`, `TC.txt`, `CAMBIOS.md`, `VMS.md`.
- `BYTES.csv` (requerido, observado, exceso, DME por corrida) y `FITS_IGUALES.csv`.
- `jobs.csv`, `corridas.csv`, `resumen.csv`, diferencias por bloque de cada tramo.
- `CONTRASTE_HIPOTESIS.md` (M1–M5: sí/no, cifras y por qué).
- `RESUMEN_RESULTADOS.md`: N, área, tamaños, tramos promedio ± desviación por variante, ΔO, ahorro de transferencia frente a ΔO/B, duración, anomalías.
- Un zip con todo.
