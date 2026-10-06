# Auditoría breve de la frontera de medición

**Proyecto:** Data Movement Assessment in Scientific Workflows  
**Corte de validación:** Gate V, ejecutado sobre Analyzer v1 en `feat/analyzer-v1`  
**Propósito:** dejar claro qué calcula el Analyzer y qué permite afirmar la evidencia.

## Pregunta de investigación

Dado un workflow y el placement real de sus tareas, ¿cuánto movimiento de datos exigen sus dependencias entre ubicaciones y cuánto movimiento produce realmente el mecanismo de ejecución?

La pregunta es clara y pertinente para comparar placements. En el documento oral, “lo que produce” se interpreta como el volumen de archivos que la ejecución declara y cuya transferencia puede confirmarse con evidencia de HTCondor a nivel de job. No significa bytes físicos capturados en la red.

## Qué calcula Analyzer v1

| Cantidad | Qué representa | Fuente | Regla principal |
|---|---|---|---|
| `M_req` — RequiredMovement | Bytes lógicos necesarios para que las dependencias científicas estén disponibles en las ubicaciones requeridas por el DAG y el placement observado. | DAG, archivos científicos, tamaños autoritativos y ubicación de las tareas. | Para cada archivo cuenta destinos nuevos distintos donde se necesita; reutilizarlo en tareas del mismo worker no vuelve a contar ese destino. |
| `M_rec` — DeclaredMovement | Payload científico que Pegasus/HTCondor declaran transferir en las ocurrencias de los manifiestos efectivos de los jobs. | Atributos efectivos de submit y manifiestos de transferencia por job. | Suma tamaños por ocurrencia declarada; declarar un archivo no prueba por sí solo que se transfirió. |
| `Coverage` | Fracción de ocurrencias científicas declaradas que se pudieron reconciliar con evidencia de transferencia. | `D_sci` — ocurrencias declaradas; `C_sci` — ocurrencias confirmadas. | `Coverage = |C_sci| / |D_sci|`. Cuando `D_sci` está vacío, la implementación usa la convención documentada de cobertura completa. |
| `M_obs` — ObservedMovement | Tamaño del payload científico de las ocurrencias de manifiesto confirmadas por la reconciliación. | Tamaños de archivo del manifiesto más estadísticas de transferencia de HTCondor por job. | Solo se informa con cobertura completa. El historial confirma a nivel de job, no identifica el payload en paquetes individuales. |
| `DME` | Razón `M_req / M_obs`. | Resultados anteriores, si cumplen sus precondiciones. | Solo se informa con cobertura completa, denominador válido y consistencia `M_obs ≥ M_req`. No es una métrica de rapidez. |

## Evidencia concreta para `M_obs`

La reconciliación combina el manifiesto científico efectivo de cada job con el historial exportado de HTCondor. Verifica dirección y método de transferencia, estado exitoso del job, worker, completitud del manifiesto, separabilidad del intento y consistencia de conteos y bytes. Entre los atributos usados están las estadísticas de entrada/salida de transferencia de ClassAds, por ejemplo `TransferInputStats` y `TransferOutputStats`, y campos de tamaño y cantidad de archivos del método de transferencia.

Después de reconciliar el job, `M_obs` suma los tamaños de las ocurrencias científicas del manifiesto. Por eso, `M_obs` es un volumen de payload científico declarado y confirmado a nivel de job. No es una suma de paquetes observados, tráfico total de interfaz, bytes de disco ni una medición por archivo en la red. `BytesSent` y `BytesRecvd` no se tratan como si fueran payload científico por archivo.

## ¿Comparten la misma frontera `M_req` y `M_obs`?

Comparten el mismo workflow/run, alcance de archivos científicos y unidad de volumen. **No comparten la misma regla de conteo ni la misma frontera de evento.** `M_req` cuenta ubicaciones de destino distintas requeridas por el modelo lógico; `M_obs` suma ocurrencias científicas declaradas por job que se reconciliaron con estadísticas agregadas de HTCondor.

En consecuencia, la DME es una comparación operacional entre esas cantidades bajo las definiciones de Analyzer v1. No es una identidad de conservación de bytes, no demuestra que `M_obs - M_req` sea desperdicio y no identifica bytes evitables. Un valor bajo indica que el requerimiento lógico calculado es menor en relación con el payload de manifiesto confirmado en esa ejecución; no prueba por sí solo una oportunidad de optimización.

## Qué se validó

- Gate V cubrió cinco patrones, diez condiciones y 31 workflows independientes, con al menos tres réplicas por condición.
- Las 31 ejecuciones fueron válidas; el placement observado coincidió con el planeado y `Coverage = 1`.
- Los oráculos manuales independientes coincidieron con `M_req` y `M_rec`; el análisis fue determinista en los casos evaluados.
- En el ejemplo de pipeline de tres tareas, cada una de las seis ocurrencias científicas pesa 10 MiB. El historial confirma las seis: `M_obs = 60 MiB`. Para tareas en un mismo worker, `M_req = 20 MiB` y `DME = 0.33`; para el placement repartido ensayado, `M_req = 40 MiB` y `DME = 0.67`.

Estos resultados respaldan el cálculo y la comparación dentro de la matriz ensayada. No validan toda arquitectura, todo método de transferencia ni placements con más de dos workers.

## Capas que no deben mezclarse

La evidencia disponible describe archivos, manifiestos, ubicaciones de tareas e historial de jobs. No mide tráfico físico de red, ancho de banda, I/O físico de disco, RAM, NUMA, FLOPs, uso de CPU/GPU ni el tiempo de ejecución del workflow. La literatura sobre comunicación o I/O motiva la pregunta, pero esos fenómenos no se convierten por ello en variables medidas por Analyzer.

## Costos que sí se observaron

Analyzer es post-mortem y no se añadió un tracer dentro de los jobs. El historial y los logs nativos de Pegasus/HTCondor sí se generan durante la ejecución; su tiempo de generación no se aisló mediante un control emparejado ON/OFF. Por tanto, no se atribuye a Analyzer un porcentaje de sobrecosto del runtime.

| Componente posterior a la ejecución | Valor observado en la campaña | Interpretación |
|---|---:|---|
| Preparación/recolección de entradas | 2.527 s de wall-clock promedio; entrada lógica de 18.617 MiB | Costo de recolectar y preparar artefactos. |
| Analyzer offline | 0.726 s de wall-clock promedio; CPU usuario 0.272 s y sistema 0.083 s; RSS pico promedio 22.49 MiB | Costo del proceso de análisis en el runner evaluado. |
| Informes | 0.185 MiB por run en promedio | Salida primaria del Analyzer. |
| Evidencia post-mortem preservada | 0.701 MiB por run en promedio | Almacenamiento adicional preservado para reproducibilidad. |
| Generación de logs nativos durante el workflow | No aislada | No hubo control emparejado ON/OFF; no se estima efecto causal en runtime. |

## Lectura académica recomendada

La contribución que los resultados respaldan es una comparación trazable entre un requerimiento lógico condicionado al placement y el payload científico que los manifiestos declaran y la evidencia de HTCondor permite confirmar a nivel de job. La utilidad demostrada es comparar los placements y patrones ensayados. Las conclusiones sobre tráfico físico, rendimiento, desperdicio, impacto económico u optimalidad requieren mediciones adicionales y no se afirman aquí.
