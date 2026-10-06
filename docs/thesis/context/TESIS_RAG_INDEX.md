# TESIS — Índice de contexto y recuperación

**Actualizado:** 26 de septiembre de 2026  
**Uso:** punto de entrada para recuperar hechos, decisiones, resultados y preguntas abiertas de esta tesis.


## 0. P2 congelado — fuente operativa principal

Para definición de la métrica, casos límite, Coverage, modelo de datos y funciones del Analyzer, la fuente operativa principal es:

`TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md`

Nomenclatura vigente:

```text
RequiredMovement = M_req
DeclaredMovement = M_rec
ObservedMovement = M_obs
Coverage = confirmados / declarados
DME = RequiredMovement / ObservedMovement, solo con Coverage=1
```

`eta_move` queda como notación histórica/deprecada.

## 1. Jerarquía de fuentes

| Prioridad | Fuente | Qué determina |
| --- | --- | --- |
| 1 | Propuesta aprobada `ppg_ls.contreras_202620 (2)(1).pdf` | Objetivo, problema, alcance, patrones, cronograma y criterios de validación. |
| 1A | `TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md` | Contrato operativo congelado de la métrica y del Analyzer; prevalece para nomenclatura y reglas de implementación. |
| 2 | `TESIS_ESTADO_MAESTRO.md` | Estado interpretativo vigente. |
| 3 | `TESIS_METRICA_FORMULACION_EJECUTABLE_20260925.md` | Formulación ejecutable actual de `M_req`, `M_rec`, `M_obs` y la métrica condicionada al placement. |
| 4 | `TESIS_DECISION_LOG.md` | Historial de decisiones y revisiones. |
| 5 | `TESIS_EXPERIMENT_LOG.md` + `TESIS_VALIDATION_PLAN.md` | Evidencia experimental, oráculos, PASS y alcance de las campañas. |
| 6 | `TESIS_AUDITORIA_EVIDENCIA_MOVIMIENTO_20260925.md` | Estado de observabilidad de transferencias y plan de auditoría. |
| 7 | `TESIS_ROADMAP_EJECUTABLE_20260925.md` | Secuencia operativa actual con gates y próximo comando. |
| 8 | `Tesis_Contexto_Problema_Literatura_20260925.md` | Fundamentación bibliográfica y delimitación del problema. |
| 9 | `TESIS_FORMULACION_PRESENTACION_ACADEMICA_20260925.md` | Guion de presentación. |
| 10 | Materiales históricos | Solo para trazabilidad; no desplazan fuentes superiores. |

## 2. Problema y objetivo

**Problema:** definir, calcular y validar una medida trazable de eficiencia del movimiento de datos científicos en ejecuciones Pegasus/HTCondor, integrando evidencia distribuida entre workflow, plan y registros de ejecución.

**Objetivo:** diseñar, implementar y validar una herramienta que calcule una métrica de eficiencia del movimiento de datos y evaluar su comportamiento con process, pipeline, data aggregation, data distribution y data redistribution.

## 3. Interpretación vigente de las cantidades

### `M_req`

`M_req` se conserva y su interpretación conceptual queda cerrada.

Es el **lower bound lógico de movimiento de payload científico condicionado al placement observado**, es decir, la demanda mínima de comunicación entre ubicaciones inducida por el dataflow, suponiendo:

- reutilización local;
- comunicación directa entre workers;
- origen externo para inputs;
- destino final explícito para outputs.

El master sigue siendo origen/destino cuando corresponde, pero no se fuerza como tránsito de cada dato intermedio.

`M_req` no minimiza sobre placements y no modela el staging `condorio`. La formulación es metodológicamente consistente con modelos de communication cost por dependencias/placement y con el uso de communication lower bounds en HPC; el bound concreto es propio de esta tesis. Referencias clave: Pietri y Sakellariou (2018), Çatalyürek et al. (2011), Ballard et al. (2011) y Tang et al. (2026).

### `M_rec`

`M_rec` es el volumen de archivos científicos reconstruido bajo el contrato de staging del execution model estudiado.

Las salidas históricas v0.5.1 rotuladas `M_obs` se reinterpretan como `M_rec`.

### `M_obs`

`M_obs` queda reservado para movimiento científico confirmado por evidencia suficiente de la corrida, incluyendo granularidad y cobertura declaradas.

Si no hay cobertura suficiente, `M_obs` queda indeterminado.

## 4. Métrica de trabajo recomendada

Cuando exista `M_obs` con cobertura suficiente:

```math
η_move(R | PL, EM) = M_req(R) / M_obs(R)
```

La interpretación es **condicionada al placement**:

> mide qué parte del movimiento observado era requerida por el dataflow para esa distribución concreta.

No usar `η_move` para ordenar placements.

Mientras `M_obs` no esté disponible:

```math
η_rec(R | PL, EM) = M_req(R) / M_rec(R)
```

es únicamente un proxy reconstruido.

Para evaluar:

- localidad/demanda del placement -> `M_req`;
- volumen materializado -> `M_obs` o `M_rec`;
- amplificación del mecanismo respecto de esa demanda -> `η_move` / recíproco.

## 5. Evidencia ya cerrada

- BALANCED-LOCAL: 5/5 PASS;
- repetibilidad: 39/39 PASS;
- tamaño: 45/45 PASS para 1, 10 y 50 MiB.

Estas campañas validan `M_req` y `M_rec` frente a oráculos bajo las condiciones ensayadas.

No validan todavía:

- cobertura completa de `M_obs`;
- retries por intento;
- bytes parciales;
- causalidad sobre makespan;
- calidad global de placements mediante `η`.

## 6. Camino crítico actual

```text
semántica M_req ─────┐
                     ├──> congelar P2 -> herramienta -> validación -> overhead -> tesis
auditoría M_obs ─────┘
```

La semántica de `M_req` está cerrada condicionalmente como lower bound lógico condicionado al placement. Solo se reabre si la auditoría revela una incompatibilidad de fronteras entre `M_req` y la evidencia observable.

La siguiente evidencia bloqueante es la auditoría de `M_obs`.

## 7. Próximo comando

```bash
BASE="$HOME/pegasus-lab/pegasus_avance_semana_1_6"

find "$BASE/experiments" -type d -name 'run000*' \
  \( -ipath '*process*' -o -ipath '*pipeline*' \) \
  -print | sort
```

No lanzar nuevas campañas antes de seleccionar y auditar una corrida process y una pipeline existentes.

## 8. Regla de actualización

Cuando haya nueva evidencia:

```text
evidencia
-> TESIS_EXPERIMENT_LOG
-> TESIS_DECISION_LOG
-> TESIS_ESTADO_MAESTRO
-> TESIS_VALIDATION_PLAN
-> TESIS_METRICA_FORMULACION_EJECUTABLE
-> TESIS_ROADMAP_EJECUTABLE
-> TESIS_RAG_INDEX
```

No transformar resultados históricos; conservarlos y reinterpretarlos explícitamente cuando cambie la semántica.

## 9. Recuperación rápida del roadmap

- **Estado actual:** 1A cerrado condicionalmente; 1B es el siguiente bloque.
- **Siguiente gate:** auditar una corrida process y una pipeline y clasificar coverage de `M_obs`.
- **Después:** congelar P2, consolidar herramienta, sensibilidad estructural, overhead/límites y cierre de tesis.
- **Archivo rector operativo:** `TESIS_ROADMAP_EJECUTABLE_20260925.md`.


---

## 10. Estado vigente tras auditoría real del 26-09-2026

La pregunta de observabilidad avanzó sustancialmente.

Se auditaron dos corridas reales existentes a S=50 MiB. HTCondor proporciona bytes agregados de transfer-in/transfer-out del sandbox por job y Pegasus conserva `.sub` + `.meta`. En los cuatro jobs científicos revisados, el transfer-in se reconcilia exactamente contra el file-set completo; el transfer-out separa 50 MiB científicos de pocos KiB auxiliares.

Coverage provisional:

```text
JOB_LEVEL_EXACT_RECONCILIATION
```

Valores piloto:

```text
process same-w1:         M_req=100 MiB, M_obs=100 MiB, eta_move=1.0
pipeline balanced-local: M_req=150 MiB, M_obs=300 MiB, eta_move=0.5
```

No interpretar esto como eventos por archivo. La observación está sustentada a nivel job por reconciliación exacta del sandbox y por un único intento.

### Próximo paso del roadmap

Auditar un pipeline SAME y un pipeline CROSS comparables, preferiblemente S=50 MiB, para comprobar que la política de coverage se sostiene independientemente del placement. Después automatizar la reconciliación y congelar P2.

## Actualización 2026-09-26 — estado de observabilidad

Se cerró el piloto de observabilidad para pipeline con SAME/BALANCED/CROSS a 10 MiB. La evidencia disponible soporta `JOB_LEVEL_RECONCILED`: HTCondor observa bytes y conteos del sandbox por job; Pegasus aporta manifiestos, IDs de tareas, placement y tamaños científicos. Bajo esta política, `M_obs=60 MiB` en los tres placements, mientras `M_req={20,30,40} MiB`; por tanto `eta_move={0.3333,0.5,0.6667}`. No usar estos valores para rankear placements.

El camino crítico pasa ahora de Gate 1B a Gate 1C: congelar P2 y su política de coverage antes de modificar el Analyzer.



---

# Actualización de gobernanza — 2026-09-30

A partir de esta fecha el flujo obligatorio del proyecto es:

```text
REQUIREMENTS -> DESIGN -> IMPLEMENTATION -> VERIFICATION / VALIDATION
```

## Jerarquía operativa actualizada

1. `ppg_ls.contreras_202620 (2)(1).pdf` — alcance y metodología oficial.
2. `TESIS_REQUIREMENTS_SPEC_20260930.md` — **fuente canónica de requerimientos**.
3. `TESIS_AUDITORIA_EDGE_CASES_LITERATURA_20260930.md` — errores conocidos, edge cases y restricciones que el diseño debe resolver.
4. `TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md` — antecedente formal de la métrica; se interpreta a través del Requirements Spec si hubiera diferencia de redacción.
5. `TESIS_ESTRUCTURA_DOCUMENTO_Y_PRESENTACION_20260930.md` — estructura académica de documento y defensa; no gobierna el comportamiento del software.
6. `TESIS_ESTADO_Y_PLAN_20260930.md` — estado compacto y camino crítico.
7. `TESIS_DESIGN_SPEC` — pendiente; será la fuente canónica de diseño cuando Gate R quede congelado.
8. Código / tests — no gobiernan semántica; deben implementar Requirements + Design.
9. Logs/resultados experimentales — evidencia, no especificación.

## Regla de conflicto

Si un resultado histórico, script, slide o documento anterior contradice el Requirements Spec vigente, **no se cambia el requisito para coincidir con el código antiguo**. Se registra la discrepancia y se corrige en la fase correspondiente.

---

# Actualización 2026-09-30 — Gate R/D cerrados

La jerarquía vigente queda:

1. `ppg_ls.contreras_202620 (2)(1).pdf` — alcance/metodología oficial.
2. `TESIS_REQUIREMENTS_SPEC_20260930.md` — requisitos congelados.
3. `TESIS_GATE_R_CIERRE_20260930.md` — cierre formal Gate R.
4. `TESIS_AUDITORIA_EDGE_CASES_LITERATURA_20260930.md` — errores/edge cases.
5. `TESIS_DESIGN_SPEC_20260930.md` — diseño canónico.
6. `TESIS_TRACEABILITY_MATRIX_20260930.md` — trazabilidad 80/80.
7. `TESIS_GATE_D_REVIEW_20260930.md` — cierre formal Gate D.
8. `TESIS_IMPLEMENTATION_PLAN_20260930.md` — fase activa.
9. `TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md` — antecedente formal compatible; Requirements/Design prevalecen en precisión operativa.
10. Código y tests — implementación, nunca fuente semántica superior.
11. Logs/resultados — evidencia experimental.

**Estado:** Requirements y Design cerrados; Implementation activa; campañas nuevas bloqueadas hasta Gate I.

## Actualización de estado del arte — 2026-09-30

`TESIS_ESTADO_ARTE_COMPARATIVO_20260930.md` queda como fuente de comparación con trabajos cercanos (Pietri & Sakellariou, DataLife, DaYu, WCP, Do et al., DFTracer y Tang et al. 2026). Su función es sostener el gap académico sin claims universales de novedad. No modifica Gate R/D; Requirements y Design siguen siendo las fuentes normativas de software.

## Actualización de implementación — 2026-09-30 20:30

La fuente de estado operativo pasa a ser `TESIS_IMPLEMENTATION_LOG_20260930.md`, complementada por `TESIS_IMPLEMENTATION_PLAN_20260930.md`. La jerarquía semántica no cambia: Requirements y Design siguen prevaleciendo sobre código, tests y logs.

Estado resumido indexado:

```text
I0  baseline                          CLOSED
I1  domain model + diagnostics        CLOSED
I2  source loaders/parsers            CLOSED
I3  identity/normalization            implemented; I3B corrective debt OPEN
I4A detector core                     CLOSED
I4B execution-model evidence builder  CLOSED
I4C CondorIOStandardAdapter            CLOSED
I4  execution model global             OPEN
I5-I14                                 PENDING
```

Suite actual: `101/101 PASS`. Commits preservados: baseline `8269f0b`, I1 `869c47b`, I2 `1675ee9`, I3 `ce6ec3f`. Los cambios I4 permanecen sin commit hasta completar las evidencias críticas y la corrección I3B.

### Hallazgos que deben recuperarse al responder desde RAG

- No asumir que un único path físico identifica un archivo: I3B debe exigir relación semántica inequívoca.
- No clasificar compute jobs por filename. En I4B se usa semántica Pegasus (`pegasus_job_class=1` + DAX id real).
- No inferir `condorio` solo porque sea compatible con el comportamiento observado o un default del software. La corrida debe aportar evidencia suficiente conforme al Design Spec.
- Runs reales inspeccionados confirman `vanilla`, `YES`, `ON_EXIT`, `cluster_size=1`, pero todavía dejan campos críticos sin demostrar.

## Actualización I3/I4 cerrados — 2026-09-30

```text
I0  baseline                    CLOSED
I1  domain model                CLOSED
I2  source loaders/parsers      CLOSED
I3  identity/normalization      CLOSED  (ce6ec3f + 1ebf309)
I4  execution model detection   CLOSED  (31f4244)
I5  scientific dataflow         NEXT
I6  RequiredMovement            PENDING
I7  DeclaredMovement            PENDING
I8-I14                          PENDING
```

Suite actual: **106/106 PASS**. Smoke real I4: PASS en `process-same-w1-20260917-222429` y `distribution-same-w1-20260917-181537`. Evidencia del execution model recuperada desde artefactos preservados: condorio, submit host, HTCondor 25.12.2, no shared filesystem, no bypass, vanilla, transfer YES, ON_EXIT, no plugins, no clustering.

Reglas a recordar: un path físico único no identifica por sí solo un archivo; compute jobs se identifican por semántica Pegasus; el adapter solo se activa con evidencia trazable; Requirements/Design continúan siendo normativos sobre código/tests.

---

## Actualización RAG — 2026-09-30 17:13

Para preguntas sobre el estado de implementación, **este checkpoint prevalece sobre las entradas anteriores del 30 de septiembre**.

```text
I0  CLOSED
I1  CLOSED
I2  CLOSED
I3  CLOSED — commit 1ebf309 encima de ce6ec3f
I4  CLOSED — commit 31f4244
I5  ACTIVE
I6-I14 PENDING
```

Hechos recuperables:

- el fallback por path físico requiere relación semántica inequívoca;
- los compute jobs se clasifican por semántica Pegasus y no por nombre;
- los runs preservados aportan `condorio`, submit host, HTCondor version, `sharedFileSystem=false` y permiten seleccionar `CondorIOStandardAdapter`;
- smoke real I4 PASS;
- suite completa `106/106 PASS`;
- analyzer histórico intacto.

Próximo frente rector: **I5 Scientific Dataflow → I6 RequiredMovement → I7 DeclaredMovement**.

---

## RAG checkpoint I5–I7 — 2026-09-30 17:35

Estado operativo vigente:

```text
I0-I4 CLOSED
I5 CLOSED — 2916cd2
I6 CLOSED — 0078892
I7 CLOSED — 0078892
I8 ACTIVE
```

Hechos a recuperar:
- Scientific Dataflow v1 ya está implementado.
- RequiredMovement v1 file-centric ya está implementado.
- DeclaredMovement v1 ya está implementado y NO equivale a ObservedMovement.
- La confirmación de transferencias comienza en I8/I9.
- Commit HEAD al cierre I7: `0078892`.

---

## Actualización RAG — cierre I8-I10

Para preguntas sobre el estado actual de implementación, este bloque prevalece sobre checkpoints anteriores.

```text
I0-I10 CLOSED
I11 ACTIVE
I12-I14 PENDING
```

Commits recuperables: `821c70c`, `e05c4b4`, `2f9331a`, `9e27fbf`, `9d4d9d2`.

Hechos clave:

- `TransferEvidence` conserva raw stats y normaliza conteos/bytes por protocolo.
- `BytesRecvd/BytesSent` no se usan directamente como payload científico.
- reconciliación soporta `EXACT_BYTES` y `SUCCESSFUL_MANIFEST`; nunca reparte residuos auxiliares.
- `Coverage < 1` hace `ObservedMovement` y `DME` indeterminados.
- `RM=0, OM=0` produce `NOT_APPLICABLE`; `OM<RM` produce `INCONSISTENT`.
- suite completa: **134/134 PASS**.

Siguiente frente: **I11 Reporting**.

---

## Estado indexado — cierre I11

Para preguntas de estado de implementación, este bloque prevalece sobre checkpoints anteriores.

```text
I0-I11 CLOSED
I12 ACTIVE
I13 PENDING
Gate I OPEN
```

Commits recientes recuperables:

- `821c70c` — normalize HTCondor transfer evidence;
- `e05c4b4` — avoid transfer evidence normalization import cycle;
- `2f9331a` — separate manifest and size completeness;
- `9e27fbf` — reconcile declared movement with transfer evidence;
- `9d4d9d2` — calculate coverage, ObservedMovement and DME;
- `f6af663` — add canonical v1 analysis reporting.

Full suite: **138/138 PASS**. Legacy analyzer SHA-256 intacto. Próximo frente: I12 regression fixtures auditados.

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
## Índice de contexto — checkpoint 2026-09-30 después de I13

Prioridad de recuperación actual:

1. `TESIS_REQUIREMENTS_SPEC_20260930.md` — Gate R congelado.
2. `TESIS_DESIGN_SPEC_20260930.md` — Gate D congelado.
3. `TESIS_EXPERIMENT_LOG.md` — evidencia I12/I13.
4. `TESIS_DECISION_LOG.md` — Gate I permanece abierto hasta closeout documental/CLI.
5. `TESIS_ESTADO_MAESTRO.md` — estado operativo vigente.
6. `TESIS_VALIDATION_PLAN.md` — I14/Gate V siguen bloqueados.
7. `Contexto_Continuidad_Tesis_Pegasus_HTCondor.md` — continuidad técnica.

Checkpoint vigente:

```text
I0–I13 CLOSED
Gate I ACTIVE
142/142 PASS
HEAD conocido 77c6ff6
I14 BLOCKED
```


---

## Checkpoint de continuidad — 2026-10-03, Gate I

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Las ramas se publicaron en GitHub el 4/10/2026 desde Windows por HTTPS; PR pendiente de creación/revisión.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
