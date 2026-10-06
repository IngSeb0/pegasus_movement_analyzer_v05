# TESIS — Design Specification

**Proyecto:** Data Movement Assessment in Scientific Workflows  
**Versión:** 1.0 — 30 de septiembre de 2026  
**Estado:** diseño completo candidato a Gate D  
**Entrada normativa:** `TESIS_REQUIREMENTS_SPEC_20260930.md` — Gate R cerrado  
**Regla:** este documento define **cómo** se satisfacen los requisitos. No cambia la semántica de la métrica.

---

# 1. Objetivo de diseño

Diseñar una herramienta post-mortem, reproducible y trazable que, para una ejecución Pegasus/HTCondor soportada, construya un modelo integrado de tareas, archivos, ubicaciones, declaraciones de transferencia y evidencia, y produzca:

```text
RequiredMovement
DeclaredMovement
Coverage
ByteCoverage
ObservedMovement o N/A
DME o N/A
estado + diagnósticos + provenance
```

El diseño separa estrictamente:

```text
SOURCES
   ↓
EXTRACTION
   ↓
NORMALIZATION
   ↓
INTEGRATION
   ↓
EXECUTION-MODEL ADAPTER
   ↓
MOVEMENT CONSTRUCTION
   ↓
EVIDENCE RECONCILIATION
   ↓
METRICS
   ↓
VALIDATION + REPORTING
```

El Analyzer no modifica artefactos de Pegasus/HTCondor y no ejecuta workflows.

---

# 2. Principios de diseño

1. **File-centric.** El archivo científico, no la arista abstracta del DAG, es la unidad base de movimiento.
2. **Evidence-first.** Una declaración de transferencia no se convierte en observación sin evidencia.
3. **Fail closed.** Ante ambigüedad se emite `N/A`, `UNSUPPORTED` o `INCONSISTENT`.
4. **No heurísticas silenciosas.** Ningún dato central se infiere solo por basename, extensión o orden temporal.
5. **Execution-model adapters.** La lógica central no hardcodea `master -> worker -> master`.
6. **Pattern-independent.** Los cinco patrones son casos de validación, no ramas del algoritmo.
7. **Placement-independent.** SAME/BALANCED/CROSS son configuración/contexto.
8. **Bytes canónicos.** Todos los cálculos internos usan enteros en bytes.
9. **Provenance por campo.** Cada tamaño, placement y evidencia conserva su origen.
10. **Compatibilidad histórica sin reinterpretación silenciosa.** v0.5.1 se conserva como baseline histórico.

---

# 3. Scope de implementación v1

## 3.1 Soportado

```text
Pegasus 5.x
condorio
HTCondor vanilla universe
HTCondor-managed file transfer
1 tarea científica lógica por job
submit host separado de workers científicos
archivos regulares con identidad/tamaño trazable
0 o 1 intento, o múltiples intentos solo con evidencia separable por intento
```

## 3.2 Detectado pero no soportado inicialmente

```text
sharedfs
bypass con origen no modelado por v1
transfer plugins/protocolos no soportados
clustered jobs
transferencia de directorios sin manifest expandido
múltiples productores ambiguos
identidad lógica no inequívoca
```

Estos casos producen `analysis_status = UNSUPPORTED` o `INCONSISTENT`, según corresponda.

---

# 4. Arquitectura lógica

## C1 — Run Source Loader

Responsabilidad: localizar y leer fuentes sin modificar el run.

Entradas posibles:

- Pegasus run directory;
- DAG y submit files;
- `.meta` / `cache.meta`;
- braindump/configuración Pegasus cuando exista;
- `condor_history -long` preservado;
- job event logs;
- experiment manifest opcional;
- archivos físicos preservados.

Salida: `RawRunSources`.

## C2 — Pegasus Semantic Extractor

Responsabilidad: reconstruir tareas científicas, declaraciones I/O y semántica de archivos usando información de Pegasus y de los submit files.

No calcula movimiento.

## C3 — HTCondor Evidence Extractor

Responsabilidad: extraer job identity, placement, estado, intentos y estadísticas de transferencia de ClassAds/history.

No atribuye bytes científicos.

## C4 — Normalizer / Identity Resolver

Responsabilidad: convertir nombres/paths/hosts a identificadores estables de corrida.

Resuelve:

- `task_id`;
- `job_id = ClusterId.ProcId`;
- `file_id` lógico estable;
- `location_id` canónico;
- mappings LFN ↔ paths/remaps.

## C5 — Execution Model Detector

Responsabilidad: construir `ExecutionModelProfile` y seleccionar adapter.

En v1 el adapter válido es `CondorIOStandardAdapter`.

## C6 — Scientific Dataflow Builder

Responsabilidad: construir `ScientificFile` y producer/consumers/roles/origin/final destinations.

## C7 — Required Movement Engine

Responsabilidad: construir y sumar `RequiredMovementRecord` con lógica file-centric.

## C8 — Declared Movement Builder

Responsabilidad: convertir el manifiesto efectivo de cada job en movimientos científicos declarados y conservar el manifiesto auxiliar completo para reconciliación.

## C9 — Transfer Evidence Reconciler

Responsabilidad: validar por job, dirección e intento si el manifiesto completo puede reconciliarse con estadísticas observadas.

## C10 — Metrics Engine

Responsabilidad: Coverage, ByteCoverage, ObservedMovement, DME e invariantes.

## C11 — Diagnostics / Provenance

Responsabilidad: registrar estados, warnings, errores y procedencia.

## C12 — Report Writer

Responsabilidad: JSON canónico, TSV y reporte legible.

## C13 — Experiment Runner

Responsabilidad separada del Analyzer: parametrizar y ejecutar campañas controladas, preservar evidence snapshots y llamar al Analyzer. Nunca contiene las fórmulas de la métrica.

---

# 5. Estructura física propuesta del repositorio

La implementación deberá evolucionar desde el repo actual sin borrar v0.5.1 durante la migración:

```text
pegasus_movement/
    __init__.py
    analyzer.py                 # v0.5.1 preservado durante transición

    model.py                    # dominio v1
    pegasus_source.py           # C1-C2
    htcondor_source.py          # C3
    normalize.py                # C4
    execution_model.py          # C5 + interfaz adapter
    condorio_adapter.py         # adapter v1
    dataflow.py                 # C6
    movement.py                 # C7-C8
    reconciliation.py           # C9
    metrics.py                  # C10
    diagnostics.py              # C11
    reporting.py                # C12
    analyzer_v1.py              # orquestación

tools/
    analyze_run.py              # CLI consolidado al final de migración
    run_validation.py           # C13, después del Analyzer

tests/
    unit/
    regression/
    integration/

fixtures/
    audited/
```

Durante implementación, el CLI histórico no se reemplaza hasta que los regression tests del nuevo pipeline pasen.

---

# 6. Modelo de datos canónico

## 6.1 `ProvenanceRef`

```text
source_kind       # submit/meta/history/event_log/physical_file/config/derived
source_path
attribute         # opcional
source_hash       # opcional, recomendado para snapshots
notes
```

Ningún campo crítico agregado debe carecer de provenance.

## 6.2 `Location`

```text
location_id       # canónico, p.ej. pegasus-master / pegasus-worker1
location_type     # submit_host | worker | external_site | final_site
raw_values[]      # hostnames/ClassAd values originales
provenance[]
```

La comparación de ubicación se hace por `location_id`, nunca por strings no normalizados.

## 6.3 `TaskExecution`

```text
task_id
pegasus_node_id
job_id            # ClusterId.ProcId
worker_location_id
job_status
exit_code
job_run_count
num_job_starts
successful
provenance[]
```

V1 exige una relación inequívoca tarea científica ↔ job científico.

## 6.4 `ScientificFile`

```text
file_id
logical_name
physical_refs[]
roles[]            # SET: external_input | intermediate | final_output
size_bytes
size_provenance
producer_task_id   # null para input externo
consumer_task_ids[]
origin_location_id # requerido para input externo
final_destination_ids[]
identity_provenance[]
```

**Decisión importante:** `roles` es un conjunto, no un único enum. Un archivo puede ser simultáneamente intermediate y final output.

V1 admite máximo un productor por `file_id`. Dos productores no versionados -> `INCONSISTENT`.

## 6.5 `ManifestFile`

Representa una entrada del sandbox, científica o auxiliar.

```text
job_id
direction          # input | output
logical_file_id    # null para auxiliar sin LFN científico
physical_path
basename
classification     # scientific | auxiliary
size_bytes
size_provenance
protocol           # cedar / http / ... si se conoce
remap_from
remap_to
```

## 6.6 `JobTransferManifest`

```text
job_id
direction
attempt_context
files[]: ManifestFile
expected_file_count
expected_total_bytes
scientific_file_count
scientific_total_bytes
complete            # todos los files/sizes necesarios conocidos
```

## 6.7 `TransferEvidence`

```text
job_id
direction
attempt_context
worker_location_id
raw_stats
methods[]
observed_file_count_last
observed_file_count_total
observed_bytes_last
observed_bytes_total
bytes_recvd
bytes_sent
transfer_started
transfer_finished
provenance[]
```

`raw_stats` conserva el nested ClassAd original para evitar perder semántica específica de versión.

## 6.8 `MovementVerification`

```text
job_id
direction
attempt_context
level               # FILE_LEVEL_CONFIRMED | JOB_LEVEL_RECONCILED | INSUFFICIENT
reconciliation_mode # EXACT_BYTES | SUCCESSFUL_MANIFEST | null
confirmed
reason_code
expected_file_count
observed_file_count
expected_total_bytes
observed_total_bytes
unexplained_bytes
confirmed_scientific_file_ids[]
provenance[]
```

## 6.9 `RequiredMovementRecord`

```text
file_id
from_location_id
to_location_id
size_bytes
required_bytes
reason              # input | consumer | final_destination
```

## 6.10 `DeclaredMovementRecord`

```text
movement_id
job_id
attempt_context
file_id
direction
from_location_id
to_location_id
size_bytes
verification_level
confirmed
verification_reason
```

## 6.11 `ExecutionModelProfile`

```text
pegasus_version
htcondor_version
data_configuration
universe
submit_host
should_transfer_files
when_to_transfer_output
bypass_enabled
plugin_methods[]
clustered_jobs
shared_filesystem
adapter_name
supported
unsupported_reasons[]
provenance[]
```

## 6.12 `MetricResult`

```text
required_movement_bytes
declared_movement_bytes
observed_movement_bytes   # null cuando indeterminado
coverage                   # 0..1 o null si no hay denominador
byte_coverage              # diagnóstico; null si denominador bytes=0
dme                        # null si N/A/indeterminado
observed_minus_required_bytes
analysis_status
metric_status
validation_reasons[]
evidence_levels[]
```

## 6.13 `RunExecution`

Agrega el modelo completo:

```text
run_id
run_path
workflow_name
pattern_context            # opcional; no gobierna cálculo
experiment_parameters      # opcional
tasks{}
scientific_files{}
locations{}
execution_model
manifests[]
evidence[]
required_movements[]
declared_movements[]
metric_result
provenance[]
```

---

# 7. Identidad y normalización

## 7.1 Tareas

`task_id` debe derivarse de identidad Pegasus estable. `ClusterId.ProcId` se usa como identidad HTCondor, no como identidad lógica de tarea.

Si dos jobs científicos reclaman representar la misma tarea sin relación explícita de retry/attempt, el análisis es `INCONSISTENT`.

## 7.2 Archivos

Nunca se identifica un archivo únicamente por `basename`.

La resolución sigue esta precedencia:

1. LFN/identidad explícita de Pegasus;
2. mapping explícito del job/metadata;
3. path físico + relación semántica inequívoca dentro de la corrida;
4. si sigue ambiguo -> `INCONSISTENT`.

Los remaps se conservan como mapping, no cambian `file_id`.

## 7.3 Locations

La normalización usa hostname completo/canonical name y aliases registrados. `worker1`, `slot1@pegasus-worker1` y hostname equivalente pueden mapearse a un único `location_id` solo si la equivalencia está documentada.

---

# 8. Construcción del dataflow científico

## 8.1 Identificación de tareas científicas

El extractor usa semántica Pegasus (nodos/jobs de cómputo del workflow) y excluye jobs de staging, cleanup, registration, create-dir y control.

La implementación no debe decidir que un job es científico solo porque el filename contiene `data_task`.

## 8.2 Clasificación de archivos

Para cada archivo lógico:

```text
producer = tarea científica que lo produce, si existe
consumers = tareas científicas que lo consumen
explicit_input = Pegasus lo registra como entrada externa / no tiene productor interno
explicit_output = stageOut/final output o salida no consumida declarada como resultado
```

Roles:

```text
external_input  si no tiene productor interno y es input científico
intermediate    si tiene productor interno y al menos un consumidor interno
final_output    si debe alcanzar un destino final declarado
```

Los roles pueden coexistir cuando la semántica lo exige.

## 8.3 Exclusión de auxiliares

El classifier usa roles de ejecución (executable, wrapper, metadata, stdout/stderr, Pegasus runtime), no extensiones como criterio único. Las extensiones pueden servir como señal auxiliar, nunca como decisión final.

---

# 9. Resolución de tamaños

Precedencia de tamaño:

1. metadata preservada de la corrida ligada inequívocamente al `file_id`;
2. manifest/cache metadata ligado al run;
3. archivo físico preservado con identidad histórica verificable;
4. si no existe tamaño confiable -> `INCOMPLETE_EVIDENCE` o `INCONSISTENT` según el caso.

Toda resolución retorna:

```text
size_bytes
size_source
confidence = authoritative | corroborated
```

No se estima tamaño por nombre, tamaño esperado del experimento o promedio.

---

# 10. Detección del execution model

`detect_execution_model()` inspecciona configuración y submit attributes relevantes antes de construir movimientos.

El `CondorIOStandardAdapter` acepta únicamente cuando puede demostrar:

```text
data_configuration == condorio
universe == vanilla
file transfer enabled
no sharedfs semantics
no unsupported bypass
no unsupported protocol/plugin semantics
1 scientific task per job
```

Un atributo no disponible que sea necesario para distinguir un caso soportado de uno no soportado produce `UNSUPPORTED`, no una suposición.

---

# 11. Algoritmo de RequiredMovement

## 11.1 Definición ejecutable

Para cada archivo científico `f`:

```text
origin =
    external origin, si external_input
    producer worker, si producido internamente

required_locations =
    set(worker de cada consumidor)
    UNION set(final destinations)

new_locations = required_locations - {origin}

contribution(f) = size(f) * count(new_locations)
```

Luego:

```text
RequiredMovement = SUM contribution(f)
```

## 11.2 Propiedades

- consumidores múltiples en el mismo worker -> una ubicación;
- fan-out a workers distintos -> una copia por worker;
- final destination ya incluida como consumer location -> no se duplica;
- archivo intermedio + final output -> unión de destinos;
- tamaño cero -> registro existe, aporta 0 bytes;
- no incluye rutas relay del execution model.

## 11.3 Salida trazable

Se genera un `RequiredMovementRecord` por par `(file_id, new_destination_location)`.

---

# 12. Algoritmo de DeclaredMovement

Para cada job científico ejecutado y cada dirección:

1. `CondorIOStandardAdapter` construye el `JobTransferManifest` efectivo.
2. Se incorporan **todos** los archivos del sandbox necesarios para reconciliación.
3. Solo los `ManifestFile.classification == scientific` generan `DeclaredMovementRecord`.
4. La dirección y locations provienen del execution model efectivo, no de una constante global.

En el scope v1 estándar:

```text
input : submit/access point -> worker
output: worker -> submit/access point
```

solo después de que el adapter confirme esa semántica para la corrida.

---

# 13. Construcción del manifiesto completo de transferencia

## 13.1 Input

El manifiesto de input debe considerar, según submit/ClassAd efectivo:

- executable si se transfiere;
- `transfer_input_files`;
- input estándar si aplica;
- PegasusLite/runtime/support files;
- archivos científicos;
- plugins transferidos como archivos auxiliares, si el adapter los soportara en el futuro.

## 13.2 Output

Debe considerar:

- `transfer_output_files` cuando está definido;
- stdout/stderr cuando HTCondor los transfiere y no son streamed;
- semántica de outputs implícitos si `transfer_output_files` no está definido;
- `when_to_transfer_output`;
- remaps explícitos.

Si el conjunto efectivo no puede determinarse exactamente, la dirección no puede obtener `JOB_LEVEL_RECONCILED`.

---

# 14. Evidencia HTCondor

El extractor conserva como mínimo:

```text
ClusterId
ProcId
GlobalJobId si existe
DAGNodeName / identidad Pegasus
LastRemoteHost / RemoteHost
JobStatus
ExitCode / ExitBySignal
JobRunCount
NumJobStarts
NumShadowStarts cuando exista
TransferInputStats
TransferOutputStats
TransferInputFileCounts cuando exista
TransferInputSizeMB solo como declaración/contexto, NO observación
BytesRecvd / BytesSent como cross-check, NO como payload científico directo
TransferIn/Out timestamps
Vacate/hold reasons cuando existan
```

Las nested ClassAds de stats se preservan en bruto y además se normalizan a campos conocidos por la versión soportada.

---

# 15. Reconciliación de transferencias

La unidad de reconciliación es:

```text
(job_id, direction, attempt_context)
```

## 15.1 Caso de un único intento

Una dirección puede recibir `JOB_LEVEL_RECONCILED` únicamente con manifiesto completo, intento conocido, worker identificado, transferencia finalizada sin error y sin métodos/protocolos no contabilizados. Después se aplica una de dos vías:

**Modo A — `EXACT_BYTES`.**

```text
observed_file_count == expected_file_count
observed_total_bytes == expected_total_bytes
unexplained_bytes == 0
```

Este es el nivel de reconciliación más fuerte a nivel job.

**Modo B — `SUCCESSFUL_MANIFEST`.**

Se usa cuando los tamaños de algunos auxiliares (por ejemplo stdout/stderr limpiados) no están disponibles para reconstruir exactamente todo el sandbox, pero sí se cumple simultáneamente:

```text
manifest efectivo completo
transferencia terminada exitosamente
observed_file_count == expected_file_count
sin hold/error de transferencia
intento único o separable
tamaño autoritativo de cada archivo científico
aggregate bytes compatible con incluir el payload científico
```

En este modo no se reparte el residuo auxiliar ni se estima el tamaño científico desde el total. El tamaño científico procede de su propia fuente autoritativa; la evidencia HTCondor confirma que el manifiesto que lo contiene fue transferido exitosamente.

Si ninguna vía se cumple, la dirección queda `INSUFFICIENT`.

## 15.2 Evidencia por archivo

Si una fuente futura prueba transferencia completa de un archivo concreto:

```text
level = FILE_LEVEL_CONFIRMED
```

Puede confirmar ese movimiento sin exigir reconciliación agregada del resto, aunque DME global seguirá requiriendo Coverage total = 1.

## 15.3 Múltiples intentos

```text
if attempts == 1:
    reconcile normally
elif evidence separates every attempt:
    build/reconcile one manifest occurrence per attempt
else:
    affected movements remain unconfirmed
    analysis_status = INCOMPLETE_EVIDENCE
```

Los campos `*Total` pueden servir para detectar multiplicidad/cross-check, pero no autorizan a multiplicar el manifiesto por `JobRunCount` sin evidencia por intento.

## 15.4 Transferencia parcial/fallida

No se confirma un archivo completo si la evidencia solo demuestra una transferencia parcial. Si existe evidencia exacta de bytes parciales, se conserva como diagnóstico, pero no sustituye el movimiento declarado completo para Coverage principal.

---

# 16. Coverage y ByteCoverage

Sea `D` el conjunto de `DeclaredMovementRecord` y `C` el subconjunto confirmado.

```text
Coverage = |C| / |D|
```

Si `|D| = 0`:

```text
Coverage = 1
```

por convención de cobertura completa de un conjunto vacío; la aplicabilidad de DME se resuelve después con los casos cero.

Diagnóstico:

```text
ByteCoverage = sum(size_bytes de C) / sum(size_bytes de D)
```

Si el denominador de bytes es cero:

```text
ByteCoverage = N/A
```

Los archivos de 0 bytes sí cuentan para `Coverage` por movimientos.

---

# 17. ObservedMovement

```text
if Coverage == 1:
    ObservedMovement = SUM(size_bytes de cada DeclaredMovementRecord confirmado)
else:
    ObservedMovement = null
```

`ObservedMovement` suma ocurrencias/materializaciones, no archivos lógicos únicos.

---

# 18. DME e invariantes

Precondiciones:

```text
Coverage == 1
same scientific scope
same location semantics
ObservedMovement is not null
```

Reglas:

```text
RM=0, OM=0  -> DME=N/A, metric_status=NOT_APPLICABLE
RM=0, OM>0  -> DME=0
RM>0, OM=0  -> INCONSISTENT, DME=N/A
OM<RM        -> INCONSISTENT, DME=N/A
otherwise    -> DME=RM/OM
```

Para resultado `VALID` con movimiento:

```text
0 <= DME <= 1
```

También se reporta:

```text
ObservedMinusRequired = ObservedMovement - RequiredMovement
```

como exceso respecto al lower bound lógico, nunca como ahorro garantizado.

---

# 19. Estados y diagnósticos

## 19.1 `analysis_status`

```text
VALID
NOT_APPLICABLE
INCOMPLETE_EVIDENCE
UNSUPPORTED
INCONSISTENT
FAILED_WORKFLOW
ERROR
```

## 19.2 Precedencia

```text
ERROR
  > INCONSISTENT
  > UNSUPPORTED
  > FAILED_WORKFLOW
  > INCOMPLETE_EVIDENCE
  > NOT_APPLICABLE
  > VALID
```

La precedencia se usa solo para el estado agregado; todos los diagnósticos individuales se conservan.

## 19.3 Reason codes mínimos

```text
UNSUPPORTED_SHARED_FS
UNSUPPORTED_BYPASS
UNSUPPORTED_TRANSFER_PLUGIN
UNSUPPORTED_CLUSTERED_JOB
UNSUPPORTED_DIRECTORY_TRANSFER
AMBIGUOUS_FILE_IDENTITY
MULTIPLE_PRODUCERS
MISSING_FILE_SIZE
CONFLICTING_FILE_SIZE
MISSING_PLACEMENT
AMBIGUOUS_JOB_IDENTITY
HISTORY_MISSING
RETRY_NOT_SEPARABLE
PARTIAL_TRANSFER
MANIFEST_INCOMPLETE
TRANSFER_COUNT_MISMATCH
TRANSFER_BYTES_MISMATCH
UNACCOUNTED_PROTOCOL
FAILED_SCIENTIFIC_JOB
OBSERVED_LT_REQUIRED
SCOPE_MISMATCH
ZERO_MOVEMENT
```

---

# 20. Provenance y auditabilidad

Cada valor crítico debe poder responder:

```text
¿de qué archivo/atributo salió?
¿cómo fue normalizado?
¿qué regla lo transformó?
¿qué registros contribuyeron al agregado?
```

El JSON final conserva referencias a fuentes y el `REPORT.txt` resume las fuentes principales.

Para experimentos oficiales se preservará un snapshot de `condor_history -long` inmediatamente después de la corrida para evitar pérdida por purga.

---

# 21. Interfaz del Analyzer

CLI objetivo:

```bash
python3 tools/analyze_run.py \
  --run /path/to/run0001 \
  --history-file /path/to/history.long \
  --experiment-manifest /path/to/experiment.json \
  --out results/run-id
```

`--experiment-manifest` es opcional para el cálculo; aporta contexto experimental/oráculos, no sustituye evidencia Pegasus/HTCondor.

Opciones futuras compatibles:

```text
--strict                 default true
--json-only
--allow-file-level-evidence
```

No se diseña un flag que fuerce cálculo de DME cuando las precondiciones fallan.

## Exit codes

```text
0  análisis válido (DME calculado o NOT_APPLICABLE legítimo)
2  INCOMPLETE_EVIDENCE
3  UNSUPPORTED
4  INCONSISTENT / FAILED_WORKFLOW
5  ERROR de herramienta/entrada
```

---

# 22. JSON canónico

Archivo principal: `analysis.json`.

Esquema conceptual:

```json
{
  "schema_version": 1,
  "analyzer_version": "...",
  "run": {},
  "execution_model": {},
  "sources": [],
  "locations": [],
  "tasks": [],
  "scientific_files": [],
  "required_movements": [],
  "declared_movements": [],
  "transfer_evidence": [],
  "verifications": [],
  "metrics": {
    "required_movement_bytes": 0,
    "declared_movement_bytes": 0,
    "coverage": 1.0,
    "byte_coverage": 1.0,
    "observed_movement_bytes": 0,
    "dme": null,
    "analysis_status": "NOT_APPLICABLE"
  },
  "diagnostics": []
}
```

No se serializa `NaN`; valores indeterminados usan `null` más reason code.

---

# 23. Tablas de salida

```text
scientific_files.tsv
    file_id roles size_bytes producer consumers origin final_destinations size_source

task_placement.tsv
    task_id job_id worker status attempts source

required_movement.tsv
    file_id source_location destination_location size_bytes required_bytes reason

declared_movement.tsv
    movement_id job_id attempt file_id direction source destination size_bytes confirmed evidence_level

transfer_evidence.tsv
    job_id direction attempt expected_files observed_files expected_bytes observed_bytes level reason

summary.tsv
    run_id RequiredMovement DeclaredMovement Coverage ByteCoverage ObservedMovement DME status
```

`REPORT.txt` presenta la misma información de forma humana y lista warnings/unsupported reasons.

---

# 24. Diseño del Experiment Runner

El runner se mantiene fuera del núcleo del Analyzer.

Entrada: `experiments.yaml`.

```yaml
campaign_id: pipeline-sensitivity-v1
pattern: pipeline
factors:
  size_mib: [1, 10, 50]
  stages: [2, 3, 5]
  placement: [same-w1, balanced-local, cross]
repetitions: 3
```

Responsabilidades:

1. validar configuración;
2. crear identificador único de caso;
3. ejecutar generador del workflow;
4. ejecutar Pegasus;
5. esperar estado terminal;
6. preservar run path;
7. snapshot de history/ClassAds;
8. escribir `experiment_manifest.json` con versiones/factores;
9. llamar Analyzer;
10. agregar resultados sin reinterpretarlos.

No selecciona casos según resultados y no reintenta silenciosamente un experimento fallido como si fuera la misma repetición.

---

# 25. Diseño de pruebas antes de implementar

## 25.1 Unit tests

### Scientific data model

- roles no exclusivos;
- duplicate LFN ambiguo;
- multiple producers;
- zero-byte file.

### RequiredMovement

- same worker;
- cross worker;
- shared file same worker;
- fan-out multiple workers;
- intermediate + final output;
- external input con origen igual/diferente.

### DeclaredMovement

- científico vs auxiliar;
- stdout/stderr auxiliares;
- remaps explícitos;
- unsupported directory.

### Reconciliation

- exact bytes/count -> reconciled;
- bytes mismatch;
- file count mismatch;
- missing size;
- retry ambiguous;
- multiple protocol unsupported;
- partial transfer.

### Metrics

- Coverage 1/0/parcial;
- ByteCoverage;
- zero cases;
- OM < RM;
- DME range.

## 25.2 Regression fixtures

Fixtures auditados candidatos a regresión:

```text
pipeline SAME 10 MiB      -> RM 20 / OM 60 / DME 0.3333
pipeline BALANCED 10 MiB  -> RM 30 / OM 60 / DME 0.5
pipeline CROSS 10 MiB     -> RM 40 / OM 60 / DME 0.6667
process SAME 50 MiB       -> RM 100 / OM 100 / DME 1.0
pipeline BALANCED 50 MiB  -> RM 150 / OM 300 / DME 0.5
```

Antes de congelarlos como oráculos automáticos, cada fixture debe registrar por dirección si usa `EXACT_BYTES` o `SUCCESSFUL_MANIFEST` y conservar la evidencia que satisface esa vía. Los inputs de 50 MiB ya muestran reconciliación exacta; los outputs cuyo auxiliar fue limpiado deben quedar explícitamente etiquetados como `SUCCESSFUL_MANIFEST` si cumplen sus condiciones.

También debe existir al menos un fixture negativo por estado `INCOMPLETE_EVIDENCE`, `UNSUPPORTED` e `INCONSISTENT`.

## 25.3 Integration tests

Se ejecutan contra copias preservadas de runs reales y comparan:

```text
identidad de tareas
scientific file set
placement
manifiestos
reconciliación
métricas
provenance
```

## 25.4 Validation experiments

Solo después de Gate I:

- cinco patrones oficiales;
- repeticiones;
- tamaño;
- pipeline stages;
- fan-out;
- fan-in;
- redistribution;
- casos negativos;
- overhead.

---

# 26. Diseño de validación independiente

El oráculo no debe ejecutar el mismo algoritmo del Analyzer.

Para casos pequeños se preservan hojas/cálculos manuales donde se enumeran explícitamente:

```text
archivo
origen lógico
consumer locations
final destination
required copies
expected declared staging occurrences
```

La comparación automática solo lee el oráculo congelado.

---

# 27. Reproducibilidad y versionado

Cada resultado oficial registra:

```text
Analyzer version/commit
Pegasus version
HTCondor version
Python version
run id/path
experiment id
execution model profile
input source hashes cuando sea práctico
UTC/local timestamps de captura
```

Los artefactos históricos nunca se reescriben para “corregir” semántica; se reanalizan produciendo una nueva carpeta/version de resultados.

---

# 28. Overhead

El Analyzer es post-mortem y no debe introducir overhead en la ejecución salvo la captura/preservación adicional de evidencia.

La campaña final medirá por separado el costo de:

```text
snapshot de ClassAds/history
instrumentación adicional, si se añade
Analyzer post-mortem
```

El tiempo del Analyzer no se suma al runtime científico.

---

# 29. Migración desde v0.5.1

1. congelar fixtures/output históricos;
2. no cambiar significado de archivos antiguos;
3. implementar v1 en módulos nuevos;
4. ejecutar tests antiguos para detectar regresiones accidentales;
5. añadir regression tests con semántica nueva;
6. comparar `DeclaredMovement_v1` contra el antiguo `m_obs` histórico donde corresponda;
7. solo cuando v1 sea estable, actualizar CLI y README;
8. mantener nota explícita: histórico `m_obs` = `M_rec`.

---

# 30. Orden de implementación después de Gate D

```text
I1 model + diagnostics
I2 source loaders/parsers
I3 normalization/identity
I4 execution model detection + condorio adapter
I5 scientific dataflow
I6 RequiredMovement
I7 declared manifests/movement
I8 HTCondor evidence
I9 reconciliation
I10 Coverage/Observed/DME
I11 reporting
I12 regression fixtures
I13 integration
I14 experiment runner
```

Cada bloque requiere unit tests antes del siguiente bloque que dependa de él.

---

# 31. Diseño de seguridad metodológica

La herramienta nunca debe:

- inventar bytes faltantes;
- inferir un worker por orden de ejecución;
- asumir master como origen universal;
- sumar sandbox total como científico;
- convertir declaración en observación;
- ocultar un retry;
- cambiar resultados históricos in-place;
- rankear placements por DME;
- usar pattern name para decidir fórmula.

---

# 32. Matriz de trazabilidad

La trazabilidad completa requisito -> componente -> modelo -> algoritmo -> fuente -> diagnóstico -> test se mantiene en:

`TESIS_TRACEABILITY_MATRIX_20260930.md`.

La matriz forma parte normativa del diseño. Un requisito sin fila bloquea Gate D.

---

# 33. Criterios de Gate D

Gate D puede cerrarse únicamente si:

- cada requisito de Gate R aparece en la matriz de trazabilidad;
- no existen decisiones de arquitectura abiertas necesarias para empezar I1;
- el modelo de datos cubre edge cases conocidos;
- los algoritmos de RM/DM/reconciliación/Coverage/DME están definidos;
- los estados y reason codes están definidos;
- interfaces y outputs están definidos;
- la estrategia de migración está definida;
- la estrategia de pruebas está definida antes de implementar.

La revisión formal se registra en `TESIS_GATE_D_REVIEW_20260930.md`.

---

<!-- SYNC_20260930_I13_GATEI -->
## Checkpoint sincronizado — 2026-09-30 después de I13

Este bloque actualiza el **estado operativo** y no redefine requisitos, diseño ni fórmulas congeladas.

```text
Gate R — Requirements      CLOSED
Gate D — Design            CLOSED
I0–I13 — Implementation   CLOSED
Gate I — Implementation    ACTIVE: cierre documental/CLI pendiente
I14 — Experiment runner    BLOCKED hasta Gate I
Gate V — Validation        BLOCKED hasta Gate I
```

Evidencia verificada:

- `55712ed` — orquestación end-to-end Analyzer v1.
- `b5880d6` — regresiones auditadas I12.
- `77c6ff6` — integración I13 con runs preservados.
- suite con integración: **142/142 PASS**.
- runs reales preservados: process 50 MiB, pipeline 50 MiB BALANCED y pipeline 10 MiB SAME/BALANCED/CROSS.
- `schema_version = 1`.
- auditoría de hardcodes: no hay ramas de cálculo dependientes de SAME/BALANCED/CROSS ni de los cinco patrones en el núcleo v1.
- analyzer histórico `pegasus_movement/analyzer.py` preservado con SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

**Cadena correcta desde este punto:** sincronizar evidencia y documentación siguiendo el protocolo, terminar README/CLI de v1, ejecutar una única suite final de Gate I, cerrar Gate I formalmente y solo entonces activar I14.

