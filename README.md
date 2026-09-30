# Pegasus Data Movement Analyzer v0.5

Analizador de una ejecución Pegasus/HTCondor para la tesis **Data Movement Assessment in Scientific Workflows**.

## Definiciones implementadas

- **M_obs**: suma del payload científico materializado por los jobs, reconstruido desde `transfer_input_files` y `transfer_output_files` de los `.sub`. Cada ocurrencia cuenta.
- **M_req**: mínimo payload científico que debe **cambiar de ubicación**, manteniendo el placement observado de las tareas y permitiendo reutilización ideal de datos locales.

Reglas de `M_req`:

1. Input externo: master → worker cuenta una vez por ubicación destino necesaria.
2. Intermedio: mismo worker = 0; worker distinto = tamaño del archivo.
3. Output final: worker → master cuenta su tamaño.

La herramienta **no** usa `BytesSent + BytesRecvd` como payload científico y no cuenta ejecutables, worker packages, logs, `.meta`, scripts ni overhead de protocolo.

## Entrada mínima

Un directorio Pegasus `runXXXX` que conserve:

- `data_task_ID*.sub`
- `data_task_ID*.meta` para tamaños de outputs
- acceso a inputs/outputs físicos, cuando el tamaño no aparece en `.meta`
- placement de cada tarea mediante una de estas fuentes:
  1. `--placement-tsv`
  2. `--history-file` generado con `condor_history -long`
  3. `condor_history` vivo en el master

## Uso recomendado en el master

Desde la raíz del repositorio:

```bash
python3 tools/analyze_run.py \
  --run /ruta/al/run0001 \
  --history-file /ruta/history.long \
  --out results/movement_v05/distribution_rep1
```

Para congelar la evidencia de placement inmediatamente después de una corrida:

```bash
condor_history -long > results/history_distribution_rep1.long
```

También puede usarse un TSV explícito:

```text
task\tworker
data_task_ID0000001\tworker2
data_task_ID0000002\tworker1
```

```bash
python3 tools/analyze_run.py \
  --run /ruta/al/run0001 \
  --placement-tsv task_placement.tsv
```

## Salidas

- `summary.tsv`: M_req, M_obs y diagnóstico agregado.
- `task_placement.tsv`: dónde ejecutó cada tarea y de qué fuente se obtuvo.
- `file_sizes.tsv`: tamaño de cada archivo científico y fuente del tamaño.
- `observed_transfers.tsv`: cada ocurrencia que aporta a M_obs.
- `required_movement.tsv`: cada entrada/dependencia/output y cuánto aporta a M_req.
- `summary.json`: todo lo anterior en un único artefacto legible por scripts.
- `REPORT.txt`: resumen humano.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

La fixture `distribution_real_reconstructed` reproduce el caso de Distribution de 10 MiB usando el placement capturado en el tracing real del 13 de septiembre de 2026: T1–T4 en worker2 y T5 en worker1. El resultado esperado es:

```text
M_req = 22.5 MiB
M_obs = 40.0 MiB
```

La fixture es una reconstrucción mínima de los artefactos científicos necesarios para probar el cálculo; no pretende ser una copia completa del `run0001` original.
