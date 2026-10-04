# Changelog

## Analyzer v1 — cierre documental de Gate I (`feat/analyzer-v1`, 2026-10-03)

- Nuevo análisis post mortem de un run Pegasus preservado y un HTCondor history proporcionado explícitamente.
- Modelo normalizado de ejecución, tareas, ubicaciones, archivos científicos, manifests, evidencia, verificaciones, movimientos, métricas y procedencia.
- Detector y adapter del perfil Pegasus 5.x + `condorio` + HTCondor vanilla/file transfer, con diagnóstico fail-closed cuando falta evidencia o el modelo no está soportado.
- Separación de `RequiredMovement`, `DeclaredMovement` y `ObservedMovement`; Coverage por ocurrencias y DME solo bajo sus precondiciones.
- Reconciliación con modos `EXACT_BYTES` y `SUCCESSFUL_MANIFEST`, niveles de evidencia y razones auditables.
- CLI `tools/analyze_run_v1.py`, reportes JSON/TSV/texto, oráculos de regresión y cinco runs preservados para integración portable.

La magnitud histórica llamada `M_obs` en la documentación v0.5 procedía de manifests `.sub`. En el contrato v1, un manifest origina `DeclaredMovement`; `ObservedMovement` exige confirmación por evidencia. No se reinterpretan los valores históricos como movimiento confirmado sin volver a analizarlos con v1.

## v0.5.1 — baseline histórico (`main`)

El analizador y CLI históricos permanecen disponibles en `main` como baseline congelado. Sus resultados y fixtures se interpretan según su propio contrato, separado del contrato v1.

## v0.5.0 — registro histórico

- `M_req` simplificado a placement observado y reutilización local ideal.
- Entrada directa `runXXXX` y placement desde TSV, snapshot `condor_history -long` o history vivo.
- Fixture Distribution reconstruida desde evidencia del proyecto.
