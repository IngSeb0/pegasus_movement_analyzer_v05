# TESIS — Estado maestro

**Proyecto:** Data Movement Assessment in Scientific Workflows  
**Autor:** Luis Sebastián Contreras Díaz  
**Versión del registro:** 2026-09-25  
**Rol:** fuente compacta del estado conceptual y experimental vigente.

---

## 1. Propuesta vigente

La tesis diseña, implementa y valida una herramienta para **calcular una métrica de eficiencia del movimiento de datos científicos** durante ejecuciones Pegasus/HTCondor. El problema declarado por la propuesta es cómo definir y calcular esa medida integrando información de fuentes distintas y cómo comprobar su corrección, trazabilidad, consistencia y sensibilidad ante cambios controlados. Los registros disponibles no equivalen automáticamente a un volumen de transferencias físicas confirmado.

**Objetivo oficial:** «Diseñar, implementar y validar una herramienta que permita calcular una métrica para evaluar la eficiencia del movimiento de datos durante la ejecución de flujos de trabajo gestionados por Pegasus, utilizando los patrones process, pipeline, data aggregation, data distribution y data redistribution para evaluar la sensibilidad de la métrica bajo condiciones controladas de ejecución». Esta redacción proviene de la propuesta `ppg_ls.contreras_202620 (2).pdf` (copia local recibida también como `(2)(1).pdf`), §1.3.1. La fórmula concreta aún requiere una decisión conceptual y verificación de evidencia; la tesis no exige desarrollar un scheduler.

Patrones sintéticos de validación:

1. process;
2. pipeline;
3. data distribution;
4. data aggregation;
5. data redistribution.

---

## 2. Modelo formal vigente

### 2.1 Workflow

El workflow se representa como un DAG:

```math
WF=(Tasks,Deps)
```

- `Tasks={T1,...,Tn}`: tareas científicas.
- `Deps ⊆ Tasks × Tasks`: dependencias entre tareas.
- Para cada `(Ti,Tj) ∈ Deps`, `Data_ij` es el dato científico producido por `Ti` y consumido por `Tj`.
- `SizeOf(Data_ij)` devuelve su tamaño en bytes.

Además se distinguen `ExternalInputs` y `FinalOutputs`, porque el master no se modela como una tarea científica.

### 2.2 Placement

```math
PL: Tasks -> Workers
```

```math
PL(Ti)=Wk
```

significa que `Ti` ejecuta en el worker `Wk`.

SAME, BALANCED-LOCAL y CROSS son placements controlados concretos; no son algoritmos de scheduling.

### 2.3 Execution model

El modelo de ejecución fijo de los experimentos es:

```text
EM_HTC = Pegasus condorio + HTCondor file transfer
```

Semántica relevante:

- cada job científico ejecuta en un sandbox aislado;
- sus inputs científicos declarados se materializan antes de ejecutar;
- sus outputs científicos declarados se materializan al finalizar;
- el analizador reconstruye esas ocurrencias de staging como `master_to_worker` y `worker_to_master`;
- esta reconstrucción representa payload científico de transferencia a nivel de archivos, no tráfico Ethernet/packet-level.

---

## 3. M_req — referencia propuesta condicionada por ubicación

Definición **de trabajo**, pendiente de precisar en la métrica definitiva: cantidad mínima de datos científicos que deben cambiar de ubicación para satisfacer productores, consumidores, entradas y salidas, manteniendo fijo el placement `PL` y suponiendo que los archivos pueden reutilizarse localmente. El mínimo es **respecto de una ruta hipotética de reutilización local**; no está demostrado que la ruta sea alcanzable dentro de `condorio` ordinario.

Para una dependencia interna:

```math
ChangesWorker_ij(PL)=0  si PL(Ti)=PL(Tj)
ChangesWorker_ij(PL)=1  si PL(Ti)!=PL(Tj)
```

Para los workloads controlados, donde cada dependencia interna corresponde a un dato productor-consumidor:

```math
M_req(WF,SizeOf,PL) =
    sum_{D in ExternalInputs} SizeOf(D)
  + sum_{(Ti,Tj) in Deps} SizeOf(Data_ij) * ChangesWorker_ij(PL)
  + sum_{D in FinalOutputs} SizeOf(D)
```

En la implementación general del Analyzer v0.5.1, si un mismo archivo lógico es consumido por varias tareas, se cuenta una copia requerida por cada worker destino distinto; no se cuenta una copia por cada consumidor cuando varios consumidores están en el mismo worker.

`M_req` no busca el placement globalmente óptimo. Para archivos con varios consumidores se agrupa por worker destino distinto; la expresión por dependencia anterior describe únicamente los workloads controlados con un dato por dependencia. El nombre «requerido» no significa «mínimo factible bajo las reglas `condorio`».

---

## 4. M_rec reconstruido y M_obs confirmado

El analizador v0.5.1 reconstruyó el staging científico que implican las entradas y salidas por trabajo, bajo las hipótesis `EM_HTC`. La notación vigente para ese cálculo es `M_rec`:

```math
M_rec^HTC(WF,SizeOf) =
  sum_{Ti in Tasks} [
      sum_{D in Inputs(Ti)} SizeOf(D)
    + sum_{D in Outputs(Ti)} SizeOf(D)
  ]
```

`Inputs(Ti)` y `Outputs(Ti)` son los archivos científicos declarados/materializados por el job de `Ti` bajo el contrato de ejecución estudiado.

Consecuencia experimental: si se mantienen fijos `WF`, `SizeOf` y `EM_HTC`, y solo cambia `PL`, el conjunto y tamaño de entradas/salidas declaradas por job no cambia. Por ello `M_rec` fue invariante al placement en los escenarios controlados. Esta propiedad no se generaliza a otros modelos de ejecución.

`M_obs` se reserva para la suma de traslados científicos **efectivamente confirmados** para una corrida y para un límite de ubicaciones definido. Para reportarlo se necesita cobertura suficiente de archivos, segmentos y reintentos; si no existe esa evidencia, `M_obs` queda indeterminado. La igualdad `M_rec=M_obs` no se presume. Las columnas `M_obs` de las salidas históricas de v0.5.1 se reinterpretan como `M_rec`, sin modificar los archivos originales de la corrida.

`M_rec` no representa tráfico total de red. No incluye ejecutables, logs, stdout/stderr, `.meta`, worker packages ni overhead de protocolo. v0.5.1 no reconstruye multiplicidad de retries por intento.

---

## 5. Relación con scheduling

El algoritmo de scheduling no es un argumento directo de `M_req` ni de `M_obs`. Si se estudia una ejecución natural, el scheduler produce un placement `PL`; luego `M_req` evalúa ese placement. En las pruebas de correctitud se evita confundir scheduler y métrica fijando `PL` deliberadamente mediante `requirements` de HTCondor.

---

## 6. Herramienta actual

- Analyzer: Pegasus Movement Analyzer v0.5.1.
- Código principal: `tools/analyze_run.py` y `pegasus_movement/analyzer.py`.
- Infraestructura controlada: `workflow_controlled.py`, `run_controlled_case.sh`, `compare_controlled.py`.
- Driver de campaña: `run_validation_campaign.py`.
- Placements implementados: `same-w1`, `same-w2`, `balanced-local`, `cross`, `natural`.
- Control de placement: `requirements` de HTCondor.

Salidas relevantes:

- `task_placement.tsv`;
- `required_movement.tsv`;
- `observed_transfers.tsv`;
- `summary.tsv`;
- `summary.json`;
- `REPORT.txt`.

---

## 7. Matriz controlada a S=10 MiB

Formato histórico reinterpretado: `M_req / M_rec` MiB; no es `M_obs` confirmado.

| Patrón | SAME | BALANCED-LOCAL | CROSS |
|---|---:|---:|---:|
| Process | 20 / 20 | 20 / 20 | — |
| Pipeline | 20 / 60 | 30 / 60 | 40 / 60 |
| Distribution | 20 / 40 | 25 / 40 | 30 / 40 |
| Aggregation | 80 / 160 | 100 / 160 | 120 / 160 |
| Redistribution | 80 / 320 | 120 / 320 | 200 / 320 |

---

## 8. Evidencia cerrada

- Validación manual/script de BALANCED-LOCAL en los cinco patrones: PASS.
- Repetibilidad a `S=10 MiB`: 39/39 PASS.
- Sensibilidad de los cálculos a tamaños `S=1,10,50 MiB`: 45/45 PASS.

Las campañas prueban coincidencia con los oráculos del **movimiento reconstruido** y las reglas de referencia utilizadas. No prueban cobertura por evento de `M_obs`, validez general de `M_req/M_rec` como eficiencia real ni causalidad sobre el tiempo total.

**Auditoría del 25-09-2026:** en el pipeline de tamaño `S=10 MiB`, `M_req/M_rec` crece de `20/60` (SAME) a `40/60` (CROSS) aunque `M_rec=60 MiB` en ambos casos. Por ello el cociente no se interpreta como un indicador general donde un valor más alto implica menos datos movidos. Al revisar `analyzer_v051.py` se confirmó que el histórico `observed_transfers.tsv` se genera de `.sub` y tamaños de archivos, sin usar eventos de traslado confirmados para calcular bytes por archivo. La auditoría de registros crudos de la VM sigue pendiente. Consultar `TESIS_FICHA_DECISION_METRICA_20260925.md` y `TESIS_AUDITORIA_EVIDENCIA_MOVIMIENTO_20260925.md`.

---

## 9. Alineación metodológica

La estructura metodológica se alinea con la tesis de referencia de Vivas separando explícitamente: sistema, workloads, escenarios y métricas. En este trabajo no existe una sección de algoritmos comparados porque el objetivo no es evaluar schedulers; en su lugar se documentan placements controlados como escenarios experimentales. El diseño también mantiene factores/níveis y repeticiones explícitos siguiendo el enfoque sistemático de evaluación de desempeño de Jain.


---

## 10. Fuente oficial de alcance y cronograma

La propuesta oficial vigente es **`ppg_ls.contreras_202620 (2).pdf`**. Versiones anteriores de la propuesta no deben usarse para decidir cronograma, alcance ni hitos.

Según esa propuesta:

- semana 8: `A7` — diseño de arquitectura y modelo de datos; producto: **Diseño técnico**;
- semana 9: `A8` — extracción y normalización Pegasus/HTCondor; producto: **Prototipo de extracción**;
- semana 10: `A8–A9` — integración, cálculo automático y pruebas; producto: **P3 herramienta funcional**;
- el uso de 1, 2 o 4 nodos es una condición experimental opcional cuando contribuya a verificar una propiedad concreta de la métrica; no es una campaña obligatoria por sí sola.

---

## 11. Cierre de semana 8 — A7

El diseño técnico queda definido con seis responsabilidades lógicas:

```text
Fuentes Pegasus/HTCondor
        ->
Extracción
        ->
Normalización
        ->
Integración
        ->
Cálculo
        ->
Validación
        ->
Resultados
```

Modelo de datos común:

```text
Run
Node
Task
File
TaskIO
Dependency
StagingEvent
RequiredMovement
MetricResult
```

Principios:

- extracción no calcula métricas;
- normalización no interpreta experimentalmente resultados;
- integración relaciona tarea, archivo, productor, consumidor, placement y staging;
- cálculo consume el modelo integrado;
- la herramienta se mantiene independiente de SAME/BALANCED-LOCAL/CROSS;
- el harness experimental se mantiene separado del núcleo de medición;
- el modelo admite N workers sin cambiar las fórmulas.

Documento asociado:

```text
TESIS_SEMANA8_DISENO_TECNICO.md
```

La implementación separada de extracción/normalización queda como siguiente hito de semana 9.

---

## 12. Interpretación vigente de `M_req` y decisión conceptual

La semántica de `M_req` queda **cerrada como referencia lógica condicionada al placement**, aunque la medición final con `M_obs` sigue pendiente de auditoría.

`M_req` no representa la ruta `condorio`. Representa el **lower bound lógico de movimiento de payload científico inducido por el dataflow y el placement observado**, bajo dos supuestos declarados: reutilización local y comunicación directa entre ubicaciones. El master puede seguir siendo origen de inputs externos o destino de outputs finales, pero no se impone como tránsito obligatorio de todos los intermedios.

Por archivo distinto `d`, `M_req` contabiliza su tamaño una vez por cada ubicación destino nueva que deba alcanzar. Si productor y consumidor están en el mismo worker, el aporte interno es cero; si están en workers distintos, aporta el tamaño del archivo; si un archivo se comparte con varios consumidores en un mismo worker, no se duplica; si llega a workers distintos, se cuenta una copia por destino distinto.

Esta interpretación es consistente con literatura de workflows que modela la comunicación a partir de dependencias, tamaños y colocación de tareas, y con la práctica de HPC de comparar implementaciones contra communication lower bounds. En esta tesis el lower bound es **específico al workflow, archivos, placement y frontera de ubicaciones definidos**, no un bound universal ni un mínimo global sobre todos los placements.

La medida candidata de eficiencia se expresa como:

```math
eta_move(R | PL, EM) = M_req(R) / M_obs(R)
```

solo cuando `M_obs` esté respaldado por evidencia con cobertura suficiente y use exactamente los mismos archivos, ubicaciones y tamaños. Su interpretación es: **fracción del movimiento observado que estaba exigida por el dataflow para ese placement concreto**. No se usa para ordenar placements.

Mientras `M_obs` siga indeterminado, puede calcularse:

```math
eta_rec(R | PL, EM) = M_req(R) / M_rec(R)
```

como proxy reconstruido del execution model, sin llamarlo eficiencia observada final.

Consecuencia para el roadmap: la duda conceptual sobre `M_req` deja de bloquear P2. El bloqueo principal pasa a ser la **auditoría de observabilidad de `M_obs`**, empezando por una corrida `process` y una `pipeline` existentes.

Referencias de apoyo: Pietri y Sakellariou (2018), DOI `10.1145/3221269.3221298`; Çatalyürek, Kaya y Uçar (2011), DOI `10.1145/1996014.1996022`; Ballard et al. (2011), DOI `10.1137/090769156`; Tang et al. (2026), DOI `10.1109/IPDPS65963.2026.00076`.

Para futuras consultas, comenzar por `TESIS_RAG_INDEX.md`; para la formulación ejecutable, `TESIS_METRICA_FORMULACION_EJECUTABLE_20260925.md`; para el plan operativo, `TESIS_ROADMAP_EJECUTABLE_20260925.md`.


---

## Actualización de evidencia 2026-09-26 — `M_obs` pasa de indeterminado a observable condicionado en dos pilotos

La auditoría de dos corridas existentes aporta por primera vez evidencia de ejecución suficiente para distinguir reconstrucción de observación a nivel job.

Pilotos:

- process same-w1, S=50 MiB: HTCondor `2435.0`, worker1;
- pipeline BALANCED-LOCAL, S=50 MiB: `2445.0` worker1, `2448.0` worker1, `2451.0` worker2.

Todos los jobs científicos tuvieron un único intento y terminaron correctamente. `TransferInputStats` y `TransferOutputStats` proporcionan bytes realmente registrados para el sandbox completo. Los `.sub` enumeran su file-set y los `.meta` preservan los tamaños científicos. La reconciliación de transfer-in es exacta en bytes en los cuatro jobs; la de transfer-out separa 50 MiB científicos de unos pocos KiB auxiliares.

Se introduce coverage provisional:

```text
JOB_LEVEL_EXACT_RECONCILIATION
```

que significa: los bytes observados son agregados por job, pero el file-set, los tamaños, el número de intentos y los totales HTCondor permiten separar de manera trazable el payload científico sin residuo inexplicado.

Valores piloto bajo el boundary científico:

```text
process same-w1 S=50:
M_req = 100 MiB
M_obs = 100 MiB
eta_move = 1.0

pipeline balanced-local S=50:
M_req = 150 MiB
M_obs = 300 MiB
eta_move = 0.5
```

La fórmula no cambia. El siguiente trabajo ya no es demostrar que HTCondor expone algún total de transferencia, sino **formalizar la política de coverage y generalizar la reconciliación a la herramienta y a casos con retries, archivos faltantes o evidencia no exacta**.

## Evidencia nueva 2026-09-26 — observación reconciliada a nivel job

El bloqueo de observabilidad avanzó sustancialmente. En un trío controlado de pipeline con `S=10 MiB` y placements SAME, BALANCED-LOCAL y CROSS, HTCondor confirma workers observados, un único intento por tarea y bytes agregados de entrada/salida del sandbox. Pegasus conserva los manifiestos de `.sub` y tamaños de los archivos científicos. La fusión de estas fuentes permite declarar cobertura `JOB_LEVEL_RECONCILED`: no hay eventos nominales por archivo, pero sí observación del sandbox a nivel job con atribución exacta/no proporcional del payload científico.

Para estas tres corridas, `M_obs=60 MiB`; `M_req` toma 20, 30 y 40 MiB respectivamente y `eta_move` toma 0.3333, 0.5 y 0.6667. Gate 1B queda cerrable para el caso controlado, sujeto a congelar en P2 la política de coverage, retries y frontera científica.


## Actualización 2026-09-26 — P2 congelado y Fase 2 activa

Gate 1B se cerró para el piloto SAME/BALANCED/CROSS de 10 MiB con evidencia `JOB_LEVEL_RECONCILED`. Gate 1C queda cerrado con el contrato `TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md`.

La formulación vigente es:

```text
RequiredMovement(R) = M_req(R)
DeclaredMovement(R) = M_rec(R)
ObservedMovement(R) = M_obs(R)
Coverage(R) = movimientos científicos confirmados / declarados
DME(R) = RequiredMovement(R) / ObservedMovement(R), solo si Coverage(R)=1
```

Un archivo científico es un input externo, intermediate u output final del dataflow. Archivos de runtime, scripts, ejecutables, metadata, logs y stdout/stderr se excluyen del payload científico.

El camino crítico pasa a Fase 2: consolidar el Analyzer alrededor del modelo de datos y funciones congeladas en P2. El primer objetivo es construir una extracción trazable que reproduzca el piloto sin depender de reglas ad hoc.

---

# Actualización normativa 2026-09-30 — Gate R y Gate D cerrados

A partir del 30 de septiembre de 2026, el estado rector del proyecto es:

```text
Gate R — Requirements      CERRADO
Gate D — Design            CERRADO
Implementation             ACTIVA
Verification/Validation    BLOQUEADA hasta Gate I
```

Fuentes normativas nuevas:

1. `TESIS_REQUIREMENTS_SPEC_20260930.md` — semántica y requisitos congelados.
2. `TESIS_GATE_R_CIERRE_20260930.md` — decisión formal de cierre de requisitos.
3. `TESIS_AUDITORIA_EDGE_CASES_LITERATURA_20260930.md` — restricciones y edge cases.
4. `TESIS_DESIGN_SPEC_20260930.md` — diseño canónico.
5. `TESIS_TRACEABILITY_MATRIX_20260930.md` — 80/80 requisitos trazados.
6. `TESIS_GATE_D_REVIEW_20260930.md` — revisión y cierre del diseño.
7. `TESIS_IMPLEMENTATION_PLAN_20260930.md` — orden de implementación.

La notación vigente es:

```text
RequiredMovement = M_req
DeclaredMovement = M_rec
ObservedMovement = M_obs
Coverage = confirmed movements / declared movements
DME = RequiredMovement / ObservedMovement, cuando sus precondiciones son válidas
```

La evidencia `JOB_LEVEL_RECONCILED` se divide en dos modos de reconciliación de diseño:

```text
EXACT_BYTES
SUCCESSFUL_MANIFEST
```

Esta separación corrige la sobreafirmación de que todo output piloto tenía necesariamente reconciliación exacta de bytes auxiliares después de cleanup.

El siguiente trabajo técnico no es redefinir la métrica: es ejecutar I0–I14 del Implementation Plan sin lanzar campañas nuevas hasta Gate I.

---

# Actualización operativa 2026-09-30 20:30 — Implementation

Esta sección prevalece sobre cualquier descripción operativa anterior del Estado Maestro que haya quedado desactualizada por el cierre de Gate R/Gate D o por la implementación v1.

## Estado de gates

```text
Gate R — Requirements      CERRADO
Gate D — Design            CERRADO
Gate I — Implementation    ACTIVO
Gate V — Validation        BLOQUEADO hasta Gate I
```

## Estado de implementación

| Etapa | Estado |
| --- | --- |
| I0 baseline | CLOSED |
| I1 domain model + diagnostics | CLOSED |
| I2 source loaders/parsers | CLOSED |
| I3 identity/normalization | implementado; corrección I3B pendiente |
| I4A detector core | CLOSED |
| I4B execution-model evidence builder | CLOSED |
| I4C CondorIOStandardAdapter | CLOSED |
| I4 global | OPEN |
| I5-I14 | PENDING |

Suite actual: **101/101 PASS**. Analyzer histórico preservado con SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

## Correcciones normativas importantes

- El core no hardcodea `master -> worker -> master`; las direcciones dependen del execution-model adapter confirmado.
- `RequiredMovement` es file-centric y condicionado al placement observado.
- Un único physical path no basta para identificar un archivo: I3B debe exigir relación semántica inequívoca.
- Los compute jobs no se identifican por filename; I4B usa semántica Pegasus (`pegasus_job_class=1` + DAX id real no nulo).
- No se infiere `condorio` por default o por apariencia de la corrida. El adapter solo se selecciona con evidencia suficiente.
- I4 permanece abierto mientras no se demuestren de manera trazable `data_configuration`, `submit_host`, `htcondor_version`, `bypass_enabled`, `shared_filesystem` y la separación submit-host/workers.

## Fuentes rectoras actuales

1. `TESIS_REQUIREMENTS_SPEC_20260930.md`
2. `TESIS_DESIGN_SPEC_20260930.md`
3. `TESIS_TRACEABILITY_MATRIX_20260930.md`
4. `TESIS_IMPLEMENTATION_PLAN_20260930.md`
5. `TESIS_IMPLEMENTATION_LOG_20260930.md`
6. `TESIS_DECISION_LOG.md`
7. `TESIS_RAG_INDEX.md`

Código, tests y logs son evidencia de implementación; no redefinen por sí solos la semántica congelada.

---

# Actualización operativa 2026-09-30 — I3/I4 cerrados

Esta sección sustituye el estado operativo 20:30 anterior.

```text
Gate R  CLOSED
Gate D  CLOSED
Gate I  ACTIVE

I0 CLOSED
I1 CLOSED
I2 CLOSED
I3 CLOSED  -> ce6ec3f + 1ebf309
I4 CLOSED  -> 31f4244
I5 NEXT
I6-I14 PENDING
```

Verificación: **106/106 tests PASS**, smoke real I4 PASS en process y distribution, `CondorIOStandardAdapter` seleccionado sin razones de rechazo y SHA-256 legacy intacto `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

Evidencia I4 preservada: Pegasus 5.1.2, HTCondor 25.12.2, condorio, submit host `pegasus-master`, vanilla, HTCondor file transfer YES, output ON_EXIT, shared filesystem false, bypass false, sin plugin no soportado y sin clustering.

Siguiente bloque rector: **I5 Scientific Dataflow + I6 RequiredMovement + I7 DeclaredMovement**.

---

# Checkpoint operativo — 2026-09-30 17:13

Esta sección prevalece sobre estados operativos anteriores.

- Gate R: CERRADO.
- Gate D: CERRADO.
- I0–I4: CERRADOS.
- I3B fix: commit `1ebf309`.
- I4 complete: commit `31f4244`.
- Full suite: `106/106 PASS`.
- Legacy analyzer SHA-256 intacto.
- Fase activa: **I5 Scientific Dataflow**.
- Siguiente bloque: I5 → I6 → I7.

---

# Checkpoint operativo I5–I7 — 2026-09-30 17:35

I0–I7 están cerrados. I5 se congeló en `2916cd2`; I6/I7 en `0078892`. La fase activa pasa a I8 HTCondor evidence, seguida de I9 Reconciliation e I10 Metrics. DeclaredMovement sigue siendo declaración hasta que la reconciliación confirme ocurrencias; no se reinterpreta como ObservedMovement.

---

# Checkpoint maestro — I10 cerrado

Estado vigente:

- Gate R: CERRADO.
- Gate D: CERRADO.
- I0-I10: CERRADOS.
- I11: ACTIVO.
- I12/I13: PENDIENTES.
- Gate I: ABIERTO.
- suite actual: **134/134 PASS**.
- HEAD al cierre I10: `9d4d9d2`.
- analyzer histórico intacto.

La métrica central ya existe end-to-end a nivel de componentes: dataflow, required movement, declared movement, evidence, reconciliation y metrics. Falta reporting/orquestación y validación de regresión/integración para cerrar Gate I.

---

# Checkpoint maestro — cierre I11

- Gate R: CERRADO.
- Gate D: CERRADO.
- I0-I11: CERRADOS.
- I11 commit: `f6af663`.
- Full suite: `138/138 PASS`.
- Legacy analyzer SHA-256 intacto.
- Fase activa: **I12 regression fixtures auditados**.
- Luego: I13 integration runs preservados → Gate I.

La cadena central ya está implementada: Scientific Dataflow → RequiredMovement → DeclaredMovement → TransferEvidence → Reconciliation → Coverage/ObservedMovement/DME → Reporting.

---

## Checkpoint operativo — cierre I12 / inicio I13

Fecha: 30 de septiembre de 2026.

Estado rector de implementación:

```text
I0-I11  CLOSED
I12      CLOSED — regression suite auditada
I13      ACTIVE — integration sobre runs reales preservados
Gate I   PENDING
I14      PENDING — solo después de Gate I
```

Evidencia de cierre I12:

- orquestador end-to-end v1 cerrado en commit `55712ed`;
- smoke real `process-same-w1-20260917-232331` reproducido con `RequiredMovement=104857600 B`, `DeclaredMovement=104857600 B`, `ObservedMovement=104857600 B`, `Coverage=1.0`, `DME=1.0`, `status=VALID`;
- ambas direcciones del process reconciliadas como `JOB_LEVEL_RECONCILED` con modo `SUCCESSFUL_MANIFEST`;
- fixtures auditados de regresión materializados en `fixtures/audited/regression_oracles.json`;
- regresiones positivas: process 50 MiB y pipeline 10 MiB SAME/BALANCED/CROSS;
- regresión negativa: retry ambiguo degrada a evidencia insuficiente y no produce `ObservedMovement`/`DME`;
- I12 commit `b5880d6` — `test: add audited v1 regression oracles`;
- suite completa al cierre: **141/141 PASS**;
- worktree limpio;
- analyzer histórico v0.5.1 preservado con SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

Siguiente objetivo: I13 debe analizar automáticamente runs reales preservados, sin ejecutar workflows nuevos. Gate I solo podrá cerrarse cuando las integration runs auditadas pasen, los outputs sigan siendo trazables y el CLI/README reflejen la semántica v1.

---

<!-- SYNC_20260930_I13_GATEI -->
## Estado maestro sincronizado — 2026-09-30

```text
Gate R  ✅ CLOSED
Gate D  ✅ CLOSED
I0–I13 ✅ CLOSED
Gate I  🟡 ACTIVE — falta cierre documental/CLI + suite final
I14     ⛔ BLOCKED
Gate V  ⛔ BLOCKED
```

Última evidencia técnica:

- Analyzer v1 end-to-end: `55712ed`.
- I12 regression: `b5880d6`, suite 141/141 PASS.
- I13 integration: `77c6ff6`, suite 142/142 PASS.
- cinco histories reales preservados bajo `fixtures/audited/history/`.
- no hay hardcodes de SAME/BALANCED/CROSS ni de patrones experimentales en el núcleo v1.
- `schema_version = 1`.
- legacy SHA intacto: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

**No se ejecutan campañas nuevas ni I14 hasta cerrar Gate I.**


---

## Checkpoint de continuidad — 2026-10-03, Gate I

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Las ramas se publicaron en GitHub el 4/10/2026 desde Windows por HTTPS; PR pendiente de creación/revisión.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
