# Auditoría de trazabilidad — Capítulo 5 y Analyzer v1

**Fecha:** 2026-10-04. **Base funcional:** `feat/analyzer-v1` en `5600ee1`; Gate I cerró en `3f44f30` mediante cambios solo documentales. Esta auditoría coteja el texto 5.1–5.12 de `05_arquitectura_implementacion.md` y el `.tex` abierto en Windows con clases/funciones reales, Requirements Spec, figuras y deck de 20 slides. No infiere resultados Gate V.

| Sección | Código de implementación verificable | Requisitos principales | Figura/tabla del capítulo y slide | Dictamen |
|---|---|---|---|---|
| 5.1 Arquitectura | `analyzer_v1.py:analyze_run_v1`, `pegasus_source.py`, `htcondor_source.py`, `reporting.py` | REQ-F-01, F-15; NF-09 | Figura TikZ de pipeline en `.tex`; slide 13 | Alineada: análisis offline con history explícito |
| 5.2 Datos normalizados | `model.py` define las 13 entidades obligatorias; `RunExecution` contiene tareas, archivos, ubicaciones, manifests, evidencia, movimientos y resultado | REQ-TRACE-01–05; F-02–06 | Tabla de 13 entidades; slide 13 | Alineada en responsabilidad, campos y relaciones |
| 5.3 Adquisición | `pegasus_source.py:load_run_sources/parse_submit_file/parse_meta_file`; `htcondor_source.py:parse_history_file` | REQ-F-01, F-09; NF-09 | Figura pipeline; slide 13 | Alineada: parsing preserva fuente antes de interpretación |
| 5.4 Normalización | `normalize.py:normalize_history_identity/resolve_file_identity/build_worker_locations`; `_scope_history` en `analyzer_v1.py` | REQ-LOC-01–03; TRACE-02,05 | Tabla de entidades; slide 13 | Alineada: basename aislado no es identidad suficiente |
| 5.5 Dataflow | `dataflow.py:build_scientific_dataflow`, resolución de tamaños y roles | REQ-DATA-01; F-03–05 | Tabla de entidades; slides 10,13 | Alineada: identidad/tamaño ambiguo bloquean dependientes |
| 5.6 Adapter | `execution_model.py:detect_execution_model/build_execution_model_evidence_from_run`; `condorio_adapter.py:CondorIOStandardAdapter.supports` | REQ-EM-01–04; DM-06 | Figura TikZ de master/workers; slide 9 | Alineada. La figura es captura de estado, no prueba de disponibilidad histórica |
| 5.7 Required/Declared | `movement.py:build_required_movements/build_condorio_manifests/build_declared_movements` | REQ-RM-01–08; DM-01–05 | Ecuaciones 5.1–5.2; slides 10,16 | Alineada. `Mreq` usa destinos distintos y placement observado; manifest no confirma bytes |
| 5.8 Evidence/reconciliation | `htcondor_source.py:build_transfer_evidence`; `reconciliation.py:reconcile_manifest/reconcile_movements` | REQ-OM-01–08; TRACE-03 | Figura TikZ de reconciliación; slide 15 | Alineada. Éxito de manifest y evidencia compatible dan nivel job, sin repartir bytes agregados |
| 5.9 Coverage/Mobs/DME | `metrics.py:calculate_metrics`; `MetricResult` en `model.py` | REQ-COV-01–04; DME-01–07 | Ecuaciones de Coverage/Mobs/DME; slide 16 | Alineada. Cobertura 1 para conjunto declarado vacío; 0/0 N/A, 0/positivo=0, Obs<Req inconsistente |
| 5.10 Reporting/provenance | `reporting.py:build_analysis_document/write_tsv_reports/write_human_report/exit_code_for_status`; `ProvenanceRef` | REQ-F-15; TRACE-01–05 | Tabla y texto; slides 13,15 | Alineada: JSON, TSV y REPORT; hash de fuente opcional |
| 5.11 Fail-closed | `diagnostics.py` estados/códigos; `analyzer_v1.py:overall_status`; `metrics.py` | REQ-F-16; NF-04 | Ramal diagnóstico en figura 5.1; slides 11,17 | Alineada: no imputar cero ante ausencia de evidencia |
| 5.12 Pruebas | `tests/unit/`, `tests/regression/test_audited_oracles.py`, `tests/integration/test_preserved_runs.py`; `TEST_REPORT.txt` | REQ-NF-01–03,05–08; EXP-01–05 | Texto, sin resultado experimental final; slide 14 | Alineada: suite e integración documentadas en Gate I |

## Entidades de 5.2 cotejadas con `model.py`

`RunExecution`, `Location`, `TaskExecution`, `ScientificFile`, `ExecutionModelProfile`, `ManifestFile`, `JobTransferManifest`, `TransferEvidence`, `MovementVerification`, `RequiredMovementRecord`, `DeclaredMovementRecord`, `MetricResult` y `ProvenanceRef` están definidas como dataclasses. Campos relevantes confirmados: `ScientificFile` conserva roles, tamaño, productores/consumidores y ubicaciones; `JobTransferManifest` conserva archivo, dirección e intento; `TransferEvidence` conserva stats, método, bytes/conteos y procedencia; `MovementVerification` conserva nivel, modo, confirmación y razón; `MetricResult` conserva bytes, cobertura, DME, estados y razones. La tabla académica no promete que todo `source_hash` esté poblado.

## Estado de figuras y diapositivas

Los tres TikZ propios del `.tex` corresponden a 5.1 (arquitectura), 5.6 (infraestructura/execution model) y 5.8 (reconciliación). Las figuras heredadas `07_tres_niveles_movimiento.tex`, `08_coverage_observed.tex`, `09_dme_interpretacion.tex` y `11_analyzer_pipeline.tex` usan la distinción v1 entre requerido/declarado/observado y la precondición de cobertura; sus PDF son del handoff validado, no compilados aquí. Las restantes son candidatas para capítulos 1–4/6 y requieren revisión editorial antes de insertarlas. Los diagramas de slides 9, 13 y 15 usan objetos PowerPoint editables. Slide 18 ya indica 129 workflows propuestos, no realizados.

## Correcciones y pendientes

1. Se corrigió en el `.tex` y el `.md` la afirmación antigua `Gate I ACTIVE`; ahora se vincula al commit `3f44f30` publicado. No se cambió la métrica ni código funcional.
2. El compilador LaTeX integrado devuelve `Unable to find standard directories for platform`; no hay PDF nuevo verificado. Conservar el `.tex` abierto y reintentar cuando el editor disponga de su plataforma.
3. La revisión académica final debe fijar bibliografía, estilo y numeración en el manuscrito maestro. Las cifras de los cinco runs preservados están fuera del Capítulo 5 como evidencia de implementación.
4. Los datos físicos de workers continúan pendientes. La figura 5.6 representa la topología prevista y la captura del 3/10; no debe leerse como que los slots estaban activos.
