# Figuras vectoriales de tesis

Este directorio contiene **18 fuentes TikZ `.tex` y sus PDF** provenientes del paquete validado del handoff del 3/10/2026, además de `common.tex` y `end.tex`. Se conservaron las fuentes editables y PDF de referencia; se excluyeron PNG redundantes. Estos PDF son los entregados en el handoff, no una nueva compilación en esta sesión. Antes de incorporarlos a la tesis final, revisar cada rótulo histórico frente a Analyzer v1 y actualizarlo si contradice la semántica actual.

| Capítulo/sección | Figuras candidatas | Uso y control |
|---|---|---|
| 1–2 | `01_contexto_workflow_movimiento`, `03_estado_arte_gap` | Contexto y gap acotado; verificar citas |
| 3 | `02_mismo_dataflow_distinto_placement`, `04_unidad_analisis`, `05_frontera_cientifica` | Sistema, ubicación, frontera |
| 4 | `06_requiredmovement_casos`, `07_tres_niveles_movimiento`, `08_coverage_observed`, `09_dme_interpretacion` | Fórmulas, niveles y cobertura; revisar `Mrec/Mobs` |
| 5.1, 5.6 | `11_analyzer_pipeline` y figura TikZ propia del Capítulo 5 | Arquitectura y execution model; preferir la figura propia ya auditada |
| 5.8–5.9 | Figura de reconciliación propia del Capítulo 5, `08_coverage_observed` | Verificación antes de DME |
| 6 | `10_metodologia_investigacion`, `12_patrones_diseno_experimental`, `13_comportamiento_esperado_patrones`, `14`–`18` oráculos por patrón | Método y predicciones, no resultados |

Los tres diagramas del archivo Windows `entregables/CAPITULO_5_ANALYZER_V1.tex` son también TikZ editables. La presentación usa objetos PowerPoint nativos para sus diagramas y conserva 20 slides. No se generaron figuras con un generador de imágenes.

La auditoría del 4/10 comparó `07_tres_niveles_movimiento.tex`, `08_coverage_observed.tex`, `09_dme_interpretacion.tex` y `11_analyzer_pipeline.tex` con la semántica v1: distinguen Mreq/Mrec/Mobs y condicionan DME a Coverage. Su asignación detallada a 5.1–5.12 figura en `../CH5_TRACEABILITY_AUDIT.md`. Esto comprueba el contenido textual de las fuentes TikZ; la inspección visual final del PDF del capítulo sigue pendiente del compilador.
