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

# Datos de la tesis vigente

La definición vigente es `condorio_coordinator_relay_v1`: incorpora el relevo obligatorio por el coordinador cuando un archivo generado se requiere en otro worker. Es una cota condicionada a la ubicación y al perfil CondorIO, no un óptimo global.

La tesis presenta 15 condiciones del bloque A, con 45 ejecuciones, y por separado nueve comparaciones con ubicación libre y un piloto GL2. El recálculo usa configuraciones documentadas y observados históricos para los 45 registros de A; los diez restantes usan desgloses nativos ya extraídos. No reaudita las 45 cápsulas completas. El archivo histórico A–H conserva su definición y sus tiempos originales.

- `derived/dme_relevo_55.csv`: tabla vigente; bytes, obligaciones, DME y procedencia.
- `derived/auditoria_relevo_55.csv`: reconstrucción mediante código separado.
- `source/relevo/configuraciones.json`: quince configuraciones documentadas.
- `validation_free_20261107/DESGLOSE_NATIVO.json`: diez desgloses extraídos y sus 40 direcciones.
- `derived/workflows_113.csv`: archivo histórico A–H, sin sustituirlo ni alterar sus tiempos.

Las entradas originales permanecen intactas. Consulte los comandos y límites en [REPRODUCIBILIDAD.md](../REPRODUCIBILIDAD.md).
