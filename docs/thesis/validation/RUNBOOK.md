# Runbook read-only de preparación y protocolo futuro Gate V

## Antes de cualquier nuevo workflow

En `pegasus-master`, registrar `date -Is`, `git rev-parse HEAD`, `git status --short`, `pegasus-version`, `condor_version`, `condor_status -startd -af Name Machine State Activity Cpus Memory`, `condor_status -schedd -af Name Machine` y el snapshot de `../environment/ENVIRONMENT_SNAPSHOT.md`. Estos comandos consultan estado; no inician jobs. Confirmar que ambos workers esperados anuncien slots compatibles. Comparar IP/hostname reales con `/etc/hosts` sin asumir que el nombre resuelve disponibilidad.

## Para cada fila, cuando se autorice la campaña

1. Crear un identificador único de caso y guardar configuración de patrón, placement, tamaño, repetición, parámetros, oráculo y versiones. El runner I14 debe rechazar colisiones de rutas y preservar el primer resultado.
2. Ejecutar el workflow con el generador y comando exactos registrados por I14. Guardar stdout/stderr, DAG, submits, `.meta`, workflow, run dir e identificadores Pegasus/Condor.
3. Extraer history acotado al run y guardar el comando de extracción y su hash. No mezclar jobs ajenos.
4. Invocar `python3 tools/analyze_run_v1.py --run <run_path> --history-file <history_path> --out <output_path>` con el commit fijado. Preservar `analysis.json`, `summary.tsv`, las tablas de archivos/movimientos/evidencia y `REPORT.txt`, código de salida y hashes.
5. Comparar placement diseñado/observado, oráculos de bytes, Coverage, estado, diagnósticos y DME aplicable. Registrar `PASS`, `FAIL` o `INDETERMINATE` con razón y sin sobrescribir evidencia fuente.
6. Reanudar solo casos sin producto íntegro; no borrar un run para repetirlo. Cada repetición usa un directorio nuevo.

## Manejo de fallos

Pool sin startd, job fallido o placement distinto: preservar artefactos y detener la condición afectada. Evidencia incompleta: `Mobs` y DME no aplicables según reglas del Analyzer; investigar fuente, no imputar cero. Configuración no soportada: registrar `UNSUPPORTED` y tratarla fuera de la matriz v1. Error de herramienta: registrar traceback/código y no reetiquetar como fallo experimental del workflow.

**Estado actual:** este documento es un protocolo, no un registro de ejecución Gate V. Los workers no estaban disponibles en la captura del 3/10/2026 y no se lanzó campaña nueva.
