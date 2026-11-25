# Guion de defensa de DME

Trece diapositivas principales. Duración objetivo **14:30**, con 30 segundos de margen. Cuatro diapositivas de respaldo para preguntas.

## 1. Evaluación del movimiento de datos en flujos científicos

**00:00–00:30**

Buenos días. Soy Luis Sebastián Contreras Díaz. En un flujo científico distribuido, una máquina puede tener listo el programa que debe ejecutar y seguir esperando los archivos que necesita. Mi trabajo estudia esos envíos. Quiero saber cuánto movimiento exige el flujo y qué entregas podrían reducirse al cambiar su forma de ejecución.

## 2. Un flujo de trabajo también mueve datos

**00:30–01:25**

Pensemos en un equipo que recoge observaciones, las procesa y reúne los resultados. Un workflow, o flujo de trabajo, define las tareas y qué archivos pasan de una a otra. Si se ejecuta en varias máquinas, cada tarea necesita recibir sus entradas antes de poder usarlas. En flujos intensivos en datos, las tareas pueden leer o producir archivos grandes o numerosos. Cada entrega ocupa recursos de transferencia. Analizar los envíos ayuda a decidir si un cambio de ejecución puede reducir ese volumen sin cambiar el resultado científico.

## 3. ¿Qué parte de los envíos era necesaria?

**01:25–02:30**

Pensemos en dos tareas, A y B, en la misma máquina de trabajo. A crea un archivo y B lo necesita. En la forma de ejecución que estudié, CondorIO, un archivo puede volver al coordinador y salir de nuevo hacia B, aunque B esté en la misma máquina. Cada uno de esos pasos se registra como una entrega. Si ambas tareas comparten un job, B puede leer la copia local. Un job es la unidad que se envía a ejecutar. El total de bytes reúne lo que exigían las dependencias y lo que añadió la forma de ejecución. Para localizar un ahorro necesito distinguir esas dos cantidades.

## 4. DME mide qué parte del volumen era necesaria

**02:30–03:40**

Mi objetivo fue definir una métrica para evaluar ese movimiento, automatizar el cálculo y validarlo. La métrica se llama DME, eficiencia del movimiento de datos. Pongo en el numerador los bytes requeridos por las dependencias y por la ubicación real de las tareas. En el denominador sumo los bytes de cada entrega completa que pude corroborar. Calculo la razón cuando el observado es positivo y puedo corroborar todas las entregas requeridas. El cociente indica qué fracción del volumen observado era requerida. Uno indica que los volúmenes coinciden. Un medio indica que la mitad del observado supera lo requerido. El desglose conserva el archivo y su destino, así que también permite ubicar el exceso.

## 5. Por qué cuenta el destino de cada archivo

**03:40–04:55**

Veamos un ejemplo de un solo archivo. Dos tareas leen el mismo archivo desde el coordinador. Si corren en la misma máquina, esa máquina necesita recibir una copia. Si corren en máquinas diferentes, hacen falta dos copias, una por destino. Supongamos que observé dos entregas en ambos casos. En el primero DME es un medio. En el segundo es uno. Los bytes observados son iguales y cambia lo que ese volumen significa. Por eso el requerido usa la ubicación efectiva y cuenta cada destino una vez. Si un archivo producido en un worker hace falta en otro, contamos también el paso obligatorio por el coordinador. Cuando el requerido es común, reducir el observado aumenta DME.

## 6. Plan de pruebas

**04:55–06:00**

Dividí la evaluación en dos preguntas. Primero, ¿la herramienta obtiene los volúmenes correctos? Usé cinco formas de conectar tareas, con dos o cuatro máquinas de trabajo disponibles y un núcleo por máquina. Mantuve seis tareas por flujo, archivos de diez MiB, el trabajo de CPU y las reglas de retorno. Segundo, ¿DME refleja un ahorro al cambiar la ejecución de un flujo real? Usé un mosaico completo de Montage. Corrí una base con tareas separadas y dos variantes que reúnen pares distintos. Conservé las entradas, el grafo y las máquinas. Eso permite atribuir el cambio de bytes a los envíos que elimina cada agrupación.

## 7. Cómo comprobamos el cálculo

**06:00–07:35**

Analyzer lee el plan de Pegasus y el historial de HTCondor para reconstruir qué tareas corrieron, en qué máquinas y qué entregas se completaron. Luego comparamos su resultado con una cuenta independiente, por archivo y destino. Tomemos el pipeline, una cadena de seis tareas. En las dos ejecuciones, la cadena completa quedó en una sola máquina. Lo requerido fue diez MiB de la entrada y diez del resultado final. Para el observado sumamos esos veinte y además cinco retornos al coordinador y cinco reenvíos al siguiente job. Cada uno pesa diez MiB. Eso da ciento veinte MiB observados. La cuenta a mano es veinte dividido por ciento veinte, un sexto. Analyzer dio los mismos tres valores en ambos ambientes.

## 8. El cálculo coincidió en los cinco patrones

**07:35–09:00**

Usé cinco tipos de flujo. En procesamiento, las tareas son independientes. En una cadena, cada una espera a la anterior. Agregación reúne varios archivos y distribución entrega uno a varias tareas. Redistribución reúne archivos y reparte el resultado en partes. La cuenta independiente y Analyzer coincidieron en los dos volúmenes y en DME en las diez ejecuciones. Miren agregación. Con dos y cuatro máquinas disponibles se movieron ciento sesenta MiB en ambos casos. Con cuatro quedó un productor más lejos del agregador. Su archivo tuvo que viajar al coordinador y luego a la máquina del agregador. El requerido subió veinte MiB y por eso subió DME. Esta es una buena razón para mostrar juntos el requerido, el observado y la métrica.

## 9. Un flujo real de astronomía con Montage

**09:00–09:50**

Con el cálculo comprobado, pasé a un flujo real. Montage toma imágenes astronómicas que cubren partes del cielo y las combina en un mosaico. Este es M101. Usé la ruta del tutorial sin ajuste de fondo y partí de diez imágenes 2MASS. La salida científica son dos archivos FITS: el mosaico y un mapa que indica qué área queda cubierta. La comparación pregunta si podemos producir esos mismos resultados haciendo menos entregas entre jobs.

## 10. El workflow completo de M101

**09:50–11:05**

A la izquierda están las diez tareas de reproyección, P01 a P10. Cada una toma su propia imagen y una cabecera común que define las coordenadas de destino. Cada tarea produce una imagen alineada y su mapa de área. Todas las reproyecciones corren en W2. En W1, mImgtbl recibe las diez imágenes alineadas y genera una tabla con su información. mAdd recibe esa tabla, las imágenes y sus áreas, y la cabecera. Con eso escribe el mosaico y su mapa de cobertura. Las flechas muestran dependencias. Los envíos entre máquinas pasan por el coordinador. En la base cada caja de tarea es un job, doce en total. La ubicación y las dependencias se mantienen cuando agrupamos.

## 11. Dónde cambiamos el workflow

**11:05–12:25**

En la primera variante junté dos tareas que alinean imágenes. Cada una sigue leyendo su propia imagen. Lo único que comparten es la cabecera con las coordenadas de destino. Por eso el ahorro es de 318 bytes. En la segunda variante junté la tarea que prepara la tabla con la que combina las imágenes. Con jobs separados, las diez imágenes alineadas llegan a los dos jobs. Al reunir las tareas, las imágenes llegan una sola vez. También se evita el reenvío de la tabla al job de combinación. Los dos cambios quitan un job. Para decidir cuál conviene por volumen, importa el tamaño de lo que las tareas comparten.

## 12. La mejor agrupación ahorró 13,53 %

**12:25–13:50**

Estos son los valores medidos. El requerido fue el mismo en las tres corridas porque cada tarea siguió usando la misma máquina y necesitó los mismos archivos. Comparen las dos filas de once jobs. La primera apenas cambia los bytes porque evita una cabecera. En la segunda desaparecen más de cuarenta y dos millones de bytes de reenvío. El volumen observado baja un 13,53 % y DME pasa de 0,864625 a 0,999966. El mosaico y el mapa de cobertura conservaron los mismos datos de píxeles y la misma geometría. El cálculo independiente coincidió con Analyzer. Por eso, para este flujo y entre las alternativas que probé, elegiría reunir la tabla y la combinación si el objetivo es mover menos datos.

## 13. Conclusiones

**13:50–14:30**

La cuenta independiente coincidió con Analyzer en los cinco patrones y los dos ambientes. En el mosaico completo, DME mejoró cuando la agrupación evitó entregar de nuevo imágenes que dos tareas podían compartir. La diferencia se explica por los archivos que dejaron de moverse. Mi conclusión es que DME permite medir la cercanía al requerido de una ejecución y explicar el exceso por archivo y destino. Para elegir una configuración por volumen miro el observado, y para elegirla por tiempo necesito medir duración en condiciones comparables. La evidencia corresponde a CondorIO y a los grafos y configuraciones probados. Gracias.

## 14. Resultados de los cinco patrones

**Respaldo**

Respaldo. Todas las razones usan los valores de las columnas requerido y observado. Cada celda corresponde a una ejecución. El observado por patrón quedó constante entre ambientes. La ubicación cambió el requerido en agregación y redistribución. En este último patrón, ambos productores quedaron en W1/W2 y W3/W4 respectivamente. El agregador y las etapas posteriores quedaron en W1 y W2 respectivamente. Así se pasó de un archivo productor remoto a dos. Los demás archivos conservaron el mismo número de destinos requeridos.

## 15. Duración con dos y cuatro workers

**Respaldo**

En agregación, los cinco productores pueden avanzar antes del agregador. Con cuatro máquinas arrancaron cuatro productores casi juntos. En los registros pasaron 16 segundos desde el envío hasta el evento de inicio del primer job con cuatro máquinas, frente a 6 con dos. La fase paralela comenzó más tarde y la ejecución completa duró cerca de cuatro segundos más. Con una corrida por ambiente se puede localizar el intervalo donde aparece la diferencia. Para atribuir esa espera a una causa concreta harían falta más ejecuciones y control de carga y planificación. En procesamiento, las seis tareas son independientes y la ejecución con cuatro terminó antes.

## 16. Qué entregas elimina cada agrupación

**Respaldo**

Respaldo. Para calcular el ahorro resté el multiconjunto de entregas de cada variante al de la base. Cada entrega se identifica por archivo, dirección, origen, destino y tamaño. La auditoría concilia los bytes y conteos nativos de las direcciones científicas, separando sus archivos auxiliares. Este desglose ubica el mecanismo de ahorro.

## 17. Alcance de las afirmaciones

**Respaldo**

Respaldo. Si cambia el requerido, DME compara proximidad a la cota de cada ubicación. La clasificación por bytes se obtiene con el observado. La cota es inferior bajo cobertura, y su alcanzabilidad depende de la configuración y de las reglas de transferencia. En M101 comparamos solo dos agrupaciones frente a la base. Para afirmar una mejora de tiempo habría que medir repetidamente y contrastar los intervalos del DAG. El objetivo de validación conserva como pendiente aislar el costo de captura nativa. El dato nuevo de M101 es la sensibilidad de DME, no una medición de ese costo.

## Preguntas del jurado

**¿Cuál agrupación optimiza más?** Entre las dos ensayadas, tabla y coadición. Ambas ahorran un job. La agrupación de dos reproyecciones evita una entrega de la cabecera. La agrupación final evita entregar de nuevo las diez imágenes reproyectadas y mover la tabla. La comparación se limita al mismo grafo, ubicación y política de transferencia.

**¿Por qué se llama mosaico completo?** Parte de las diez entradas FITS y llega a un mosaico FITS y su mapa de cobertura. Se usa la ruta oficial sin ajuste de fondo. Las tres ejecuciones recorren las mismas doce tareas científicas.

**¿Por qué se ven franjas en la portada?** La ruta del tutorial combina las imágenes sin igualar previamente sus fondos. Esa elección se mantuvo en las tres configuraciones. La portada muestra la imagen medida con un ajuste de contraste para visualización.

**¿Por qué DME subió en agregación con cuatro workers si el observado siguió igual?** Un productor adicional quedó lejos del agregador y su intermedio añadió dos entregas obligatorias. Cambió el requerido. Los bytes observados empataron.

**¿Por qué dos workers fueron más rápidos en algunos casos?** En agregación, los registros muestran 6 y 16 segundos desde el envío de los productores hasta la primera ejecución. La fase paralela comenzó más tarde con cuatro workers. Con una corrida por ambiente, esa localización del retraso queda respaldada y su causa específica queda abierta.

**¿Se mantuvo la salida científica?** Sí. El mosaico y su mapa de cobertura coincidieron en los datos binarios de píxeles y en las tarjetas FITS comparadas, incluidas las de geometría.

**¿Por qué DME queda cerca de uno?** En la agrupación final, el exceso restante es de 9 146 bytes. Para distinguir esta fracción de uno, la tabla muestra seis decimales.

**¿Por qué una ejecución por variante?** El objetivo del contraste es cotejar una cuenta de bytes determinada por el grafo, los tamaños, la colocación y las entregas. La auditoría corrobora cada entrega. La duración se reporta como descripción de cada corrida.

**¿El requerido es siempre alcanzable?** La cobertura garantiza que es una cota inferior. Alcanzarla depende de las restricciones de los jobs y del mecanismo de transferencia. La tesis incluye un contraejemplo para un grafo concreto con jobs aislados y sin caché.

**¿Qué queda pendiente en los objetivos?** Se caracterizaron los patrones, se definió DME, se implementó el cálculo y se evaluaron la correctitud y la sensibilidad. La validación conserva un componente parcial, el costo de captura nativa.

**Si quedan dos minutos al empezar Montage:** muestra el grafo, señala tabla y coadición y explica qué entregas se eliminan. Cierra con el alcance de la comparación y el criterio para elegir por volumen.

## Evidencia

- Tutorial oficial de Montage: https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html
- Validación de cinco patrones, 10 de noviembre de 2026. RESULTADOS_REUNION.csv y jobstate.log de las cápsulas de agregación y redistribución.
- Experimento M101, 11 de noviembre de 2026. VERIFICACION_DEFENSA.json, auditorías independientes y FITS_EQUIVALENCE.json.
