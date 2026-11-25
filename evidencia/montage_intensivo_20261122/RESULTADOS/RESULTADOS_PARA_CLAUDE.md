# Montage M101 con red limitada · 22 de noviembre de 2026

## Entradas y planes cotejados

IRSA SIA entregó 167 filas de catálogo Atlas J de 2MASS. El filtro cuadrado de 2,0° × 2,0° conservó 147 centros. Los FITS descomprimidos suman 303 059 520 bytes y sus SHA-256 están en `ENTRADAS.json`. `mImgtbl` indexó las 147 imágenes sin errores y `mMakeHdr` construyó la cabecera de 7 536 × 8 104 píxeles. El área de selección y las hipótesis selladas se conservaron.

El cotejo de los `.sub` nativos coincidió con la cuenta desde el grafo y los grupos. Estos valores son **predicciones del plan**.

| Variante | Jobs científicos | Requerido (B) | Observado previsto (B) | DME prevista |
| --- | ---: | ---: | ---: | ---: |
| MG-BASE | 149 | 3 744 551 296 | 4 360 834 806 | 0,858677630 |
| MG-FINAL | 148 | 3 744 551 296 | 3 744 673 019 | 0,999967494 |

El plan agrupado elimina 616 161 787 bytes en entregas a W1: una entrega de cada imagen alineada y la entrega de la tabla de imágenes al job de mosaico. El requerido se conserva porque todas las tareas mantienen la ubicación. La cuenta exacta y las direcciones retiradas están en `PLAN_ACCOUNTS.json` y `PREDICCIONES.json`.

## Medición

Se ejecutó un piloto MG-BASE. Analyzer y la auditoría de los registros coincidieron entre sí y con el plan en 3 744 551 296 B requeridos, 4 360 834 806 B observados y DME exacta de 1 872 275 648 / 2 180 417 403. El exceso del piloto fue 616 283 510 B. Las 298 direcciones de entrada o salida de jobs científicos conciliaron con residuo cero. La calibración de 1 GiB dio 91 s de entrada y 90 s de salida, equivalentes a 94,4 y 95,4 Mbit/s.

El DAG duró 837,556 s. El desglose asigna cada segundo de la ventana a un solo tramo, con prioridad para la ejecución cuando se solapa con transferencia. El tramo de ejecución representa tiempo de pared de los jobs en esa clasificación.

| Tramo | Segundos |
| --- | ---: |
| Ejecución | 394 |
| Transferencias CondorIO | 289 |
| Jobs auxiliares de Pegasus | 63 |
| Espera de máquina | 49 |
| Cierre y post-script | 21 |
| Espera de DAGMan | 21 |

**Decisión del protocolo.** La transferencia fue el segundo tramo en duración. La ejecución la superó por 105 s. El piloto queda como evidencia de la condición de parada y la fase 3 no se inició. El ahorro de 616 161 787 B corresponde al plan de FINAL. Con los 11 799 360,70 B/s medidos de entrada, equivale a una predicción de 52,22 s de transferencia. La reducción efectiva de tiempo, el ahorro efectivo de bytes en FINAL y la igualdad entre sus salidas quedan pendientes de una comparación ejecutada. El número de observaciones por variante impide estimar desviaciones o diferencias por bloque.

El detalle se puede reproducir a partir de `evidencia_nativa/`, `PILOTO.json`, `BYTES.csv`, `corridas.csv` y `ANCHO_DE_BANDA.json`. El estado de las máquinas y la restauración de red se documentan en `VMS.md` y `TC.txt`.
