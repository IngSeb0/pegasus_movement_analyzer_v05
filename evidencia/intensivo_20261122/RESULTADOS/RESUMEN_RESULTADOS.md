# Flujos intensivos en datos

Se aceptaron 30 workflows. Fase 2: 2 mediciones de enlace y 1 pilotos aceptados. Fase 3: 20 de 20 corridas de patrones y 9 de 9 corridas de contraste. Se conciliaron 324 direcciones científicas con residuo cero.

| Condición | n | Total (s) | Transferencia | Ejecución | Auxiliares | Cola | Cierre | Espera sin atribuir |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AGGREGATION-W2 | 2 | 374.092 ± 10.595 | 214.500 ± 0.707 | 52.500 ± 0.707 | 45.500 ± 6.364 | 28.000 ± 2.828 | 13.000 ± 1.414 | 21.000 ± 0.000 |
| AGGREGATION-W4 | 2 | 368.999 ± 10.709 | 201.000 ± 0.000 | 44.000 ± 0.000 | 47.500 ± 3.536 | 39.500 ± 6.364 | 15.500 ± 0.707 | 21.000 ± 0.000 |
| DISTRIBUTION-W2 | 2 | 286.988 ± 7.799 | 145.000 ± 2.828 | 43.500 ± 0.707 | 45.000 ± 7.071 | 18.500 ± 0.707 | 13.500 ± 0.707 | 21.000 ± 0.000 |
| DISTRIBUTION-W4 | 2 | 276.349 ± 0.086 | 110.000 ± 15.556 | 65.500 ± 27.577 | 50.000 ± 0.000 | 14.500 ± 10.607 | 15.000 ± 1.414 | 21.000 ± 0.000 |
| PIPELINE-W2 | 2 | 414.068 ± 3.608 | 221.500 ± 0.707 | 46.500 ± 0.707 | 42.500 ± 3.536 | 17.000 ± 7.071 | 45.500 ± 0.707 | 41.000 ± 0.000 |
| PIPELINE-W4 | 2 | 430.587 ± 6.997 | 222.000 ± 0.000 | 47.000 ± 1.414 | 42.500 ± 3.536 | 30.000 ± 15.556 | 48.500 ± 6.364 | 41.000 ± 0.000 |
| PROCESS-W2 | 2 | 258.553 ± 4.284 | 126.500 ± 16.263 | 43.000 ± 4.243 | 57.500 ± 3.536 | 9.500 ± 4.950 | 6.000 ± 0.000 | 16.000 ± 0.000 |
| PROCESS-W4 | 2 | 236.079 ± 13.472 | 96.000 ± 0.000 | 46.000 ± 0.000 | 58.000 ± 2.828 | 12.000 ± 8.485 | 8.500 ± 2.121 | 16.000 ± 0.000 |
| REDISTRIBUTION-W2 | 2 | 391.638 ± 7.035 | 207.500 ± 0.707 | 48.500 ± 0.707 | 45.000 ± 0.000 | 28.000 ± 11.314 | 31.500 ± 3.536 | 31.000 ± 0.000 |
| REDISTRIBUTION-W4 | 2 | 384.500 ± 18.335 | 205.000 ± 2.828 | 52.000 ± 1.414 | 47.500 ± 3.536 | 18.000 ± 11.314 | 30.500 ± 0.707 | 31.500 ± 0.707 |
| REP | 3 | 248.256 ± 5.119 | 115.000 ± 1.000 | 32.333 ± 1.528 | 48.333 ± 2.887 | 14.333 ± 8.145 | 16.667 ± 2.517 | 21.333 ± 0.577 |
| W2-AGR | 3 | 263.648 ± 20.799 | 126.667 ± 0.577 | 29.333 ± 0.577 | 48.333 ± 2.887 | 22.667 ± 17.673 | 15.333 ± 1.528 | 21.000 ± 0.000 |
| W2-SEP | 3 | 329.007 ± 3.204 | 183.333 ± 0.577 | 39.333 ± 1.528 | 45.000 ± 5.000 | 25.333 ± 7.638 | 15.333 ± 1.528 | 21.000 ± 0.000 |

Medias ± desviación estándar muestral en segundos. Pegasus se cronometra por separado en PLANIFICACION.csv. La espera sin atribuir se calcula por complemento. Las marcas de transferencia del historial tienen resolución de un segundo.

| Diferencia pareada | n | Total (s) | Transferencia | Ejecución | Auxiliares | Cola | Cierre | Espera sin atribuir |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W2-AGR − REP | 3 | 15.392 ± 20.040 | 11.667 ± 1.155 | -3.000 ± 2.000 | 0.000 ± 0.000 | 8.333 ± 17.010 | -1.333 ± 3.786 | -0.333 ± 0.577 |
| W2-SEP − W2-AGR | 3 | 65.359 ± 19.144 | 56.667 ± 0.577 | 10.000 ± 1.000 | -3.333 ± 7.638 | 2.667 ± 12.342 | 0.000 ± 2.646 | 0.000 ± 0.000 |
| REP − W2-SEP | 3 | -80.751 ± 7.571 | -68.333 ± 0.577 | -7.000 ± 3.000 | 3.333 ± 7.638 | -11.000 ± 12.767 | 1.333 ± 3.215 | 0.333 ± 0.577 |

La unión de intervalos y la suma por job se conservan en TRANSFERENCIA_VS_OBSERVADO.csv. El tramo exclusivo de transferencia aplica la prioridad de ejecución de la herramienta histórica. Un intervalo de transferencia concurrente con ejecución puede quedar fuera del tramo exclusivo. La duración clasificada como ejecución puede incluir tiempo antes de transferir la salida, además del bucle FMA.
Kickstart registra 171 mediciones de CPU del bucle FMA entre 1.424 y 1.426 s por tarea. Véase CPU_FMA_POR_TAREA.csv.
Ancho de banda de entrada. 11.80 MB/s.
Ancho de banda de salida. 11.93 MB/s.

# Contraste de hipótesis

| Hipótesis | Cifras e interpretación |
|---|---|
| D1 | 30 comprobaciones, 9 con control FMA medido en la misma ubicación. Para las demás se reconstruyó la referencia de 10 MiB sobre la ubicación efectiva. Véase BYTES.csv y D1.json. |
| D2 | 13 de 13 condiciones con transferencia media como tramo mayor. El criterio por corrida se cumple en 29 de 29 corridas principales. Véase INTENSIVO.csv y corridas.csv. |
| D3 | 16 de 30 corridas dentro del 25 %. En promedio, se predijeron 210.365 s, el tramo exclusivo registró 163.567 s y la unión de los intervalos registró 185.833 s. Las transferencias pueden solaparse entre jobs y con la ejecución. Véase TRANSFERENCIA_VS_OBSERVADO.csv. |
| D4 | La transferencia no bajó en 1 de 5 patrones. Diferencia W4 − W2. PROCESS -30.500 s, PIPELINE +0.500 s, AGGREGATION -13.500 s, DISTRIBUTION -35.000 s, REDISTRIBUTION -2.500 s. Cada worker limita su salida al coordinador por separado. La concurrencia y el solapamiento del tramo exclusivo pueden variar. Véase INTENSIVO.csv. |
| D5 | No cumple la dirección en el promedio de 3 pares. AGR terminó antes en 1 de 3 bloques. W2-AGR − REP total 15.392 s y transferencia 11.667 s. El exceso evitado de 600 MiB predice 53.320 s de transferencia de entrada. Véase DIFERENCIAS_POR_BLOQUE.csv y los CSV de jobs. |
| D6 | Cumple la dirección en el promedio de 3 pares. AGR terminó antes en 3 de 3 bloques. W2-SEP − W2-AGR total 65.359 s y transferencia 56.667 s. El exceso evitado de 600 MiB predice 53.320 s de transferencia de entrada. Véase DIFERENCIAS_POR_BLOQUE.csv y los CSV de jobs. |


Se retiró tc y se registró el estado posterior en los cinco nodos.

Con la ubicación de los consumidores fija, agrupar elimina tres entregas de 200 MiB. El ahorro medido del tramo de transferencia queda cerca de ΔO/B. REP distribuye los consumidores entre cuatro workers y conserva el mismo observado que W2-SEP. Los workers pueden devolver datos en paralelo porque cada uno tiene su propio TBF de salida. Este diseño no impone un único límite agregado de entrada en el coordinador. El historial y las tablas de jobs conservan los intervalos superpuestos. En la campaña previa de 10 MiB, W2-AGR tardó 48,091 s más que REP en promedio. En esta campaña la brecha media bajó a 15,392 s. Cambiaron los tamaños, la red y el presupuesto de cómputo de los consumidores, así que la comparación entre campañas es descriptiva.

El primer arranque terminó antes de aplicar tc y enviar jobs. El preflight leyó las líneas de contadores como si fueran declaraciones de colas. La corrección filtra las líneas qdisc. Las evidencias del ensayo y su cierre quedan en sesion.
