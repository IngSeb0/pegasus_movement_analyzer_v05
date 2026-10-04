# Plan integral de continuidad — 4 de octubre de 2026

**Objeto:** cerrar el manuscrito y la presentación de la tesis con evidencia verificable de Analyzer v1, preparar I14/Gate V sin lanzar la campaña antes de una decisión explícita, y conservar el trabajo en GitHub. La VM `pegasus-master` es la fuente autoritativa para software, pool, runs, cálculos y pruebas; Windows conserva el editor LaTeX y el deck. Este plan distingue tareas ejecutables ahora, dependencias externas y decisiones académicas.

## 1. Línea base comprobada

| Elemento | Estado y evidencia |
|---|---|
| Gate R, Gate D, I0–I13 | Cerrados según Requirements/Design y handoff |
| Gate I | **CLOSED** en `3f44f30a9540861fbe1eeb0e0a515a6f9d7d79e6`; suite 142 correctas/1 omitida, dos integraciones de cinco runs, CLI smoke `VALID`, fixtures 179 hashes correctos |
| GitHub | `main=8269f0b`; `feat/analyzer-v1=3f44f30`; `docs/thesis-v1=6749433`, confirmados por `ls-remote` el 4/10; sin merge |
| VM | master accesible; Pegasus 5.1.2 y HTCondor 25.12.2 capturados el 3/10 |
| Workers | worker1 `.137` y worker2 `.139` previstos; el 4/10 no respondieron a un ping desde master y `condor_status -startd` no anunció slots. Causa y hardware desconocidos |
| Documentos | Capítulos 1–6 redactados como borradores; Capítulo 5 `.tex` editado en sitio, 5.1–5.12; editor LaTeX no logra compilar por entorno |
| Presentación | 20 slides editables; slides 12/18 y notas actualizadas a Gate I CLOSED; integridad, geometría e importación correctas |
| Gate V | Matriz base de 117 y bloque estructural de 12: **129 workflows propuestos**; protocolo y runbook escritos; ningún workflow nuevo lanzado |

## 2. Ruta crítica y fases

| Fase | Acción concreta | Producto/criterio de cierre | Dependencia | Estado |
|---|---|---|---|---|
| A. Publicación y revisión | Mantener dos ramas publicadas; PR [#1 Analyzer v1 → main](https://github.com/IngSeb0/pegasus_movement_analyzer_v05/pull/1) y [#2 tesis → feat/analyzer-v1](https://github.com/IngSeb0/pegasus_movement_analyzer_v05/pull/2) abiertos como borradores | URLs verificadas, base/head correctos, sin merge | Revisión humana de diffs y decisión de integración | PRs abiertos; revisión pendiente |
| B. Infraestructura | Diagnosticar energía/conectividad de ambos workers fuera de esta sesión; después capturar hostname, SO, CPU/vCPU, RAM, red, versiones y rol por SSH o consola; confirmar `startd` en collector | Snapshot por host con comandos y fecha, dos slots anunciados, placement posible | Intervención sobre VMs/red si siguen inaccesibles | Bloqueada |
| C. Congelación académica | Revisión editorial de capítulos 1–6, concordancia con Requirements/Design y código; insertar figuras TikZ revisadas, bibliografía primaria y tabla de trazabilidad | Texto revisado sin resultados inventados; símbolos consistentes; 5.1–5.12 auditadas | No requiere workers para capítulos 1–5; capítulo 6 se etiqueta protocolo | En progreso |
| D. Compilación y deck | Reparar disponibilidad del compilador integrado o compilar en un entorno autorizado existente; inspeccionar figuras, saltos y tipografía; mantener 20 slides hasta tener resultados | PDF de Capítulo 5 compilado y revisado; deck editable con notas/figuras correctas | Herramienta LaTeX operativa; no instalar paquetes de sistema automáticamente | Bloqueada por editor |
| E. Preparación experimental | Revisar 129 filas propuestas, oráculos, negativos y criterios de aceptación; especificar I14 y su manifest idempotente | Plan aprobado con comandos, directorios, presupuesto, reanudación y riesgos | Workers disponibles; decisión sobre alcance | Preparada, sin ejecución |
| F. Piloto y presupuesto | Ejecutar solo un piloto corto autorizado para medir tiempo/disco y confirmar captura de history/placement | Medición real de duración y almacenamiento por caso; presupuesto reproducible `T≈Σ t_i`, `S≈Σ s_i` con reserva explícita | Decisión del usuario; workers y pool sanos; runner controlado | No iniciado |
| G. Gate V | Ejecutar 129 casos propuestos o la matriz acordada, preservar artefactos, comparar oráculos, casos negativos, sensibilidad, repeticiones y overhead | Resultados completos y auditables; estado Gate V según criterios de validación | Autorización **expresa** de la campaña larga después de mostrar costo | No iniciado |
| H. Tesis final | Redactar capítulos 7–9 con datos de Gate V, discusión/amenazas/conclusiones; actualizar presentación y repositorio | Manuscrito/defensa con resultados respaldados por run IDs y provenance | Gate V completo | Bloqueada |

## 3. Acciones seguras que continúan ahora

1. Auditar que cada afirmación de capítulos 1–6 tenga fuente normativa, código, captura o artículo primario y marcar las lagunas. Dar prioridad a símbolos, semántica de `JOB_LEVEL_RECONCILED` y fronteras científicas.
2. Crear un índice de trazabilidad por sección del Capítulo 5: código, entidad, requisito, figura y diapositiva. Corregir únicamente errores observados en el `.tex` abierto, compilar mediante el editor después de cada edición.
3. Revisar los PDF/TikZ heredados antes de incorporarlos: algunos anteceden a Analyzer v1 y pueden usar `Mobs` con sentido antiguo. Conservar fuentes; no presentar una figura histórica como medición v1 sin auditoría.
4. Registrar en `environment/` el estado del pool por fecha y comandos read-only. Volver a comprobar ambos workers antes de cualquier decisión experimental.
5. Mantener GitHub y los PRs sincronizados mediante commits ordinarios. La VM conserva el repo principal; los bundles permiten publicar desde Windows cuando la VM no tiene credenciales. Nunca force push ni merge automático.

## 4. Diseño Gate V que necesita criterio

La matriz base contiene `process` con `same-w1` y los otros cuatro patrones con `same-w1`, `balanced-local`, `cross`: 13 condiciones por tamaño. Tres tamaños (1, 10, 50 MiB) y tres repeticiones producen **117 runs**. Cuatro perturbaciones estructurales obligatorias con `same-w1`, 10 MiB y tres repeticiones agregan **12 runs**: pipeline de 4 etapas, distribution/aggregation/redistribution de 6 ramas. El total es **129 workflows nuevos propuestos**. Los casos negativos son análisis offline adicionales. La ejecución debe incluir `pattern`, `placement`, `size`, `replicate`, parámetros del workflow, commit Analyzer, versiones Pegasus/HTCondor, snapshot de entorno, oráculos, rutas y hashes. La predicción cualitativa es que `Mreq` puede crecer con ubicaciones distintas; `Mrec` puede mantenerse para contratos por job fijos; `Mobs` y DME solo se informan con cobertura completa.

**Decisiones pendientes del usuario antes de trabajo dependiente:** (i) restablecer/autorizar intervención sobre VMs worker si no están disponibles; (ii) revisar la matriz propuesta de 129 workflows, incluidos los 12 estructurales exigidos por Requirements; (iii) autorizar un piloto nuevo y después la campaña larga con duración/espacio medidos; (iv) decidir el momento de merge de cada PR tras revisión. La falta de respuesta no constituye aprobación.

## 5. Registro de límites y recuperación

- Si `condor_status` no muestra startds, no ejecutar casos distribuidos ni atribuirles hardware observado. Conservar salida del diagnóstico.
- Si placement real difiere del diseñado, preservar run y marcar la condición prevista como no cumplida; recalcular solo la referencia para el placement observado con provenance.
- Si history/manifests son incompletos, no imputar cero ni DME; conservar `INCOMPLETE_EVIDENCE`/diagnósticos.
- Si un run falla, no sobrescribirlo. Repetir con nuevo identificador y vincular intento/razón.
- Si el editor LaTeX vuelve a fallar por plataforma, conservar el `.tex` y reportar compilación no verificada sin afirmar PDF.
- Si GitHub rechaza PR por permisos, conservar ramas publicadas y el diff para revisión; no usar credenciales extraídas ni reconfigurar el repositorio sin necesidad.

## 6. Siguiente bloque recomendado

La auditoría de trazabilidad capítulo 5 ↔ código/requisitos/figuras/slides y el inventario de afirmaciones por revisar en capítulos 1–6 están documentados. El siguiente bloque es revisar oráculos estructurales y preparar el presupuesto de piloto en papel, mientras se resuelve la disponibilidad de workers. Cuando vuelvan, capturar su entorno y medir un piloto **solo después** de acordar su alcance; con ese costo real se podrá solicitar decisión informada para los 129 workflows propuestos.
