# Guion de sustentación — versión clara

**Duración sugerida:** 7–9 minutos.  
**Idea que debe recordar el jurado:** las dependencias de un workflow y el lugar real donde corren sus tareas determinan qué archivos deben estar disponibles; el Analyzer compara ese requerimiento lógico con el payload científico que la ejecución declara y HTCondor permite confirmar a nivel de job.

## 1. Título — Movimiento de datos en workflows científicos

“Mi trabajo estudia una pregunta concreta: dado un workflow y el lugar donde corrieron realmente sus tareas, ¿cuántos datos requieren sus dependencias y cuánto payload confirma la evidencia del mecanismo de ejecución? La respuesta ayuda a comparar placements. No estoy midiendo paquetes de red.”

## 2. El problema

“En big data, las tareas trabajan sobre archivos. Si una tarea consume un archivo producido en otra ubicación, ese archivo tiene que estar disponible donde corre el consumidor. Cuando hay muchos datos y muchas dependencias entre ubicaciones, la comunicación puede convertirse en un cuello de botella. La literatura estudia este problema; mi experimento no mide tiempo perdido ni tráfico físico de red.”

## 3. Qué aporta la investigación previa

“Los trabajos consultados explican partes distintas del problema. Bharathi y colegas describen patrones de workflows; Deelman y colegas explican cómo Pegasus ejecuta workflows científicos. Pietri y Sakellariou consideran el costo de comunicación al programar tareas. Lee y colegas siguen el ciclo de vida de los datos. Tang y colegas relacionan semántica de datos con operaciones de I/O. Devarajan y colegas presentan DFTracer para recolectar trazas de varias capas. Aurelio Vivas Meza estudia estrategias de scheduling que incluyen movimiento y localidad NUMA.

“No afirmo que esas métricas sean inútiles. Responden preguntas diferentes. Mi pregunta reúne DAG, placement observado, archivos científicos y evidencia de Pegasus/HTCondor para comparar movimiento lógico requerido con payload confirmado. La tesis tampoco confunde movimiento entre workers con localidad dentro de un nodo, como NUMA.”

## 4. Pregunta de investigación

“Esta es la pregunta que organiza el trabajo: dado un workflow y el placement real de sus tareas, ¿cuánto movimiento de datos exigen sus dependencias entre ubicaciones y cuánto movimiento produce realmente el mecanismo de ejecución? En esta investigación, ‘produce’ se estima con manifiestos de transferencia y evidencia de HTCondor por job; no con captura de paquetes.”

## 5. Tres cantidades

“Separé tres cosas. `M_req` es el movimiento lógico necesario según los archivos, el workflow y el placement. `M_rec` es lo que los manifiestos de los jobs declaran transferir. `M_obs` es el tamaño de las ocurrencias científicas declaradas que sí se pueden reconciliar con el historial de HTCondor. `Coverage` indica qué fracción de las ocurrencias declaradas quedó confirmada. Si la cobertura es incompleta, no presento `M_obs` ni DME como valores cerrados.”

## 6. Cómo leer las fórmulas

“Para `M_req`, tomo el tamaño de cada archivo y cuento los destinos nuevos distintos donde se necesita. Si varias tareas del mismo worker usan el archivo, ese worker no se cuenta varias veces. `D_sci` son las ocurrencias científicas declaradas en manifiestos; `C_sci` es el subconjunto confirmado por la reconciliación del historial. La cobertura es el tamaño de `C_sci` dividido por el tamaño de `D_sci`. Con cobertura completa, sumo tamaños confirmados para `M_obs`. Finalmente, DME es `M_req / M_obs`. La DME compara volúmenes; no mide rapidez ni prueba por sí sola que la diferencia sea desperdicio.”

## 7. Dónde corre el sistema

“Durante la ejecución, Pegasus y los servicios centrales de HTCondor están en `pegasus-master`; los jobs científicos corren en `pegasus-worker1` y `pegasus-worker2`. Después del workflow, Analyzer lee el run preservado y el historial exportado. Es post-mortem: no cambia el scheduler ni decide el placement. El diagrama separa control, ejecución y análisis; no afirma una ruta física de archivos.”

## 8. Patrones del workflow

“Validé cinco formas: process, pipeline, distribución, agregación y redistribución. Cada dibujo muestra quién produce y quién consume archivos. La forma del workflow y el placement son dos cosas diferentes: el mismo patrón puede ejecutarse en un solo worker o repartido entre workers.”

## 9. Método y validación

“Fijé workflow, archivos y placement esperado; ejecuté Pegasus y HTCondor; comparé manifiestos con el historial por job; y contrasté los cálculos del Analyzer con oráculos manuales. Gate V cubrió cinco patrones, diez condiciones y 31 workflows independientes, con tres o más réplicas por condición. Las 31 ejecuciones fueron válidas, la ubicación observada coincidió con la planeada y la cobertura fue completa. La conclusión se limita a este pool de dos workers y a las condiciones ensayadas.”

## 10. Ejemplo manual de pipeline

“Cada una de las seis ocurrencias científicas del ejemplo pesa 10 MiB. El historial confirma las seis; por tanto, `M_obs = 6 × 10 = 60 MiB` en ambos placements. Si las tareas están en W1, el requerimiento del modelo es 20 MiB: `20/60 = 0.33`. Si repartimos T1, T2 y T3 entre W1 y W2 como muestra el diagrama, `M_req = 40 MiB`: `40/60 = 0.67`. La flecha muestra la dependencia lógica de archivos, no una ruta física de red.”

## 11. Resultados al comparar placements

“En las cuatro comparaciones del gráfico, DME aumenta cuando el placement ensayado requiere más ubicaciones nuevas. Pipeline pasa de 0.33 a 0.67; distribución y agregación, de 0.50 a 0.75; redistribución, de 0.25 a 0.625. En cada patrón comparado, el payload confirmado se mantuvo igual y cambió el requerimiento lógico. Esto demuestra que la métrica distingue esos placements en la matriz probada; no demuestra que uno sea más rápido.”

## 12. Costo de obtener la evidencia

“Separé preparación de archivos, análisis offline y almacenamiento preservado. La preparación tomó 2.53 segundos promedio; Analyzer, 0.73 segundos, con aproximadamente 0.36 segundos de CPU. El RSS pico promedio fue 22.49 MiB. Los informes ocuparon 0.185 MiB por run y la evidencia adicional preservada, 0.701 MiB. Los logs nativos se generan durante el workflow, pero no aislé su costo con una comparación ON/OFF; no digo que Analyzer aumente el runtime en cierto porcentaje.”

## 13. Para qué sirve y qué no mide

“La utilidad demostrada es comparar placements y patrones bajo una misma definición, identificar cuáles exigen más ubicaciones de datos y escoger qué casos conviene estudiar después. Eso puede orientar decisiones de placement o staging, pero su impacto en tiempo, costo o rendimiento debe medirse por separado. No mide tráfico de red, ancho de banda, I/O físico, RAM, NUMA, uso de CPU/GPU ni optimalidad del scheduler.”

## 14. Cierre

“En síntesis, esta tesis conecta tres piezas que deben leerse juntas: dependencias del workflow, placement observado y evidencia de transferencia de Pegasus/HTCondor. El resultado es una comparación explicable y reproducible para los casos evaluados. Su alcance termina ahí: es una métrica de movimiento de archivos definida por el modelo y por las trazas disponibles, no una medición universal del costo físico de mover datos.”

## Respuestas breves si preguntan

**¿`M_obs` son bytes de red?**  
“No. Son tamaños de ocurrencias científicas declaradas y confirmadas con estadísticas de transferencia HTCondor por job. No hay captura packet-level.”

**¿`M_obs - M_req` son bytes desperdiciados?**  
“No puedo concluir eso. Las dos cantidades comparten run y payload científico, pero cuentan cosas distintas: ubicaciones requeridas y ocurrencias de manifiesto confirmadas.”

**¿La DME demuestra que un placement es mejor?**  
“Demuestra cómo cambia la razón entre estas cantidades. Para decir que mejora el runtime, el ancho de banda o el costo, tendría que medir esas variables aparte.”

**¿Qué indican los papers?**  
“Que la estructura de workflows, el costo de comunicación, los ciclos de vida de datos, el I/O y la localidad NUMA son líneas de investigación relacionadas. Mi aporte es una pregunta de medición post-mortem acotada a Pegasus/HTCondor y a los archivos y placements que sus evidencias permiten reconstruir.”
