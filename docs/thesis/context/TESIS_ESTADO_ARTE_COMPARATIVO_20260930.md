# TESIS — Estado del arte comparativo para la contribución de DME

**Fecha:** 30 de septiembre de 2026  
**Propósito:** ubicar la contribución de la tesis frente a líneas cercanas sin formular un claim universal de novedad que exceda la evidencia revisada.

## 1. Conclusión ejecutiva

La revisión adicional **no contradice** la formulación vigente de la tesis. Al contrario, permite precisar mejor el gap.

La literatura revisada cubre al menos cinco líneas cercanas:

1. reducción de comunicación mediante scheduling/placement;
2. modelado y análisis workflow-centric del dataflow;
3. métricas de rendimiento o eficiencia a nivel workflow;
4. tracing/observabilidad de I/O y dataflow;
5. caracterización de relaciones productor-consumidor para scheduling consciente de I/O.

La formulación actual de esta tesis ocupa una intersección distinta: para una **ejecución concreta** y su **placement observado**, calcula una referencia mínima lógica de payload científico (`RequiredMovement`), confirma el movimiento científico materializado (`ObservedMovement`) bajo una política explícita de evidencia, y define `DME = RequiredMovement / ObservedMovement` únicamente cuando existe cobertura completa.

La redacción académicamente defendible del gap es:

> En la literatura revisada se encontraron trabajos que optimizan placement para reducir comunicación, caracterizan dataflows e I/O, introducen métricas workflow-level y proporcionan mecanismos de tracing. Sin embargo, **no se identificó en este conjunto de fuentes una métrica con la misma semántica operacional de DME**: comparar, para la misma ejecución y placement, un lower bound lógico file-centric de movimiento requerido contra payload científico observado y trazable, con una condición explícita de cobertura antes de calcular la razón.

No usar expresiones como “es la primera métrica existente” hasta completar y documentar una revisión sistemática suficientemente exhaustiva.

---

## 2. Comparación verificada

| Línea / trabajo | Qué aporta | Relación con nuestra tesis | Diferencia principal |
| --- | --- | --- | --- |
| **Pietri & Sakellariou (2018), Scheduling Data-Intensive Scientific Workflows with Reduced Communication** | Propone un scheduling que aumenta el peso de comunicación para co-localizar tareas con transferencias grandes y reducir el volumen/costo de comunicación. | Refuerza que dataflow, tamaño y placement determinan comunicación relevante. | Optimiza el placement. DME no selecciona placement; mide una ejecución dado su placement observado. |
| **Lee et al. (DataLife, SC 2023)** | Enriquece el DAG con objetos de datos y propiedades de flujo; mide, analiza y visualiza data lifecycles, e identifica oportunidades de mejor placement y menor movimiento. | Es uno de los antecedentes más cercanos: trata los datos como entidades de primer nivel y relaciona tareas, archivos y flujo. | Su objetivo es análisis y oportunidad de optimización; no define la comparación `RequiredMovement / ObservedMovement` condicionada al mismo placement ni una regla de coverage equivalente. |
| **Tang et al. (DaYu, CLUSTER 2024)** | Relaciona semántica de datasets, direcciones/operaciones de archivos e I/O de bajo nivel para identificar cuellos de botella y orientar optimizaciones. | Refuerza la necesidad de fusionar semántica workflow-level con evidencia de ejecución. | Analiza semántica/I/O y propone guías de optimización; no construye nuestro referente lógico mínimo ni DME. |
| **Workflow Critical Path — WCP (2021)** | Define una métrica data-oriented de camino crítico para workflows HPC holísticos; representa estados de datos y mutaciones y calcula el camino crítico temporal. | Es evidencia de que una métrica workflow-level, respaldada por un modelo de datos y una herramienta, es una contribución metodológica válida. | Su magnitud central es critical path/costo temporal; no mide eficiencia de movimiento en bytes contra un lower bound lógico. |
| **Do et al. (2021), A Lightweight Method for Evaluating In Situ Workflow Efficiency** | Define una métrica ligera de eficiencia de uso de recursos para workflows in situ, basada en idle time y un execution model explícito. | Antecedente metodológico útil: formaliza el execution model, precondiciones y una métrica específica de workflow. | Mide resource-use efficiency/tiempo en workflows in situ, no payload científico requerido vs. observado. |
| **DFTracer (SC 2024)** | Captura eventos de aplicación e I/O a múltiples niveles y produce trazas orientadas al análisis. | Es relevante para la capa `Tracing/Evidence`; podría proporcionar evidencia más fina para futuras versiones del Analyzer. | Es infraestructura de tracing/observabilidad, no una métrica que construya una referencia lógica requerida y la compare contra movimiento observado. |
| **Tang et al. (IPDPS 2026), Characterizing Dataflow for I/O-Aware Scheduling in HPC Workflows** | Metodología workflow-centric que correlaciona estructura, orden, relaciones productor-consumidor, reutilización, tipo de acceso, número de operaciones y tamaño. | Muy cercano al modelo file-centric que necesitamos y útil para justificar producer/consumer, reuse y size como variables. | Usa la caracterización para I/O-aware scheduling y oportunidades de optimización; no define DME ni nuestro criterio de cobertura. |

---

## 3. Qué cambia en nuestra argumentación

### 3.1 No afirmar que “nadie mide data movement”

Eso sería incorrecto. DataLife, DaYu, DFTracer y el trabajo de Tang et al. muestran medición, tracing y caracterización detallada de dataflow/I/O.

### 3.2 El gap debe estar en la **relación entre referencia y observación**

Nuestro foco no es simplemente observar bytes. La contribución candidata está en combinar:

```text
workflow + archivos + tamaños + placement observado
                ↓
        RequiredMovement

execution contract + evidence + reconciliation
                ↓
        ObservedMovement

Coverage = 1
                ↓
DME = RequiredMovement / ObservedMovement
```

### 3.3 Separar medición de optimización

Pietri & Sakellariou, DataLife, DaYu y Tang et al. muestran que la información de data movement puede utilizarse para mejorar scheduling o coordinación. Nuestra tesis se limita a **medición y validación**; una optimización posterior es una aplicación potencial, no el objetivo central.

### 3.4 DFTracer no debe incorporarse al scope v1 sin rediseño experimental

DFTracer podría elevar la granularidad de evidencia hacia file/event-level, pero añadir instrumentación cambia el protocolo y obliga a medir overhead. Para la tesis vigente debe citarse como trabajo relacionado y posible extensión, no incorporarse silenciosamente al testbed aprobado.

---

## 4. Implicaciones para Requirements y Design

La revisión no obliga a reabrir Gate R ni Gate D. Las decisiones vigentes siguen siendo compatibles:

- modelo file-centric;
- separación Workflow -> Placement -> Execution -> Tracing -> Measurement;
- `RequiredMovement` condicionado al placement observado;
- `ObservedMovement` sujeto a evidencia;
- `Coverage = 1` como precondición;
- `DME` no rankea placements;
- core independiente de patrones y número de workers;
- tracing desacoplado mediante adapters.

Sí debe añadirse a la redacción académica una comparación explícita con estos antecedentes y evitar claims universales de novedad.

---

## 5. Referencias verificadas

- Pietri, I., & Sakellariou, R. (2018). *Scheduling Data-Intensive Scientific Workflows with Reduced Communication*. SSDBM 2018. DOI: `10.1145/3221269.3221298`.
- Lee, H., Guo, L., Tang, M., Firoz, J., Tallent, N., Kougkas, A., & Sun, X.-H. (2023). *Data Lifecycles: Optimizing Workflow Task & Data Coordination*. SC'23.
- Tang, M., Cernuda, J., Ye, J., Guo, L., Tallent, N., Kougkas, A., & Sun, X.-H. (2024). *DaYu: Optimizing Distributed Scientific Workflows by Decoding Dataflow Semantics and Dynamics*. IEEE CLUSTER 2024. DOI: `10.1109/CLUSTER59578.2024.00038`.
- *Workflow Critical Path: A data-oriented critical path metric for Holistic HPC Workflows* (2021). BenchCouncil Transactions on Benchmarks, Standards and Evaluations, 1(1), 100001. DOI: `10.1016/j.tbench.2021.100001`.
- Do, T. M. A., Pottier, L., Caíno-Lores, S., Ferreira da Silva, R., Cuendet, M. A., Weinstein, H., Estrada, T., Taufer, M., & Deelman, E. (2021). *A lightweight method for evaluating in situ workflow efficiency*. Journal of Computational Science, 48, 101259. DOI: `10.1016/j.jocs.2020.101259`.
- Devarajan, H., et al. (2024). *DFTracer: An Analysis-Friendly Data Flow Tracer for AI-Driven Workflows*. SC24.
- Tang, M., Guo, L., Kougkas, A., Sun, X.-H., & Tallent, N. R. (2026). *Characterizing Dataflow for I/O-Aware Scheduling in HPC Workflows*. IPDPS 2026. DOI: `10.1109/IPDPS65963.2026.00076`.

---

## 6. Frase recomendada para tesis/presentación

> Los trabajos relacionados muestran que el movimiento y la localidad de datos pueden abordarse mediante scheduling, caracterización de dataflows, tracing y métricas de rendimiento a nivel workflow. La propuesta de esta tesis se diferencia en que define una medida post-mortem condicionada al placement observado: contrasta el volumen mínimo de payload científico requerido por el dataflow para esa colocación con el volumen científico confirmado durante la ejecución, y solo calcula la eficiencia cuando la evidencia cubre completamente los movimientos declarados.

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

