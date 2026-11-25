# Contraste de hipótesis

| Hipótesis | Cifras e interpretación |
|---|---|
| D1 | 30 comprobaciones, 9 con control FMA medido en la misma ubicación. Para las demás se reconstruyó la referencia de 10 MiB sobre la ubicación efectiva. Véase BYTES.csv y D1.json. |
| D2 | 13 de 13 condiciones con transferencia media como tramo mayor. El criterio por corrida se cumple en 29 de 29 corridas principales. Véase INTENSIVO.csv y corridas.csv. |
| D3 | 16 de 30 corridas dentro del 25 %. En promedio, se predijeron 210.365 s, el tramo exclusivo registró 163.567 s y la unión de los intervalos registró 185.833 s. Las transferencias pueden solaparse entre jobs y con la ejecución. Véase TRANSFERENCIA_VS_OBSERVADO.csv. |
| D4 | La transferencia no bajó en 1 de 5 patrones. Diferencia W4 − W2. PROCESS -30.500 s, PIPELINE +0.500 s, AGGREGATION -13.500 s, DISTRIBUTION -35.000 s, REDISTRIBUTION -2.500 s. Cada worker limita su salida al coordinador por separado. La concurrencia y el solapamiento del tramo exclusivo pueden variar. Véase INTENSIVO.csv. |
| D5 | No cumple la dirección en el promedio de 3 pares. AGR terminó antes en 1 de 3 bloques. W2-AGR − REP total 15.392 s y transferencia 11.667 s. El exceso evitado de 600 MiB predice 53.320 s de transferencia de entrada. Véase DIFERENCIAS_POR_BLOQUE.csv y los CSV de jobs. |
| D6 | Cumple la dirección en el promedio de 3 pares. AGR terminó antes en 3 de 3 bloques. W2-SEP − W2-AGR total 65.359 s y transferencia 56.667 s. El exceso evitado de 600 MiB predice 53.320 s de transferencia de entrada. Véase DIFERENCIAS_POR_BLOQUE.csv y los CSV de jobs. |
