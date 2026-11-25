# Cambios

Se añadió un lanzador de descarga desde el coordinador con MontagePy 2.3.0 y huellas SHA-256 para las entradas descargadas. El primer paso llamó a mArchiveList sobre el endpoint legado y agotó el tiempo de espera. Se consultó por separado el catálogo oficial SIA de IRSA como prueba de disponibilidad. La consulta alternativa circular quedó fuera de la campaña. La red no se modificó.
# Continuación por SIA · 22 de noviembre de 2026

- Consulta oficial de IRSA desde `dme-master`. Se conserva el VOTable completo y la selección cuadrada de 147 centros, sin modificar el área de selección.
- Los enlaces de IRSA devuelven FITS comprimidos. Se descomprimen y se verifican los SHA-256 del FITS entregado a las tareas. El límite por imagen es de tres intentos en total, la solicitud inicial más dos reintentos de curl.
- `mImgtbl` indexó las 147 imágenes sin errores de FITS ni de coordenadas; `mMakeHdr` generó la cabecera TAN de 7 536 × 8 104 píxeles. El mosaico cubre las huellas completas de las imágenes escogidas por centro.
- El diseño conserva las ubicaciones y las operaciones del protocolo. Reparte las reproyecciones entre W2, W3 y W4 y compara en W1 dos jobs separados con un job que contiene ambas tareas finales.
