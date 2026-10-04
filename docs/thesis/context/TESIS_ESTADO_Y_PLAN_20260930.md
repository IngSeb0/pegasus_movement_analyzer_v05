# TESIS — Estado actual y siguiente ruta

**Fecha:** 30 de septiembre de 2026

## Dónde estamos

La tesis sigue teniendo el mismo objetivo oficial: **definir, implementar y validar una herramienta que calcule una métrica de eficiencia del movimiento de datos en ejecuciones Pegasus/HTCondor**.

### Cerrado conceptualmente

- separación `Workflow -> Placement -> Execution -> Tracing -> Measurement`;
- `RequiredMovement`: referencia mínima condicionada al placement observado;
- `DeclaredMovement`: movimiento científico declarado/reconstruido por los jobs;
- `ObservedMovement`: movimiento científico confirmado con evidencia;
- `Coverage`: confirmados / declarados;
- `DME = RequiredMovement / ObservedMovement`, solo con `Coverage = 1`;
- DME **no** rankea placements;
- bytes medidos = payload científico, no tráfico packet-level;
- piloto pipeline 10 MiB SAME/BALANCED/CROSS auditado con evidencia `JOB_LEVEL_RECONCILED`.

### Evidencia piloto

```text
              Required   Observed   Coverage   DME
SAME            20 MiB     60 MiB      1      0.3333
BALANCED        30 MiB     60 MiB      1      0.5000
CROSS           40 MiB     60 MiB      1      0.6667
```

También existe evidencia process 50 MiB y pipeline BALANCED 50 MiB auditada.

## Qué estaba mal en nuestro flujo

Avanzamos en código y experimentos antes de congelar todos los requisitos y edge cases. Esto produjo cambios de nombres, dudas sobre `M_obs`, `coverage`, retries y execution model.

## Flujo obligatorio desde ahora

```text
1. REQUIREMENTS            ✅ Gate R cerrado
2. DESIGN COMPLETO         ✅ Gate D cerrado
3. IMPLEMENTATION          <- AHORA
4. VERIFICATION/VALIDATION ⏳
5. REDACCIÓN FINAL/DEFENSA ⏳
```

## Gates cerrados

### Gate R — CERRADO

Se congelaron scope v1, evidencia, retries/fallos, payload semantics, casos no soportados, estados y outputs. Ver `TESIS_GATE_R_CIERRE_20260930.md`.

### Gate D — CERRADO

Se completaron arquitectura, modelo de datos, adapters, algoritmos, reconciliación, estados, CLI/outputs, runner, tests y trazabilidad 80/80. Ver `TESIS_DESIGN_SPEC_20260930.md`, `TESIS_TRACEABILITY_MATRIX_20260930.md` y `TESIS_GATE_D_REVIEW_20260930.md`.

## Fase activa — Implementation

Orden: I0 baseline -> I1 modelo -> I2 fuentes -> I3 identidad -> I4 execution model -> I5 dataflow -> I6 RequiredMovement -> I7 DeclaredMovement -> I8 evidencia -> I9 reconciliación -> I10 métricas -> I11 reporting -> I12 regresión -> I13 integración -> I14 runner.

### Estado de implementación al 2026-09-30 20:30

| Bloque | Estado | Evidencia / nota |
| --- | --- | --- |
| I0 Baseline | CERRADO | `main` congelado en `8269f0b`; analyzer histórico preservado |
| I1 Domain model + diagnostics | CERRADO | commit `869c47b` |
| I2 Source loaders/parsers | CERRADO | commit `1675ee9` |
| I3 Identity / normalization | CERRADO | base `ce6ec3f` + corrección I3B `1ebf309`; un path físico solo ya no basta sin relación semántica inequívoca |
| I4 Execution model detection | CERRADO | commit `31f4244`; detector + evidence builder + `CondorIOStandardAdapter` + extracción desde artefactos reales |
| I5 Scientific dataflow | SIGUIENTE | construir archivos científicos, producer/consumers/roles, tamaños y ambigüedades |
| I6 RequiredMovement | PENDIENTE | algoritmo file-centric congelado en Design §11 |
| I7 DeclaredMovement | PENDIENTE | manifiestos completos + movimientos científicos declarados |
| I8–I14 | PENDIENTE | después del bloque I5–I7 |

Suite actual: **106/106 tests PASS**. Smoke real I4: PASS para `process-same-w1-20260917-222429` y `distribution-same-w1-20260917-181537`; ambos seleccionan `CondorIOStandardAdapter`. Checksum histórico de `pegasus_movement/analyzer.py`: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`. Worktree limpio tras commits `1ebf309` y `31f4244`.

No se ejecutan campañas nuevas hasta Gate I.

## Documento y presentación

La tesis formal y la presentación deben derivarse del mismo Requirements Spec + Design Spec para evitar volver a tener definiciones distintas entre código, LaTeX y slides.

---

## Actualización operativa — 2026-09-30 17:13

Esta sección **prevalece sobre el estado de implementación anterior** de este documento.

```text
I0  Baseline                         ✅ CLOSED
I1  Domain model + diagnostics       ✅ CLOSED
I2  Source loaders/parsers           ✅ CLOSED
I3  Identity / normalization         ✅ CLOSED
I4  Execution model detection        ✅ CLOSED
I5  Scientific dataflow              ← AHORA
I6  RequiredMovement                 ⏳
I7  DeclaredMovement                 ⏳
I8–I14                               ⏳
```

### Cierre I3

Se corrigió I3B para que un único `physical_path` **no** sea identidad suficiente por sí solo. El fallback físico solo puede resolver identidad cuando existe además una relación semántica inequívoca dentro del run.

Commit: `1ebf309` — `fix: require semantic evidence for physical file identity`.

### Cierre I4

El detector de execution model queda cerrado para el scope v1. En runs preservados se recupera evidencia trazable de Pegasus `5.1.2`, HTCondor `25.12.2`, `data_configuration=condorio`, `submit_host=pegasus-master`, `universe=vanilla`, `should_transfer_files=YES`, `when_to_transfer_output=ON_EXIT`, `sharedFileSystem=false`, bypass deshabilitado, sin plugin/protocolo no soportado detectado y `cluster_size=1`.

El smoke real sobre `process-same-w1` y `distribution-same-w1` selecciona `CondorIOStandardAdapter` con `supported=True`.

Commit: `31f4244` — `feat: complete v1 execution model detection`.

### Calidad actual

Suite completa: **106/106 PASS**.

Checksum histórico preservado:

```text
d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2
```

Siguiente frente: **I5 Scientific Dataflow**, seguido por I6 e I7 en un mismo bloque de implementación.

---

## Checkpoint I5–I7 — 2026-09-30 17:35

Esta sección prevalece sobre checkpoints operativos anteriores.

```text
I0 ✅ CLOSED
I1 ✅ CLOSED
I2 ✅ CLOSED
I3 ✅ CLOSED
I4 ✅ CLOSED
I5 ✅ CLOSED — 2916cd2
I6 ✅ CLOSED — 0078892
I7 ✅ CLOSED — 0078892
I8 ← ACTIVO
I9–I14 ⏳
```

I5 materializa el Scientific Dataflow v1 (`ScientificFile`, producer/consumers/roles/origin/final destinations) sin usar patrón o placement como ramas del algoritmo. I6 implementa `RequiredMovement` file-centric condicionado al placement observado. I7 construye manifiestos científicos+auxiliares y `DeclaredMovement`; los movimientos declarados permanecen sin confirmar hasta I8–I9.

Commits:
- `2916cd2 feat: build v1 scientific dataflow`
- `0078892 feat: add required and declared movement engines`

El analyzer histórico conserva SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

---

## Checkpoint de implementación — cierre I8-I10

Esta sección prevalece sobre checkpoints operativos anteriores.

```text
I0  ✅ CLOSED
I1  ✅ CLOSED
I2  ✅ CLOSED
I3  ✅ CLOSED
I4  ✅ CLOSED
I5  ✅ CLOSED
I6  ✅ CLOSED
I7  ✅ CLOSED
I8  ✅ CLOSED
I9  ✅ CLOSED
I10 ✅ CLOSED
I11 ← ACTIVO
I12-I14 ⏳
```

Commits relevantes:

- I8 transfer evidence: `821c70c`; fix de import circular `e05c4b4`.
- ajuste semántico de manifiestos: `2f9331a`.
- I9 reconciliation: `9e27fbf`.
- I10 metrics: `9d4d9d2`.

Validación actual: **134/134 tests PASS**, worktree limpio y SHA-256 del analyzer histórico intacto: `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

La cadena central ya está implementada: `RequiredMovement -> DeclaredMovement -> TransferEvidence -> Reconciliation -> Coverage/ObservedMovement/DME`.

---

## Checkpoint operativo — cierre I11

Este checkpoint prevalece sobre estados operativos anteriores del mismo día.

```text
I0-I10  CLOSED
I11      CLOSED — commit f6af663
I12      ACTIVE — regression fixtures auditados
I13      PENDING — integration sobre runs preservados
I14      PENDING — experiment runner / validación nueva, después de Gate I
```

Evidencia de cierre I11:

- `analysis.json`, TSV canónicos y `REPORT.txt` implementados;
- exit codes implementados según Design;
- tests I11: 4/4 PASS;
- full suite: **138/138 PASS**;
- commit `f6af663` — `feat: add canonical v1 analysis reporting`;
- analyzer histórico conserva SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

Siguiente frente: I12 regression fixtures con oráculos auditados, seguido por I13 integration runs.

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
