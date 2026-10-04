# TESIS — Registro experimental

**Última actualización interpretativa:** 2026-09-25. Las observaciones y cifras del 21 de septiembre permanecen como registro original; en sus tablas, el campo histórico `M_obs` se interpreta como `M_rec`.

---

## EXP-20260918-01 — Validación manual y controlada BALANCED-LOCAL

**Pregunta:** ¿El analizador reproduce los valores calculados manualmente para placements intermedios que usan ambos workers y preservan localidad razonable?

**Tamaño base:** 10 MiB  
**Execution model:** `EM_HTC` = condorio + HTCondor file transfer con sandbox por job  
**Workers:** worker1, worker2  
**Control:** `requirements` de HTCondor  
**Herramienta:** Analyzer v0.5.1 + Controlled Placement

### Resultados

| Patrón | Placement | M_req manual/script | M_obs manual/script | Estado |
|---|---|---:|---:|---|
| Process | T1=W1 | 20 / 20 | 20 / 20 | PASS |
| Pipeline | T1,T2=W1; T3=W2 | 30 / 30 | 60 / 60 | PASS |
| Distribution | T1,T2,T3=W1; T4,T5=W2 | 25 / 25 | 40 / 40 | PASS |
| Aggregation | T1,T2,T5=W1; T3,T4=W2 | 100 / 100 | 160 / 160 | PASS |
| Redistribution | T1-T5=W1; T6-T10=W2 | 120 / 120 | 320 / 320 | PASS |

Interpretación: `M_req` refleja las fronteras de ubicación bajo el placement fijado. `M_obs` refleja las materializaciones científicas por job del execution model estudiado.

---

## EXP-20260918-02 — Campaña de repetibilidad a S=10 MiB

**Diseño:** 13 condiciones x 3 repeticiones.  
**Resultado:** 39/39 PASS.

Interpretación: en el mismo testbed y bajo condiciones controladas, el placement observado, `M_req` y `M_obs` fueron repetibles. No se describe como reproducibilidad entre plataformas.

---

## EXP-20260918-03 — Sensibilidad completa al tamaño

**Pregunta:** ¿Las métricas escalan linealmente al cambiar el tamaño base S manteniendo estructura, placement y execution model?

**Diseño:** 5 patrones x 3 tamaños x 3 repeticiones = 45 casos.  
**Tamaños:** S=1, 10 y 50 MiB.  
**Resultado:** 45/45 PASS.

Relaciones confirmadas para el placement balanced-local (process usa same-w1):

```text
Process        : M_req=2S,   M_obs=2S
Pipeline       : M_req=3S,   M_obs=6S
Distribution   : M_req=2.5S, M_obs=4S
Aggregation    : M_req=10S,  M_obs=16S
Redistribution : M_req=12S,  M_obs=32S
```

---

## Interpretación general

- `M_req` depende del workflow, de los tamaños científicos y del placement estudiado.
- Al cambiar únicamente `PL`, `M_req` cambia cuando cambian las fronteras productor-consumidor que cruzan workers.
- Bajo `EM_HTC`, `M_obs` se obtiene de las ocurrencias de inputs/outputs científicos por job; en los casos controlados permaneció constante entre SAME, BALANCED-LOCAL y CROSS.
- `M_obs` no debe interpretarse como bytes de red observados con packet tracing.
- La campaña `size-full` confirma linealidad con S=1,10,50 MiB y tres repeticiones por condición.

---

## REV-20260925-01 — Alcance de los resultados históricos (sin nuevas corridas)

**Motivo:** el cálculo histórico etiquetado `M_obs` sumó tamaños de entradas y salidas científicas por job según el contrato de `condorio`. Se denomina **`M_rec`** a partir de esta revisión; no se ha aportado en este registro una verificación completa archivo por archivo de transferencias efectivamente confirmadas. `M_obs` queda pendiente cuando falta esa evidencia.

**Qué permanece válido:** 5/5 BALANCED-LOCAL, 39/39 repetibilidad y 45/45 sensibilidad a tamaño verifican acuerdo entre script, placements y oráculos manuales dentro del experimento. La linealidad demostrada corresponde a los volúmenes definidos por esos oráculos, no a una validación causal del rendimiento ni a una certificación de tráfico físico.

**Qué no se ha demostrado:** que `M_req` sea factible como mínimo bajo el staging ordinario `condorio`, que `M_req/M_rec` sea la eficiencia definitiva de la tesis, que las transferencias parciales o reintentos estén capturados, o que los cinco patrones cubran por sí solos todos los factores estructurales. Esta es una **revisión de interpretación**, no un experimento adicional ni un cambio de cifras.


---

## REV-20260926-01 — Auditoría de observabilidad con corridas reales existentes

Sin ejecutar nuevas campañas se auditaron `process-same-w1-20260917-232331` y `pipeline-balanced-local-20260917-232616`, ambas con archivos científicos de 50 MiB.

Los jobs científicos quedaron mapeados a HTCondor y al placement realmente observado: process `2435.0 -> worker1`; pipeline `2445.0 -> worker1`, `2448.0 -> worker1`, `2451.0 -> worker2`. Todos terminaron normalmente y presentan un único inicio/intento.

Los `.meta` confirman 50 MiB para `input.dat`, `process.out` y las tres etapas `pipeline.stage*.dat`, y 2,879 B para `data_task`.

La suma de los archivos declarados para transfer-in se reconcilia **exactamente en bytes** con `BytesRecvd`/`TransferInputStats.CedarSizeBytesTotal` en los cuatro jobs. Para transfer-out, `TransferOutputStats` reporta 3 archivos y el total es igual a 50 MiB de output científico más un residuo de 6,169–6,251 B atribuible al conjunto auxiliar de stdout/stderr.

Resultado metodológico: estas corridas soportan observación a nivel job con reconciliación exacta del file-set. La etiqueta provisional de coverage es `JOB_LEVEL_EXACT_RECONCILIATION`; no se afirma aún disponer de un evento independiente por archivo.

Bajo el boundary de payload científico:

- process S=50 MiB: `M_req=100 MiB`, `M_obs_reconciliado=100 MiB`, `eta_move=1.0`;
- pipeline BALANCED-LOCAL S=50 MiB: `M_req=150 MiB`, `M_obs_reconciliado=300 MiB`, `eta_move=0.5`.

Esto proporciona por primera vez evidencia de ejecución que conecta el contrato de staging con bytes agregados realmente registrados por HTCondor, sin confundir artefactos auxiliares con payload científico.

## 2026-09-26 — Pipeline placement trio, S=10 MiB, evidencia HTCondor reconciliada

Corridas seleccionadas: SAME `pipeline-same-w1-20260917-171234`, BALANCED-LOCAL `pipeline-balanced-local-20260917-171539`, CROSS `pipeline-cross-20260917-171907`. En las tres, `input.dat` y `pipeline.stage1/2/3.dat` miden 10 MiB. Placement observado: SAME `W1,W1,W1`; BALANCED `W1,W1,W2`; CROSS `W1,W2,W1`. Todos los jobs científicos tuvieron un solo inicio.

Los ClassAds registran `TransferInputStats`/`TransferOutputStats` y bytes agregados por job. La semántica de `.sub` y los metadatos Pegasus permiten separar el payload científico del overhead del sandbox a nivel job. Resultado de trabajo: `M_obs=60 MiB` para cada una de las tres corridas, con cobertura `JOB_LEVEL_RECONCILED`. Oráculos: `M_req={20,30,40} MiB` y `eta_move={0.3333,0.5000,0.6667}` para SAME, BALANCED y CROSS. No interpretar la razón como ranking de placements.


## 2026-09-26 — Piloto oficial para congelación de P2

Se adopta como conjunto piloto oficial el pipeline de 3 tareas y `S=10 MiB`:

- SAME: `pipeline-same-w1-20260917-171234`, placement observado `W1,W1,W1`;
- BALANCED-LOCAL: `pipeline-balanced-local-20260917-171539`, placement observado `W1,W1,W2`;
- CROSS: `pipeline-cross-20260917-171907`, placement observado `W1,W2,W1`.

Todos los jobs científicos tienen un intento. Los cuatro archivos científicos de cada corrida miden exactamente 10 MiB. La evidencia se clasifica `JOB_LEVEL_RECONCILED` y permite `Coverage=1`.

| Placement | RequiredMovement | DeclaredMovement | ObservedMovement | DME |
| --- | ---: | ---: | ---: | ---: |
| SAME | 20 MiB | 60 MiB | 60 MiB | 0.3333 |
| BALANCED-LOCAL | 30 MiB | 60 MiB | 60 MiB | 0.5000 |
| CROSS | 40 MiB | 60 MiB | 60 MiB | 0.6667 |

Este conjunto se usa como regression oracle inicial del Analyzer consolidado.

---

<!-- SYNC_20260930_I13_GATEI -->
## Evidencia nueva — cierre I12/I13 y candidato a Gate I

Orden de actualización respetado desde este checkpoint: **evidencia → experiment log → decision log → estado maestro → validation plan → continuidad → RAG index**.

### I12 — Regression suite

- commit: `b5880d6`
- 3 regresiones auditadas PASS:
  - pipeline 10 MiB SAME/BALANCED/CROSS contra oráculos congelados;
  - process 50 MiB con `SUCCESSFUL_MANIFEST`;
  - retry ambiguo fail-closed con `ObservedMovement=None` y `DME=None`.
- suite total al cierre I12: **141/141 PASS**.

### I13 — Integration suite sobre runs preservados

- commit: `77c6ff6`
- histories preservados para cinco runs reales:
  - process 50 MiB;
  - pipeline 50 MiB BALANCED;
  - pipeline 10 MiB SAME;
  - pipeline 10 MiB BALANCED;
  - pipeline 10 MiB CROSS.
- prueba `tests.integration.test_preserved_runs`: PASS.
- suite total con integración: **142/142 PASS**.

### Estado de Gate I

La implementación funcional I0–I13 está completa, pero **Gate I todavía no se marca CLOSED**. Falta cerrar la parte documental/CLI y ejecutar una suite final después de ese cambio. I14 sigue bloqueado.


---

## Checkpoint de continuidad — 2026-10-03, Gate I

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit local `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Publicación remota/PR pendiente por autenticación GitHub desde la VM.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
