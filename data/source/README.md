# Procedencia de los datos procesados

Estos archivos se copiaron sin transformar de los cierres de investigación fechados entre el 30 de octubre y el 2 de noviembre de 2026. Las rutas originales se indican como procedencia, no como requisitos para ejecutar la reconstrucción.

| Archivo local | Fuente preservada | Uso |
| --- | --- | --- |
| `A/TIEMPOS_INDIVIDUALES.csv` | `mejoras_evaluacion_20261030/TIEMPOS_INDIVIDUALES.csv` | Métricas y duraciones de las 78 filas históricas; la selección final conserva 72 UUID elegibles. |
| `A/INDICE_EVIDENCIA_TESIS.json` | `retiro_common_files_20261031/datos/INDICE_EVIDENCIA_TESIS.json` | Selección verificable de las 24 condiciones y 72 workflows elegibles. |
| `BD/COMPLEMENTARIOS_INDIVIDUALES.csv` | `retiro_common_files_20261031/datos/COMPLEMENTARIOS_INDIVIDUALES.csv` | Contrastes temporal, costo operacional y ubicación libre. |
| `E/RESULTADOS_INTENSIDAD.json` | `mejoras_evaluacion_20261030/analisis_intensidad/RESULTADOS_INTENSIDAD.json` | Cinco casos de caracterización de intensidad. |
| `E/DESGLOSE_TEMPORAL_E.json` | `revision_observaciones_20261102/datos/DESGLOSE_TEMPORAL_E.json` | Partición temporal de los cinco casos E. |
| `E/COSTO_VERIFICADO.json` | `revision_observaciones_20261102/datos/COSTO_VERIFICADO.json` | Verificación de los tres pares de costo posterior del protocolo. |
| `FH/ACCEPTED_RESULTS_SESSION_FINAL_18.json` | `pruebas_cierre_sin_cf_20261031/new_evidence/ACCEPTED_RESULTS_SESSION_FINAL_18.json` | Casos de escala, subworkflow Montage y observación de receptor. |
| `FH/COST_RESULTS_SESSION_FINAL_18.json` | `pruebas_cierre_sin_cf_20261031/new_evidence/COST_RESULTS_SESSION_FINAL_18.json` | Resumen complementario del bloque de costo. |

Los datos fuente conservan sus valores y campos originales. El script crea una tabla derivada, sin modificar estos archivos.
