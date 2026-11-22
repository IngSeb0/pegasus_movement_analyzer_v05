# Cómo funciona el Analyzer

Son dos programas cortos que leen lo que dejaron Pegasus y HTCondor. Ninguno ejecuta nada.

| Programa | Líneas | Responde |
|---|---|---|
| `analyzer.py` | 114 | ¿Cuántos bytes eran necesarios, cuántos se movieron según el contrato y cuál es el DME? |
| `tiempos.py` | 57 | ¿En qué se fue la duración del flujo? |

```
python analyzer.py CARPETA_run0001 history.long [-v]
python tiempos.py  CARPETA_run0001 history.long
```

---

# Parte 1. `analyzer.py`: bytes y DME

## Qué lee

| Entrada | Qué es | Qué se saca de ahí |
|---|---|---|
| `run0001/workflow.yml` | El flujo tal como se diseñó | Qué tarea produce y qué tareas leen cada archivo; cuáles son resultados finales |
| `run0001/00/00/*.meta` | Datos que Pegasus anota por job | El tamaño en bytes de cada archivo |
| `run0001/00/00/*.sub` | El **contrato** de cada job: lo que HTCondor debe enviarle y recogerle | Qué archivos debía recibir y devolver cada job |
| `history.long` | Historial de HTCondor | Dónde corrió cada job, cuántas veces, cómo terminó y qué transferencias registró |

La máquina se toma del historial y no del plan: el plan puede decir una cosa y HTCondor hacer otra.

## Los pasos (cada uno tiene su comentario `# N.` en el código)

| Paso | Líneas | Qué hace |
|---|---|---|
| 1 | 27–31 | Tamaño de cada archivo, desde los `.meta`. |
| 2 | 33–42 | Productor y lectores de cada archivo, desde `workflow.yml`. |
| 3 | 44–51 | Qué tareas van en cada job. Normalmente una; si Pegasus agrupó (`merge_*`), las lee del `.in`. |
| 4 | 53–58 | Un bloque del historial por cada intento de cada job. |
| — | 60–74 | **Diagnóstico 1**: un solo intento por job, terminado bien y con máquina conocida. |
| 5 | 76–90 | **Requerido** (aquí está la suma, línea 88). |
| 6 | 92–110 | **Contrato** (suma en la línea 102) y **Diagnóstico 2**: lo que HTCondor registró debe cuadrar con el contrato. |

**Requerido** (paso 5): para cada archivo científico se cuenta una vez por cada máquina que lo necesita y no lo tiene. Como CondorIO hace pasar todo por el coordinador (`dme-master`), un archivo que un worker produce y otro worker lee también cuenta hacia el coordinador, y los resultados finales también llegan allí. Fórmula: `requerido += tamaño × número de destinos`.

**Contrato** (paso 6): suma, job por job, los archivos científicos que aparecen en `transfer_input_files` y `transfer_output_files` de su `.sub`.

## Reintentos y transferencias incompletas

Antes de dar un número, el programa exige tres cosas y, si alguna falla, **no calcula DME** y dice qué job y por qué:

| Control | Cómo se comprueba | Mensaje |
|---|---|---|
| Un solo intento por job | Un único bloque por job en `history.long` y `NumJobStarts = 1` | `2 registros en el historial (falta, o hubo reintentos)` / `se inició 2 veces (reintento)` |
| El job terminó bien y dice dónde corrió | `JobStatus = 4`, `ExitCode = 0`, `LastRemoteHost` presente | `no terminó bien o el historial no dice dónde corrió` |
| La transferencia cuadra con el contrato | `TransferInputStats` y `TransferOutputStats` existen; `CedarFilesCountTotal` es igual al número de archivos del `.sub` más el ejecutable (entrada) o más `stdout` y `stderr` (salida); `CedarSizeBytesTotal` es al menos la suma de los archivos científicos | `no registró la transferencia` / `registró 8 archivos y 1000000 B; el contrato pide 8 archivos y al menos 209715200 B` |

Estos controles se probaron con la evidencia real y con cuatro casos fabricados a partir de una corrida real (se quitó el registro de transferencia de un job, se duplicó un job como reintento, se puso `NumJobStarts = 2` y se recortaron los bytes de una entrada): en los cuatro el programa se negó a calcular y señaló el job.

## Contrato y «observado» de la tesis

El **observado** de la tesis es el contrato corroborado con los registros de HTCondor, que además distingue los reintentos. Con los tres controles anteriores, la salida de `analyzer.py` es ese mismo volumen: cada job corrió una vez y HTCondor registró el número de archivos del contrato y al menos sus bytes.

Una diferencia que se debe decir en voz alta: la tesis exige además **residuo cero** (los bytes registrados por HTCondor menos los auxiliares menos los científicos deben ser exactamente cero). Esta versión corta no conoce el tamaño de los auxiliares (paquete de Pegasus, scripts, ejecutable), así que comprueba el número exacto de archivos y que los bytes científicos estén cubiertos, pero no cierra la cuenta al byte. El Analyzer completo sí lo hace y queda en la rama `version-completa`.

## Archivo científico y archivo del contrato

El `.sub` lista **todo** lo que HTCondor le envía a un job, incluidos archivos que no son datos del flujo: el programa (`campaign_task`), el paquete de Pegasus, scripts y `.meta`. Un **archivo científico** es solo un dato del flujo: `A`, `g`, `B1`… Los que no son productor ni lector de ninguna tarea se ignoran y por eso no cuentan en DME. Un job agrupado repite nombres en su lista; se cuentan una vez, como hace HTCondor.

## Ejemplo real (Distribución, 2 workers, 200 MiB)

```
$ python analyzer.py run0001 history.long -v
  g:  dme-worker1 -> ['dme-master', 'dme-worker2']     2 copias
  B1: dme-worker1 -> ['dme-master']                     1 cada una de B1…B5 = 5
  ...
  A:  dme-master  -> ['dme-worker1']                    1
Requerido:           1677721600 B      (8 archivos de 200 MiB)
Contrato (.sub):     2516582400 B   (corroborado: un intento por job y mismo número de archivos)
DME con el contrato: 0.666667
```

El exceso son 4 envíos de `g`: tres jobs corrieron en el mismo worker que lo produjo y CondorIO se lo volvió a enviar desde el coordinador, y `g` llegó dos veces al segundo worker cuando bastaba una.

**Validación:** sobre las 30 corridas de 200 MiB, `analyzer.py` da los mismos bytes requeridos y el mismo volumen observado que `RESULTADOS/BYTES.csv` (30 de 30), sin que ninguno de los controles se active.

---

# Parte 2. `tiempos.py`: dónde se fue el tiempo

## La idea

La duración del flujo (`end_time − start_time` de `.dag.metrics`, DAGMan) se parte en seis tramos que **suman el total**. Se recorre la corrida segundo a segundo y cada segundo se asigna a **un solo** tramo: el primero de esta lista que lo cubre. Si ninguno lo cubre, es tiempo de DAGMan sin ningún job activo.

| # | Tramo | Qué es | De dónde sale |
|---|---|---|---|
| 1 | `ejecucion` | La tarea ya tiene sus entradas y corre hasta que empieza a devolver | `TransferInFinished` → `TransferOutStarted` (history) |
| 2 | `transferencia` | CondorIO moviendo entradas y salidas | `TransferInStarted`→`Finished` y `TransferOutStarted`→`Finished` (history) |
| 3 | `auxiliares` | Jobs de Pegasus (`create_dir`, `stage_in`, `stage_out`, `cleanup`, …) | envío → fin del post-script (jobstate.log) |
| 4 | `cola` | La tarea espera una máquina | envío (jobstate.log) → `TransferInStarted` (history) |
| 5 | `cierre` | Post-script de Pegasus tras terminar la tarea | `TransferOutFinished` → fin del post-script |
| 6 | `dagman` | Ningún job activo: DAGMan decide qué enviar | lo que no cubre ninguno de los anteriores |

La prioridad es el orden de la tabla: si una tarea ejecuta mientras otra transfiere, ese segundo es de ejecución. Por eso `transferencia` es lo que queda **sin** solaparse con cómputo, y es el valor que se compara con la ejecución para saber si el flujo es intensivo en datos.

HTCondor y Pegasus registran en segundos enteros: cada tramo tiene ±1 s de incertidumbre, y un tramo de 0 s significa «menos de un segundo». La base del desglose es Chen y Deelman (2011).

## Pasos del código

| Paso | Líneas | Qué hace |
|---|---|---|
| 1 | 19–29 | Lee `jobstate.log`: inicio y fin de DAGMan, envío de cada job y fin de su post-script. |
| 2 | 31–45 | Lee `history.long` y arma los intervalos de cada tramo. |
| 3 | 48–52 | Reparte cada segundo al primer tramo que lo cubre. |

## Ejemplo real (Distribución, 2 workers, 200 MiB)

```
$ python tiempos.py run0001 history.long
Duración del flujo (DAGMan): 292.5 s   (suma de tramos: 292 s)
  ejecucion        43 s   14.7 %
  transferencia   147 s   50.3 %
  auxiliares       50 s   17.1 %
  cola             18 s    6.2 %
  cierre           13 s    4.5 %
  dagman           21 s    7.2 %
```

La transferencia es el tramo mayor: ahí está el régimen intensivo en datos.

**Validación:** en las 30 corridas, los seis tramos coinciden segundo a segundo con los de `RESULTADOS/patrones/corridas.csv` (30 de 30).
