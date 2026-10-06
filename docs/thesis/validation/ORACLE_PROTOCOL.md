# Protocolo de oráculos independientes

1. Congelar DAG, archivos científicos, tamaños exactos en bytes, parámetros y placement diseñado. Guardar su manifest y hashes antes de lanzar la corrida.
2. Dibujar para cada archivo el origen y el conjunto de ubicaciones que lo requieren; deduplicar consumers en la misma ubicación. Sumar `Mreq_manual = Σ_f Size(f)·|RequiredLocations(f) ∖ {Origin(f)}|`.
3. A partir del contrato `condorio` de cada job, listar entradas y salidas científicas por dirección y ocurrencia. Sumar `Mrec_manual`; un manifest por sí solo no confirma transferencia.
4. Ejecutar y preservar el run solo cuando el pool esté listo y la campaña autorizada. Extraer history con el alcance del run, registrar hashes y mapear placement observado. Si difiere del diseñado, no declarar PASS para la condición prevista; recalcular la referencia sobre el placement observado y conservar el diagnóstico.
5. Evaluar por job, dirección e intento la completitud de manifest, éxito, worker, protocolo, conteos y bytes. Etiquetar evidencia `FILE_LEVEL_CONFIRMED`, `JOB_LEVEL_RECONCILED` o `INSUFFICIENT`, y modo `EXACT_BYTES` o `SUCCESSFUL_MANIFEST` cuando corresponda. No repartir bytes agregados entre archivos.
6. `Coverage = |C_sci|/|D_sci|` (`1` si `D_sci` está vacío). `ByteCoverage` es diagnóstico. Con `Coverage < 1`, `Mobs=N/A` y `DME=N/A`; ausencia de evidencia nunca vale cero.
7. Con cobertura completa, sumar tamaños de ocurrencias científicas confirmadas. Si `Mobs < Mreq`, marcar inconsistencia; si ambos son cero, DME es no aplicable; si `Mreq=0<Mobs`, DME=0; en los demás casos `DME=Mreq/Mobs`.
8. Comparar los oráculos de `Mreq` y `Mrec` con Analyzer en bytes exactos, sin tolerancia porcentual. Examinar cada desacuerdo con `analysis.json`, TSV y provenance antes de asignar causa. Los casos de retries, datos faltantes, tamaños en conflicto y protocolos no soportados deben comprobar que la herramienta falla cerrado.

Los oráculos históricos v0.5 de `Mrec` pueden orientar predicciones bajo el mismo contrato de I/O; no se convierten en observaciones v1. `Mobs` de los cinco runs preservados es una salida reconciliada de Analyzer, no un oráculo manual independiente ni medida packet-level.
