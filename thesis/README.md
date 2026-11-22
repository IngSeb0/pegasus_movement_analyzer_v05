# Tesis vigente

## Entrega vigente: validación completa del 8 de noviembre de 2026

La tesis vigente es `thesis/Tesis_DME_Validacion_Completa_20261108.pdf`: 41 páginas físicas y 39 antes de referencias. Centra la contribución en DME, su referencia por ubicación/relevo y los mecanismos de agrupación. Las fuentes están en `thesis/source/`.

La campaña prospectiva completó exactamente la matriz original: 63 principales en doce condiciones (n=6 sintéticas, n=3 Montage), 12 pilotos válidos separados y un fallo técnico CRLF preservado sin DME. Total: 76 intentos y 75 observaciones evaluables. Se completó el orden programado en tres sesiones, con sus pausas documentadas. Las 312 direcciones principales y 368 contando pilotos conciliaron exactamente. Los finales sintéticos coinciden por SHA256; en Montage coinciden dimensiones, máscaras y píxeles (diferencia máxima cero).

`python analysis/prospective_20261108/rebuild.py` recalcula desde registros extraídos en `data/prospective_20261108/`. Es reproducción de datos procesados, no reextracción nativa autosuficiente: requiere cápsulas y paquetes estáticos compartidos para repetir la auditoría completa. `CAPSULES.json` identifica esos archivos y exclusiones por hash. `verify_equivalence.py` requiere además los archivos científicos conservados.

La evidencia histórica de A (45 detalladas), las nueve comparaciones libres más un piloto y las cuatro ejecuciones históricas de Montage siguen separadas. La reextracción histórica de las 45 cápsulas administrativas usa manifiesto exitoso; no se presenta como conciliación exacta nueva. El costo nativo de captura sigue sin aislarse: OE4 conserva ese límite.

Tres sesiones cerradas dentro de sus límites, cinco VMs desasignadas y SSH restaurado; sin commit, push ni cambio de visibilidad. Depósito privado y licencias de redistribución pendientes. Las notas de versiones anteriores siguientes son históricas y quedan supersedidas por esta entrega.

