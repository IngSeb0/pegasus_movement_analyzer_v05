# TESIS — Implementation Log

**Fecha de corte:** 30 de septiembre de 2026, 20:30
**Branch:** `feat/analyzer-v1`
**Estado global:** Gate I abierto; implementación en curso.

## 1. Commits congelados

| Bloque | Commit | Estado |
| --- | --- | --- |
| I0 baseline | `8269f0b222805efd3191a41f94d4ee0f6cf03856` | CLOSED |
| I1 domain model + diagnostics | `869c47b` | CLOSED |
| I2 source loaders/parsers | `1675ee9` | CLOSED |
| I3 identity/location normalization | `ce6ec3f` | implementado; corrección I3B pendiente |
| I4 | sin commit | I4A/I4B/I4C cerrados; I4 global abierto |

## 2. Estado por etapa

### I0 — Baseline

Cerrado. `main` permanece como baseline histórico. El analyzer v0.5.1 no se modifica durante la migración.

### I1 — Domain model + diagnostics

Cerrado. Se implementaron las entidades del Design Spec y validaciones locales. `Diagnostic` conserva status/reason/context/provenance; `MetricStatus` distingue calculado, N/A, indeterminado e inválido.

### I2 — Source loaders/parsers

Cerrado. Existen loaders read-only para run sources, parser `.sub`, parser `.meta/cache.meta` y parser raw de history/ClassAds. Deuda conocida para I8: revisar preservación literal de nested ClassAds multiline antes de normalizar estadísticas HTCondor.

### I3 — Identity / normalization

Implementado en commit `ce6ec3f`, con una corrección semántica pendiente: el fallback por un único physical path no debe producir identidad por sí solo; el Design Spec exige `physical path + unambiguous semantic relation within run`. Esta deuda se corrige antes de continuar a I5.

### I4A — Execution Model Detector Core

Cerrado. El detector es fail-closed. Soporta el perfil v1 solo con evidencia explícita suficiente; sharedfs, bypass, plugins/protocolos no soportados y clustered jobs se rechazan. La ausencia de un atributo necesario para distinguir soporte también impide seleccionar adapter.

### I4B — Evidence Builder

Cerrado. El builder extrae evidencia desde submits de compute jobs sin mezclar staging/cleanup/registration/control.

Corrección importante descubierta en smoke real: `pegasus_wf_dax_job_id` no basta, porque jobs auxiliares pueden declarar `"null"`. La clasificación final exige semántica Pegasus: `+pegasus_job_class = 1` y DAX id real no nulo.

Smoke real:

- `process-same-w1-20260917-222429`: 10 submits totales, 1 compute job;
- `distribution-same-w1-20260917-181537`: 16 submits totales, 5 compute jobs;
- ambos: Pegasus 5.1.2, universe vanilla, HTCondor transfer YES, output ON_EXIT, cluster size 1, sin conflicto.

### I4C — CondorIOStandardAdapter

Cerrado. `CondorIOStandardAdapter.supports()` no completa defaults; delega la decisión al detector canónico y solo acepta un `ExecutionModelProfile` explícitamente soportado.

### I4 global — OPEN

Los runs preservados inspeccionados todavía no demuestran automáticamente todos estos campos:

```text
htcondor_version
data_configuration
submit_host
bypass_enabled
shared_filesystem
```

También debe verificarse la condición de scope `submit host separado de workers científicos` cuando se integren locations. Mientras falte esa evidencia, `supported=False`, `adapter_name=None` y el diagnóstico permanece fail-closed.

## 3. Tests y regresión

Estado actual:

```text
CondorIO adapter tests: 7/7 PASS
I4 tests:              33/33 PASS
Full suite:           101/101 PASS
```

Checksum histórico preservado:

```text
d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2  pegasus_movement/analyzer.py
```

## 4. Worktree I4 al corte

Pendiente de commit:

```text
M  pegasus_movement/diagnostics.py
?? pegasus_movement/condorio_adapter.py
?? pegasus_movement/execution_model.py
?? tests/unit/test_condorio_adapter.py
?? tests/unit/test_execution_model.py
```

No hacer commit hasta corregir I3B y cerrar la evidencia restante de I4.

## 5. Próximo camino crítico

1. corregir I3B y añadir prueba negativa para path físico sin relación semántica;
2. localizar/extraer evidencia real de los campos restantes de I4 o marcar explícitamente qué no puede demostrarse desde un run preservado;
3. verificar submit-host vs workers;
4. cerrar y commitear I4;
5. implementar I5 Scientific Dataflow;
6. continuar I6-I11;
7. cerrar I12/I13 y Gate I;
8. solo entonces ejecutar I14/validación experimental nueva.

## 6. Regla de gobernanza

Este log registra estado de implementación y evidencia de pruebas. **No reemplaza** Requirements ni Design. Si el código o un test contradicen `TESIS_REQUIREMENTS_SPEC_20260930.md` o `TESIS_DESIGN_SPEC_20260930.md`, se corrige la implementación o se abre un change request explícito.

## 7. Cierre I3B + I4

**Fecha:** 2026-09-30

- I3B fix commit: `1ebf309` — physical path requiere evidencia semántica inequívoca.
- I4 commit: `31f4244` — execution model detection completo.
- Suite completa: **106/106 PASS**.
- Smoke real I4: PASS en process y distribution preservados.
- Adapter seleccionado: `CondorIOStandardAdapter`.
- Perfil real confirmado: Pegasus 5.1.2, HTCondor 25.12.2, condorio, `pegasus-master`, vanilla, transfer YES, ON_EXIT, shared filesystem false, bypass false, sin plugins, sin clustering.
- Legacy analyzer SHA-256 intacto: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.
- Worktree limpio al finalizar commits.

**Estado:** I3 CLOSED, I4 CLOSED. Siguiente bloque: I5–I7.

---

## Checkpoint — 2026-09-30 17:13

Esta sección **prevalece sobre el corte 20:30**.

### Nuevos commits

| Bloque | Commit | Resultado |
|---|---|---|
| I3B fix | `1ebf309` | physical path requiere evidencia semántica inequívoca |
| I4 completo | `31f4244` | execution-model detection v1 cerrado |

### Estado actualizado

```text
I0 CLOSED
I1 CLOSED
I2 CLOSED
I3 CLOSED
I4 CLOSED
I5 ACTIVE
I6-I14 PENDING
```

### Validación

- targeted I3/I4: PASS;
- real I4 smoke: PASS en process y distribution;
- `CondorIOStandardAdapter`: seleccionado;
- full suite: **106/106 PASS**;
- legacy SHA-256: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

### Siguiente bloque

Implementar I5 + I6 + I7 con una sola suite conjunta y smoke sobre runs preservados.

---

## Checkpoint I5–I7 — 2026-09-30 17:35

### Commits

- I5: `2916cd2 feat: build v1 scientific dataflow`
- I6/I7: `0078892 feat: add required and declared movement engines`

### Estado

```text
I0 CLOSED
I1 CLOSED
I2 CLOSED
I3 CLOSED
I4 CLOSED
I5 CLOSED
I6 CLOSED
I7 CLOSED
I8 ACTIVE
```

Worktree reportado limpio al checkpoint posterior al commit `0078892`. Analyzer histórico intacto.

---

## Checkpoint I8-I10

### Commits

```text
821c70c feat: normalize HTCondor transfer evidence
e05c4b4 fix: avoid transfer evidence normalization import cycle
2f9331a fix: separate manifest and size completeness
9e27fbf feat: reconcile declared movement with transfer evidence
9d4d9d2 feat: calculate coverage observed movement and dme
```

### Resultados

- I8 normaliza stats HTCondor preservando ClassAds crudos y protocolos.
- retries no separables permanecen no confirmados.
- I9 implementa `EXACT_BYTES` y `SUCCESSFUL_MANIFEST` sin imputación proporcional.
- I10 implementa Coverage, ByteCoverage, ObservedMovement, DME y casos cero/inconsistentes.
- suite completa: **134/134 PASS**.
- worktree limpio.
- analyzer v0.5.1 preservado por SHA-256.

Estado: **I0-I10 CLOSED; I11 ACTIVE**.

---

## Checkpoint — I11 cerrado

### Commits nuevos

| Bloque | Commit | Resultado |
|---|---|---|
| I8 | `821c70c` | TransferEvidence HTCondor normalizado |
| I8 fix | `e05c4b4` | elimina import circular |
| I7 fix | `2f9331a` | separa manifest completeness de size completeness |
| I9 | `9e27fbf` | reconciliation `EXACT_BYTES` / `SUCCESSFUL_MANIFEST` |
| I10 | `9d4d9d2` | Coverage, ObservedMovement, DME |
| I11 | `f6af663` | JSON/TSV/REPORT + exit codes |

### Calidad

- I11 tests: 4/4 PASS;
- suite completa: **138/138 PASS**;
- worktree limpio al corte;
- legacy analyzer SHA-256 intacto.

### Estado

```text
I0-I11 CLOSED
I12 ACTIVE
I13 PENDING
I14 PENDING
```

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

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Las ramas se publicaron en GitHub el 4/10/2026 desde Windows por HTTPS; PR pendiente de creación/revisión.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
