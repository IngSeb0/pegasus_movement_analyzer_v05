# Variantes arquitectónicas y alcance de validación

**Línea base:** VMware con `pegasus-master`, `pegasus-worker1` y `pegasus-worker2`; Pegasus 5.1.2, `condorio`, HTCondor vanilla y transferencia administrada por job. Analyzer v1 evalúa una ejecución preservada y su placement observado. Las hipótesis de la tabla son predicciones para diseñar pruebas, no resultados. `Mobs` solo se informa con cobertura completa.

## Variantes dentro del modelo de ejecución actual

| Variante | Qué cambia | Qué permanece fijo | ¿Soportada por v1? | ¿Gate V actual? | ¿Nuevo adapter? | Hipótesis Mreq | Hipótesis Mrec/Mobs | Confusores | Costo | Prioridad |
|---|---|---|---|---|---|---|---|---|---|---|
| SAME vs BALANCED-LOCAL vs CROSS | Placement controlado | DAG, tamaños, condorio | Sí, si history y manifests completos | Sí | No | Crece con destinos worker distintos | Mrec puede permanecer constante para I/O por job fijo; Mobs requiere confirmación | Scheduling real, retries, cache | Medio | Alta |
| Tamaño 1/10/50 MiB | Payload científico | Patrón, placement | Sí | Sí | No | Escala con tamaño | Declarado escala con tamaño; observado sujeto a evidencia | Compresión, metadatos de tamaño | Medio | Alta |
| Cinco patrones oficiales | DAG y relaciones productor–consumidor | Execution model | Sí, core sin ramas por patrón | Sí | No | Cambia según dataflow y ubicación | Cambia según manifests por job | Fan-out, duplicados, outputs finales | Alto | Alta |
| Número de etapas, fan-out, fan-in y consumidores compartidos | Topología del DAG | condorio | Modelo sí; generadores/casos adicionales requieren preparación | Subconjunto priorizado | No | Cuenta una copia por ubicación distinta, no por consumidor colocalizado | Materializaciones por sandbox; Mobs condicionado a cobertura | Identidad compartida, granularidad job-level | Alto | Media |
| Distribución de jobs entre 1 y 2 workers | Recursos/placement efectivo | condorio y contrato I/O | Sí si pool anuncia ambos | Sí | No | Sensible a cambios de ubicación | Invariancia declarada solo si I/O por job no cambia | Disponibilidad de worker, política Condor | Medio | Alta |

## Cambios del modelo de ejecución — estudio futuro

| Variante | Qué cambia | Qué permanece fijo | ¿Soportada por v1? | ¿Gate V actual? | ¿Nuevo adapter? | Hipótesis Mreq | Hipótesis Mrec/Mobs | Confusores | Costo | Prioridad |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `sharedfs` | Acceso y ubicación de archivos | DAG y objetivos de medición | No | No | Sí | Definición lógica aplicable tras redefinir ubicaciones | Staging/observación cambian; no usar adapter condorio | Caché del filesystem, servidores | Alto | Futura |
| `bypass` | Ruta Pegasus/transferencia | DAG | No | No | Sí | Requiere frontera coherente | Manifests y evidencia cambian | Rutas directas y plugins | Alto | Futura |
| Plugins o storage remoto | Transporte y destino | DAG | No | No | Sí | Requiere nueva topología de ubicaciones | Fuente de evidencia y bytes distinta | Retries, protocolos, almacenamiento | Alto | Futura |
| Jobs agrupados/clustered | Mapeo tarea–job/sandbox | DAG | No | No | Sí | Puede conservar definición por archivo | Contrato por job e intentos cambia | Coalescencia de archivos | Alto | Futura |

No se infiere soporte por haber podido escribir un submit. Cualquier cambio de execution model requiere requisitos, adapter, evidencias, pruebas y protocolo propios antes de comparar DME.
