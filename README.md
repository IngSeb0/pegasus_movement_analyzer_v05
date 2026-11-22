# Evaluación del movimiento de datos en flujos científicos con Pegasus bajo CondorIO

Calcula los **bytes requeridos**, el **volumen observado** (contrato de transferencia corroborado con HTCondor) y su cociente (DME) de un flujo ejecutado con Pegasus y HTCondor (CondorIO), desglosa en qué se fue el tiempo y trae lo necesario para producir esas corridas.

| Carpeta | Archivo de código | Guía |
|---|---|---|
| `analyzer/` | `analyzer.py` (114 líneas): DME de una corrida y control de reintentos y transferencias incompletas; `tiempos.py` (57 líneas): desglose de tiempos | `COMO_FUNCIONA.md` |
| `coordinador/` | `llevar.py` (29 líneas): sube, ejecuta y baja por SSH | `COMO_FUNCIONA.md` |
| `flujos/` | `crear_flujo.py`, `ejecutar_flujo.py`, `tarea.py`, `fma_kernel.c`; Montage: `montage.py`, `tarea_montage.py` | `COMO_FUNCIONA.md` |

`flujos/especificaciones.json` define las 13 condiciones sintéticas (cinco patrones con 2 y 4 workers, más tres de contraste), con archivos de 200 MiB. Las de Montage (147 fotos, `MG-BASE` y `MG-FINAL`) las escribe `flujos/montage.py`.

## Uso

```
python coordinador/llevar.py subir flujos analyzer
python coordinador/llevar.py correr "python3 flujos/crear_flujo.py flujos/especificaciones.json DISTRIBUTION-W2 caso1"
python coordinador/llevar.py correr "python3 flujos/ejecutar_flujo.py caso1"
python coordinador/llevar.py correr "python3 analyzer/analyzer.py RUTA_run0001 caso1/history.long -v"
```

Si ya tienes una corrida:

```
python analyzer/analyzer.py CARPETA_run0001 history.long -v     # bytes y DME
python analyzer/tiempos.py  CARPETA_run0001 history.long        # dónde se fue el tiempo
```

Solo necesitan Python y PyYAML.

## Requisitos

- **Analyzer:** Python 3 y `pyyaml`.
- **Coordinador:** Pegasus 5.1.2, HTCondor 26.0.1, `pegasus-wms.api`, `pyyaml` y `gcc`.

## Qué se comprobó

- `analyzer.py` da los mismos bytes requeridos y el mismo volumen observado que el Analyzer completo en las 30 corridas de 200 MiB y en 2 corridas de ejemplo (32 de 32). Se niega a calcular, y dice qué job falla, cuando hay reintentos, jobs incompletos o transferencias que no cuadran con el contrato (probado con 4 casos fabricados).
- `tiempos.py` reproduce los seis tramos de tiempo medidos de las 30 corridas (30 de 30).
- La tesis exige además residuo cero al byte; esta versión comprueba el número exacto de archivos y que los bytes científicos estén cubiertos, pero no conoce el tamaño de los archivos auxiliares.
- `crear_flujo.py` genera un `workflow.yml` con los mismos jobs, argumentos, archivos y requisitos que los de las corridas reales.
- Montage: `montage.py` y `crear_flujo.py` se probaron con fotos sintéticas (flujo completo en local); la descarga desde IRSA no se pudo probar desde aquí.
- No se ejecutó `pegasus-plan` sobre esos `workflow.yml` fuera del coordinador.

## Relación con los experimentos

Las 30 corridas de la tesis se hicieron con scripts más largos (control de tiempo y disco, hashes, auditoría independiente), conservados junto con su evidencia en `intensivo_20261122_resultados.zip`. Este repositorio es la versión corta de lo mismo: calcula igual, pero no incluye esas protecciones ni el cierre al byte del Analyzer completo.
