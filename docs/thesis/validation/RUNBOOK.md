# Runbook read-only de preparación y protocolo futuro Gate V

## Antes de cualquier nuevo workflow

En `pegasus-master`, registrar `date -Is`, `git rev-parse HEAD`, `git status --short`, `pegasus-version`, `condor_version`, `condor_status -startd -af Name Machine State Activity Cpus Memory`, `condor_status -schedd -af Name Machine` y el snapshot de `../environment/ENVIRONMENT_SNAPSHOT.md`. Estos comandos son de solo lectura y no inician jobs. La captura actual (2026-10-04 03:30:13 -05:00) mostró un slot en cada worker. La verificación de ClassAds/slots se hace desde el master; no requiere SSH directo a los workers. Repetirla justo antes de una campaña y comparar nombre/IP anunciados con el snapshot.

## Para cada fila, cuando se autorice la campaña

1. Crear un identificador único de caso y guardar configuración de patrón, placement, tamaño, repetición, parámetros, oráculo y versiones. El runner I14 debe rechazar colisiones de rutas y preservar el primer resultado.
2. Ejecutar el workflow con el generador y comando exactos registrados por I14. Guardar stdout/stderr, DAG, submits, `.meta`, workflow, run dir e identificadores Pegasus/Condor.
3. Extraer history acotado al run y guardar el comando de extracción y su hash. No mezclar jobs ajenos.
4. Invocar `python3 tools/analyze_run_v1.py --run <run_path> --history-file <history_path> --out <output_path>` con el commit fijado. Preservar `analysis.json`, `summary.tsv`, las tablas de archivos/movimientos/evidencia y `REPORT.txt`, código de salida y hashes.
5. Comparar placement diseñado/observado, oráculos de bytes, Coverage, estado, diagnósticos y DME aplicable. Registrar `PASS`, `FAIL` o `INDETERMINATE` con razón y sin sobrescribir evidencia fuente.
6. Reanudar solo casos sin producto íntegro; no borrar un run para repetirlo. Cada repetición usa un directorio nuevo.

## Manejo de fallos

Pool sin startd, job fallido o placement distinto: preservar artefactos y detener la condición afectada. Evidencia incompleta: `Mobs` y DME no aplicables según reglas del Analyzer; investigar fuente, no imputar cero. Configuración no soportada: registrar `UNSUPPORTED` y tratarla fuera de la matriz v1. Error de herramienta: registrar traceback/código y no reetiquetar como fallo experimental del workflow.

**Estado actual:** este documento es un protocolo, no un registro de ejecución Gate V. Ningún workflow nuevo se ha ejecutado en este checkpoint. El protocolo futuro debe cumplir los criterios de la propuesta oficial; la matriz de 129 filas es una opción interna, no una cantidad oficial obligatoria. Cualquier ejecución requiere que se acuerde el protocolo y su alcance.
