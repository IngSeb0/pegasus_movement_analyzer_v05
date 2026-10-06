# Capítulo 7 — Resultados de la validación

Este capítulo reporta los resultados de la campaña controlada de Gate V para Analyzer v1. Se ejecutaron 31 workflows Pegasus/HTCondor independientes en diez condiciones que cubren los cinco patrones oficiales. Cada condición cuenta con al menos tres ejecuciones válidas; `process/same-w1/10 MiB` tiene cuatro réplicas métricas. Para las estadísticas temporales de esa condición se usan tres réplicas completas, porque el registro histórico `r01b` no conservó los límites de `T_gen`. No se imputaron tiempos ausentes.

## 7.1 Validez, oráculos y consistencia

Las 31 ejecuciones fueron aceptadas como `VALID`. En cada una, el placement observado coincidió con la condición, los valores de `Mreq` y `Mrec` coincidieron con los oráculos manuales y `Coverage=1`. En consecuencia, `Mobs` pudo informarse y coincidió con `Mrec` en todos los casos.

Cada artefacto se analizó tres veces. Las ternas de salidas canónicas fueron idénticas, lo que comprueba determinismo del análisis sobre el mismo run. Por separado, las métricas fueron idénticas entre workflows independientes de una misma condición. Las repeticiones del Analyzer no se contaron como réplicas experimentales.

## 7.2 Métricas por condición

Las cantidades siguientes son los valores observados por workflow y se expresan en MiB binarios, donde 1 MiB = 1 048 576 bytes. La columna $n$ indica el número de workflows métricos válidos.

| Patrón | Placement | Tamaño de entrada | $n$ | $M_{\mathrm{req}}$ | $M_{\mathrm{rec}}$ | Coverage | $M_{\mathrm{obs}}$ | DME |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Process | same-w1 | 10 MiB | 4 | 20 | 20 | 1 | 20 | 1.0000 |
| Pipeline | same-w1 | 10 MiB | 3 | 20 | 60 | 1 | 60 | 0.3333 |
| Data distribution | same-w1 | 10 MiB | 3 | 20 | 40 | 1 | 40 | 0.5000 |
| Data aggregation | same-w1 | 10 MiB | 3 | 80 | 160 | 1 | 160 | 0.5000 |
| Data redistribution | same-w1 | 10 MiB | 3 | 80 | 320 | 1 | 320 | 0.2500 |
| Pipeline | cross | 10 MiB | 3 | 40 | 60 | 1 | 60 | 0.6667 |
| Data distribution | cross | 10 MiB | 3 | 30 | 40 | 1 | 40 | 0.7500 |
| Data aggregation | cross | 10 MiB | 3 | 120 | 160 | 1 | 160 | 0.7500 |
| Data redistribution | cross | 10 MiB | 3 | 200 | 320 | 1 | 320 | 0.6250 |
| Process | same-w1 | 20 MiB | 3 | 40 | 40 | 1 | 40 | 1.0000 |

## 7.3 Cálculo manual reproducible de pipeline

El caso de `pipeline` permite reconstruir las magnitudes a mano. Hay tres tareas y seis ocurrencias científicas declaradas de 10 MiB: input, dos archivos intermedios y tres materiales de salida asociados al contrato. Todas las ocurrencias fueron confirmadas, por lo que

$$
|D_{\mathrm{sci}}|=6,\qquad |C_{\mathrm{sci}}|=6,\qquad \mathrm{Coverage}=\frac{6}{6}=1,
$$

$$
M_{\mathrm{obs}}=6\cdot 10\ \mathrm{MiB}=60\ \mathrm{MiB}=62\,914\,560\ \mathrm{B}.
$$

Con `same-w1`, el input y la salida final aportan 10 MiB cada uno; los intermedios quedan locales al worker. Así, $M_{\mathrm{req}}=20$ MiB y

$$
\mathrm{DME}_{\mathrm{same}}=\frac{20}{60}=\frac{1}{3}\approx0.3333.
$$

Con `cross`, el primer intermedio debe llegar a worker2 y el segundo regresar a worker1, además del input y el destino final: $M_{\mathrm{req}}=10+10+10+10=40$ MiB. Entonces

$$
\mathrm{DME}_{\mathrm{cross}}=\frac{40}{60}=\frac{2}{3}\approx0.6667.
$$

El mismo payload declarado y confirmado produce un lower bound diferente cuando cambia el placement observado. El ejemplo demuestra el cálculo de la métrica; no demuestra que una ruta de red física haya seguido una trayectoria específica.

## 7.4 Sensibilidad a placement y tamaño

| Patrón o factor | $M_{\mathrm{req}}$ base → variante | $M_{\mathrm{rec}}=M_{\mathrm{obs}}$ | DME base → variante |
|---|---:|---:|---:|
| Pipeline, same-w1 → cross | 20 → 40 MiB | 60 MiB | 0.3333 → 0.6667 |
| Data distribution, same-w1 → cross | 20 → 30 MiB | 40 MiB | 0.5000 → 0.7500 |
| Data aggregation, same-w1 → cross | 80 → 120 MiB | 160 MiB | 0.5000 → 0.7500 |
| Data redistribution, same-w1 → cross | 80 → 200 MiB | 320 MiB | 0.2500 → 0.6250 |
| Process, 10 → 20 MiB de input | 20 → 40 MiB | 20 → 40 MiB | 1.0000 → 1.0000 |

En las cuatro comparaciones de placement, $M_{\mathrm{rec}}$ y $M_{\mathrm{obs}}$ permanecieron constantes dentro de cada patrón y $M_{\mathrm{req}}$ cambió conforme a las ubicaciones requeridas. Al duplicar el tamaño de entrada de `process`, $M_{\mathrm{req}}$ y $M_{\mathrm{obs}}$ se duplicaron y la DME permaneció en uno. Estos resultados muestran sensibilidad coherente para los factores y niveles ejecutados; no comparan schedulers ni prueban optimalidad.

## 7.5 Duración por etapa

Los valores se presentan como media ± desviación estándar muestral, en segundos. En cada condición se usan tres cronometrajes completos. $T_{\mathrm{total}}$ es la ruta mínima medida, no una diferencia respecto a un baseline sin logs.

| Condición | $n$ | $T_{\mathrm{gen}}$ | $T_{\mathrm{collect}}$ | $T_{\mathrm{analyzer}}$ | $T_{\mathrm{total}}$ |
|---|---:|---:|---:|---:|---:|
| Process, same-w1, 10 MiB | 3 | 193.877 ± 21.325 | 2.816 ± 0.688 | 0.666 ± 0.263 | 197.359 ± 20.837 |
| Process, same-w1, 20 MiB | 3 | 170.069 ± 30.007 | 3.471 ± 2.401 | 0.811 ± 0.242 | 174.351 ± 27.786 |
| Pipeline, same-w1 | 3 | 211.138 ± 25.003 | 2.223 ± 1.196 | 0.715 ± 0.215 | 214.077 ± 23.924 |
| Pipeline, cross | 3 | 289.390 ± 34.401 | 2.385 ± 0.786 | 0.582 ± 0.184 | 292.358 ± 34.744 |
| Distribution, same-w1 | 3 | 230.123 ± 20.931 | 2.173 ± 0.671 | 0.508 ± 0.054 | 232.804 ± 20.213 |
| Distribution, cross | 3 | 254.864 ± 38.734 | 2.820 ± 1.651 | 0.639 ± 0.261 | 258.323 ± 37.013 |
| Aggregation, same-w1 | 3 | 260.627 ± 70.557 | 1.823 ± 0.619 | 0.917 ± 0.774 | 263.367 ± 69.774 |
| Aggregation, cross | 3 | 271.482 ± 15.675 | 2.188 ± 0.538 | 0.794 ± 0.567 | 274.464 ± 15.975 |
| Redistribution, same-w1 | 3 | 363.417 ± 89.944 | 2.761 ± 1.245 | 0.690 ± 0.072 | 366.868 ± 88.748 |
| Redistribution, cross | 3 | 474.078 ± 89.618 | 2.575 ± 1.336 | 0.879 ± 0.452 | 477.531 ± 91.062 |

$T_{\mathrm{gen}}$ incluye planificación, ejecución científica y generación de logs nativos. Su coeficiente de variación por condición estuvo entre 5.8 % y 27.1 % con $n=3$. Se informa como variabilidad normal observada y no como overhead atribuible a Analyzer.

## 7.6 Recursos del Analyzer y almacenamiento

| Medida post-mortem | Casos | Resultado observado |
|---|---:|---|
| $T_{\mathrm{collect}}$ | 31 | Media 2.527 s; rango 1.111–6.211 s |
| $T_{\mathrm{analyzer}}$ wall-clock | 31 | Media 0.726 s; rango 0.391–1.806 s |
| CPU del Analyzer, usuario / sistema | 31 | Medias 0.272 s / 0.083 s por invocación |
| RSS pico del Analyzer | 31 | Media 22.49 MiB; rango 21.24–24.11 MiB |
| Entrada lógica ofrecida al Analyzer | 31 | Media 18.617 MiB; rango 18.291–19.084 MiB |
| Informes primarios | 31 | Media 0.185 MiB; rango 0.053–0.379 MiB por run |
| Logs nativos `.log`, `.out`, `.err` | 31 | Media 210,273 B (0.2005 MiB); rango 120,232–334,561 B; total 6,518,472 B |
| Artefactos post-mortem adicionales preservados | 31 | Total 21.72 MiB; media 0.701 MiB; rango 0.135–1.356 MiB por run |

El inventario lógico adicional excluye inputs/outputs científicos, la copia de `workflow.yml` y el directorio nativo del run. Incluye history exportado, informes, metadatos y salidas de determinismo cuando estaban disponibles. El bundle compacto de evidencia ocupa 1.58 MiB, pero no incluye los árboles Pegasus completos preservados en el master.

`pegasus-analyzer analyze/statistics` tomó una media de 5.946 s en 21 casos y la verificación final de inventario/hash, 0.875 s en 21 casos; ambos son auxiliares posteriores al resultado y no se incluyen en la ruta mínima. No se capturaron CPU ni RSS para recolección, análisis auxiliar de Pegasus o hash final.

## 7.7 Síntesis de resultados

La campaña respalda el cálculo correcto y reproducible de las magnitudes para las diez condiciones ejecutadas, el acuerdo de los oráculos, la consistencia entre réplicas y la sensibilidad a los placements y tamaño seleccionados. El costo offline y el almacenamiento adicional quedan cuantificados. La evidencia no representa tráfico de red a nivel de paquetes, rendimiento de scheduler ni impacto causal del logging nativo. Todas las ejecuciones empíricas tuvieron cobertura completa; los casos con cobertura parcial permanecen evaluados en pruebas de software.
