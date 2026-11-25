# Guion de defensa de DME

Trece diapositivas principales. Duración objetivo **14:30**, con 30 segundos de margen. Tres diapositivas de respaldo para preguntas.

## 1. Evaluación del movimiento de datos en flujos científicos

**00:00–00:30**

Buenos días. Soy Luis Sebastián Contreras Díaz. Cuando un equipo científico ejecuta un flujo en varias máquinas, sus archivos también tienen que moverse. Mi pregunta es cuánto de ese movimiento hace falta y cuánto se puede reducir. Para explicarlo, voy a empezar con un producto que todos podemos ver: un mosaico del cielo.

## 2. De diez imágenes a un mosaico del cielo

**00:30–01:20**

Este es el mosaico de M101 que salió del experimento. Para construirlo, el programa toma diez imágenes del cielo, las alinea y las combina. Cada operación es una tarea. Un flujo de trabajo, o workflow, indica qué tareas se hacen y qué archivos pasan de una a otra. En los flujos intensivos en datos, esas tareas leen o generan muchos archivos o archivos grandes. Si corren en varias máquinas, hay que entregar cada archivo donde se necesita. Aquí surge el problema: dos tareas pueden pedir por separado una imagen que podrían compartir.

## 3. Un archivo puede viajar dos veces

**01:20–02:25**

Pensemos en dos tareas, A y B, en una misma máquina de trabajo. A crea un archivo y B lo necesita. Si las tareas corren por separado, el archivo puede volver al coordinador y salir de nuevo hacia B. Si las reúno en un mismo job, B puede leer la copia local. Un job es la unidad que se envía a ejecutar y puede contener varias tareas. Este es el problema de la tesis: el total de bytes registra todas las entregas juntas. Para saber dónde ahorrar, necesito distinguir qué entregas eran necesarias y cuáles aparecieron por la forma de ejecutar el flujo.

## 4. Pregunta y objetivos

**02:25–03:10**

Quiero saber cuántos bytes necesita mover un flujo, dadas sus dependencias y las máquinas que usó, y compararlos con los bytes que efectivamente se entregaron. Definí DME para responder esa pregunta. Analyzer hace la cuenta a partir de los planes de Pegasus y los registros de HTCondor. La evaluación tiene dos partes: revisar el cálculo con ejemplos que puedo resolver a mano y probar si DME detecta un ahorro cuando agrupo tareas en Montage.

## 5. Qué mide DME

**03:10–04:35**

En el numerador está el requerido. Para cada archivo anoto dónde se origina y qué máquinas necesitan recibirlo. Cuento una vez cada destino distinto del origen. Si un archivo producido por un worker se necesita en otro, CondorIO obliga a pasarlo por el coordinador, así que cuento el retorno y el envío al worker receptor. En el denominador está el observado. Sumo el tamaño por cada entrega completa corroborada. Una entrega adicional del mismo archivo vuelve a sumar bytes. Solo calculo la razón cuando el observado es positivo y puedo asociar cada obligación a una entrega distinta del mismo archivo y destino. En esas condiciones, DME igual a uno significa que todo el volumen observado coincide con el requerido. Por ejemplo, DME igual a un medio significa que la mitad del observado excede esa cota. Con un requerido fijo, una ejecución que mueve menos bytes mejora su DME. Si cambia la ubicación efectiva, también puede cambiar el numerador. Para elegir por volumen en ese caso miro primero los bytes observados y uso DME para explicar su composición.

## 6. Prueba 1 · Correctitud del cálculo

**04:35–05:40**

Para revisar el cálculo utilicé cinco estructuras distintas. En procesamiento las tareas son independientes. En pipeline forman una cadena. En agregación varias tareas producen archivos para una sola. En distribución varios consumidores leen el mismo archivo. En redistribución se agrega y luego se divide el resultado en particiones. Cada grafo tiene seis tareas, con archivos de diez MiB, la misma cantidad de trabajo de CPU por tarea y la misma política de retorno. Ejecuté una vez cada patrón con dos workers elegibles y una vez con cuatro. Cada worker ofreció un core. HTCondor hizo la asignación y la recuperé del historial. Comparé el requerido y el observado de Analyzer con una cuenta independiente que parte de los archivos, los destinos y las entregas corroboradas. Ambas cuentas coincidieron en las diez ejecuciones.

## 7. La cuenta a mano en una cadena

**05:40–07:00**

El pipeline tiene seis tareas y cinco intermedios. En cada ejecución, las seis tareas quedaron en un mismo worker. Con dos workers fue W1 y con cuatro fue W3. Como las dependencias se resuelven en una sola máquina, los bytes requeridos son diez MiB de la entrada que llega desde el coordinador y diez del resultado final que vuelve. Eso da veinte. Para el observado, además de esos veinte, contamos cinco retornos de intermedios y cinco reenvíos al siguiente job. Cada uno pesa diez MiB. Son cien MiB adicionales, de modo que observamos ciento veinte. DME es veinte dividido por ciento veinte, un sexto. Analyzer entrega los mismos valores. Este ejemplo explica por qué que haya más workers disponibles no obliga a mover más datos. El grafo tiene una sola tarea científica lista a la vez, y en ambas ejecuciones se mantuvo la colocación de toda la cadena en una máquina.

## 8. Los mismos bytes, dos valores de DME

**07:00–08:10**

El caso de agregación muestra qué agrega la métrica al total de bytes. Cinco productores generan un archivo de diez MiB cada uno. El agregador los reúne. Con jobs separados y retornos fijos, el coordinador recibe los cinco intermedios y los reenvía al agregador. El observado es el mismo en ambas corridas. Ahora miremos la ubicación efectiva. El agregador quedó en W1. Con dos workers, tres productores quedaron fuera de W1. Con cuatro, quedaron fuera cuatro. Ese cuarto intermedio remoto añade dos entregas obligatorias de diez MiB, una del productor al coordinador y otra del coordinador a W1. El requerido pasa de ciento veinte a ciento cuarenta. El observado sigue en ciento sesenta y DME sube de tres cuartos a siete octavos. Lo que cambió fue cuánto del volumen era obligatorio para esa ubicación. Si mi decisión es ahorrar bytes, las dos ejecuciones empatan.

## 9. Duración con dos y cuatro workers

**08:10–09:25**

Los workers ofrecen capacidad. Cuánto se aprovecha depende de las tareas listas y de los tiempos entre eventos del DAG. En agregación, los cinco productores pueden avanzar antes del agregador. Los registros muestran que con cuatro workers arrancaron cuatro productores casi juntos. Pero el intervalo desde el envío de los productores hasta el inicio del primero fue de 16 segundos con cuatro y de 6 con dos. La parte paralela empezó más tarde y la ejecución completa terminó cerca de cuatro segundos después. Esto identifica dónde aparece la diferencia, aunque con una corrida por ambiente queda abierta la causa de esa espera. En redistribución también observé un arranque inicial más tardío con cuatro. En procesamiento, donde las seis tareas son independientes, el resultado temporal favoreció a cuatro workers. Así que dos workers fueron más rápidos en agregación y redistribución en estas observaciones. Elegir por tiempo para futuras ejecuciones exigiría repetir y controlar las condiciones que afectan esos intervalos.

## 10. Prueba 2 · Cómo Montage construye M101

**09:25–10:40**

Volvamos al mosaico del comienzo. Seguí la ruta sin ajuste de fondo del tutorial de Montage. En una máquina se alinean las diez imágenes al mismo sistema de coordenadas. La tabla registra qué imágenes hay y dónde cae cada una. El último paso combina las imágenes usando esa tabla y sus mapas de área. A esa combinación se le llama coadición. La base ejecuta las doce tareas por separado. En las variantes mantuve las mismas entradas, operaciones, salidas y máquinas. Cambié qué par de tareas comparte un job.

## 11. Qué comparte cada par de tareas

**10:40–12:00**

En la primera variante junté dos tareas que alinean imágenes. Cada una sigue leyendo su propia imagen. Lo único que comparten es la cabecera con las coordenadas de destino. Por eso el ahorro es de 318 bytes. En la segunda variante junté la tarea que prepara la tabla con la que combina las imágenes. Con jobs separados, las diez imágenes alineadas llegan a los dos jobs. Al reunir las tareas, las imágenes llegan una sola vez. También se evita el reenvío de la tabla al job de combinación. Los dos cambios quitan un job. Para decidir cuál conviene por volumen, importa el tamaño de lo que las tareas comparten.

## 12. La mejor agrupación ahorró 13,53 %

**12:00–13:45**

Estos son los valores medidos. El requerido fue el mismo en las tres corridas porque cada tarea siguió usando la misma máquina y necesitó los mismos archivos. Comparen las dos filas de once jobs. La primera apenas cambia los bytes porque evita una cabecera. En la segunda desaparecen más de cuarenta y dos millones de bytes de reenvío. El volumen observado baja un 13,53 % y DME pasa de 0,864625 a 0,999966. El mosaico y el mapa de cobertura conservaron los mismos datos de píxeles y la misma geometría. El cálculo independiente coincidió con Analyzer. Por eso, para este flujo y entre las alternativas que probé, elegiría reunir la tabla y la combinación si el objetivo es mover menos datos.

## 13. Conclusiones

**13:45–14:30**

La cuenta independiente coincidió con Analyzer en los cinco patrones y los dos ambientes. En el mosaico completo, DME mejoró cuando la agrupación evitó entregar de nuevo imágenes que dos tareas podían compartir. La diferencia se explica por los archivos que dejaron de moverse. Mi conclusión es que DME permite medir la cercanía al requerido de una ejecución y explicar el exceso por archivo y destino. Para elegir una configuración por volumen miro el observado, y para elegirla por tiempo necesito medir duración en condiciones comparables. La evidencia corresponde a CondorIO y a los grafos y configuraciones probados. Gracias.

## 14. Resultados de los cinco patrones

**Respaldo**

Respaldo. Todas las razones usan los valores de las columnas requerido y observado. Cada celda corresponde a una ejecución. El observado por patrón quedó constante entre ambientes. La ubicación cambió el requerido en agregación y redistribución. En este último patrón, ambos productores quedaron en W1/W2 y W3/W4 respectivamente. El agregador y las etapas posteriores quedaron en W1 y W2 respectivamente. Así se pasó de un archivo productor remoto a dos. Los demás archivos conservaron el mismo número de destinos requeridos.

## 15. Qué entregas elimina cada agrupación

**Respaldo**

Respaldo. Para calcular el ahorro resté el multiconjunto de entregas de cada variante al de la base. Cada entrega se identifica por archivo, dirección, origen, destino y tamaño. La auditoría concilia los bytes y conteos nativos de las direcciones científicas, separando sus archivos auxiliares. Este desglose ubica el mecanismo de ahorro.

## 16. Alcance de las afirmaciones

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
