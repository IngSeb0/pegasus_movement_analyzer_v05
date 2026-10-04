# TESIS — Requirements-to-Design Traceability Matrix

**Fecha:** 30 de septiembre de 2026  
**Entrada:** `TESIS_REQUIREMENTS_SPEC_20260930.md`  
**Diseño:** `TESIS_DESIGN_SPEC_20260930.md`

Cada requisito congelado en Gate R debe tener una ruta explícita a diseño y prueba futura.

| Requirement | Componente | Modelo de datos | Algoritmo/responsabilidad | Fuente | Diagnóstico | Test family |
|---|---|---|---|---|---|---|
| REQ-COV-01 | C10 Metrics Engine | MetricResult | calculate_coverage / byte_coverage | Declared movements + verifications | INCOMPLETE_EVIDENCE | T-COV |
| REQ-COV-02 | C10 Metrics Engine | MetricResult | calculate_coverage / byte_coverage | Declared movements + verifications | INCOMPLETE_EVIDENCE | T-COV |
| REQ-COV-03 | C10 Metrics Engine | MetricResult | calculate_coverage / byte_coverage | Declared movements + verifications | INCOMPLETE_EVIDENCE | T-COV |
| REQ-COV-04 | C10 Metrics Engine | MetricResult | calculate_coverage / byte_coverage | Declared movements + verifications | INCOMPLETE_EVIDENCE | T-COV |
| REQ-DATA-01 | C6 Scientific Dataflow Builder | ScientificFile | classify_scientific_files | Pegasus semantic I/O | INCONSISTENT | T-DATA |
| REQ-DM-01 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DM-02 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DM-03 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DM-04 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DM-05 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DM-06 | C5 Adapter + C8 Declared Movement Builder | JobTransferManifest + DeclaredMovementRecord | build_declared_movements | submit/ClassAd transfer contract | UNSUPPORTED/INCOMPLETE_EVIDENCE | T-DM |
| REQ-DME-01 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-02 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-03 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-04 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-05 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-06 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-DME-07 | C10 Metrics Engine | MetricResult | validate_metric_preconditions / calculate_dme | RM + OM + Coverage | NOT_APPLICABLE/INCONSISTENT | T-DME |
| REQ-EM-01 | C5 Execution Model Detector | ExecutionModelProfile | detect_execution_model / supports | Pegasus config + submit/ClassAds | UNSUPPORTED | T-EM |
| REQ-EM-02 | C5 Execution Model Detector | ExecutionModelProfile | detect_execution_model / supports | Pegasus config + submit/ClassAds | UNSUPPORTED | T-EM |
| REQ-EM-03 | C5 Execution Model Detector | ExecutionModelProfile | detect_execution_model / supports | Pegasus config + submit/ClassAds | UNSUPPORTED | T-EM |
| REQ-EM-04 | C5 Execution Model Detector | ExecutionModelProfile | detect_execution_model / supports | Pegasus config + submit/ClassAds | UNSUPPORTED | T-EM |
| REQ-EXP-01 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-02 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-03 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-04 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-05 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-06 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-07 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-EXP-08 | C13 Experiment Runner | ExperimentSpec + RunManifest | run_validation_campaign | experiment config + run artifacts | experiment failure status | T-EXP |
| REQ-F-01 | C1 Run Source Loader | RawRunSources | load_run_sources | run directory | ERROR | T-F-01 |
| REQ-F-02 | C2 Pegasus Extractor | TaskExecution | identify_scientific_tasks | Pegasus DAG/plan | INCONSISTENT | T-F-02 |
| REQ-F-03 | C6 Dataflow Builder | ScientificFile | classify_scientific_files | Pegasus semantics | INCONSISTENT | T-F-03 |
| REQ-F-04 | C6 Dataflow Builder | ScientificFile | resolve_file_sizes | meta/cache/physical | INCOMPLETE_EVIDENCE | T-F-04 |
| REQ-F-05 | C6 Dataflow Builder | ScientificFile | build_producer_consumer_graph | Pegasus I/O | INCONSISTENT | T-F-05 |
| REQ-F-06 | C3+C4 | TaskExecution + Location | extract_observed_placement | HTCondor history | INCOMPLETE_EVIDENCE | T-F-06 |
| REQ-F-07 | C7 | RequiredMovementRecord | build_required_movements | integrated model | INCONSISTENT | T-F-07 |
| REQ-F-08 | C8 | DeclaredMovementRecord | build_declared_movements | job manifests | UNSUPPORTED | T-F-08 |
| REQ-F-09 | C3 | TransferEvidence | collect_transfer_evidence | HTCondor stats | INCOMPLETE_EVIDENCE | T-F-09 |
| REQ-F-10 | C9 | MovementVerification | reconcile_job_transfers | manifest + HTCondor stats | INCOMPLETE_EVIDENCE | T-F-10 |
| REQ-F-11 | C10 | MetricResult | calculate_coverage | verification records | INCOMPLETE_EVIDENCE | T-F-11 |
| REQ-F-12 | C10 | MetricResult | calculate_observed_movement | confirmed declared movements | INCOMPLETE_EVIDENCE | T-F-12 |
| REQ-F-13 | C10+C11 | MetricResult + diagnostics | validate_metric_preconditions | integrated model | INCONSISTENT | T-F-13 |
| REQ-F-14 | C10 | MetricResult | calculate_dme | RM+OM+Coverage | NOT_APPLICABLE/INCONSISTENT | T-F-14 |
| REQ-F-15 | C12 | analysis.json + TSV + REPORT | write_report | MetricResult + provenance | ERROR | T-F-15 |
| REQ-F-16 | C11+C12 | Diagnostic | emit_diagnostics | all stages | structured status/reason | T-F-16 |
| REQ-LOC-01 | C4 Normalizer + C5 Execution Model | Location | normalize_locations | HTCondor host/ClassAds + config | UNSUPPORTED/INCONSISTENT | T-LOC |
| REQ-LOC-02 | C4 Normalizer + C5 Execution Model | Location | normalize_locations | HTCondor host/ClassAds + config | UNSUPPORTED/INCONSISTENT | T-LOC |
| REQ-LOC-03 | C4 Normalizer + C5 Execution Model | Location | normalize_locations | HTCondor host/ClassAds + config | UNSUPPORTED/INCONSISTENT | T-LOC |
| REQ-NF-01 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-02 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-03 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-04 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-05 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-06 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-07 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-08 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-09 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-NF-10 | Cross-cutting architecture | all canonical models | pipeline invariants | all sources | varies | T-NF |
| REQ-OM-01 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-02 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-03 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-04 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-05 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-06 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-07 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-OM-08 | C3 Evidence Extractor + C9 Reconciler | TransferEvidence + MovementVerification | reconcile_job_transfers | HTCondor history/ClassAds + full manifest | INCOMPLETE_EVIDENCE/INCONSISTENT | T-OM |
| REQ-RM-01 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-02 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-03 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-04 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-05 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-06 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-07 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-RM-08 | C7 Required Movement Engine | ScientificFile + RequiredMovementRecord | build_required_movements | Integrated dataflow + placement | INCONSISTENT | T-RM |
| REQ-TRACE-01 | C11 Provenance | ProvenanceRef | attach_provenance / validate_conflicts | all raw sources | INCONSISTENT | T-TRACE |
| REQ-TRACE-02 | C11 Provenance | ProvenanceRef | attach_provenance / validate_conflicts | all raw sources | INCONSISTENT | T-TRACE |
| REQ-TRACE-03 | C11 Provenance | ProvenanceRef | attach_provenance / validate_conflicts | all raw sources | INCONSISTENT | T-TRACE |
| REQ-TRACE-04 | C11 Provenance | ProvenanceRef | attach_provenance / validate_conflicts | all raw sources | INCONSISTENT | T-TRACE |
| REQ-TRACE-05 | C11 Provenance | ProvenanceRef | attach_provenance / validate_conflicts | all raw sources | INCONSISTENT | T-TRACE |

**Cobertura:** 80/80 requisitos trazados.

Gate D falla si aparece un nuevo `REQ-*` sin una fila correspondiente.

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
