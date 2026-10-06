# Pegasus Data Movement Analyzer v1

Analizador post mortem de una ejecución Pegasus/HTCondor para la tesis **Data Movement Assessment in Scientific Workflows**. Esta rama contiene Analyzer v1. El analizador v0.5.1 permanece como referencia histórica en `main`; su CLI es `tools/analyze_run.py` y su semántica de movimiento observado no debe trasladarse a v1.

## Entradas y alcance

La CLI v1 lee un directorio Pegasus `runXXXX` preservado y un archivo HTCondor history explícito (`condor_history -long` archivado). No consulta el collector ni el history vivo durante el análisis. El run aporta `workflow.yml`, submits `.sub`, metadatos `.meta`, DAG y configuración disponible; el history aporta estado de jobs, placement y estadísticas de transferencia. Las decisiones conservan referencias de procedencia y diagnósticos.

El perfil de ejecución v1 admite Pegasus 5.x con `pegasus.data.configuration=condorio`, jobs HTCondor vanilla y transferencia de archivos gestionada por HTCondor, con submit host distinto de los workers científicos. El detector exige evidencia del perfil; un valor ausente no se supone compatible. Shared filesystem, bypass no modelado, plugins/protocolos no contabilizados, clustered jobs y retries sin intento separable quedan fuera del cálculo válido. También bloquean las magnitudes dependientes las identidades, tamaños, placements o evidencias insuficientes/contradictorias.

## Frontera científica y magnitudes

El payload científico incluye inputs externos, intermedios y outputs finales del dataflow. Ejecutables, paquetes de worker, scripts auxiliares, metadatos, stdout/stderr, logs, archivos de control y overhead de protocolo no se suman como movimiento científico.

- **RequiredMovement** (`M_req`) es el límite lógico file-centric condicionado al placement observado: para cada archivo científico `f`, `Size(f)` se suma una vez por ubicación requerida distinta que no sea su origen. Consumers en el mismo worker comparten una ubicación requerida; producer y consumer en el mismo worker aportan cero. Un destino final nuevo sí cuenta. No se fuerza al master como tránsito de un intermedio ni se optimiza el placement.
- **DeclaredMovement** (`M_rec`) suma las ocurrencias científicas declaradas por los manifests efectivos del modelo de ejecución. Un manifest expresa lo esperado; por sí mismo no demuestra transferencia.
- **TransferEvidence** y **MovementVerification** cotejan manifest, job, worker, dirección e intento con el HTCondor history. Los niveles de evidencia son `FILE_LEVEL_CONFIRMED`, `JOB_LEVEL_RECONCILED` e `INSUFFICIENT`; los modos de reconciliación representados son `EXACT_BYTES` y `SUCCESSFUL_MANIFEST`. Los bytes auxiliares no se reparten proporcionalmente entre archivos científicos.
- **Coverage** es el cociente entre ocurrencias científicas declaradas confirmadas y ocurrencias científicas declaradas. Si el conjunto declarado está vacío, su valor es 1 por convención. Las ocurrencias de cero bytes también cuentan. `ByteCoverage` es un diagnóstico separado.
- **ObservedMovement** (`M_obs`) suma tamaños de ocurrencias científicas declaradas confirmadas, solo cuando `Coverage=1`. Si falta evidencia, `M_obs` completo y DME son indeterminados; la falta de evidencia no equivale a cero bytes.
- **DME** es `M_req/M_obs` cuando las precondiciones son válidas. Si ambos movimientos son cero, DME es `N/A`; si `M_req=0` y `M_obs>0`, DME es 0. `M_obs<M_req` produce estado inconsistente, no una DME válida.

`M_obs−M_req` expresa movimiento adicional respecto al límite lógico bajo ese placement. No demuestra bytes ahorrables. DME no mide tiempo, latencia, bandwidth, costo ni calidad global del scheduler.

## Uso de la CLI v1

Desde la raíz del repositorio:

```bash
python3 tools/analyze_run_v1.py \
  --run fixtures/audited/runs/process-same-w1-20260917-232331/luis/pegasus/dm-process/run0001 \
  --history-file fixtures/audited/history/process_50mib.long \
  --out /tmp/analyzer-v1-process
```

Las tres rutas son obligatorias. `--out` es el único destino de escritura de reportes; use una ruta nueva para no reemplazar una salida anterior. El comando genera `analysis.json`, `summary.tsv`, `scientific_files.tsv`, `task_placement.tsv`, `required_movement.tsv`, `declared_movement.tsv`, `transfer_evidence.tsv` y `REPORT.txt`. Los reportes conservan estado, razones y procedencia; `N/A` se representa como `null` en JSON.

Los códigos de salida siguen el estado global: `0` para `VALID` o `NOT_APPLICABLE`; `2` para `INCOMPLETE_EVIDENCE`; `3` para `UNSUPPORTED`; `4` para `INCONSISTENT` o `FAILED_WORKFLOW`; `5` para `ERROR`. Un diagnóstico bloqueante impide informar métricas dependientes como si fueran válidas.

## Pruebas y evidencia preservada

```bash
python3 -m unittest discover -s tests -v
```

La integración de cinco runs auditados se activa explícitamente. Para las copias portables:

```bash
PEGASUS_EXPERIMENTS_ROOT="$PWD/fixtures/audited/runs" \
PEGASUS_RUN_INTEGRATION=1 \
python3 -m unittest tests.integration.test_preserved_runs -v
```

En `pegasus-master`, para leer los runs originales preservados:

```bash
PEGASUS_EXPERIMENTS_ROOT="$HOME/pegasus-lab/pegasus_avance_semana_1_6/experiments" \
PEGASUS_RUN_INTEGRATION=1 \
python3 -m unittest tests.integration.test_preserved_runs -v
```

Las copias en `fixtures/audited/runs/` preservan los artefactos necesarios para análisis y sus checksums están en `MANIFEST.sha256`. El mapa de casos, histories y oráculos está en `fixtures/audited/integration_runs.json`. Estos tests son evidencia de implementación/regresión; no son la campaña experimental final de Gate V. Consulte `TEST_REPORT.txt` para resultados ejecutados y el commit al que se atribuyen.

## Material de tesis

- Nueva presentación: [`docs/thesis/presentation/PRESENTACION_DATA_MOVEMENT_CLARA_20261005.pptx`](docs/thesis/presentation/PRESENTACION_DATA_MOVEMENT_CLARA_20261005.pptx)
- Guion oral: [`docs/thesis/presentation/GUION_SUSTENTACION_CLARO_20261005.md`](docs/thesis/presentation/GUION_SUSTENTACION_CLARO_20261005.md)
- Auditoría de frontera de medición: [`docs/thesis/presentation/AUDITORIA_FRONTERA_METRICA_20261005.md`](docs/thesis/presentation/AUDITORIA_FRONTERA_METRICA_20261005.md)
- Código fuente reproducible de la presentación: [`docs/thesis/presentation/build_presentacion_clara_20261005.mjs`](docs/thesis/presentation/build_presentacion_clara_20261005.mjs)
