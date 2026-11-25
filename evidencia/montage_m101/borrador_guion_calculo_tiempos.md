# Guion de defensa de DME

Catorce diapositivas principales. Duración objetivo **14:30**, con 30 segundos de margen. Cuatro diapositivas de respaldo para preguntas.

## 1. Evaluación del movimiento de datos en flujos científicos

**00:00–00:30**

Buenos días. Soy Luis Sebastián Contreras Díaz. En un flujo científico distribuido, una máquina puede tener listo el programa que debe ejecutar y seguir esperando los archivos que necesita. Mi trabajo estudia esos envíos. Quiero saber cuánto movimiento exige el flujo y qué entregas podrían reducirse al cambiar su forma de ejecución.

## 2. Un flujo de trabajo también mueve datos

**00:30–01:15**

Pensemos en un equipo que recoge observaciones, las procesa y reúne los resultados. Un workflow, o flujo de trabajo, define las tareas y qué archivos pasan de una a otra. Si se ejecuta en varias máquinas, cada tarea necesita recibir sus entradas antes de poder usarlas. En flujos intensivos en datos, las tareas pueden leer o producir archivos grandes o numerosos. Cada entrega ocupa recursos de transferencia. Analizar los envíos ayuda a decidir si un cambio de ejecución puede reducir ese volumen sin cambiar el resultado científico.

## 3. ¿Qué parte de los envíos era necesaria?

**01:15–02:20**

Pensemos en dos tareas, A y B, en la misma máquina de trabajo. A crea un archivo y B lo necesita. En la forma de ejecución que estudié, CondorIO, un archivo puede volver al coordinador y salir de nuevo hacia B, aunque B esté en la misma máquina. Cada uno de esos pasos se registra como una entrega. Si ambas tareas comparten un job, B puede leer la copia local. Un job es la unidad que se envía a ejecutar. El total de bytes reúne lo que exigían las dependencias y lo que añadió la forma de ejecución. Para localizar un ahorro necesito distinguir esas dos cantidades.

## 4. DME mide qué parte del volumen era necesaria

**02:20–03:30**

Mi objetivo fue definir una métrica para evaluar ese movimiento, automatizar el cálculo y validarlo. La métrica se llama DME, eficiencia del movimiento de datos. Pongo en el numerador los bytes requeridos por las dependencias y por la ubicación real de las tareas. En el denominador sumo los bytes de cada entrega completa que pude corroborar. Calculo la razón cuando el observado es positivo y puedo corroborar todas las entregas requeridas. El cociente indica qué fracción del volumen observado era requerida. Uno indica que los volúmenes coinciden. Un medio indica que la mitad del observado supera lo requerido. El desglose conserva el archivo y su destino, así que también permite ubicar el exceso.

## 5. Por qué cuenta el destino de cada archivo

**03:30–04:30**

Veamos un ejemplo de un solo archivo. Dos tareas leen el mismo archivo desde el coordinador. Si corren en la misma máquina, esa máquina necesita recibir una copia. Si corren en máquinas diferentes, hacen falta dos copias, una por destino. Supongamos que observé dos entregas en ambos casos. En el primero DME es un medio. En el segundo es uno. Los bytes observados son iguales y cambia lo que ese volumen significa. Por eso el requerido usa la ubicación efectiva y cuenta cada destino una vez. Si un archivo producido en un worker hace falta en otro, contamos también el paso obligatorio por el coordinador. Cuando el requerido es común, reducir el observado aumenta DME.

## 6. Plan de pruebas

**04:30–05:35**

Dividí la evaluación en dos preguntas. Primero, ¿la herramienta obtiene los volúmenes correctos? Usé cinco formas de conectar tareas, con dos o cuatro máquinas de trabajo disponibles y un núcleo por máquina. Mantuve seis tareas por flujo, archivos de diez MiB, el trabajo de CPU y las reglas de retorno. Segundo, ¿DME refleja un ahorro al cambiar la ejecución de un flujo real? Usé un mosaico completo de Montage. Corrí una base con tareas separadas y dos variantes que reúnen pares distintos. Conservé las entradas, el grafo y las máquinas. Eso permite atribuir el cambio de bytes a los envíos que elimina cada agrupación.

## 7. Requerido y observado en distribución

**05:35–07:10**

Analyzer lee el plan de Pegasus y el historial de HTCondor. Reconstruye los destinos de los archivos y las entregas completas. Para comprobarlo hice una cuenta independiente. En distribución un productor recibe A, genera g y cinco tareas leen g. Cada archivo pesa diez MiB. A entra una vez y los cinco resultados vuelven una vez cada uno. Ahí coinciden requerido y observado. Con dos workers, dos consumidores de g quedaron en W2. Con cuatro, uno quedó en W4. En ambas corridas hay un solo worker consumidor distinto del que produjo g. Por eso el requerido de g son dos tramos: el retorno al coordinador y una entrega a esa máquina. En los registros vimos un retorno y cinco entregas de g, una por job consumidor. Así, el requerido suma ochenta MiB y el observado ciento veinte. Analyzer obtuvo la misma cuenta. El cociente dos tercios dice que dos tercios de lo entregado correspondían a obligaciones del flujo.

## 8. El cálculo coincidió en los cinco patrones

**07:10–08:15**

Estas son las cinco estructuras que probamos. La cuenta independiente y Analyzer coincidieron en los dos volúmenes y en DME en las diez ejecuciones. Ya vimos por qué distribución dio dos tercios en ambos ambientes. En agregación y redistribución sí cambió el requerido. En cada uno, quedó un productor adicional en una máquina distinta de su consumidor. Su archivo añadió dos tramos obligatorios, de vuelta al coordinador y del coordinador al consumidor. Eso agregó veinte MiB requeridos, con el mismo observado en cada patrón. Por eso leemos DME junto con sus dos volúmenes.

## 9. Mismos bytes, distintos tiempos

**08:15–09:10**

Distribución movió ciento veinte MiB en ambas corridas. Con cuatro workers, DAGMan envió los consumidores cinco segundos antes y terminó cerca de cinco segundos antes. Los registros muestran dónde aparece la diferencia. En agregación pasó al revés. El primer job tardó dieciséis segundos en empezar tras el envío, frente a seis con dos workers. Con una ejecución por ambiente, describimos lo que pasó en esas corridas. Para atribuir esas esperas a una causa específica necesitaríamos repetir bajo condiciones controladas.

## 10. Un flujo real de astronomía con Montage

**09:10–09:50**

Con el cálculo comprobado, pasé a un flujo real. Montage toma imágenes astronómicas que cubren partes del cielo y las combina en un mosaico. Este es M101. Usé la ruta del tutorial sin ajuste de fondo y partí de diez imágenes 2MASS. La salida científica son dos archivos FITS: el mosaico y un mapa que indica qué área queda cubierta. La comparación pregunta si podemos producir esos mismos resultados haciendo menos entregas entre jobs.

## 11. El workflow completo de M101

**09:50–11:05**

A la izquierda están las diez tareas de reproyección, P01 a P10. Cada una toma su propia imagen y una cabecera común que define las coordenadas de destino. Cada tarea produce una imagen alineada y su mapa de área. Todas las reproyecciones corren en W2. En W1, mImgtbl recibe las diez imágenes alineadas y genera una tabla con su información. mAdd recibe esa tabla, las imágenes y sus áreas, y la cabecera. Con eso escribe el mosaico y su mapa de cobertura. Las flechas muestran dependencias. Los envíos entre máquinas pasan por el coordinador. En la base cada caja de tarea es un job, doce en total. La ubicación y las dependencias se mantienen cuando agrupamos.

## 12. Dónde cambiamos el workflow

**11:05–12:25**

Probé dos tipos de agrupación de pares sin mover las tareas de máquina. En W2, P01 y P02 comparten la cabecera, de 318 bytes. Cada tarea sigue leyendo su propia imagen. Al revisar el grafo vemos que los otros pares de reproyección comparten esa misma cabecera. En W1 hay un solo par: la tabla y la combinación. Con jobs separados, las diez imágenes alineadas llegan a ambos jobs. Al reunir las tareas, llegan una vez y la tabla se lee dentro del mismo job. Los dos cambios quitan un job. El ahorro depende de cuánto pesan las entregas que desaparecen.

## 13. La mejor agrupación ahorró 13,53 %

**12:25–13:50**

El requerido fue el mismo porque las tareas conservaron los archivos y su ubicación. Al juntar la tabla y la combinación evitamos más de cuarenta y dos millones de bytes. El observado bajó un 13,53 % y DME pasó de 0,864625 a 0,999966. Los píxeles y la geometría del mosaico y del mapa coincidieron. La agrupación final también terminó antes en esta corrida. El primer job ya había empezado dieciocho segundos antes que en la base, cuando todavía faltaba ejecutar la agrupación final. La duración, por tanto, recoge diferencias que aparecen en varias etapas. Para escoger por volumen, la opción que medimos con menos bytes fue agrupar la tabla y la combinación.

## 14. Conclusiones

**13:50–14:30**

La cuenta independiente coincidió con Analyzer en los cinco patrones y los dos ambientes. En el mosaico completo, DME mejoró cuando la agrupación evitó entregar de nuevo imágenes que dos tareas podían compartir. La diferencia se explica por los archivos que dejaron de moverse. Mi conclusión es que DME permite medir la cercanía al requerido de una ejecución y explicar el exceso por archivo y destino. Para elegir una configuración por volumen miro el observado, y para elegirla por tiempo necesito medir duración en condiciones comparables. La evidencia corresponde a CondorIO y a los grafos y configuraciones probados. Gracias.

## 15. Resultados de los cinco patrones

**Respaldo**

Respaldo. Todas las razones usan los valores de las columnas requerido y observado. Cada celda corresponde a una ejecución. El observado por patrón quedó constante entre ambientes. La ubicación cambió el requerido en agregación y redistribución. En este último patrón, ambos productores quedaron en W1/W2 y W3/W4 respectivamente. El agregador y las etapas posteriores quedaron en W1 y W2 respectivamente. Así se pasó de un archivo productor remoto a dos. Los demás archivos conservaron el mismo número de destinos requeridos.

## 16. Duración con dos y cuatro workers

**Respaldo**

En agregación, los cinco productores pueden avanzar antes del agregador. Con cuatro máquinas arrancaron cuatro productores casi juntos. En los registros pasaron 16 segundos desde el envío hasta el evento de inicio del primer job con cuatro máquinas, frente a 6 con dos. La fase paralela comenzó más tarde y la ejecución completa duró cerca de cuatro segundos más. Con una corrida por ambiente se puede localizar el intervalo donde aparece la diferencia. Para atribuir esa espera a una causa concreta harían falta más ejecuciones y control de carga y planificación. En procesamiento, las seis tareas son independientes y la ejecución con cuatro terminó antes.

## 17. Qué entregas elimina cada agrupación

**Respaldo**

Respaldo. Para calcular el ahorro resté el multiconjunto de entregas de cada variante al de la base. Cada entrega se identifica por archivo, dirección, origen, destino y tamaño. La auditoría concilia los bytes y conteos nativos de las direcciones científicas, separando sus archivos auxiliares. Este desglose ubica el mecanismo de ahorro.

## 18. Alcance de las afirmaciones

**Respaldo**

Respaldo. Si cambia el requerido, DME compara proximidad a la cota de cada ubicación. La clasificación por bytes se obtiene con el observado. La cota es inferior bajo cobertura, y su alcanzabilidad depende de la configuración y de las reglas de transferencia. En M101 comparamos solo dos agrupaciones frente a la base. Para afirmar una mejora de tiempo habría que medir repetidamente y contrastar los intervalos del DAG. El objetivo de validación conserva como pendiente aislar el costo de captura nativa. El dato nuevo de M101 es la sensibilidad de DME, no una medición de ese costo.

## Preguntas del jurado

**¿Cuál agrupación optimiza más?** Entre las dos ensayadas, tabla y coadición. Ambas ahorran un job. La agrupación de dos reproyecciones evita una entrega de la cabecera. La agrupación final evita entregar de nuevo las diez imágenes reproyectadas y mover la tabla. La comparación se limita al mismo grafo, ubicación y política de transferencia.

**¿Hace falta un Montage más complejo?** M101 basta para explicar este mecanismo. El grafo completo tiene doce tareas y conserva los dos FITS finales. Si agrupo exactamente dos tareas sin cambiarlas de máquina, hay 45 pares posibles de reproyecciones en W2 y un par en W1. Los 45 comparten únicamente la cabecera de 318 bytes. El par de W1 comparte diez imágenes y consume la tabla que él mismo produce. Eso se deduce del grafo y del contrato de archivos. Medí una configuración de cada tipo. El análisis queda acotado a agrupar dos tareas con ubicación fija.

**¿Por qué distribución dio lo mismo con dos y cuatro workers?** Con dos workers, el productor quedó en W1 y dos consumidores en W2. Con cuatro workers, el productor quedó en W3 y un consumidor en W4. En cada caso hay una sola máquina remota que necesita g. El requerido son 10 MiB de entrada, 20 del intermedio y 50 de finales. El observado son 10, 60 y 50 MiB, respectivamente, porque se corroboraron cinco entregas de g a jobs separados y un retorno. DME es 80/120 en los dos casos.

**¿Por qué se llama mosaico completo?** Parte de las diez entradas FITS y llega a un mosaico FITS y su mapa de cobertura. Se usa la ruta oficial sin ajuste de fondo. Las tres ejecuciones recorren las mismas doce tareas científicas.

**¿Por qué se ven franjas en la portada?** La ruta del tutorial combina las imágenes sin igualar previamente sus fondos. Esa elección se mantuvo en las tres configuraciones. La portada muestra la imagen medida con un ajuste de contraste para visualización.

**¿Por qué DME subió en agregación con cuatro workers si el observado siguió igual?** Un productor adicional quedó lejos del agregador y su intermedio añadió dos entregas obligatorias. Cambió el requerido. Los bytes observados empataron.

**¿Por qué dos workers fueron más rápidos en algunos casos?** En agregación, los registros muestran 6 y 16 segundos desde el envío de los productores hasta la primera ejecución. La fase paralela comenzó más tarde con cuatro workers. Con una corrida por ambiente, esa localización del retraso queda respaldada y su causa específica queda abierta.

**¿Se mantuvo la salida científica?** Sí. El mosaico y su mapa de cobertura coincidieron en los datos binarios de píxeles y en las tarjetas FITS comparadas, incluidas las de geometría.

**¿Por qué DME queda cerca de uno?** En la agrupación final quedan 9 146 bytes de exceso. Son nueve entregas adicionales de la cabecera a W2, de 318 bytes cada una, más el retorno de la tabla al coordinador, de 6 284 bytes.

**¿Por qué una ejecución por variante?** El objetivo del contraste es cotejar una cuenta de bytes determinada por el grafo, los tamaños, la colocación y las entregas. La auditoría corrobora cada entrega. La duración se reporta como descripción de cada corrida.

**¿El requerido es siempre alcanzable?** La cobertura garantiza que es una cota inferior. Alcanzarla depende de las restricciones de los jobs y del mecanismo de transferencia. La tesis incluye un contraejemplo para un grafo concreto con jobs aislados y sin caché.

**¿Qué queda pendiente en los objetivos?** Se caracterizaron los patrones, se definió DME, se implementó el cálculo y se evaluaron la correctitud y la sensibilidad. La validación conserva un componente parcial, el costo de captura nativa.

**Si quedan dos minutos al empezar Montage:** muestra el grafo, señala tabla y coadición y explica qué entregas se eliminan. Cierra con el alcance de la comparación y el criterio para elegir por volumen.

## Cómo explicar cada resultado y su tiempo

Las marcas de eventos son segundos desde el inicio del flujo. La duración de DAGMan tiene mayor precisión. Cada comparación describe las corridas disponibles.

- **Procesamiento.** Las seis tareas tienen archivos propios. En ambos ambientes se requieren y se observan 120 MiB, seis entradas y seis finales. DME vale uno. Con cuatro workers comenzaron cuatro jobs a la vez, y con dos comenzaron dos. El intervalo entre el inicio del primero y el fin del último bajó de 14 a 9 s. El flujo completo pasó de 101,949 a 90,984 s.

- **Pipeline.** Las seis tareas en cadena quedaron en una sola máquina en ambos casos. La entrada y el final suman 20 MiB requeridos. Los cinco intermedios añaden un retorno y un reenvío por archivo, para 120 MiB observados. La ventana de los jobs científicos fue de 103 y 102 s. Tras el último job transcurrieron 26 y 22 s hasta el cierre. El flujo completo pasó de 181,368 a 176,423 s.

- **Agregación.** Cinco productores entregan sus intermedios a un agregador. Con cuatro workers, un productor adicional quedó fuera de la máquina del agregador y su archivo agregó 20 MiB requeridos. El observado se mantuvo en 160 MiB. La espera tras el primer envío pasó de 6 a 16 s y la ventana de jobs científicos pasó de 32 a 28 s. El flujo completo pasó de 106,254 a 110,199 s.

- **Distribución.** El único destino remoto de g explica por qué se conservaron 80 MiB requeridos, 120 MiB observados y DME de dos tercios. Con cuatro workers el productor terminó a los 62 s frente a 66 s con dos. DAGMan envió los consumidores a los 76 s frente a 81 s. El flujo pasó de 136,178 a 131,380 s.

- **Redistribución.** Con dos workers un productor estaba fuera de la máquina del agregador. Con cuatro estaban fuera los dos. El requerido pasó de 60 a 80 MiB y el observado quedó en 140 MiB. El primer job empezó 10 s después del envío con dos workers y 23 s después con cuatro. El flujo completo pasó de 151,274 a 161,405 s.

- **Montage.** La base duró 251,237 s. La agrupación de dos reproyecciones duró 256,224 s y su ventana de jobs científicos fue más larga, 170 frente a 156 s. La agrupación de tabla y combinación duró 222,195 s. Su primer job empezó 18 s antes que el de la base y su ventana de jobs científicos duró 10 s menos. La diferencia de duración ya se estaba acumulando antes de la agrupación final. El ahorro de bytes se atribuye a las entregas eliminadas. Para aislar su efecto temporal harían falta más ejecuciones.

## Evidencia

- Tutorial oficial de Montage: https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html
- Validación de cinco patrones, 10 de noviembre de 2026. RESULTADOS_REUNION.csv y jobstate.log de las cápsulas de agregación y redistribución.
- Experimento M101, 11 de noviembre de 2026. VERIFICACION_DEFENSA.json, auditorías independientes y FITS_EQUIVALENCE.json.
