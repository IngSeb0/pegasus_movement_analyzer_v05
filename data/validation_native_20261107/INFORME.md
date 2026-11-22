# Reextracción local de las 45 ejecuciones del bloque A

## Resultado

Se localizaron las 45 cápsulas compactas seleccionadas, verificadas contra sus 45 recibos SHA-256 de cierre. Se cotejaron 870 referencias a fuentes nativas y metadatos contra sus hashes archivados. Las referencias pueden repetir un mismo archivo; no son 870 archivos únicos.

Las copias administrativas extraídas permiten ejecutar el Analyzer vigente: 45 estados VALID, sin diagnósticos, con requerido y observado idénticos a los 45 registros vigentes. Un oráculo separado vuelve a leer workflow.yml, submits, listas nativas de grupos, history.json y metadatos; reconstruye ubicaciones, productores, consumidores, finales, obligaciones con relevo, entregas por contrato y cobertura por identidad/destino. Los 45 cálculos coinciden con el CSV vigente, incluidos los conteos de obligaciones. El oráculo no importa los parsers de Analyzer ni toma los volúmenes del INDEPENDENT_AUDIT histórico.

El script importa Analyzer solo para la comparación con la implementación vigente. El cálculo separado está identificado en el mismo script y utiliza sus propios parsers.

## Frontera de esta comprobación

No se extrajeron los payloads científicos ni los bundles auxiliares. Las 348 direcciones del nuevo análisis de las copias administrativas usan SUCCESSFUL_MANIFEST. Por ello, no se afirma una nueva conciliación independiente exacta de los bytes auxiliares, ni una nueva verificación del contenido de todos los archivos científicos. Tampoco se ejecutaron workflows.

EvidenceLevel.JOB_LEVEL_RECONCILED aparece también en el modo SUCCESSFUL_MANIFEST por diseño de reconciliation.py. No debe interpretarse como EXACT_BYTES: el campo reconciliation_mode es el que distingue ambos procedimientos y el residuo de SUCCESSFUL_MANIFEST es indeterminado. El cambio de modo al analizar una copia administrativa incompleta no es una discrepancia numérica ni justifica reparar fuentes para obtener otro estado.

Se supera el límite anterior de reconstruir estos 45 casos únicamente desde configuraciones documentadas y observados derivados: ahora se reextraen grafo, ubicación, tamaños y contratos de las fuentes nativas archivadas. Permanece pendiente la reauditoría independiente de conciliación exacta y contenido científico. Las cápsulas originales siguen fuera del paquete compacto y no se modificaron.

## Reproducción y evidencia

Desde la raíz de THESIS:

```powershell
python validacion_mejorada_20261107/reauditoria/inventario_y_reextraccion.py
```

Requiere Python, PyYAML, vm_repo y las cápsulas locales de continuacion_cloud_20261026_noche, continuacion_cloud_20261027_reintento y continuacion_cloud_20261028_cierre. Se limita cada archivo descomprimido en memoria a menos de 512 MiB; las copias administrativas producidas suman aproximadamente 46 MB.

- RESULTADOS.json: cápsula y hash, identidad, fuentes cotejadas, diagnósticos, métricas Analyzer, modo de corroboración y cálculo separado por ejecución.
- RESUMEN.json: conteos globales y límites.
- COMPARACION_45.csv: tabla por ejecución de requerido/observado en bytes del Analyzer y del oráculo, obligaciones, entregas, cobertura y coincidencia con el CSV vigente.
- copias/: fuentes administrativas extraídas sin reemplazar rutas ni corregir contenidos originales; las rutas absolutas de campaña se conservan como evidencia.

No se modificó vm_repo, tesis, cápsulas ni fuentes originales; no hubo conexión cloud, encendido de VMs, SSH, commit ni push.
