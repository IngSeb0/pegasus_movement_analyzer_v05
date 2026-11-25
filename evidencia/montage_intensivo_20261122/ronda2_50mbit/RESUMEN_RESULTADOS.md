# Montage M101 · Ronda enmendada a 50 Mbit/s

Se conservaron los planes, las 147 imágenes y las hipótesis selladas. El límite de red se cambió después de conocer el piloto a 100 Mbit/s.

## Comparación de los pilotos

| Medida | 100 Mbit/s | 50 Mbit/s |
| --- | ---: | ---: |
| Ancho de banda de entrada (Mbit/s) | 94,39 | 47,72 |
| Ancho de banda de salida (Mbit/s) | 95,44 | 47,72 |
| Duración DAGMan (s) | 837,556 | 1 408,221 |
| Transferencia CondorIO (s) | 289 | 815 |
| Ejecución (s) | 394 | 465 |
| Jobs auxiliares (s) | 63 | 66 |
| Espera de máquina (s) | 49 | 17 |
| Cierre y post-script (s) | 21 | 23 |
| Espera de DAGMan (s) | 21 | 22 |

El piloto a 50 Mbit/s superó el criterio.
Entre los dos pilotos el tramo de transferencia aumentó 526 s. La estimación previa de 578 s era una aproximación basada en duplicar el primer tramo. La comparación entre límites usa un piloto por límite y es descriptiva.

## Matriz

Se conservaron 6 corridas principales auditadas.
El presupuesto permitió programar 3 bloques rotados.
Los planes prevén un ahorro de 616 161 787 B, equivalente a 103,29 s con la tasa de entrada medida.

| Variante | Requerido (B) | Observado (B) | DME exacta |
| --- | ---: | ---: | ---: |
| MG-BASE | 3 744 551 296 | 4 360 834 806 | 1872275648/2180417403 |
| MG-FINAL | 3 744 551 296 | 3 744 673 019 | 3744551296/3744673019 |

| Variante | Medida | n | Promedio ± desviación (s) |
| --- | --- | ---: | ---: |
| MG-BASE | duracion_dagman_s | 3 | 1 442,95 ± 31,60 |
| MG-BASE | tramo_ejecucion_s | 3 | 477,67 ± 22,55 |
| MG-BASE | tramo_transferencia_s | 3 | 814,67 ± 43,25 |
| MG-BASE | tramo_auxiliares_s | 3 | 67,67 ± 6,66 |
| MG-BASE | tramo_cola_s | 3 | 38,00 ± 10,82 |
| MG-BASE | tramo_cierre_post_s | 3 | 24,00 ± 2,65 |
| MG-BASE | tramo_dagman_s | 3 | 21,00 ± 0,00 |
| MG-FINAL | duracion_dagman_s | 3 | 1 305,32 ± 46,70 |
| MG-FINAL | tramo_ejecucion_s | 3 | 489,33 ± 9,61 |
| MG-FINAL | tramo_transferencia_s | 3 | 703,00 ± 54,29 |
| MG-FINAL | tramo_auxiliares_s | 3 | 69,00 ± 5,29 |
| MG-FINAL | tramo_cola_s | 3 | 13,67 ± 4,16 |
| MG-FINAL | tramo_cierre_post_s | 3 | 14,33 ± 2,08 |
| MG-FINAL | tramo_dagman_s | 3 | 16,33 ± 0,58 |

| Bloque | BASE − FINAL en transferencia (s) | BASE − FINAL total (s) |
| --- | ---: | ---: |
| 1 | 84,00 | 113,97 |
| 2 | 56,00 | 106,85 |
| 3 | 195,00 | 192,08 |

El ahorro medio por bloque fue 111,67 s en transferencia y 137,63 s en duración total. La agrupación reúne en W1 dos tareas que ya eran consecutivas por dependencia.

El reparto temporal asigna cada segundo a un solo tramo. Los segundos de ejecución corresponden a tiempo de pared de los jobs según esa clasificación.

Los registros por corrida están en `evidencia_nativa/`. El cierre y la red se documentan en `VMS.md` y `TC.txt`.
