# Auditoría de la presentación de tesis — 2026-10-04

La versión de entrega mantiene **20 diapositivas** y organiza la exposición en torno a problema → métrica → sistema → evidencia → utilidad. Conserva las dimensiones 16:9, la tipografía Aptos del deck y el estilo visual existente. Los diagramas de arquitectura y rutas se construyeron con formas y conectores editables de PowerPoint.

El cuerpo principal ya no presenta la secuencia de gates como narrativa para el jurado. El estado del proyecto y el roadmap quedan en notas del presentador. Gate I cerró en `3f44f30`; I14 y Gate V siguen sin iniciar. No se añadieron resultados experimentales finales.

| Slides | Función | Contenido clave | Estado |
|---|---|---|---|
| 1–8 | Portada, contexto, problema, objetivos, literatura | Workflow científico, frontera del payload, pregunta y brecha | Conservadas; citas definitivas del capítulo 2 siguen por revisar |
| 9 | Infraestructura y execution model | Master, workers previstos, Pegasus/HTCondor y disponibilidad observada | Captura del master y limitación de workers declaradas |
| 10–11 | Métrica y precondiciones | Required, Declared, ObservedMovement, Coverage y DME | Semántica congelada y cobertura explícita |
| 12 | Metodología | Problema → formalización → Analyzer v1 → validación con oráculos | Gate status retirado de la lámina; queda en notas |
| 13 | Flujo central Analyzer v1 | Workflow + placement → RequiredMovement; condorio → DeclaredMovement; history + evidencia → Coverage = 1 → ObservedMovement → DME | Diagrama editable; M_obs y DME quedan indeterminadas con Coverage < 1 |
| 14 | Diseño de validación | Cinco patrones y placements controlados | Diseño propuesto; no son resultados de Gate V |
| 15 | Evidencia y reconciliation | Manifest, TransferEvidence y MovementVerification | Separa declaración de evidencia por job |
| 16 | Formalización matemática | M_req, Coverage, M_obs y DME | Notación editable; ensayar legibilidad en defensa |
| 17 | Lower bound y condorio | worker1 → archivo científico → worker2; worker1 → master → worker2 | Referencia conceptual; explica movimiento adicional posible, no ahorro garantizado ni packet tracing |
| 18 | Utilidad y límites | Diagnóstico, comparación y decisiones; límites de medición explícitos | Sustituye el roadmap visible por contenido dirigido al jurado; roadmap en notas |
| 19–20 | Cierre y referencias | Mensaje central y referencias | Resultados empíricos definitivos se reservan para después de Gate V |

La utilidad presentada abarca detectar movimiento científico adicional, diagnosticar staging por job, comparar patrones y placements, apoyar decisiones de arquitectura y evitar afirmaciones de rendimiento no sustentadas. Se declara que Analyzer no mide FLOPs, uso de CPU/GPU, runtime directo, ancho de banda ni costo; tampoco evalúa optimalidad del scheduler ni optimiza placement.

**Validación del archivo:** 20 slides; paquete íntegro; geometría sin hallazgos; tipografías Aptos/Aptos Display verificadas contra el deck de referencia; importación final por Artifact Tool aprobada. Se renderizaron las 20 diapositivas y se revisaron visualmente las láminas modificadas. No se verificó renderizado nativo en Microsoft PowerPoint.
