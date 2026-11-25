# Evaluación del movimiento de datos en flujos científicos con Pegasus bajo CondorIO

Calcula los **bytes requeridos**, el **volumen observado** (contrato de transferencia corroborado con HTCondor) y su cociente (DME) de un flujo ejecutado con Pegasus y HTCondor (CondorIO), desglosa en qué se fue el tiempo y trae lo necesario para producir esas corridas.

| Carpeta | Archivo de código | Guía |
|---|---|---|
| `analyzer/` | `analyzer.py`: DME de una corrida y control de reintentos y transferencias incompletas; `recomendar.py`: qué jobs juntar en cada máquina y cuántos bytes evita cada unión; `tiempos.py`: desglose de tiempos | `COMO_FUNCIONA.md` |
| `coordinador/` | `llevar.py` (29 líneas): sube, ejecuta y baja por SSH; `red.py`: limita la red para que el flujo sea intensivo en datos | `COMO_FUNCIONA.md` |
| `flujos/` | `crear_flujo.py`, `ejecutar_flujo.py`, `tarea.py`, `fma_kernel.c`; Montage: `montage.py`, `tarea_montage.py` | `COMO_FUNCIONA.md` |

`flujos/especificaciones.json` define las 13 condiciones sintéticas (cinco patrones con 2 y 4 workers, más tres de contraste), con archivos de 200 MiB. Las de Montage (147 fotos, `MG-BASE` y `MG-FINAL`) las escribe `flujos/montage.py`.

## Uso

```
python coordinador/llevar.py subir flujos analyzer
python coordinador/llevar.py correr "python3 flujos/crear_flujo.py flujos/especificaciones.json DISTRIBUTION-W2 caso1"
python coordinador/llevar.py correr "python3 flujos/ejecutar_flujo.py caso1"
python coordinador/llevar.py correr "python3 analyzer/analyzer.py RUTA_run0001 caso1/history.long -v"
```

Montage (147 fotos; `MG-BASE` o `MG-FINAL`):

```
python coordinador/red.py limitar 50        # (opcional) tope de red para el régimen intensivo en datos; «quitar» al terminar
python coordinador/llevar.py correr "python3 flujos/montage.py montage_m101"
python coordinador/llevar.py correr "python3 flujos/crear_flujo.py montage_m101/especificaciones.json MG-BASE montage_base"
python coordinador/llevar.py correr "python3 flujos/ejecutar_flujo.py montage_base"
```

Si ya tienes una corrida:

```
python analyzer/analyzer.py CARPETA_run0001 history.long -v     # bytes y DME
python analyzer/tiempos.py  CARPETA_run0001 history.long        # dónde se fue el tiempo
```

Solo necesitan Python y PyYAML.

## Probar en 1 minuto con los datos de prueba

`datos_prueba/distribucion_2workers/` trae una corrida real y pequeña (382 KB, sin los archivos de 200 MiB): el patrón de distribución con dos workers. Solo hace falta Python 3 y `pyyaml` (`pip install pyyaml`):

```
python analyzer/analyzer.py datos_prueba/distribucion_2workers/run0001 datos_prueba/distribucion_2workers/history.long -v
python analyzer/tiempos.py  datos_prueba/distribucion_2workers/run0001 datos_prueba/distribucion_2workers/history.long
```

Resultado esperado: requerido 1 677 721 600 B (1600 MiB), observado 2 516 582 400 B (2400 MiB) y **DME 0,666667** (2/3); duración 292,5 s, con la transferencia como tramo mayor (147 s). `calculo_esperado.json` tiene la cuenta independiente, archivo por archivo, para compararla.

Para ver qué agrupar:

```
python analyzer/recomendar.py datos_prueba/distribucion_2workers/run0001 datos_prueba/distribucion_2workers/history.long --ancho 11.8
```

Propone juntar en W1 el productor con sus tres consumidores y en W2 los otros dos; el observado previsto baja a 1 677 721 600 B, igual al requerido (DME 1). `--ancho` es el ancho de banda medido en MB/s y da un orden de magnitud del ahorro de transferencia. El recomendador supone que cada tarea sigue en la misma máquina y que cada máquina corre un job a la vez.

## Requisitos

- **Analyzer:** Python 3 y `pyyaml`.
- **Coordinador:** Pegasus 5.1.2, HTCondor 26.0.1, `pegasus-wms.api`, `pyyaml` y `gcc`.

## Qué se comprobó

- `analyzer.py` da los mismos bytes requeridos y el mismo volumen observado que el Analyzer completo en las 30 corridas de 200 MiB y en 2 corridas de ejemplo (32 de 32). Se niega a calcular, y dice qué job falla, cuando hay reintentos, jobs incompletos o transferencias que no cuadran con el contrato (probado con 4 casos fabricados).
- `recomendar.py`, sobre las corridas guardadas, propone primero la agrupación que se midió y con los mismos bytes evitados: Montage de 10 fotos (42 111 884 B), Montage de 147 fotos (616 161 787 B) y W2-SEP (600 MiB); sobre W2-AGR, ya agrupado, no propone nada. Sus propuestas en REP y en los patrones no se han ejecutado.
- `tiempos.py` reproduce los seis tramos de tiempo medidos de las 30 corridas (30 de 30).
- La tesis exige además residuo cero al byte; esta versión comprueba el número exacto de archivos y que los bytes científicos estén cubiertos, pero no conoce el tamaño de los archivos auxiliares.
- `crear_flujo.py` genera un `workflow.yml` con los mismos jobs, argumentos, archivos y requisitos que los de las corridas reales.
- Montage: `analyzer.py` da los mismos bytes que la tesis en las corridas reales de 147 fotos (MG-BASE: DME 0,858678; MG-FINAL: 0,999967). `montage.py` y `crear_flujo.py` se probaron con fotos sintéticas (flujo completo en local); la descarga desde IRSA no se pudo probar desde aquí.
- No se ejecutó `pegasus-plan` sobre esos `workflow.yml` fuera del coordinador.

## Relación con los experimentos

Las 30 corridas de la tesis se hicieron con scripts más largos (control de tiempo y disco, hashes, auditoría independiente), conservados junto con su evidencia en `intensivo_20261122_resultados.zip`. Este repositorio es la versión corta de lo mismo: calcula igual, pero no incluye esas protecciones ni el cierre al byte del Analyzer completo.
