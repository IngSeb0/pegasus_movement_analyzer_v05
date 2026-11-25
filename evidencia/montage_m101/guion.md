# Guion de defensa de DME

Once diapositivas principales. Duración objetivo **14:30**, con 30 segundos de margen. Tres diapositivas de respaldo para preguntas.

## 1. Evaluación del movimiento de datos en flujos científicos

**00:00–00:35**

Buenos días. Soy Luis Sebastián Contreras Díaz. Pensemos en dos ejecuciones del mismo flujo que entregan los mismos bytes. Una puede estar enviando archivos que sus tareas necesitan en máquinas distintas. La otra puede estar repitiendo entregas que ya tenía resueltas. Mi trabajo propone una forma de distinguirlas. La llamo DME, eficiencia del movimiento de datos. Voy a mostrar cómo se calcula y qué permite explicar en el mosaico astronómico de la portada.

## 2. El recorrido de un archivo intermedio

**00:35–01:50**

Un flujo científico organiza tareas que producen y consumen archivos. Pegasus prepara el plan. DAGMan respeta las dependencias y HTCondor asigna los jobs a los workers. Una tarea es una operación del flujo. Un job es la unidad que recibe HTCondor y puede contener varias tareas. En CondorIO, el coordinador entrega las entradas al job y recibe sus salidas declaradas. Supongamos que una tarea genera un archivo que otra necesita. Aunque ambas estén en el mismo worker, si corren en jobs aislados el archivo puede volver al coordinador y entrar de nuevo al segundo job. Si comparten job, la segunda puede leerlo en el mismo espacio de trabajo. El volumen total dice cuánto se entregó. Para interpretar esa cifra hace falta saber qué exigían el grafo, las máquinas utilizadas y el relevo por el coordinador.

## 3. Pregunta y objetivos

**01:50–02:50**

La pregunta es qué volumen mínimo imponen las dependencias y el relevo cuando ya conocemos dónde corrió cada tarea, y cómo se compara con las entregas completas confirmadas. El objetivo general es diseñar, implementar y validar una herramienta que calcule una métrica para evaluar esa eficiencia en ejecuciones de Pegasus. Para llegar ahí caractericé los patrones y las fuentes de datos, definí la métrica, automaticé el cálculo y evalué dos cosas. Primero, si la reconstrucción coincide con una cuenta independiente. Segundo, si DME refleja una intervención cuyo efecto se puede seguir archivo por archivo. Analyzer automatiza la lectura de los planes y registros. El aporte es la forma de interpretar el movimiento de datos que reconstruye.

## 4. Qué mide DME

**02:50–04:30**

En el numerador está el requerido. Para cada archivo anoto dónde se origina y qué máquinas necesitan recibirlo. Cuento una vez cada destino distinto del origen. Si un archivo producido por un worker se necesita en otro, CondorIO obliga a pasarlo por el coordinador, así que cuento el retorno y el envío al worker receptor. En el denominador está el observado. Sumo el tamaño por cada entrega completa corroborada. Una entrega adicional del mismo archivo vuelve a sumar bytes. Solo calculo la razón cuando el observado es positivo y puedo asociar cada obligación a una entrega distinta del mismo archivo y destino. En esas condiciones, DME igual a uno significa que todo el volumen observado coincide con el requerido. Por ejemplo, DME igual a un medio significa que la mitad del observado excede esa cota. Con un requerido fijo, una ejecución que mueve menos bytes mejora su DME. Si cambia la ubicación efectiva, también puede cambiar el numerador. Para elegir por volumen en ese caso miro primero los bytes observados y uso DME para explicar su composición.

## 5. Prueba 1 · Correctitud del cálculo

**04:30–05:40**

Para revisar el cálculo utilicé cinco estructuras distintas. En procesamiento las tareas son independientes. En pipeline forman una cadena. En agregación varias tareas producen archivos para una sola. En distribución varios consumidores leen el mismo archivo. En redistribución se agrega y luego se divide el resultado en particiones. Cada grafo tiene seis tareas, con archivos de diez MiB, la misma cantidad de trabajo de CPU por tarea y la misma política de retorno. Ejecuté una vez cada patrón con dos workers elegibles y una vez con cuatro. Cada worker ofreció un core. HTCondor hizo la asignación y la recuperé del historial. Comparé el requerido y el observado de Analyzer con una cuenta independiente que parte de los archivos, los destinos y las entregas corroboradas. Ambas cuentas coincidieron en las diez ejecuciones.

## 6. Cuenta a mano de un pipeline

**05:40–07:15**

El pipeline tiene seis tareas y cinco intermedios. En cada ejecución, las seis tareas quedaron en un mismo worker. Con dos workers fue W1 y con cuatro fue W3. Como las dependencias se resuelven en una sola máquina, los bytes requeridos son diez MiB de la entrada que llega desde el coordinador y diez del resultado final que vuelve. Eso da veinte. Para el observado, además de esos veinte, contamos cinco retornos de intermedios y cinco reenvíos al siguiente job. Cada uno pesa diez MiB. Son cien MiB adicionales, de modo que observamos ciento veinte. DME es veinte dividido por ciento veinte, un sexto. Analyzer entrega los mismos valores. Este ejemplo explica por qué que haya más workers disponibles no obliga a mover más datos. El grafo tiene una sola tarea científica lista a la vez, y en ambas ejecuciones se mantuvo la colocación de toda la cadena en una máquina.

## 7. Agregación · 160 MiB en ambos ambientes

**07:15–08:35**

El caso de agregación muestra qué agrega la métrica al total de bytes. Cinco productores generan un archivo de diez MiB cada uno. El agregador los reúne. Con jobs separados y retornos fijos, el coordinador recibe los cinco intermedios y los reenvía al agregador. El observado es el mismo en ambas corridas. Ahora miremos la ubicación efectiva. El agregador quedó en W1. Con dos workers, tres productores quedaron fuera de W1. Con cuatro, quedaron fuera cuatro. Ese cuarto intermedio remoto añade dos entregas obligatorias de diez MiB, una del productor al coordinador y otra del coordinador a W1. El requerido pasa de ciento veinte a ciento cuarenta. El observado sigue en ciento sesenta y DME sube de tres cuartos a siete octavos. Lo que cambió fue cuánto del volumen era obligatorio para esa ubicación. Si mi decisión es ahorrar bytes, las dos ejecuciones empatan.

## 8. Duración con dos y cuatro workers

**08:35–10:05**

Los workers ofrecen capacidad. Cuánto se aprovecha depende de las tareas listas y de los tiempos entre eventos del DAG. En agregación, los cinco productores pueden avanzar antes del agregador. Los registros muestran que con cuatro workers arrancaron cuatro productores casi juntos. Pero el intervalo desde el envío de los productores hasta el inicio del primero fue de 16 segundos con cuatro y de 6 con dos. La parte paralela empezó más tarde y la ejecución completa terminó cerca de cuatro segundos después. Esto identifica dónde aparece la diferencia, aunque con una corrida por ambiente queda abierta la causa de esa espera. En redistribución también observé un arranque inicial más tardío con cuatro. En procesamiento, donde las seis tareas son independientes, el resultado temporal favoreció a cuatro workers. Así que dos workers fueron más rápidos en agregación y redistribución en estas observaciones. Elegir por tiempo para futuras ejecuciones exigiría repetir y controlar las condiciones que afectan esos intervalos.

## 9. Prueba 2 · Un mosaico completo de M101

**10:05–11:45**

Para la segunda pregunta elegí la ruta de mosaico sin ajuste de fondo del tutorial oficial de Montage. La entrada son diez imágenes 2MASS de la misma banda y una cabecera de destino. Cada reproyección lleva una imagen al sistema común y genera también su imagen de área. Después, mImgtbl recoge la información de las imágenes reproyectadas. Finalmente, mAdd combina las imágenes con sus áreas y esa tabla. Los productos son el mosaico FITS y su mapa de cobertura. La línea base ejecuta las doce tareas como doce jobs. Probé dos formas de agrupar exactamente dos tareas. La primera reúne dos reproyecciones que comparten la cabecera. La segunda reúne la tabla con la coadición, que consumen las mismas imágenes reproyectadas. En las tres corridas mantuve los mismos archivos, tareas, dependencias, recursos y ubicación efectiva. Las reproyecciones corren en W2. La tabla y la coadición, en W1. Así la diferencia de bytes se puede relacionar con las entregas que elimina cada agrupación.

## 10. La agrupación final elimina más bytes

**11:45–13:45**

En las tres condiciones, el requerido es 269 021 436 bytes. Ese valor se conserva porque el trabajo, los archivos y sus destinos efectivos son los mismos. Con la base observé 311 142 466 bytes. Al agrupar dos reproyecciones ahorré 318 bytes, una entrega de la cabecera. Al agrupar la tabla con la coadición ahorré 42 111 884 bytes, el 13,53 % de la base. La mayor parte del ahorro, 42 105 600 bytes, se explica porque las diez imágenes reproyectadas entran una vez al job que comparten la tabla y la coadición. Los 6 284 bytes restantes corresponden al movimiento de la tabla que desapareció. En ambos casos se quita un job, así que contar jobs no alcanza para decidir cuánto se ahorra. DME subió de 0,864625 a 0,999966 con la segunda agrupación. El auditor y Analyzer coincidieron, y los datos de píxeles y las cabeceras comparadas del mosaico y del mapa de cobertura coinciden. Entre las configuraciones probadas, la agrupación final es la que mueve menos datos. Esa afirmación queda acotada a estas alternativas y a este entorno.

## 11. Conclusiones

**13:45–14:30**

La cuenta independiente coincidió con Analyzer en los cinco patrones y los dos ambientes. En el mosaico completo, DME mejoró cuando la agrupación evitó entregar de nuevo imágenes que dos tareas podían compartir. La diferencia se explica por los archivos que dejaron de moverse. Mi conclusión es que DME permite medir la cercanía al requerido de una ejecución y explicar el exceso por archivo y destino. Para elegir una configuración por volumen miro el observado, y para elegirla por tiempo necesito medir duración en condiciones comparables. La evidencia corresponde a CondorIO y a los grafos y configuraciones probados. Gracias.

## 12. Resultados de los cinco patrones

**Respaldo**

Respaldo. Todas las razones usan los valores de las columnas requerido y observado. Cada celda corresponde a una ejecución. El observado por patrón quedó constante entre ambientes. La ubicación cambió el requerido en agregación y redistribución. En este último patrón, ambos productores quedaron en W1/W2 y W3/W4 respectivamente. El agregador y las etapas posteriores quedaron en W1 y W2 respectivamente. Así se pasó de un archivo productor remoto a dos. Los demás archivos conservaron el mismo número de destinos requeridos.

## 13. Qué entregas elimina cada agrupación

**Respaldo**

Respaldo. Para calcular el ahorro resté el multiconjunto de entregas de cada variante al de la base. Cada entrega se identifica por archivo, dirección, origen, destino y tamaño. La auditoría concilia los bytes y conteos nativos de las direcciones científicas, separando sus archivos auxiliares. Este desglose ubica el mecanismo de ahorro.

## 14. Alcance de las afirmaciones

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
