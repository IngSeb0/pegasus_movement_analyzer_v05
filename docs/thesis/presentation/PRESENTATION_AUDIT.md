# Auditoría de la presentación de tesis — 2026-10-03

Fuente editable Windows: `C:\Users\Acer\Documents\ChatGPT\THESIS\entregables\PRESENTACION_TESIS_DATA_MOVEMENT_ACTUALIZADA.pptx`. Se conserva una copia sincronizada en este directorio para el repositorio. Mantiene **20 diapositivas** y los diagramas en objetos editables PowerPoint. Tras corregir el estado de Gate I en slides 12 y 18 (y notas), pasó integridad de paquete, geometría y reimportación por Artifact Tool. La revisión cotejó su texto con Gate I y el Capítulo 5.

| Slides | Función | Figura/contenido clave | Estado |
|---|---|---|---|
| 1–8 | Portada, contexto, problema, objetivos, literatura | Workflow, frontera científica, comparación de líneas | Redactadas; revisar citas definitivas del capítulo 2 |
| 9 | Infraestructura y execution model | Master, dos workers previstos, condorio/HTCondor; captura sin startds | Datos del master y limitación worker correctos |
| 10–11 | Semántica y validez | Mreq, Mrec, Mobs, Coverage, DME | Correctas en principio; mantener precondiciones visibles |
| 12 | Metodología | Secuencia científica separada de gates | Actualizada a Gate I CLOSED; Gate V pendiente |
| 13 | Arquitectura Analyzer v1 | Fuentes → parsing → normalización → adapter/dataflow → métrica | Diagrama editable, alineado con capítulo 5 |
| 14 | Patrones y oráculos | Cinco patrones y placement | Diseño, no resultados Gate V |
| 15 | Evidencia/reconciliation | Manifest, TransferEvidence, MovementVerification | Distingue job-level y file-level |
| 16 | Fórmulas | Coverage, Mobs y DME | Notación editable; verificar símbolos al ensayar defensa |
| 17 | Limitaciones | Alcance condorio y evidencia | Vigente |
| 18 | Roadmap | Cierre I, I14 pendiente, V preparado | Actualizada al checkpoint |
| 19–20 | Mensaje final y fuentes | Síntesis y referencias | Resultados empíricos definitivos deben añadirse tras Gate V |

Para la defensa final aún faltan cifras de Gate V, sensibilidad, casos negativos, overhead y amenazas observadas. No se insertaron valores experimentales futuros. El conteo de slides de la defensa final puede revisarse cuando exista Capítulo 7; el deck actual se conserva como versión de trabajo.
