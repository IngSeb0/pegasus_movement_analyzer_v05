# Piloto propuesto para presupuestar Gate V

**Estado:** plan, `NOT_RUN`. El piloto requiere workers `startd` visibles, oráculos completos y autorización específica para lanzar nuevos workflows. No es un permiso para ejecutar la campaña de 129 runs.

## Selección mínima de casos

Las tres filas pertenecen a `experiment_cases_proposed.csv`. Si I14, entorno y protocolo permanecen idénticos tras el piloto, pueden contar como sus repeticiones `r1` dentro de los 129. Si el protocolo cambia, se preservan como piloto aparte y se repiten con nuevos IDs, sin sobrescribirlos.

| Case ID | Motivo | Condición previa |
|---|---|---|
| `B-process-same-w1-10MiB-r1` | Ruta mínima de entrada/salida científica | worker1 anunciado y placement verificable |
| `B-pipeline-balanced-local-10MiB-r1` | Dependencias intermedias y dos workers | worker1 y worker2 anunciados |
| `B-redistribution-cross-10MiB-r1` | Mayor multiplicidad de archivos/sandbox dentro de los patrones base | dos workers anunciados y oráculo manual final |

Las predicciones históricas del Validation Plan sirven para detectar anomalías preliminares; antes de cada run se debe reconstruir el oráculo en bytes a partir del DAG y los archivos que el generador vaya a producir. No se copian valores de la implementación v0.5 como resultado observado de v1.

## Captura por caso

1. Guardar `case_id`, `run_id` real, timestamps de inicio/fin, commit Analyzer, versión del generador, Pegasus, HTCondor, snapshot de master/workers y `condor_status`.
2. Guardar parámetros, oráculo de `Mreq`, oráculo de `Mrec`, placement diseñado, ruta del run, ruta history filtrada, salida Analyzer y hashes de fuentes.
3. Medir duración del workflow desde envío hasta finalización y duración del análisis v1 por separado. Registrar unidades en segundos y distinguir espera de cola del tiempo de ejecución. No interpretar esas duraciones como DME.
4. Medir bytes de disco por run, history y reportes con `du -sb` sobre **sus rutas nuevas**, sin tocar runs previos; registrar espacio libre antes/después con `df -B1`.
5. Capturar uso de memoria y CPU de Analyzer con herramienta ya disponible, si existe; si no, marcarlo pendiente. No instalar instrumentación ni alterar el pool durante el piloto.
6. Validar placement, estado del workflow, oráculos de bytes, Coverage, nivel de evidencia, diagnósticos y DME aplicable. Un fallo se conserva, se analiza y no se reemplaza silenciosamente.

## Presupuesto de la campaña

Con mediciones reales, construir una tabla por patrón, placement y tamaño con tiempo y espacio esperado. El tamaño del payload científico **no** es el tamaño del run completo: también se preservan logs, DAG, history, outputs y reportes. Reportar la regla de extrapolación y un margen de reserva explícito antes de pedir autorización para la campaña larga. Si tres casos no representan adecuadamente los 129, ampliar el piloto mediante una decisión nueva y documentada. Ninguna estimación numérica se asigna antes de medir.

## Parada y recuperación

Si falta un `startd`, el placement no coincide, falla un job, falta history o Analyzer devuelve estado no válido, detener el piloto afectado y conservar todo. Reanudar con `case_id` nuevo y vínculo al anterior; no borrar ni sobrescribir artefactos. El script histórico `run_controlled_case.sh` llama a Analyzer v0.5.1 y no debe usarse para este piloto. I14 deberá invocar `tools/analyze_run_v1.py` y escribir un manifest del caso antes del envío.
