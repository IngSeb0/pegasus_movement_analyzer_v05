# Capítulo 8 — Discusión y amenazas a la validez

## 8.1 Qué problema resuelve la medición

El problema observado en este trabajo es la distancia entre tres preguntas que suelen confundirse: cuánto movimiento sería lógicamente necesario para el dataflow y el placement ejecutado; qué transferencias declara el contrato del execution model; y qué ocurrencias de movimiento pueden confirmarse con las fuentes preservadas. Analyzer v1 conserva esas capas como `RequiredMovement`, `DeclaredMovement` y `ObservedMovement`, y evita convertir ausencia de evidencia en cero. Esta separación es coherente con la distinción entre workflow abstracto y ejecución distribuida descrita por Deelman et al. (2015), y con la necesidad de representar relaciones entre datos señalada por Lee et al. (2023) y Tang et al. (2024).

La reconciliación depende del adapter `condorio` y de HTCondor history a nivel de job. Por tanto, “observado” significa confirmado por la evidencia operacional disponible para el modelo probado. No significa captura de paquetes, lectura de contadores de interfaz o reconstrucción de cada salto físico de red. El esquema worker–master–worker se emplea como explicación conceptual del staging administrado; la campaña no mide la ruta de cada paquete.

## 8.2 Lectura de los resultados de movimiento

En las 31 ejecuciones válidas, distribuidas en diez condiciones, `Coverage=1`; por ello pudieron reportarse `Mobs` y DME. Las ocurrencias científicas declaradas fueron confirmadas y `Mobs=Mrec` en todos los casos. Los oráculos manuales de `Mreq` y `Mrec` coincidieron con los valores del Analyzer, y los resultados fueron idénticos entre workflows independientes de una misma condición.

Los resultados diferencian patrones y placements. `Process` produjo DME=1 en los dos tamaños ensayados. Para los otros cuatro patrones, el placement `cross` elevó `Mreq` manteniendo constante el payload confirmado: pipeline pasó de 20 a 40 MiB requeridos frente a 60 MiB confirmados; distribución, de 20 a 30 MiB frente a 40 MiB; agregación, de 80 a 120 MiB frente a 160 MiB; redistribución, de 80 a 200 MiB frente a 320 MiB. La DME aumentó en cada comparación, según los valores del capítulo 7. En `process`, duplicar el input de 10 a 20 MiB duplicó `Mreq` y `Mobs` y dejó DME en uno.

Estos contrastes muestran que, bajo el modelo y la matriz ensayados, la métrica responde a cambios controlados de tamaño y placement de una manera coherente con el cálculo file-centric. Cuando `Mobs>Mreq`, la diferencia se interpreta solo respecto al lower bound definido; no prueba que ese volumen pueda eliminarse, que el scheduler haya sido subóptimo o que la red transportara exactamente esa cantidad de bytes. Un resultado DME=1 tampoco demuestra optimalidad global ni ausencia de costos fuera del constructo medido.

La interpretación coincide con la diferencia entre medir y optimizar. Pietri y Sakellariou (2018) cambian el peso de comunicación durante la construcción del schedule para favorecer localidad. Analyzer evalúa una ejecución una vez observado su placement. La disertación de Vivas Meza (2026) aporta contexto sobre decisiones de scheduling informadas por workflow y arquitectura NUMA; Analyzer no implementa esas decisiones ni estima NUMA.

## 8.3 Relación con las contribuciones previas

Bharathi et al. (2008) caracterizan estructuras de workflows que ayudan a justificar la variedad de patrones probados; la matriz de esta tesis comprueba esos patrones según la propuesta oficial y no pretende reproducir sus aplicaciones científicas originales. DataLife (Lee et al., 2023) motiva considerar productores, consumidores y ciclos de vida de archivos. DaYu (Tang et al., 2024) evidencia que la semántica lógica puede no revelar detalles del I/O físico. DFTracer (Devarajan et al., 2024) representa una alternativa de observación basada en trazas multicapas, mientras que Analyzer v1 usa fuentes nativas existentes y análisis post-mortem.

Workflow Critical Path de Nguyen y Karavanic (2021) calcula una cantidad temporal para diagnóstico de ruta crítica; la métrica de Do et al. (2021) caracteriza eficiencia de recursos en workflows *in situ*. Ambos trabajos refuerzan la necesidad de declarar unidad, modelo y precondiciones, pero contestan preguntas diferentes. DME se expresa como razón entre magnitudes de movimiento de datos científicos y no debe compararse numéricamente con runtime, camino crítico, ancho de banda o eficiencia de recursos.

En el conjunto revisado no se encontró una definición que reúna simultáneamente el límite lógico condicionado al placement observado, el payload científico confirmado para el mismo run y la regla de cobertura completa. Esa delimitación es resultado de la revisión realizada, no prueba de inexistencia universal ni reemplaza una revisión sistemática.

## 8.4 Costo de obtención de la métrica

Los componentes se interpretan por separado. `T_gen` incluye planificación, ejecución científica y logging nativo de Pegasus/HTCondor; describe la duración observada de la etapa runtime y su variabilidad. No es una medida del tiempo añadido por Analyzer. `T_collect` corresponde a exportar y preparar evidencia después del workflow. `T_analyzer` mide la ejecución offline del Analyzer; para esta etapa se registraron wall-clock, CPU y RSS pico, junto con tamaños lógicos de entrada y de informes. El almacenamiento de logs nativos y de artefactos post-mortem se informa aparte.

La campaña no añadió tracer, profiler ni logger dentro de los jobs. Por eso el costo operacional medido atribuible al análisis está en las etapas post-mortem. El tamaño de los logs nativos cuantifica almacenamiento; por sí solo no estima el tiempo de CPU, I/O o runtime que generó el logging basal. No se afirma “Analyzer añade X% al runtime”, ni que el costo de los logs nativos sea cero. Las medias, rangos y exclusiones están en la tabla del capítulo 7; CPU/RSS de recolección y algunas operaciones auxiliares no pudieron medirse.

Esta formulación sigue el criterio de la propuesta oficial: documenta la obtención y el sobrecosto de instrumentación dentro de la implementación efectivamente usada sin hacer una afirmación causal que requiera un control que no forma parte de ella. Si en una extensión se añade instrumentación runtime o se afirma un efecto causal, entonces se necesitará un control emparejado que preserve workflow, tamaño, modelo, workers, placement y configuración de planificación.

## 8.5 Amenazas y alcance de las inferencias

**Validez externa.** Los resultados provienen de un pool virtualizado de dos workers, Pegasus 5.1.2, HTCondor 25.12.2, jobs `vanilla` y transferencias `condorio`. No se generalizan automáticamente a más nodos, otros adapters, sistemas de archivos compartidos, otros schedulers o infraestructura física distinta.

**Variabilidad temporal.** Cada condición tiene tres workflows con cronometraje completo; una condición tiene una cuarta réplica métrica sin límites históricos completos de `T_gen`. El orden no se documentó como aleatorizado o contrabalanceado y no se midió carga del host antes de cada run. La desviación estándar resume la dispersión de esta campaña; con n=3 no permite inferencia poblacional ni conclusiones firmes sobre diferencias pequeñas.

**Cobertura y fallos.** Todas las ejecuciones válidas de Gate V tuvieron cobertura completa. Los estados parciales o contradictorios se cubrieron en pruebas de software, no mediante una condición empírica de workflow en esta campaña. Por ello, Gate V valida el cálculo sobre evidencia completa, mientras que el comportamiento fail-closed para cobertura incompleta se respalda por pruebas de implementación.

**Medición de transferencia.** HTCondor history y los manifests aportan evidencia a nivel de job y de contrato de transferencia; no identifican paquetes, saltos, retransmisiones o bytes físicos de red. `Mreq` es un lower bound lógico file-centric condicionado por los archivos, tamaños, consumidores y placement representados. No es un límite físico universal.

**Oráculo y determinismo.** Los oráculos se calcularon manualmente fuera del Analyzer y las salidas canónicas se repitieron tres veces. Esto reduce dependencia de una sola ejecución o del mismo camino de cálculo, pero no equivale a revisión ciega por una persona externa ni a una validación independiente de otro equipo.

Estas amenazas no invalidan los resultados dentro de sus condiciones; limitan la extensión de las afirmaciones. La conclusión adecuada es una validación operacional y descriptiva acotada al modelo y al pool documentados.
