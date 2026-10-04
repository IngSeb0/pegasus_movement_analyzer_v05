# TESIS — Estructura académica del documento y de la presentación

**Estado:** guía de estructura. No reemplaza Requirements Spec ni Design Spec.

## 1. Principio estructural

Se conserva la lógica metodológica observada en el documento de referencia del profesor:

```text
Problem Statement
Literature Review
Problem Formulation / System Model
Proposed Method / Tool
Experimental Framework
Evaluation and Analysis
Conclusion
```

Adaptada a esta tesis, donde la contribución es una métrica + herramienta de medición, no un scheduler.

## 2. Estructura recomendada del documento final

### Capítulo 1 — Introducción y formulación del problema

- contexto de scientific workflows;
- relevancia de data movement;
- problema específico de medición;
- pregunta de investigación;
- justificación;
- objetivo general y específicos;
- alcance y exclusiones;
- contribuciones esperadas;
- organización del documento.

### Capítulo 2 — Estado del arte

- workflow management y Pegasus;
- data movement / staging;
- data placement y locality;
- profiling/tracing/measurement;
- communication cost/lower bounds como fundamento conceptual;
- patrones de scientific workflows;
- síntesis: qué aporta cada línea y qué necesidad queda para la tesis.

### Capítulo 3 — Formulación y modelo del sistema

- workflow model;
- scientific data model;
- machine/location model;
- placement model;
- execution model;
- tracing/evidence model;
- supuestos y scope soportado.

### Capítulo 4 — Especificación de la métrica

- RequiredMovement;
- DeclaredMovement;
- ObservedMovement;
- Coverage;
- DME;
- interpretación;
- casos cero/inconsistencia;
- shared files/fan-out/final outputs/retries;
- condiciones de aplicabilidad;
- oráculos manuales.

### Capítulo 5 — Diseño de la herramienta

Se redactará **después de Gate D**:

- requerimientos trazados;
- arquitectura;
- modelo de datos;
- extractores/adapters;
- integración;
- reconciliación;
- cálculo;
- reporting;
- manejo de errores;
- decisiones de diseño y alternativas descartadas.

### Capítulo 6 — Metodología experimental

- enfoque experimental/cuantiativo;
- testbed oficial VMware;
- versiones;
- cinco patrones;
- factores y niveles;
- placements como escenarios controlados;
- protocolo de ejecución;
- preservación de evidencia;
- oráculos;
- repetibilidad;
- overhead;
- criterios de validez.

### Capítulo 7 — Resultados

- corrección de la herramienta;
- piloto de observabilidad;
- resultados por patrón;
- sensibilidad estructural;
- repetibilidad;
- overhead;
- casos inválidos/incompletos.

### Capítulo 8 — Discusión y amenazas a la validez

- interpretación de DME;
- qué mide y qué no mide;
- relación con literatura;
- limits de `condorio`;
- observabilidad a nivel job;
- external validity;
- construct validity;
- instrumentation/evidence limitations.

### Capítulo 9 — Conclusiones y trabajo futuro

- respuesta al problema;
- contribuciones verificadas;
- limitaciones;
- adapters futuros (sharedfs/plugins/etc.);
- validación en workloads científicos de mayor escala solo como trabajo futuro si no pertenece al alcance final aprobado.

## 3. Estructura de presentación formal

La presentación debe contar una historia lineal y defendible. Guías universitarias de defensa recomiendan comenzar por problema/importancia, explicar metodología, presentar claims/resultados y terminar en contribuciones, limitaciones y futuro. También recomiendan slides legibles, poco saturadas y figuras claras.

### Bloque A — Motivación y pregunta

1. Portada.
2. Qué es un scientific workflow y dónde aparece data movement.
3. Por qué data movement importa — evidencia de literatura.
4. Qué hace Pegasus/HTCondor y qué información queda dispersa.
5. Problema de investigación.
6. Objetivo y alcance: medición, no scheduling.

### Bloque B — Fundamento formal

7. Mapa conceptual: Workflow -> Placement -> Execution -> Tracing -> Measurement.
8. Workflow/data model.
9. Machine/location + placement model.
10. Execution model `condorio`.
11. Evidence/tracing model.
12. Qué cuenta como archivo científico.
13. RequiredMovement, explicado con diagrama.
14. Declared vs Observed Movement.
15. Coverage y por qué evita inventar datos.
16. DME y su interpretación.
17. Ejemplo manual pipeline BALANCED.

### Bloque C — Método y herramienta

18. Metodología de investigación.
19. Cinco patrones de validación.
20. Testbed experimental oficial.
21. Requerimientos de la herramienta.
22. Arquitectura del Analyzer — solo cuando Gate D esté cerrado.
23. Protocolo de evidencia/reconciliación.

### Bloque D — Evidencia actual y validación pendiente

24. Auditoría HTCondor del piloto.
25. SAME/BALANCED/CROSS: Required vs Observed.
26. Qué demuestra el piloto y qué no demuestra.
27. Edge cases y condiciones de aplicación.
28. Plan de validación completa.
29. Estado actual / roadmap.
30. Contribuciones y cierre.
31. Referencias esenciales.

## 4. Reglas visuales

- títulos que expresen una conclusión, no solo un tema;
- una idea principal por slide;
- diagramas antes que párrafos para workflow/placement/staging;
- fórmulas acompañadas de ejemplo numérico;
- mínimo texto legible y consistente;
- resultados mediante tablas o gráficos, no logs de terminal;
- cada resultado debe indicar configuración/runs cuando sea necesario;
- no presentar como resultado final nada que aún sea una hipótesis o requerimiento.

## 5. Fuentes metodológicas para la presentación

- Naval Postgraduate School: priorizar problema, importancia, contribuciones y validación.
- University of Rochester: slides enfocadas en hallazgos salientes, gráficos legibles y narrativa clara.
- Texas A&M Writing Center: problema -> métodos -> hallazgos -> implicaciones -> futuro.
- MIT Communication Lab: usar roadmap, fondo mínimo necesario y títulos que cuenten la historia por sí solos.

## 6. Regla antes de construir PPTX final

No se congela una presentación “formal final” hasta cerrar:

```text
Gate R — Requirements
Gate D — Design
```

Antes de esos gates se puede mantener un deck de avance, pero no debe fijar arquitectura o comportamiento que aún pueda cambiar.

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
