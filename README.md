# Analyzer

Calcula el volumen requerido y el observado en bytes para una ejecución de Pegasus con CondorIO.
DME divide el requerido entre el observado. El exceso es la diferencia entre el observado y el requerido.
El informe incluye un desglose por archivo y máquina.

**Entrada.** Directorio de la corrida de Pegasus e historial exportado de HTCondor.
**Salida.** Informe de texto, JSON y tablas TSV para consultar el cálculo y sus diagnósticos.

```powershell
python tools/analyze_run_v1.py --run fixtures/audited/runs/process-same-w1-20260917-232331/luis/pegasus/dm-process/run0001 --history-file fixtures/audited/history/process_50mib.long --out results/demo
```

Salida esperada del ejemplo: estado `VALID`, requerido y observado de 104 857 600 B cada uno, DME 1, exceso 0 B.

## Mapa del código

| Archivo | Función y quién lo usa |
|---|---|
| `tools/analyze_run_v1.py` | Lee los argumentos y llama al núcleo y al generador de informes. |
| `analyzer_v1.py` | Coordina el análisis llamado por la CLI. |
| `analyzer.py` | Expone la interfaz anterior para sus consumidores existentes. |
| `pegasus_source.py` | Lee el plan de Pegasus para el análisis. |
| `htcondor_source.py` | Lee el historial de HTCondor para el análisis. |
| `normalize.py` | Normaliza datos de Pegasus y HTCondor para el análisis. |
| `execution_model.py` | Construye el modelo de ejecución para el análisis. |
| `grouping.py` | Reconstruye tareas agrupadas para el modelo de ejecución. |
| `dataflow.py` | Representa los archivos científicos y sus dependencias para el análisis. |
| `condorio_adapter.py` | Adapta la información CondorIO para el análisis. |
| `movement.py` | Construye los registros de movimiento para el cálculo. |
| `reconciliation.py` | Concilia registros y manifiestos para el análisis. |
| `metrics.py` | Calcula volúmenes y DME a partir de los registros de movimiento. |
| `model.py` | Define los registros que comparten los módulos. |
| `diagnostics.py` | Define estados y razones que usan el núcleo y el informe. |
| `reporting.py` | Escribe los informes que solicita la CLI. |
| `__init__.py` | Identifica el paquete importado por la CLI y los scripts. |

Ejecuta después del flujo. El perfil de medición es CondorIO. Entorno de las campañas recientes: Pegasus 5.1.2 y HTCondor 26.0.1. El ejemplo funciona con Python 3.12 y PyYAML. Consulta [reproducción](REPRODUCIBILIDAD.md) e [historial](HISTORIAL.md).
