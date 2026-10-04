# TESIS — Implementation Plan

**Fecha:** 30 de septiembre de 2026  
**Prerequisitos:** Gate R y Gate D cerrados  
**Estado:** implementación activa — I0/I1/I2/I3/I4 cerrados; siguiente bloque I5–I7

## Regla

La implementación no redefine requisitos ni diseño. Cuando aparece una duda conceptual se detiene el código y se abre un change request; no se “resuelve” cambiando una fórmula.

## Orden obligatorio

### I0 — Baseline

- crear branch de implementación;
- registrar commit base;
- correr tests v0.5.1 sin cambios;
- guardar salida;
- no modificar resultados históricos.

**Criterio:** baseline verde.

### I1 — Domain model + diagnostics

Implementar:

```text
ProvenanceRef
Location
TaskExecution
ScientificFile
ManifestFile
JobTransferManifest
TransferEvidence
MovementVerification
RequiredMovementRecord
DeclaredMovementRecord
ExecutionModelProfile
MetricResult
RunExecution
Diagnostic + enums
```

**Tests:** construcción, validaciones locales, roles múltiples, zero bytes, estados.

### I2 — Source loaders

Implementar lectura read-only de:

```text
Pegasus run
.sub
.meta/cache.meta
DAG/metadata relevante
history.long/ClassAds
job event logs cuando estén disponibles
```

**Tests:** fixtures mínimos de parsing; no métricas todavía.

### I3 — Identity / normalization

- task identity;
- job identity;
- LFN/path/remap;
- locations;
- provenance.

**Tests:** aliases, duplicate basename, ambiguous IDs.

### I4 — Execution model detection

Implementar `ExecutionModelProfile` + `CondorIOStandardAdapter.supports()`.

**Tests:** condorio válido, sharedfs, bypass, plugin, clustered job.

### I5 — Scientific dataflow

- identificar tareas científicas;
- construir archivos, producer/consumers/roles;
- resolver tamaños;
- detectar multiple producers y ambigüedades.

### I6 — RequiredMovement

Implementar exactamente el algoritmo file-centric de Design Spec §11.

**Primero tests unitarios; luego oráculos manuales.**

### I7 — Job manifests + DeclaredMovement

Construir manifiesto completo científico+auxiliar por job/dirección y luego movimientos científicos declarados.

### I8 — HTCondor evidence

Normalizar ClassAds de 25.12.2 conservando raw stats.

No usar `TransferInputSizeMB` como observación.

### I9 — Reconciliation

Implementar:

```text
EXACT_BYTES
SUCCESSFUL_MANIFEST
FILE_LEVEL_CONFIRMED (interfaz; usar si existe evidencia)
INSUFFICIENT
```

### I10 — Metrics

Coverage, ByteCoverage, ObservedMovement, validación de invariantes y DME.

### I11 — Reporting

`analysis.json`, TSVs, REPORT.txt y exit codes.

### I12 — Regression suite

Materializar fixtures auditados y congelar sus evidence modes.

### I13 — Integration suite

Analizar runs reales preservados sin ejecutar nuevos workflows.

### I14 — Experiment runner

Solo después de que Analyzer pase I12/I13.


## Seguimiento de implementación — 2026-09-30 20:30

| Etapa | Estado | Resultado verificable |
| --- | --- | --- |
| I0 | CERRADO | baseline `8269f0b`; v0.5.1 preservado |
| I1 | CERRADO | modelo de dominio + diagnostics; commit `869c47b` |
| I2 | CERRADO | loaders/parsers `.sub`, `.meta`, history y fuentes opcionales; commit `1675ee9` |
| I3 | CERRADO | `ce6ec3f` + fix `1ebf309`; fallback por path físico exige evidencia semántica inequívoca |
| I4 | CERRADO | commit `31f4244`; detector, evidence builder, adapter y extracción de artefactos reales completados |
| I5 | SIGUIENTE | Scientific Dataflow |
| I6 | PENDIENTE | RequiredMovement |
| I7 | PENDIENTE | Job manifests + DeclaredMovement |
| I8–I14 | PENDIENTE | siguen después del bloque I5–I7 |

### Evidencia de calidad actual

- suite completa: **106/106 PASS**;
- smoke real I4: **PASS** en process y distribution preservados;
- evidencia real recuperada: `data_configuration=condorio`, `submit_host=pegasus-master`, `htcondor_version=25.12.2`, `shared_filesystem=false`, `bypass_enabled=false`, `universe=vanilla`, `should_transfer_files=YES`, `when_to_transfer_output=ON_EXIT`, sin plugins ni clustering;
- I3B commit: `1ebf309`;
- I4 commit: `31f4244`;
- checksum legacy intacto: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`;
- worktree limpio tras ambos commits.

### Camino crítico inmediato

1. I5: construir Scientific Dataflow desde semántica Pegasus, sin hardcode de patrón/filename;
2. I6: implementar RequiredMovement exactamente según Design §11;
3. I7: construir manifest completo y DeclaredMovement;
4. ejecutar una suite conjunta y smoke sobre runs preservados;
5. continuar con I8–I11.

## Gate I

Gate I se cierra cuando:

- unit suite completa pasa;
- regression fixtures positivos y negativos pasan;
- integration runs auditados pasan;
- ningún requisito está implementado mediante hardcode de patrón/placement;
- outputs son trazables;
- README/CLI describen la semántica nueva;
- v0.5.1 queda preservado o migrado de forma explícita.

Después de Gate I comienza validación experimental nueva.

---

## Checkpoint de implementación — 2026-09-30 17:13

Esta sección **sustituye el checkpoint 20:30 anterior**.

| Etapa | Estado | Evidencia |
|---|---|---|
| I0 | CLOSED | baseline `8269f0b` |
| I1 | CLOSED | `869c47b` |
| I2 | CLOSED | `1675ee9` |
| I3 | CLOSED | base `ce6ec3f` + fix I3B `1ebf309` |
| I4 | CLOSED | `31f4244`; smoke real soportado |
| I5 | ACTIVA | Scientific Dataflow |
| I6 | PENDIENTE | RequiredMovement |
| I7 | PENDIENTE | manifests + DeclaredMovement |
| I8–I14 | PENDIENTE | según plan rector |

### Evidencia de cierre I4

Los runs `process-same-w1-20260917-222429` y `distribution-same-w1-20260917-181537` reconstruyen el execution model v1 y seleccionan `CondorIOStandardAdapter`. La suite completa queda en **106/106 PASS** y el analyzer v0.5.1 permanece byte-a-byte intacto.

### Camino crítico actualizado

```text
I5 Scientific Dataflow
        ↓
I6 RequiredMovement
        ↓
I7 DeclaredMovement
        ↓
I8 HTCondor evidence
        ↓
I9 Reconciliation
        ↓
I10 Metrics
        ↓
I11 Reporting
        ↓
I12/I13 regression + integration
        ↓
Gate I
```

---

## Checkpoint I5–I7 — 2026-09-30 17:35

| Etapa | Estado | Commit |
|---|---|---|
| I5 Scientific Dataflow | CLOSED | `2916cd2` |
| I6 RequiredMovement | CLOSED | `0078892` |
| I7 DeclaredMovement | CLOSED | `0078892` |
| I8 HTCondor evidence | ACTIVE | — |
| I9 Reconciliation | PENDING | — |
| I10 Metrics | PENDING | — |
| I11 Reporting | PENDING | — |

Siguiente bloque: I8 + I9 + I10. No repetir I5–I7 salvo regresión posterior.

---

## Checkpoint actualizado — I8-I10 cerrados

| Etapa | Estado | Commit / evidencia |
|---|---|---|
| I8 HTCondor evidence | CLOSED | `821c70c` + fix `e05c4b4` |
| I9 Reconciliation | CLOSED | `9e27fbf` |
| I10 Metrics | CLOSED | `9d4d9d2` |
| I11 Reporting | ACTIVE | siguiente bloque |
| I12/I13 | PENDING | regression + integration |
| I14 | PENDING | solo después de Gate I |

Suite completa al cierre: **134/134 PASS**.

Camino crítico restante: `I11 -> I12/I13 -> Gate I -> I14/validación experimental`.

---

## Checkpoint — I11 cerrado

| Etapa | Estado | Evidencia |
|---|---|---|
| I8 | CLOSED | `821c70c` + fix `e05c4b4` |
| I9 | CLOSED | `9e27fbf` |
| I10 | CLOSED | `9d4d9d2` |
| I11 | CLOSED | `f6af663`; reporting canónico |
| I12 | ACTIVE | regression fixtures auditados |
| I13 | PENDING | integration runs preservados |
| I14 | PENDING | solo después de Gate I |

Suite completa al cierre I11: **138/138 PASS**.

Desde este punto la fórmula y las capas centrales del Analyzer no deben alterarse salvo defecto demostrado por I12/I13 o change request explícito.

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


---

## Checkpoint de continuidad — 2026-10-03, Gate I

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit local `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Publicación remota/PR pendiente por autenticación GitHub desde la VM.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
