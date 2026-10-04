# Índice y precedencia documental

Entrada recomendada para una nueva sesión: `CODEX_CONTEXT.md`, luego este índice, luego Requirements/Design y solo después los documentos derivados. No pedir al usuario reconstruir hechos que estén aquí o en el repositorio.

| Autoridad | Documento/ruta | Función y estado |
|---|---|---|
| 1 | `context/TESIS_REQUIREMENTS_SPEC_20260930.md` | Requisitos cerrados; semántica normativa |
| 2 | `context/TESIS_DESIGN_SPEC_20260930.md` | Diseño y decisiones cerradas |
| 3 | `context/TESIS_DECISION_LOG.md` | Decisiones explícitas, con apéndice Gate I 3/10 |
| 4 | Código en `feat/analyzer-v1` y `3f44f30` | Implementación verificada; tres docs cambiaron al cerrar I |
| 5 | `validation/EXISTING_RUNS_IMPLEMENTATION_EVIDENCE.md` y fuentes en VM | Evidencia de cinco runs; no Gate V |
| 6 | `01_…` a `06_…`, `environment/`, `validation/`, `presentation/` | Redacción y plan derivados |
| 7 | `context/TESIS_ESTADO_MAESTRO.md`, planes, roadmap y Validation Plan históricos | Historia; encabezados de v0.5 pueden estar superados por apéndice 3/10 |

Las copias de gobernanza bajo `context/` preservan el texto histórico y añaden un checkpoint de 2026-10-03. Los Requirements y Design se copiaron **sin edición**. La matriz de trazabilidad, plan/log de implementación, estado/plan, RAG, log experimental, estructura y guion llevan un apéndice común de Gate I; las afirmaciones históricas de Gate I `ACTIVE` anteriores a ese apéndice no describen el estado actual. La tabla de referencias de Capítulo 2 se debe contrastar con artículos primarios al preparar bibliografía final.

| Ruta principal | Contenido |
|---|---|
| `ROADMAP_16_SEMANAS_ACTUALIZADO.md` | Mapeo sin alterar cronología académica |
| `ARCHITECTURE_VARIANTS.md` | Escenarios condorio frente a cambios del execution model |
| `environment/ENVIRONMENT_SNAPSHOT.md` | Datos observados, pendientes y comandos read-only |
| `figures/FIGURE_INDEX.md` | Fuentes TikZ/PDF del handoff y asignación a capítulos/slides |
| `presentation/PRESENTATION_AUDIT.md` | Estado y cambios de las 20 slides Windows |
| `validation/I14_READINESS.md` | Dependencias antes de runner/campaña |
| `validation/EXPERIMENT_MATRIX.md` | 117 casos propuestos, no ejecutados |
| `validation/ORACLE_PROTOCOL.md` | Comparación manual e invariantes de evidencia |
| `validation/RUNBOOK.md` | Secuencia de captura y análisis futuro |

No se ha hecho merge a `main`, no se ha iniciado I14 ni se ejecutaron nuevos workflows para este checkpoint.
