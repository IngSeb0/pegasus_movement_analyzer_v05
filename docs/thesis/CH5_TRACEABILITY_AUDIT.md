# Auditoría de trazabilidad — Capítulo 5 y Analyzer v1

**Corte:** 2026-10-04. **Autoridad académica:** `Propuesta_oficial_Data_Movement_Assessment_2026.md`. **Base funcional:** `feat/analyzer-v1` en `3f44f30`; Gate I CLOSED. La descripción corresponde al código v1 y no a modelos históricos v35/v36. No incorpora resultados Gate V.

| Sección | Base implementada comprobada | Figura o slide | Dictamen |
|---|---|---|---|
| 5.1 Arquitectura | `analyzer_v1.py`, parsers Pegasus/HTCondor, `reporting.py` | TikZ pipeline; PPTX slide 13 | Análisis offline de run e history preservados. |
| 5.2 Modelo normalizado | `model.py`: las 13 entidades requeridas | TikZ de dominio; PPTX slides 14–15 | Entidades, campos y relaciones cotejados con dataclasses. |
| 5.3 Adquisición | `pegasus_source.py`, `htcondor_source.py` | TikZ pipeline; slide 13 | Fuentes se leen explícitamente antes de su interpretación. |
| 5.4 Normalización | `normalize.py`, delimitación de history en `analyzer_v1.py` | Modelo de dominio; slide 14 | Identidades y ubicación se normalizan; basename aislado no basta como identidad. |
| 5.5 Dataflow | `dataflow.py` | Capítulo 5; slides 13–14 | Relaciones científicas, roles, tamaños y placement alimentan RequiredMovement. |
| 5.6 Execution model adapter | `execution_model.py`, `condorio_adapter.py` | TikZ infraestructura; PPTX slide 9 | Alcance `condorio`/vanilla; límites del perfil explícitos. |
| 5.7 Required/Declared | `movement.py` | Ecuaciones del `.tex`; PPTX slides 13–15 | Se conserva la semántica congelada; manifest declara, no observa. |
| 5.8 Evidence/reconciliation | `htcondor_source.py`, `reconciliation.py` | TikZ reconciliation; PPTX slides 15 y 17 | Granularidad job-level no se presenta como captura file-level. |
| 5.9 Coverage/Mobs/DME | `metrics.py`, `MetricResult` | Ecuaciones del `.tex`; PPTX slide 18 | Precondiciones, estados cero e inconsistencia visibles. |
| 5.10 Reporting/provenance | `reporting.py`, `ProvenanceRef` | PPTX slides 13–15 | Reporta contexto del patrón, parámetros, modelo, fuentes y provenance. No normaliza todos los argumentos del planner ni un ID de snapshot ambiental. |
| 5.11 Fail-closed | `diagnostics.py`, estado global y bloqueo de etapas | Figura del flujo; PPTX slides 13 y 17 | No se imputan ceros ante ausencia de evidencia suficiente. |
| 5.12 Estrategia de pruebas | `tests/`, `TEST_REPORT.txt`, integración con runs preservados | PPTX slide 16 | Gate I y pruebas de implementación; no equivalen a la validación de los cinco patrones. |

## Trazabilidad de entidades

Las clases `RunExecution`, `Location`, `TaskExecution`, `ScientificFile`, `ExecutionModelProfile`, `ManifestFile`, `JobTransferManifest`, `TransferEvidence`, `MovementVerification`, `RequiredMovementRecord`, `DeclaredMovementRecord`, `MetricResult` y `ProvenanceRef` son dataclasses en `model.py`. Las figuras editables las distribuyen en dos vistas: ejecución/dataflow (slide 14) y contrato/evidencia/métrica (slide 15). Las flechas expresan relaciones o dependencias del modelo; no implican cardinalidades empíricas por run.

## Alineación académica y límites

La propuesta oficial prescribe cinco patrones —process, pipeline, data aggregation, data distribution y data redistribution—, e interpretación por patrón, configuración de planificación Pegasus y ambiente de cómputo. El deck (slide 16) y la metodología registran los cinco patrones y criterios de validación; la matriz interna de 129 casos se etiqueta como opción de diseño, no como requisito oficial.

El modelo de salida serializa `pattern_context`, `experiment_parameters`, `execution_model`, fuentes y provenance. La configuración de planificación completa y el snapshot del ambiente deben enlazarse a los artifacts de cada run; no existe un campo normalizado que garantice por sí solo su captura integral. Esta limitación se declara en los materiales para no atribuir a Analyzer una captura no implementada.

La consulta del 4/10 a las 03:30:13 -05:00 desde master registró slots de ambos workers, 1 CPU/1410 MiB por slot y estado `Unclaimed/Idle`. Es una captura del pool, no inventario físico completo. La clase de acceso no exige conexión SSH directa a los workers.

## Estado de verificación del artefacto

- Gate I está CLOSED en `3f44f30`; los cinco runs preservados son evidencia de integración y regresión.
- No se ejecutaron workflows nuevos ni se inició I14/Gate V.
- El `.tex` está editado en sitio, pero el compilador integrado devolvió `Unable to find standard directories for platform`; el PDF no está verificado.
- El deck final contiene 22 slides editables, incluidos máquina (9), arquitectura (13), modelo de datos (14–15), diseño de validación (16), reconciliación (17) y métricas (18). Integridad, geometría, fuentes e importación por Artifact Tool: PASS.
