# Capítulo 6 — Metodología experimental

**Estado:** protocolo propuesto y documentado; la campaña de Gate V no se ha realizado. Los cinco runs preservados son evidencia de implementación/regresión, no resultados finales de este capítulo.

## 6.1 Secuencia de investigación

La investigación caracteriza fuentes y patrones, formaliza una métrica con dominio explícito, operacionaliza las fuentes Pegasus/HTCondor, implementa Analyzer v1, diseña escenarios controlados y compara sus salidas con oráculos independientes. El análisis posterior evaluará sensibilidad, aplicabilidad, repetibilidad y amenazas a la validez. Gates R/D/I/V aseguran hitos de desarrollo; **no son el método científico principal**.

## 6.2 Testbed y unidad experimental

La unidad experimental es un run nuevo de Pegasus/HTCondor con DAG, tamaño, placement diseñado y versión de Analyzer fijados. El testbed previsto tiene un master y dos workers VMware. El master está inventariado en `environment/ENVIRONMENT_SNAPSHOT.md`; los workers no estaban disponibles el 3/10 y sus características deben capturarse antes de experimentos. Cada run se conserva con workflow, submits, metadatos, history filtrado, configuración, resultado Analyzer y hashes. La disponibilidad del pool y placement real se comprueban antes de interpretar una condición.

## 6.3 Variables y controles

| Tipo | Variable | Registro/criterio |
|---|---|---|
| Independiente | Patrón | process, pipeline, distribution, aggregation, redistribution |
| Independiente | Placement diseñado | same-w1; same-w1/balanced-local/cross para los otros patrones |
| Independiente | Tamaño base | 1, 10, 50 MiB, convertido a bytes exactos |
| Control | Execution model | Pegasus `condorio`, HTCondor vanilla y managed file transfer |
| Control | Parámetros de workflow | 3 etapas de pipeline y 4 ramas cuando aplica; registrar generador/seed |
| Control | Versiones y host | Commit Analyzer, Pegasus, HTCondor y snapshot del entorno |
| Observada | Placement efectivo | History; discrepancia con el diseñado invalida esa condición prevista |
| Dependiente | `Mreq`, `Mrec`, Coverage, `Mobs`, DME | Analyzer y oráculos manuales aplicables, con provenance |
| Dependiente futura | Tiempo, costo de análisis y overhead | Medir con protocolo adicional antes de afirmar cifras |

La matriz base propone 13 condiciones × 3 tamaños × 3 repeticiones = **117 runs**, sujetos a revisión y disponibilidad del pool. El detalle fila por fila y sus campos está en `validation/EXPERIMENT_MATRIX.md`. Variaciones estructurales de etapas, fan-out/fan-in y archivos compartidos se priorizarán como extensiones explícitas, con presupuesto separado. Ninguna ejecución nueva se infiere de este diseño.

## 6.4 Procedimiento y oráculos

Antes de ejecutar, se congela cada DAG, lista de archivos científicos, tamaños, placement diseñado y referencia manual `Mreq`. El oráculo de `Mrec` se construye desde los contratos de entrada/salida por job bajo el execution model soportado. Se preserva un run nuevo y history acotado; Analyzer v1 se invoca con commit fijado. Se compara placement observado, oráculos en bytes exactos y diagnósticos. `Coverage=1` es precondición de `Mobs` y DME. Casos con evidencia incompleta se reportan indeterminados, no como cero. El protocolo detallado está en `validation/ORACLE_PROTOCOL.md`; el runbook operativo está en `validation/RUNBOOK.md`.

## 6.5 Repetibilidad, negativos y aceptación

Tres repeticiones por condición permiten examinar consistencia de estado y magnitudes, siempre conservando artefactos únicos. Casos negativos previstos: tamaño ausente/conflictivo, productor ambiguo, placement ausente, job fallido, intento no separable, manifest incompleto, protocolo no soportado y discrepancias de evidencia. Un PASS de exactitud exige bytes exactos y placement correcto; un PASS de política fail-closed exige estado/diagnóstico y supresión de magnitudes dependientes. Los errores de plataforma, workflow y Analyzer se distinguen y preservan.

## 6.6 Amenazas a la validez

La referencia usa reutilización local ideal que puede no ser alcanzable por `condorio`; DME no implica bytes físicamente evitables. History puede aportar reconciliación job-level sin evidencia de cada archivo; el nivel de evidencia se reporta. Workloads sintéticos favorecen control pero limitan generalización; el pool VMware de dos workers limita escala y puede sufrir interferencia. El scheduler puede incumplir placement diseñado, por lo que se verifica el real. Instrumentación adicional modificaría el execution model y su overhead, y no se introduce silenciosamente. Resultados finales, intervalos o claims comparativos deben esperar Gate V.
