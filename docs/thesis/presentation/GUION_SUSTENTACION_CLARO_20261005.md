# Guion de sustentación — versión sencilla

**Duración sugerida:** 7–9 minutos.  
**Idea central:** comparar el movimiento de archivos que requieren las tareas con el payload científico que los registros disponibles permiten confirmar.

## 1. Movimiento de datos en workflows científicos

“Mi trabajo responde una pregunta: dado un workflow y el worker donde corrió cada tarea, ¿cuánto movimiento exigen sus dependencias y cuánto payload científico declara y confirma la ejecución? No estoy midiendo paquetes de red.”

## 2. El problema

“En Big Data, los workflows manejan archivos grandes. La salida de una tarea puede ser la entrada de otra, y ese archivo debe llegar a la máquina donde corre la tarea que lo necesita. Cuando hay muchos datos y dependencias entre máquinas, mover archivos puede convertirse en un cuello de botella.”

“Saber que se transfirieron 500 GB no dice, por sí solo, si era mucho o poco. Para interpretarlo hace falta saber qué movimiento exigían el workflow y el lugar donde corrió cada tarea.”

“Por ejemplo, 500 GB observados no dicen si las dependencias requerían 300 GB o los 500 GB. Es una pregunta ilustrativa, no un resultado de mi experimento.”

## 3. Métricas y trabajos relacionados

“Bytes transferidos, duración y ancho de banda describen la transferencia. El tiempo total describe cuánto duró el workflow. Son medidas útiles, pero no comparan ese volumen con los destinos de archivo que exigían las dependencias.”

“La investigación relacionada aporta piezas importantes. Bharathi y Deelman describen patrones de workflows y Pegasus. Pietri y Sakellariou incorporan comunicación al programar tareas. Lee estudia ciclos de vida de datos y Tang conecta datos con operaciones de entrada y salida. Devarajan presenta DFTracer para observar flujos desde varias capas. Aurelio Vivas Meza estudia scheduling y movimiento de datos, incluida la localidad NUMA. Cada trabajo responde preguntas relacionadas desde otra perspectiva; mi propuesta las complementa.”

## 4. Pregunta de investigación

“Cuando digo ubicación de una tarea, me refiero al worker donde realmente se ejecutó. Con esa definición, la pregunta es: para este workflow y estas ubicaciones, ¿cuánto movimiento exigen sus dependencias y cuánto payload científico declara y confirma la ejecución?”

## 5. Tres cantidades

“`M_req` es el movimiento lógico que exige el workflow según los archivos y los destinos donde se necesitan. `M_rec` es lo que los manifiestos de los jobs declaran transferir. `M_obs` suma los tamaños de esas ocurrencias científicas cuando la evidencia de HTCondor permite conciliarlas por job.”

“No son la misma frontera de conteo: `M_req` cuenta destinos lógicos; `M_obs` cuenta ocurrencias declaradas y confirmadas por job. `M_obs` tampoco es una captura de todo el tráfico de red.”

## 6. Cómo leer las fórmulas

“Para calcular `M_req`, tomo el tamaño de cada archivo y lo multiplico por la cantidad de nuevos destinos que ese archivo necesita según las dependencias y el worker de cada tarea. Después sumo los archivos.”

“`D_sci` es el conjunto de ocurrencias científicas declaradas por los manifiestos. `C_sci` es el conjunto que se pudo relacionar con la evidencia de HTCondor por job. `Coverage` es la fracción confirmada. Si es igual a uno, sumamos el tamaño de las ocurrencias confirmadas para obtener `M_obs`. Finalmente, DME divide `M_req` entre `M_obs`. Esa razón compara volúmenes definidos de manera distinta; no identifica bytes desperdiciados.”

## 7. Ejemplo del cálculo

“Aquí tenemos tres tareas y dos formas de ubicarlas. En ambos casos, la evidencia confirma seis ocurrencias científicas de 10 MiB: `M_obs = 60 MiB` y `Coverage = 6/6 = 1`.”

“Si las tres tareas corren en W1, el cálculo de referencia da `M_req = 20 MiB`; entonces DME es `20/60 = 0.33`. Si T1 corre en W1, T2 en W2 y T3 vuelve a W1, el requerimiento es `40 MiB`; DME es `40/60 = 0.67`.”

“El ejemplo muestra cómo cambió la referencia lógica al repartir tareas entre workers. No demuestra que los 20 MiB de diferencia sean bytes físicos evitables ni que una alternativa sea más rápida.”

## 8. Formas de los workflows

“Validamos cinco formas: process, pipeline, distribución, agregación y redistribución. Esas palabras describen quién produce un archivo y quién lo consume. La ubicación indica en qué worker corre cada tarea. Son dos aspectos distintos del mismo workflow.”

## 9. Despliegue del sistema

“Durante la ejecución, Pegasus y los servicios centrales de HTCondor corren en el master. Los jobs científicos corren en worker1 y worker2. Después, Analyzer procesa el run preservado y el historial exportado. Es un análisis post-mortem; no decide dónde corre cada tarea ni se inserta dentro del workflow.”

## 10. Validación

“Fijamos el workflow y sus archivos, ejecutamos Pegasus y HTCondor, relacionamos los manifiestos con el historial de cada job y comparamos los resultados del Analyzer con cálculos independientes. Se cubrieron cinco patrones, diez condiciones y 31 ejecuciones, con al menos tres réplicas por condición. Las 31 fueron válidas y `Coverage` fue uno. Esta evidencia corresponde al pool de dos workers y a las condiciones ensayadas.”

## 11. Resultados

“El gráfico muestra que, en los cuatro patrones comparados, repartir las tareas cambió `M_req` y DME mientras el volumen manifestado y confirmado se mantuvo. Esto demuestra que la métrica distingue esas configuraciones en las condiciones probadas. No demuestra que una haya mejorado el tiempo de ejecución.”

## 12. Costo de obtener la evidencia

“Separamos preparación de archivos, análisis offline y almacenamiento preservado. En esta campaña la preparación tomó 2.53 segundos en promedio; Analyzer, 0.73 segundos de wall-clock y 0.36 segundos de CPU. La memoria pico fue 22.49 MiB. No añadimos un tracer adicional dentro de los jobs ni medimos un control de logging encendido frente a apagado; por eso no atribuimos a Analyzer un porcentaje del runtime.”

## 13. Utilidad

“Para un equipo que ejecuta workflows, esta referencia ayuda a comparar dónde corren las tareas, detectar qué patrones requieren más destinos de archivos y decidir qué configuraciones vale la pena investigar. Si luego se cambia el staging o la distribución de tareas, el efecto en tiempo y costo se mide aparte.”

## 14. Cierre

“La conclusión para el cliente es sencilla: el volumen transferido necesita contexto. Esta métrica añade una referencia basada en las dependencias y en el worker donde corrió cada tarea. Sirve para comparar y elegir qué revisar; no promete ahorro ni reemplaza las mediciones de tiempo, red o costo.”

## Respuestas cortas

**¿`M_obs` son bytes de red?**
“No. Son tamaños de archivos científicos declarados y conciliados con evidencia de HTCondor por job.”

**¿La diferencia `M_obs - M_req` son bytes desperdiciados?**
“No puedo concluir eso: cada valor sigue una regla de conteo distinta.”

**¿La métrica demuestra que un worker es más rápido?**
“No. Compara volúmenes; el tiempo debe medirse aparte.”

**¿Qué aportan los artículos?**
“Dan contexto sobre workflows, scheduling, flujos de datos, I/O, trazas y NUMA. Mi trabajo conecta esas ideas con una comparación post-mortem acotada a archivos científicos y evidencia de Pegasus/HTCondor.”
