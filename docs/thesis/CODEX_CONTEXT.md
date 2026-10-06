# CODEX_CONTEXT

## Proyecto
Data Movement Assessment in Scientific Workflows. Alcance gobernado por `Propuesta_oficial_Data_Movement_Assessment_2026.md`.

## Pregunta y objetivo
Dado un workflow y el placement real de sus tareas, ¿cuánto movimiento exigen sus dependencias entre ubicaciones y cuánto payload científico declara y permite confirmar la ejecución? Comparar esas cantidades sin confundirlas con tráfico físico.

## Semántica congelada
- `M_req`: tamaño de archivos científicos por destinos nuevos distintos que el DAG y el placement observado requieren.
- `M_rec`: payload científico declarado en ocurrencias de manifiesto por job.
- `D_sci`: ocurrencias declaradas; `C_sci`: ocurrencias reconciliadas con evidencia HTCondor por job; `Coverage=|C_sci|/|D_sci|`.
- `M_obs`: tamaños de ocurrencias científicas confirmadas; solo con cobertura completa. `DME=M_req/M_obs` bajo precondiciones válidas.
- Las cantidades comparten run, alcance científico y unidades; sus reglas de conteo/eventos son diferentes. `M_obs−M_req` no demuestra desperdicio ni bytes evitables.
- No medir ni afirmar paquetes de red, ancho de banda, I/O físico, RAM/NUMA, rendimiento, costo económico u optimalidad del scheduler.

## Execution model
Pegasus 5.1.2, HTCondor 25.12.2, jobs `vanilla`, transferencia `condorio`; master `pegasus-master`, workers `pegasus-worker1/2`. Analyzer v1 es post-mortem y usa run preservado más HTCondor history. No necesita SSH directo a workers.

## Estado de gates
- Gates R, D e I: constan como cerrados en el contexto heredado.
- Gate V: completado según el informe heredado; 5 patrones, 10 condiciones, 31 workflows independientes, ≥3 por condición, 31 válidos, placement y oráculos concordantes, `Coverage=1`.
- El contexto heredado asocia la validación Gate V al commit `3f44f30a9540861fbe1eeb0a0e515a6f9d7d79e6`; ese commit no está presente en este clon. El HEAD local de `feat/analyzer-v1` es `5600ee17f5da7e48d46689cb8bf0b4e74cbfe158`. Verificar la relación entre el hash validado y ese HEAD antes de atribuir la campaña al código actual.

## HEAD y rama
Base: `feat/analyzer-v1` en `5600ee17f5da7e48d46689cb8bf0b4e74cbfe158`. Rama de entregables: `codex/presentacion-clara-20261005`. No se modificó código funcional.

## Terminado
Gate V documentado; capítulos 1–9 y especificaciones disponibles en `docs/thesis`; nueva presentación clara y editable, guion oral y auditoría de frontera de medición en `docs/thesis/presentation`.

## Pendiente o bloqueado
- No se aisló el costo de generación de logs nativos con control ON/OFF; no afirmar porcentaje causal de runtime.
- Overleaf: falta abrir/acceder al proyecto correcto para integrar los capítulos, compilar el PDF completo y revisar su versión final.
- Evaluación externa limitada al pool de dos workers y a las diez condiciones probadas; no iniciar I14 sin autorización posterior.

## Siguiente acción
Revisar esta presentación con el usuario/profesor; luego integrar los capítulos al proyecto Overleaf accesible, compilar el PDF y cerrar una revisión editorial conjunta. No hacer merge a `main`, no iniciar I14 y no redefinir la métrica.
