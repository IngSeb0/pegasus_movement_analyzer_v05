# Cinco runs preservados — evidencia de integración, no Gate V

Analyzer v1 del commit de cierre `3f44f30a9540861fbe1eeb0e0a515a6f9d7d79e6` procesó el 3/10/2026 los **directorios originales** de Pegasus en `pegasus-master` usando los history auditados en `fixtures/audited/history`. Los artefactos fuente no fueron modificados. Cada caso produjo `analysis.json`; la tabla reproducible está en `existing_runs_consolidated.tsv` y el registro estructurado en `existing_runs_consolidated.json`. Un MiB son 1,048,576 bytes. Los valores que siguen son salidas de Analyzer, no oráculos independientes ni resultados experimentales finales.

| Caso | Placement | Mreq (B) | Mrec (B) | Coverage | Mobs (B) | DME | Estado |
|---|---|---:|---:|---:|---:|---:|---|
| process 50 MiB | same-w1 | 104,857,600 | 104,857,600 | 1 | 104,857,600 | 1 | VALID |
| pipeline 50 MiB | balanced-local | 157,286,400 | 314,572,800 | 1 | 314,572,800 | 0.5 | VALID |
| pipeline 10 MiB | same-w1 | 20,971,520 | 62,914,560 | 1 | 62,914,560 | 1/3 | VALID |
| pipeline 10 MiB | balanced-local | 31,457,280 | 62,914,560 | 1 | 62,914,560 | 0.5 | VALID |
| pipeline 10 MiB | cross | 41,943,040 | 62,914,560 | 1 | 62,914,560 | 2/3 | VALID |

Los cinco reportes usan `SUCCESSFUL_MANIFEST` y nivel `JOB_LEVEL_RECONCILED`. El nivel no debe describirse como medición directa de bytes por archivo ni como tráfico de red. `Mobs` está condicionado a la reconciliación completa del manifest científico; la cobertura resultó 1 en estos artefactos. Los cinco runs no constituyen repeticiones planificadas de la futura matriz Gate V; el campo `replicate` no consta en la evidencia y queda vacío. El detalle de `run_id`, rutas, bytes de diferencia y archivos de salida figura en las tablas adjuntas.

Para reproducir un caso se usa `python3 tools/analyze_run_v1.py --run <run_path> --history-file <history_path> --out <out_path>` en el commit indicado. El script de consolidación empleado en esta captura está preservado en el workspace de la sesión; sus resultados no reemplazan la invocación individual de la CLI ni la evidencia primaria.
