# Índice y precedencia documental

## Estado vigente — 4 de octubre de 2026

La autoridad de alcance es `../../../Propuesta_oficial_Data_Movement_Assessment_2026.md`. Gates R/D/I están cerrados; la campaña Gate V se ejecutó con 31 workflows independientes en diez condiciones. El detalle vigente está en `CODEX_CONTEXT.md`, el informe controlado y capítulos 6–9. La revisión documental actual no ejecuta más workflows, no inicia I14 y no hace merge a `main`.

El manuscrito tiene capítulos 1–9 en Markdown; el capítulo técnico 5 también existe como `.tex`. No hay un `.tex` maestro local. El Overleaf conectado muestra la página de bienvenida sin el proyecto de tesis. Por tanto, integración, PDF único y revisión página por página dependen de acceso al proyecto correcto.

| Precedencia | Fuente | Función |
|---|---|---|
| 1 | `../../../Propuesta_oficial_Data_Movement_Assessment_2026.md` | Fuente normativa: pregunta, alcance, criterios y cinco patrones |
| 2 | `context/TESIS_REQUIREMENTS_SPEC_20260930.md` y `context/TESIS_DESIGN_SPEC_20260930.md` | Requisitos y diseño técnico subordinados a la propuesta |
| 3 | HEAD Analyzer `feat/analyzer-v1` `3f44f30a9540861fbe1eeb0a0e515a6f9d7d79e6` y código | Implementación verificada para Gate I y usada en Gate V |
| 4 | `CODEX_CONTEXT.md`, informe Gate V, protocolo y bundle de runs | Checkpoint vigente, números y procedencia experimental |
| 5 | Capítulos `01`–`09`, `environment/` y `presentation/` | Redacción derivada y artefactos académicos actualizados |
| 6 | `context/` histórico, matrices antiguas y planes previos | Archivo de decisiones; leer con su fecha y no sustituir el estado vigente |

## Rutas principales

| Ruta | Uso |
|---|---|
| `CODEX_CONTEXT.md` | Contexto mínimo para retomar |
| `01_introduccion.md`–`09_conclusiones.md` | Texto de capítulos disponibles |
| `ACADEMIC_REVIEW_QUEUE.md` | Estado editorial por capítulo y límites de claims |
| `PLAN_INTEGRAL_CONTINUIDAD_20261004.md` y `ROADMAP_16_SEMANAS_ACTUALIZADO.md` | Secuencia y dependencias para cierre |
| `CH5_TRACEABILITY_AUDIT.md` | Capítulo 5 ↔ código/requisitos/figuras/slides |
| `environment/ENVIRONMENT_SNAPSHOT.md` | Observaciones del entorno y límites de ClassAds |
| `figures/FIGURE_INDEX.md` | Fuentes TikZ/PDF e índice de figuras |
| `presentation/PRESENTATION_AUDIT.md` | Auditoría visual/estructural del deck actualizado |
| `validation/EXISTING_RUNS_IMPLEMENTATION_EVIDENCE.md` | Cinco runs históricos de integración, separados de Gate V |
| `validation/` restante | Planes, matrices y runbooks históricos; revisar estado de fecha antes de usar |

Los documentos bajo `context/` conservan formulaciones anteriores a Gate V y pueden decir que Gate V o I14 estaban pendientes. Son registro histórico, no checkpoint actual. No borrar ese historial. Para el estado actual, seguir `CODEX_CONTEXT.md` y este índice.
