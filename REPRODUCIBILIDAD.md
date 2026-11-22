## Entrega vigente: validación completa del 8 de noviembre de 2026

La tesis vigente es `thesis/Tesis_DME_Validacion_Completa_20261108.pdf`: 41 páginas físicas y 39 antes de referencias. Centra la contribución en DME, su referencia por ubicación/relevo y los mecanismos de agrupación. Las fuentes están en `thesis/source/`.

La campaña prospectiva completó exactamente la matriz original: 63 principales en doce condiciones (n=6 sintéticas, n=3 Montage), 12 pilotos válidos separados y un fallo técnico CRLF preservado sin DME. Total: 76 intentos y 75 observaciones evaluables. Se completó el orden programado en tres sesiones, con sus pausas documentadas. Las 312 direcciones principales y 368 contando pilotos conciliaron exactamente. Los finales sintéticos coinciden por SHA256; en Montage coinciden dimensiones, máscaras y píxeles (diferencia máxima cero).

`python analysis/prospective_20261108/rebuild.py` recalcula desde registros extraídos en `data/prospective_20261108/`. Es reproducción de datos procesados, no reextracción nativa autosuficiente: requiere cápsulas y paquetes estáticos compartidos para repetir la auditoría completa. `CAPSULES.json` identifica esos archivos y exclusiones por hash. `verify_equivalence.py` requiere además los archivos científicos conservados.

La evidencia histórica de A (45 detalladas), las nueve comparaciones libres más un piloto y las cuatro ejecuciones históricas de Montage siguen separadas. La reextracción histórica de las 45 cápsulas administrativas usa manifiesto exitoso; no se presenta como conciliación exacta nueva. El costo nativo de captura sigue sin aislarse: OE4 conserva ese límite.

Tres sesiones cerradas dentro de sus límites, cinco VMs desasignadas y SSH restaurado; sin commit, push ni cambio de visibilidad. Depósito privado y licencias de redistribución pendientes. Las notas de versiones anteriores siguientes son históricas y quedan supersedidas por esta entrega.

## Actualización del 8 de noviembre de 2026

La tesis vigente es `thesis/Tesis_DME_Metrica_Redaccion_20261108.pdf`: 41 páginas físicas y 39 antes de referencias. Se refuerza la interpretación de DME y agrupación; se corrigen los signos de interrogación en las fuentes mediante comandos explícitos de LaTeX. La corrección anterior de ToUnicode no reparaba el signo visible.

`python analysis/rebuild_montage_relay.py` comprueba cuatro ejecuciones preservadas (piloto y tres repeticiones) desde `data/validation_montage_20261108/`. Con relevo: requerido=observado=3375611 B, DME=1 y seis obligaciones/entregas. El recálculo inicial cotejó fuentes nativas y ubicación; el comando portable usa el desglose extraído. No ejecuta Montage ni reextrae las cápsulas.

`data/validation_native_20261107/` conserva la reextracción de 45 cápsulas administrativas: 45 VALID y acuerdo de volúmenes/cobertura con reconstrucción separada. Sus 348 direcciones se corroboraron por SUCCESSFUL_MANIFEST en copias sin contenido científico ni paquetes auxiliares; no es una nueva conciliación exacta de auxiliares. Para repetirla hacen falta las cápsulas del archivo de investigación.

La campaña prospectiva de agrupación sigue preparada, sin ejecutar. La medición de captura nativa de OE4 sigue parcial. No hubo nuevos workflows, cloud, commit/push ni cambio de visibilidad.

# Reproducir la entrega corregida

La definición vigente es `condorio_coordinator_relay_v1`: incorpora el relevo obligatorio por el coordinador cuando un archivo generado se requiere en otro worker. Es una cota condicionada a la ubicación y al perfil CondorIO, no un óptimo global.

La tesis presenta 15 condiciones del bloque A, con 45 ejecuciones, y por separado nueve comparaciones con ubicación libre y un piloto GL2. El recálculo usa configuraciones documentadas y observados históricos para los 45 registros de A; los diez restantes usan desgloses nativos ya extraídos. No reaudita las 45 cápsulas completas. El archivo histórico A–H conserva su definición y sus tiempos originales.

## Requisitos

Python 3.12 y PyYAML. `requirements-repro.txt` fija PyYAML 6.0.3; las comprobaciones locales utilizan Python 3.12.5/PyYAML 6.0.2 ya instalados. No se probó instalar dependencias desde una máquina limpia. No se requiere acceso cloud.

Desde la raíz del paquete, en PowerShell:

```powershell
python tools/verify_snapshot.py
python analysis/rebuild_relay_dataset.py
python analysis/audit_relay.py
python -m unittest discover -s tests -v
$env:PEGASUS_EXPERIMENTS_ROOT = (Resolve-Path 'fixtures/audited/runs').Path
$env:PEGASUS_RUN_INTEGRATION = '1'
python -m unittest tests.integration.test_preserved_runs -v
```

El recálculo produce `data/derived/dme_relevo_55.csv`; el auditor produce `data/derived/auditoria_relevo_55.csv` y `reproducibility/AUDITORIA_RELEVO.json`. Ambos coinciden en bytes, obligaciones y DME de los 55 registros. En los diez desgloses, el auditor también comprueba cobertura por archivo/destino, identidad de entregas, sumas científicas y auxiliares, residuo cero y conteos de 40 direcciones. No vuelve a extraer logs ni payloads nativos.

La suite contabiliza 170 pruebas: 169 satisfactorias y una integración omitida por defecto. La integración explícita es una prueba con cinco workflows portables: procesamiento de 50 MiB y pipelines de 50 MiB repartido, 10 MiB local, 10 MiB repartido y 10 MiB cruzado. Los pares requerido/observado son 100/100, 200/300, 20/60, 40/60 y 60/60 MiB. Usan corroboración por manifiesto exitoso; no sustituyen la conciliación exacta de A.

Ejemplo de CLI:

```powershell
python tools/analyze_run_v1.py --run fixtures/audited/runs/process-same-w1-20260917-232331/luis/pegasus/dm-process/run0001 --history-file fixtures/audited/history/process_50mib.long --out results/reproduccion-process
```

Resultado del control: VALID, 104857600 bytes requeridos y observados, DME=1.

## Archivo histórico

`analysis/rebuild_dataset.py` reconstruye los 113 registros A–H. `analysis/rebuild_free_validation.py` conserva la referencia anterior del contraste libre. Sus resultados no sustituyen el CSV de 55 registros con relevo. Las 27 ejecuciones de las nueve condiciones no detalladas de A no se presentan como recalculadas en esta tesis.

Los tiempos de Analyzer conservados corresponden al ejecutable de campaña, antes de incorporar el relevo. No son una medición del rendimiento del código actual ni del costo de captura nativa. OE4 sigue parcial.

## Integridad y límites

`tools/verify_snapshot.py` coteja el manifiesto y `ACTIVE_CORE_REFERENCE.json`. Verifica identidad de archivos, no correctitud científica. No regenere el manifiesto para ocultar una discrepancia: `tools/update_manifest.py` es una herramienta de mantenimiento para cambios deliberados.

Las cápsulas completas están fuera del paquete compacto. Reauditar todas las ejecuciones exige ese archivo de investigación. No se reconstruyó la infraestructura ni se ejecutaron nuevos workflows. La compilación TeX se comprobó localmente con Tectonic y recursos en caché; no desde una máquina limpia.
