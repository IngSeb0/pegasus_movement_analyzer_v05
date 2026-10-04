# Guion histórico de presentación v12

**Estado al 25 de septiembre de 2026:** guía histórica para la estructura de láminas. No usar sus definiciones de `M_obs` o «mínimo» sin contrastarlas con `TESIS_ESTADO_MAESTRO.md`, `TESIS_RAG_INDEX.md` y la propuesta aprobada. En la presentación nueva, abrir con **contexto, problema oficial y justificación del enfoque en movimiento de datos**; diferenciar `M_rec` de `M_obs` y presentar `M_req/M_rec` como formulación en evaluación.

## Diapositiva 1: portada

Abrir diciendo que la presentación se enfoca en comprensión del sistema. La idea central es separar cuatro niveles: workflow lógico, software de ejecución, infraestructura y medición.

---

## Diapositiva 2: Qué debe quedar claro antes de mirar resultados

Esta diapositiva marca el contrato de la presentación: qué se está modelando, dónde ejecuta, cómo se materializan los archivos y cómo se calculan las métricas.

---

## Diapositiva 3: Modelo lógico del flujo de trabajo

Explicar que el workflow es un DAG G=(V,E). V son tareas científicas y E contiene dependencias. En las dependencias de datos existe un archivo d con tamaño s(d). En este nivel todavía no se sabe dónde se ejecuta nada.

---

## Diapositiva 4: Modelo de flujo de trabajo: patrones considerados I

Explicar process y pipeline. Estos modelos son lógicos: no hay worker ni master. Process no tiene dependencias internas. Pipeline encadena tres tareas; la salida de una etapa alimenta la siguiente.

---

## Diapositiva 5: Modelo de flujo de trabajo: patrones considerados II

Explicar que aggregation fuerza convergencia de ramas hacia un agregador. Distribution introduce fan-out: una fuente genera varios datos que alimentan consumidores distintos. Aún no se habla de workers.

---

## Diapositiva 6: Modelo de flujo de trabajo: data redistribution

Explicar que primero hay productores que alimentan Agg; luego Agg produce un archivo agregado; Split consume ese archivo y produce chunks para consumidores. Este patrón fue el que más confundió, por eso debe quedar claro que esto aún no es observado.

---

## Diapositiva 7: Modelo de máquina del experimento

Explicar la máquina: master como submit host con staging; workers como puntos de ejecución con un slot. Aclarar que el master no ejecuta tareas científicas en el baseline.

---

## Diapositiva 8: Modelo de software: Pegasus + HTCondor

Explicar los componentes: Pegasus planifica, DAGMan libera jobs según dependencias, Schedd maneja la cola, Collector y Negotiator realizan matchmaking, Startd anuncia recursos y Starter ejecuta el job en el worker.

---

## Diapositiva 9: Dependencia lógica ≠ transferencia física

Explicar con calma: la dependencia lógica T1 produce d y T2 consume d. En condorio, esa dependencia se puede materializar como sandbox T1 -> master/staging -> sandbox T2. Esto aplica aunque T1 y T2 estén en el mismo worker.

---

## Diapositiva 10: Process observado: caso base

Process permite verificar el caso base. Hay una entrada científica que entra al sandbox de T1 y un output que regresa al master. No hay dependencias internas ni localidad que analizar.

---

## Diapositiva 11: Pipeline observado: staging entre etapas

Pipeline es útil porque muestra que la localidad de tareas no siempre evita staging. Aunque T1, T2 y T3 están en worker2, cada intermedio puede salir al master y volver a entrar al siguiente job.

---

## Diapositiva 12: Distribution observado: separar decisiones

Explicar que Distribution se entiende en tres capas: el workflow dice qué chunk consume cada tarea; HTCondor decide dónde corre cada job; staging lleva el archivo al sandbox de ese job.

---

## Diapositiva 13: Distribution rep1: movimiento materializado

Explicar de arriba hacia abajo. T1 en worker2 recibe input, produce chunks y los devuelve al master. Luego cada consumidor recibe su chunk desde staging. T2 está en worker1 porque HTCondor lo colocó ahí.

---

## Diapositiva 14: Redistribution observado: placement antes de movimiento

Explicar que esta es la colocación observada de rep1. P1, P2, Agg, Split, C2, C3, C4 están en worker1. P3, P4 y C1 en worker2. Este placement no es la definición del patrón, sino el resultado de HTCondor.

---

## Diapositiva 15: Redistribution rep1: productores, Agg y Split

Explicar que los inputs van a P1..P4, los productores generan producer0..3, esos outputs se materializan en staging, Agg recibe los cuatro, produce merged.dat y ese archivo vuelve a staging. Luego Split recibe merged.dat.

---

## Diapositiva 16: Redistribution rep1: Split, consumidores y salidas

Explicar que Split produce cuatro chunks de 10 MiB, los devuelve a staging y después cada consumer recibe su chunk según el placement. C1 está en worker2; C2-C4 están en worker1.

---

## Diapositiva 17: Diferencia entre M_rec y M_obs

Explicar que `M_rec` reconstruye el staging científico esperado por job bajo `condorio`, mientras `M_obs` exige eventos completos de traslados confirmados. No atribuir el nombre `M_obs` a la suma de tamaños declarados en la implementación histórica. No son tráfico total Ethernet ni BytesSent/BytesRecvd sin filtrar.

---

## Diapositiva 18: Factores específicos que afectan M_obs

Explicar los factores que pueden modificar volumen reconstruido o confirmado y separar los que afectan tiempo pero no volumen. Registrar patrón, placement y configuración de staging.

---

## Diapositiva 19: Definición exacta de M_req^π

Explicar que `M_req` no viene de logs: es una referencia de trabajo con placement fijo y reutilización local ideal. Aclarar que esa reutilización puede no ser alcanzable bajo `condorio`; por tanto el cociente con `M_rec` aún no es eficiencia definitiva.

---

## Diapositiva 20: Qué información necesita M_req y qué significa “mínimo”

Explicar la diferencia: M_req^π_obs mantiene la colocación que HTCondor produjo. M_req* optimiza también la colocación. En el baseline se usa M_req^π_obs.

---

## Diapositiva 21: Trazabilidad: de código y logs a la métrica

Explicar que la herramienta histórica reconstruye `M_rec` desde datos científicos declarados y el contrato de staging; `M_req` se calcula desde archivos, tamaños y placement; `M_obs` queda pendiente de evidencias completas por archivo/tramo. El tiempo de Pegasus statistics es otra dimensión, no un sustituto de volumen.

---

## Diapositiva 22: Diseño experimental de ejecución

Cerrar explicando cómo continúa el trabajo: baseline natural, luego placements controlados same/cross, tamaños, modelos de ejecución y tiempo.

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

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Las ramas se publicaron en GitHub el 4/10/2026 desde Windows por HTTPS; PR pendiente de creación/revisión.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
