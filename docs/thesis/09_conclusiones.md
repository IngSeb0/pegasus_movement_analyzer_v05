# Capítulo 9 — Conclusiones

## 9.1 Respuesta a la pregunta de investigación

La pregunta de investigación se respondió mediante el diseño y la validación de una métrica trazable de movimiento de datos para workflows Pegasus bajo un execution model y un pool documentados. Analyzer v1 separa la necesidad lógica condicionada al placement (`Mreq`), el movimiento declarado por el contrato de ejecución (`Mrec`) y el movimiento científico confirmado (`Mobs`). `Coverage` controla si la evidencia permite informar `Mobs` y DME. La validación de Gate V respalda esta operacionalización para las diez condiciones y las 31 ejecuciones reportadas; no establece validez universal para otras arquitecturas o execution models.

## 9.2 Conclusiones principales

1. **La semántica separada es operable.** La campaña distinguió el lower bound lógico de las ocurrencias declaradas y confirmadas. En todas las ejecuciones válidas, `Coverage=1`, los oráculos manuales coincidieron con los valores del Analyzer y `Mobs=Mrec`.

2. **La métrica respondió a las variaciones ensayadas.** Los patrones, placements y tamaños produjeron las magnitudes reportadas en el capítulo 7. Al mover tareas entre workers, `Mreq` cambió mientras el payload confirmado del patrón permaneció constante; al duplicar el tamaño de entrada de `process`, se duplicaron los movimientos requeridos y confirmados. Estas observaciones son descriptivas del diseño ejecutado y no comparan schedulers.

3. **La evidencia tiene granularidad de job.** Pegasus artifacts, HTCondor history, manifests y provenance permiten reconciliar transferencias del modelo `condorio` a nivel de job. No se midieron paquetes ni tráfico físico. Por tanto, `Mobs` es movimiento confirmado según la evidencia disponible, y `Mreq` es la referencia lógica file-centric definida en esta tesis.

4. **El costo offline pudo separarse del runtime.** No se añadió un tracer, profiler o logger dentro de los jobs. La duración runtime con logs nativos, la preparación post-mortem, el Analyzer offline y el almacenamiento preservado se reportaron en componentes separados. Para el Analyzer también se midieron CPU, RSS, entrada y salida. No se estimó un delta causal de logging y no se atribuye al Analyzer un incremento porcentual del runtime.

5. **La conclusión está limitada al entorno medido.** Tres réplicas por condición permiten describir consistencia y variabilidad observadas, no soportan inferencia amplia. El resultado se restringe al pool de dos workers y a Pegasus/HTCondor con `condorio` y jobs `vanilla` descritos en el capítulo 6.

## 9.3 Utilidad de la contribución

Analyzer v1 ofrece una forma reproducible de revisar si la evidencia de staging concuerda con los archivos científicos, el modelo de ejecución y el placement de un run. Esa información puede apoyar el diagnóstico de transferencias, la comparación de patrones y la evaluación de decisiones de arquitectura. La herramienta no reemplaza una medición de rendimiento ni recomienda automáticamente una configuración: ayuda a formular preguntas correctas sobre movimiento y a evitar inferencias que los artefactos no sostienen.

## 9.4 Líneas de investigación derivadas

Los resultados abren líneas que pueden evaluarse en trabajos posteriores, siempre que se mantenga explícita la pregunta de investigación:

- Replicar la validación en otra configuración de almacenamiento o en pools con más workers para estudiar validez externa.
- Diseñar, si aporta a los criterios oficiales, una condición empírica con evidencia incompleta y contrastarla con los estados fail-closed ya probados a nivel de software.
- Ampliar el número de réplicas cuando se requiera estimar diferencias pequeñas, usando primero un efecto de interés y una precisión objetivo para justificar el tamaño muestral.
- Aleatorizar o intercalar condiciones y registrar carga previa del pool cuando el objetivo incluya separar mejor la variabilidad temporal.
- Evaluar instrumentación runtime únicamente si se decide incorporarla; cualquier afirmación causal sobre su efecto debe emplear un control emparejado.

Estas líneas amplían la evidencia sin cambiar la semántica de DME. Los resultados presentados en esta tesis se limitan a las ejecuciones, fuentes y condiciones efectivamente documentadas.
