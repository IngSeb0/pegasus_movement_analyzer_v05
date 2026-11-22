# Plan fijado y verificación final de la campaña DME

**Estado final verificado:** se completaron las 63 ejecuciones principales previstas: seis por cada condición sintética y tres por cada variante de Montage. Los doce pilotos válidos se analizaron aparte; se preservó un fallo técnico CRLF sin DME. Total: 76 intentos y 75 observaciones evaluables.

Se mantuvieron la matriz y el orden relativo originales durante tres sesiones, cuyas pausas se documentan. Las 312 direcciones principales (368 contando pilotos) conciliaron exactamente. Los finales sintéticos coincidieron por SHA256; en Montage coincidieron dimensiones, máscaras y píxeles, con diferencia máxima cero. Las cinco VMs quedaron desasignadas y SSH fue restaurado.

Los apartados siguientes describen el diseño y sus predicciones. Este cierre procede de los registros auditados y conserva separado el pilotaje de la muestra principal.

## Preguntas y alcance

La campaña examina cuatro preguntas acotadas:

1. ¿DME distingue la reducción de entregas por agrupación del pipeline y del archivo compartido, y la invariancia al agrupar particiones distintas?
2. ¿Un mismo volumen observado expresa relaciones distintas con las obligaciones? Se interpreta GL3/GD4 sin clasificar globalmente trabajos diferentes.
3. ¿Qué parte del exceso puede eliminarse omitiendo retornos intermedios dentro de un grupo, sin cambiar los finales científicos?
4. ¿Se observan agrupación y retorno selectivo con las dos operaciones reales de Montage, manteniendo ubicación, entradas y finales verificables?

La respuesta primaria es el volumen observado, desglosado en entregas identificables. El volumen requerido (`M_req`) expresa las obligaciones por archivo, destino y relevo según la ubicación efectiva; DME se calcula como `M_req / M_obs`. DME contextualiza la proximidad a esa referencia. Cuando `M_req` es común, su orden coincide con el orden inverso de `M_obs`; cuando difiere, DME por sí sola no ordena los volúmenes observados. La duración es secundaria y descriptiva, no una medida de DME.

## Diseño y tamaño previsto

Se fijan 12 condiciones. Nueve condiciones sintéticas tendrán seis ejecuciones principales cada una; tres variantes de Montage tendrán tres cada una. El diseño comprende 63 ejecuciones principales. Se añadirá un piloto válido por condición, 12 en total, analizados separadamente. Durante el pilotaje, el primer intento de Montage falló por CRLF antes de iniciar la aplicación. Se conservó sin DME. Una enmienda técnica anterior a la muestra principal corrigió ese formato con identificadores nuevos y elevó el máximo a 76 intentos, manteniendo las 75 observaciones evaluables previstas. No se autorizó reposición automática.

| Familia | Condición | Contraste | n principal previsto |
|---|---|---|---:|
| Pipeline | L01 | Tres etapas sin agrupar | 6 |
| Pipeline | GL2 | Agrupación de dos etapas | 6 |
| Pipeline | GL3 | Agrupación de tres etapas | 6 |
| Pipeline | GL3_FINAL | GL3 con retorno solo de finales | 6 |
| Compartido | AC1 | Un consumidor por job | 6 |
| Compartido | AC2 | Dos consumidores por job | 6 |
| Compartido | AC4 | Cuatro consumidores por job | 6 |
| Particiones | D02 | Consumidores de particiones en jobs separados | 6 |
| Particiones | GD4 | Consumidores de particiones agrupados | 6 |
| Montage | MONTAGE_SEP | PROJECT y SHRINK en jobs separados, W1 | 3 |
| Montage | MONTAGE_GROUP | PROJECT y SHRINK agrupados, W1 | 3 |
| Montage | MONTAGE_GROUP_FINAL | Agrupados, retorno solo de finales, W1 | 3 |
| **Total principal previsto** |  |  | **63** |

La matriz preestablecida contiene la identidad y el orden de cada fila. Se emplea la semilla `2026110809`. En cada terna sintética, los seis bloques cubren las seis permutaciones del orden de condiciones; para D02/GD4, los dos órdenes se programan tres veces cada uno (`pair3`). La ubicación de las tareas está fijada; no se asigna al azar a los workers. Montage cuenta con tres bloques: es una comprobación acotada y no completa las seis permutaciones. Se conservarán el orden real, las sesiones y los cortes de ejecución.

## Predicciones volumétricas

Los valores siguientes son por ejecución. MiB corresponde a `2^20` bytes. Para Montage se informan bytes enteros porque los archivos FITS y la cabecera se contabilizan en bytes.

| Condición | `M_req` previsto | `M_obs` previsto | DME previsto |
|---|---:|---:|---:|
| L01 | 20 MiB | 60 MiB | `1/3` |
| GL2 | 20 MiB | 50 MiB | `2/5` |
| GL3 | 20 MiB | 40 MiB | `1/2` |
| GL3_FINAL | 20 MiB | 20 MiB | `1` |
| AC1 | 70 MiB | 100 MiB | `7/10` |
| AC2 | 70 MiB | 80 MiB | `7/8` |
| AC4 | 70 MiB | 70 MiB | `1` |
| D02 | 40 MiB | 40 MiB | `1` |
| GD4 | 40 MiB | 40 MiB | `1` |
| MONTAGE_SEP | 2 315 771 B | 3 375 611 B | `2315771/3375611` |
| MONTAGE_GROUP | 2 315 771 B | 2 845 691 B | `2315771/2845691` |
| MONTAGE_GROUP_FINAL | 2 315 771 B | 2 315 771 B | `1` |

En el pipeline, los 20 MiB requeridos son comunes a las cuatro condiciones. AC1/AC2/AC4 comparten 70 MiB requeridos. D02 y GD4 comparten 40 MiB y se prevé que mantengan el observado. En Montage, las tareas permanecen en W1: el requerido incluye imagen y cabecera de entrada más los finales, total 2 315 771 B. El intermedio `project.fits` de 529 920 B permanece en W1 y no añade un destino remoto requerido. Este diseño no es equivalente al contraste histórico de Montage con PROJECT en W1 y SHRINK en W2, cuyo requerido fue 3 375 611 B.

## Controles, fuentes y aceptación

Dentro de cada contraste se fijan grafo, tareas científicas, entradas, tamaños, programa, ubicación declarada y finales; las diferencias intencionales son la agrupación o, en GL3_FINAL y MONTAGE_GROUP_FINAL, la política explícita de retorno. Todos los jobs científicos solicitan 1 CPU y 256 MiB en el mismo pool de dos workers. Se registrarán configuración, ubicación efectiva y duración; la carga de fondo no se controla. Se usa un directorio nuevo por caso; no se presupone caché fría. Un workflow estará activo a la vez.

Antes del envío se revisarán los planes efectivos: identidad y pertenencia de tareas, asignación a worker, entradas/salidas científicas, dependencias, finales y política de reintento cero. Tras cada ejecución se preservarán UUID, plan y submit, historial/eventos, metadatos, contratos nativos, estadísticas, entradas y finales científicos, checksums y auxiliares administrativos disponibles.

La auditoría independiente reconstruirá las obligaciones y entregas nativas por archivo, destino y relevo, y conciliará exactamente bytes y conteos en cada dirección. La cobertura se comprobará por identidad y destino, no solo por igualdad de totales. Se registrarán las direcciones no conciliables y cualquier falta de cobertura; no se completarán con cifras de las predicciones. Después se cotejará el cálculo de DME con el núcleo vigente.

Los finales sintéticos se compararán por identidad, tamaño y SHA-256 entre variantes con la misma entrada. Para Montage se comprobarán, además, dimensiones FITS, máscara de valores finitos y valores de píxel entre variantes. Además de la integridad de los archivos, se exige formato FITS válido, dimensiones esperadas y datos finitos no triviales.

## Análisis e interpretación

Para cada ejecución se reportarán `M_req`, `M_obs`, DME exacto, obligaciones, entregas, cobertura y estado de equivalencia final. Las predicciones se mostrarán junto a lo medido solo después de obtenerlo desde fuentes nativas. Si hay discrepancia, se conserva y se detiene el avance para diagnosticarla; no se excluye por contrariar la hipótesis ni se sustituye por un reenvío. Los fallos y resultados no conciliables permanecen visibles en el flujo de la muestra.

Las comparaciones de bytes se interpretarán dentro del grafo, tamaños, ubicaciones y contratos ensayados. Agrupar modifica jobs y fronteras administrativas; GL3_FINAL y MONTAGE_GROUP_FINAL también cambian el contrato de retorno. Por ello, una reducción observada respalda la posibilidad de evitar entregas concretas en esa configuración, no una regla causal general para toda agrupación ni optimalidad global. La duración se resumirá por condición como respuesta secundaria; no se atribuirá exclusivamente a bytes, pues puede reflejar agrupación, actividad administrativa, carga de fondo y caché. Montage cubre dos operaciones en una ubicación y no representa un mosaico completo ni permite generalización estadística. El costo nativo de captura no queda aislado por este diseño.
