# Por qué varió el ahorro de transferencia de M4

**Causa de la variación del indicador: demostrada. Causa física de la anomalía de red o del servicio: no determinada.** El ahorro en las transferencias del cierre en W1 fue de 108, 108 y 107 s. El resto del workflow añadió variación en la duración y el solapamiento de las transferencias de reproyección. Al quitar la prioridad de ejecución, los ahorros fueron 96, 47 y 122 s. La prioridad elevó el intervalo entre el menor y el mayor ahorro de 75 a 139 s.

**Para la defensa**  
«Agrupar ahorró unos 108 segundos de transferencia al final en los tres bloques. El ahorro total varió porque las reproyecciones transfirieron durante tiempos distintos y, cuando coincidieron con ejecución, el desglose asignó esos segundos a ejecución».

## 1. Qué mide el tramo

Para cada segundo del DAG reconstruí tres conjuntos de intervalos. T contiene la unión de entradas y salidas de los jobs científicos. E contiene la unión de los intervalos entre el fin de entrada y el inicio de salida de esos jobs. A contiene la vida registrada de los jobs auxiliares. El tramo publicado cuenta T menos E. Por construcción, la transferencia gana sobre un auxiliar cuando ambos están activos y E está vacío. Se cotejaron los siete valores de la reconstrucción con `TIEMPOS.json`.

| Corrida | Solo transferencia, sin ejecución ni auxiliares | Coincide con auxiliares y se cuenta como transferencia | Coincide con ejecución y se cuenta como ejecución | Unión sin prioridad |
| --- | ---: | ---: | ---: | ---: |
| Piloto BASE | 806 | 9 | 411 | 1 226 |
| BASE B1 | 768 | 1 | 450 | 1 219 |
| FINAL B1 | 681 | 4 | 438 | 1 123 |
| FINAL B2 | 763 | 1 | 419 | 1 183 |
| BASE B2 | 820 | 0 | 410 | 1 230 |
| BASE B3 | 851 | 4 | 377 | 1 232 |
| FINAL B3 | 660 | 0 | 450 | 1 110 |

Son segundos de reloj. «Solo transferencia» describe la clasificación por intervalos. Los registros no indican cuántos bytes circularon en cada uno de esos segundos.

| Bloque | Ahorro en unión del cierre de W1 | Diferencia en unión de reproyecciones | Ahorro total sin prioridad | Diferencia de solapamiento con ejecución | Ahorro publicado |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 108 | −12 | 96 | 12 | 84 |
| 2 | 108 | −61 | 47 | −9 | 56 |
| 3 | 107 | 15 | 122 | −73 | 195 |

Todas las diferencias son BASE menos FINAL. En el bloque 3, FINAL solapó 73 s más con ejecución. Restar el solapamiento a cada variante elevó la diferencia de 122 a 195 s. En el bloque 2, las entradas de reproyección de FINAL ocuparon 788 s de unión frente a 719 s en BASE. Al combinar entradas y salidas, la unión de reproyecciones de FINAL excedió la de BASE en 61 s.

## 2. Tasas efectivas, concurrencia y espera

La prueba aislada de 1 GiB dio 47,72 Mbit/s en cada sentido (180 s). `TC.txt` registró el límite de 50 Mbit/s en el coordinador y en cada worker. Los bytes por job tomados de `history.json` se cotejaron con `history.long`. La tasa de una dirección por corrida divide la suma de bytes de esa dirección entre la duración de la unión de sus intervalos. La tasa ponderada por job usa la suma de duraciones de los jobs y mide un denominador distinto. Se dejan sin tasa las transferencias con bytes y duración registrada de cero segundos.

- **Entrada compartida del coordinador.** Seis corridas quedaron entre 47,36 y 47,52 Mbit/s. FINAL B2 dio 44,09 Mbit/s en la corrida y 43,17 Mbit/s en la entrada de reproyecciones. En esa corrida, el segundo cuartil de reproyecciones ordenadas por inicio dio 33,81 Mbit/s frente a 46,31–47,34 en los otros tres. Los grupos se definen por jobs: sus intervalos pueden solaparse entre cuartiles.
- **Anomalía localizada.** En FINAL B2, las entradas de P23, P57 y P88 duraron 77, 81 y 53 s en W3, W4 y W2. En los demás registros esos mismos jobs tardaron 5–10, 5–17 y 7–21 s, respectivamente. Las tres entradas lentas se solaparon entre los segundos 434 y 481 de la corrida. Cada una movió aproximadamente 29 MB. Los registros muestran una degradación simultánea del servicio aparente; no separan espera interna de HTCondor, contención del coordinador, red o almacenamiento.
- **Salida de los workers.** La tasa agregada por unión quedó entre 47,92 y 49,96 Mbit/s. Cada worker tiene su propio límite y la suma puede superar la tasa de una conexión aislada. La salida del mosaico en W1, por sí sola, duró 164–165 s.
- **Concurrencia.** Todas las corridas alcanzaron tres entradas científicas simultáneas. El tiempo con dos o más fue de 499 a 578 s y el mayor valor fue FINAL B2. La mediana entre envío y comienzo de entrada de las reproyecciones fue de 364–380 s en las otras corridas y 445 s en FINAL B2. Esa espera incluye el tiempo hasta disponer de ejecución y hasta iniciar la entrada. No identifica espera en la cola de red. En `jobs_intervalos.csv` quedan los valores por job.
- **Stage-in auxiliar.** Los DAG conservan `MAXJOBS stagein 10` y 16 nodos stage-in por corrida. El máximo observado de vidas de estos jobs en paralelo fue 10 en todas. Su solapamiento con transferencias científicas fue de 0–9 s. La anomalía de FINAL B2 ocurrió cientos de segundos después de iniciar el DAG. El máximo del DAG y el solapamiento inicial no explican esa anomalía.

## 3. Qué bytes salieron de la secuencia de cierre

Para M4, **ΔO es 616 161 787 B**, diferencia entre observado BASE y observado FINAL. **616 283 510 B** es el exceso de BASE sobre el requerido y contiene los **121 723 B** de exceso que permanecen en FINAL. Con la calibración de entrada, ΔO/B es **103,29 s**. La columna `bytes_transferidos` añade los archivos auxiliares de los jobs científicos. Su diferencia fue de 643 140 048 a 643 140 187 B, alrededor de **107,81 s** a esa tasa. Los dos cálculos tienen alcances distintos.

Los DAG y el historial ubican el ahorro en la secuencia dependiente de cierre. Las reproyecciones alimentan la tabla y el mosaico, y el mosaico depende de la tabla. Los intervalos de transferencia de reproyecciones y cierre no se solaparon en ninguna de las siete corridas. En BASE, TABLE recibe 643 044 934 B en 108 s. ADD recibe después unos 1 259 217 822 B en 212 s. En FINAL, el job agrupado recibe unos 1 259 143 600 B en 212 s. Por tanto, la entrada removida estaba en la secuencia final y su eliminación se observa directamente. El segundo de diferencia del bloque 3 corresponde a la salida del mosaico (164 frente a 165 s). Esto reconstruye el tramo serial observado en W1. Un camino crítico contrafactual de toda la ejecución con la misma asignación de segundos requeriría información de servicio y colas que los registros no contienen.

## 4. Orden, resolución e hipótesis descartadas

El orden real, con sus horas UTC y el predecesor, está en `corridas_intervalos.csv`. BASE subió de 769 a 820 y 855 s en las corridas principales; FINAL subió de 685 a 764 y después bajó a 660 s. La entrada de BASE se mantuvo cerca de la calibración. Los dos bloques con BASE primero produjeron el ahorro de 84 y 195 s; solo hay un bloque con FINAL primero. Estos datos descartan una deriva monotónica común como descripción de la secuencia. El efecto causal del orden y las perturbaciones de infraestructura quedan sin identificar.

El total de DAGMan difiere del total entero del jobstate entre −0,737 y +0,347 s. Esa concordancia controla los extremos del DAG; no acota a ±1 s una unión con cientos de fronteras. La cuantización se ve en devoluciones positivas que aparecen como 0 s. Incluso asignando ±1 s a cada extremo de una entrada, las diferencias de 32–67 s observadas entre las entradas anómalas y el mayor tiempo del mismo job en las otras corridas quedan fuera de esa resolución. Los 73 s de diferencia de solapamiento del bloque 3 se reconstruyeron a partir de todos los intervalos enteros. Su valor exacto a resolución subsegundo queda indeterminado.

En conjunto quedan descartados como explicaciones suficientes la variación de los bytes científicos observados, una variación apreciable del servicio de entrada en el cierre de W1, cambios en el tope de stage-in y un error de redondeo del tiempo total del DAG. La evidencia localiza el problema de FINAL B2 y cuantifica la contribución del solapamiento. No hay telemetría continua de paquetes, colas internas ni uso de red o disco con la cual atribuir el origen de la anomalía.

## 5. Precisión para una medición posterior

Para estimar la **media** del ahorro por bloque, con un intervalo bilateral del 95 % y semiancho de **25,82 s** (25 % de 103,29), se usa la desviación muestral de **73,51 s** de los tres pares. La primera n que cumple `t(0.975,n−1) × 73.51 / √n ≤ 25.82` es **34 pares, 68 corridas**. Es una cuenta orientativa con tres observaciones y supone pares independientes y variabilidad similar. Aumentar n mejora la precisión de la media; el cumplimiento de cada bloque requiere controlar la variabilidad del diseño.

Si la pregunta es cuánto tarda en desaparecer la segunda entrega, la medida directa es el intervalo de entrada en el cierre serial de W1, con ambos órdenes balanceados y una calibración aislada por bloque. El rango de 107–108 s del cierre observado muestra por qué conviene esa medida para aislar el mecanismo. Se puede conservar el tramo global como una medida distinta del efecto sobre el workflow completo. El veredicto publicado de M4 permanece «No».

## Archivos reproducibles

- `corridas_intervalos.csv`, `jobs_intervalos.csv`, `tasas_concurrencia.csv`, `tasas_por_cuartil.csv`, `bloques_descomposicion.csv` y `precision_muestra.csv`.
- `diagnostico_m4.png` reúne la descomposición, tasas, concurrencia y comparación por bloque.
- `analizar.py` regenera las tablas y la figura con Python, Matplotlib y SciPy. Lee los registros archivados, `ANCHO_DE_BANDA.json`, `PREDICCIONES.json` y el lector original de `tabla_tiempos.py`. No modifica los archivos fuente.
