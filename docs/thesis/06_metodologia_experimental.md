# Capítulo 6 — Metodología experimental

La validación se realizó con ejecuciones nuevas e independientes de Pegasus/HTCondor y con oráculos calculados por separado de Analyzer v1. El diseño cubrió los cinco patrones oficiales, dos placements para cuatro patrones y dos tamaños para `process`. La matriz ejecutada comprende diez condiciones y 31 workflows válidos. Cada condición aporta al menos tres réplicas; `process/same-w1/10 MiB` cuenta con cuatro réplicas métricas.

## 6.1 Diseño de investigación

El trabajo siguió una secuencia de caracterización, formalización, operacionalización, implementación y validación. La validación pregunta si Analyzer calcula magnitudes coherentes con el dataflow y la evidencia disponible bajo el modelo declarado. No compara schedulers, no mide rendimiento y no busca un placement óptimo. Los gates R/D/I/V son controles de avance; la unidad científica de comparación es el workflow independiente.

## 6.2 Testbed y unidad experimental

La unidad experimental es un workflow nuevo, planificado y enviado de forma independiente, con identificador de run propio, artefactos frescos, un placement diseñado y una condición de patrón/tamaño. El entorno observado fue un pool virtualizado con `pegasus-master` y dos workers, Pegasus 5.1.2, HTCondor 25.12.2, jobs `vanilla` y transferencia administrada mediante `condorio`. El master permitió consultar los workers y sus ClassAds; no se necesitó SSH directo a cada worker.

La unidad de análisis de Analyzer es el run preservado junto con su archivo de HTCondor history. Se conservaron DAG y workflow, submits y metadatos Pegasus, configuración y snapshots del entorno, history filtrado por caso, parámetros, placement, oráculos, salidas del Analyzer y hashes. La descripción del entorno y sus límites están en `environment/ENVIRONMENT_SNAPSHOT.md` y en el informe de validación.

## 6.3 Matriz y variables

La matriz contiene cinco condiciones `same-w1` de 10 MiB —una por patrón—, cuatro condiciones `cross` de 10 MiB para `pipeline`, `data distribution`, `data aggregation` y `data redistribution`, y una condición adicional `process/same-w1` de 20 MiB. Se ejecutaron tres workflows válidos por condición y una réplica métrica adicional para `process/same-w1/10 MiB`.

| Clase | Variable | Valores o tratamiento |
|---|---|---|
| Factor de workflow | Patrón | `process`, `pipeline`, `data distribution`, `data aggregation`, `data redistribution` |
| Factor de placement | Ubicación de tareas | `same-w1`; además `cross` para los cuatro patrones multi-etapa/ramificados |
| Factor de tamaño | Archivo de entrada de `process` | 10 MiB y 20 MiB |
| Control | Modelo de ejecución | Pegasus `condorio`, HTCondor `vanilla`, transferencias administradas |
| Observada | Placement efectivo | Worker registrado por cada job; se verifica frente a la condición diseñada |
| Respuestas | Movimiento y cobertura | `Mreq`, `Mrec`, `Coverage`, `Mobs`, DME y estado de validez |
| Costos | Obtención de la métrica | `T_gen`, `T_collect`, `T_analyzer`, recursos offline y almacenamiento |

La matriz ejecutada se mantuvo acotada a las condiciones necesarias para los cinco patrones y a los contrastes indicados. No se ejecutó la matriz candidata de 129 casos ni una campaña de 1, 2 y 4 workers.

## 6.4 Procedimiento y oráculos

Antes de interpretar cada resultado se verificaron el run ID, los artefactos del workflow, el patrón, los parámetros, el placement efectivo y el snapshot del entorno. El oráculo de `Mreq` se calculó manualmente desde el grafo de archivos, los tamaños y las ubicaciones requeridas por el placement observado. El oráculo de `Mrec` se obtuvo de las ocurrencias científicas declaradas por los contratos de entrada y salida del modelo de ejecución. Estos cálculos se conservaron separados de la salida del Analyzer.

HTCondor history se exportó y acotó al caso. Analyzer v1 procesó los artefactos preservados en modo offline. La aceptación requirió estado válido, placement acorde a la condición, acuerdo con los oráculos, consistencia de las precondiciones y cobertura completa cuando se reportaban `Mobs` y DME. Todos los 31 workflows válidos cumplieron esos criterios y tuvieron `Coverage=1`.

## 6.5 Réplicas, determinismo y aceptación

Las réplicas experimentales son workflows separados, no reanálisis del mismo run. Cada run se analizó tres veces para comprobar determinismo; las salidas canónicas de cada terna fueron idénticas. A su vez, los valores métricos coincidieron entre las réplicas independientes de una misma condición. El primer resultado comprueba repetibilidad del análisis; el segundo, consistencia observada de las ejecuciones replicadas.

La evidencia empírica de Gate V no contiene un caso válido con `Coverage<1`. Los estados incompletos, ambiguos o contradictorios se cubrieron mediante pruebas de software y se preservan en la validación de implementación. Por tanto, esa política fail-closed no se presenta como un resultado de una condición experimental incompleta real.

## 6.6 Medición del costo de obtención

El costo se desagregó en tres componentes. `T_gen` registra planificación y finalización del workflow con el logging nativo de Pegasus/HTCondor activo e incluye el trabajo científico; es una duración observada, no un delta causal atribuible al Analyzer. No se añadió tracer, profiler ni logger dentro de los jobs.

`T_collect` mide la exportación de history, la normalización de ClassAds de control cuando aplica y el inventario/hash de las fuentes antes del análisis. `T_analyzer` mide la invocación primaria offline. Para esta última se registraron wall-clock, CPU de usuario y sistema, RSS pico, tamaño lógico del conjunto de entrada y tamaño de informes. El tamaño lógico de entrada no se interpreta como bytes leídos físicamente del disco. CPU/RSS de recolección y de pasos auxiliares no quedó registrada.

La ruta mínima se define como $T_{\mathrm{total}}=T_{\mathrm{gen}}+T_{\mathrm{collect}}+T_{\mathrm{analyzer}}$. Informes auxiliares de Pegasus, verificaciones de integridad posteriores y reanálisis para determinismo se informan aparte. El almacenamiento de logs nativos, fuentes, informes primarios y artefactos adicionales preservados se contabiliza en magnitudes separadas; el bundle compacto no representa por sí solo el espacio ocupado por los árboles de runs.

La variabilidad de $T_{\mathrm{gen}}$ se describe entre workflows independientes, con estadísticos muestrales por condición. Como el tamaño por condición es tres, la inferencia es descriptiva. No se afirma un efecto causal del logging nativo y, dado que no se introdujo instrumentación durante runtime, no se realizó un control pareado ON/OFF.

## 6.7 Amenazas a la validez

Los resultados corresponden a un pool virtualizado de dos workers, `condorio`, jobs `vanilla` y las condiciones ejecutadas. No se generalizan automáticamente a sistemas de archivos compartidos, otros adapters, más nodos, políticas de planificación diferentes ni otros clusters. El orden de condiciones no fue documentado como aleatorizado o contrabalanceado y no se registró una medición de carga del host previa a cada run; esa variación puede contribuir a los tiempos observados.

La confirmación de movimiento usa manifests y HTCondor history a nivel job; no cuenta paquetes ni bytes físicos de red. La referencia `Mreq` es un lower bound lógico condicionado al placement y a los archivos modelados. Tres réplicas permiten describir la dispersión observada, pero no probar diferencias pequeñas ni sostener inferencia poblacional. Estas restricciones delimitan las conclusiones del capítulo 7 y la discusión del capítulo 8.
