# Sensibilidad de DME en el mosaico M101

El [tutorial oficial de Montage](https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html) proporciona diez imágenes 2MASS J y la cabecera de destino. Se ejecutó la ruta de reproyección, tabla de imágenes y coadición hasta producir el mosaico FITS y su mapa de cobertura. Los tres casos conservaron el grafo de doce tareas, los parámetros, las entradas y la ubicación observada.

| Configuración | Jobs científicos | Requerido (bytes) | Observado (bytes) | DME exacta | Duración (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base sin agrupación | 12 | 269 021 436 | 311 142 466 | 134510718/155571233 | 251,237 |
| Dos reproyecciones juntas | 11 | 269 021 436 | 311 142 148 | 67255359/77785537 | 256,224 |
| Tabla y coadición juntas | 11 | 269 021 436 | 269 030 582 | 134510718/134515291 | 222,195 |

Cada fila representa una ejecución. La duración es descriptiva.

## Entregas eliminadas frente a la base

| Configuración | Archivo | Dirección | Bytes ahorrados |
| --- | --- | --- | ---: |
| Dos reproyecciones juntas | `template.hdr` | dme-master → dme-worker2 | 318 |
| Tabla y coadición juntas | `images.tbl` | dme-master → dme-worker1 | 6 284 |
| Tabla y coadición juntas | `p01.fits` | dme-master → dme-worker1 | 4 230 720 |
| Tabla y coadición juntas | `p02.fits` | dme-master → dme-worker1 | 4 222 080 |
| Tabla y coadición juntas | `p03.fits` | dme-master → dme-worker1 | 4 199 040 |
| Tabla y coadición juntas | `p04.fits` | dme-master → dme-worker1 | 4 199 040 |
| Tabla y coadición juntas | `p05.fits` | dme-master → dme-worker1 | 4 190 400 |
| Tabla y coadición juntas | `p06.fits` | dme-master → dme-worker1 | 4 181 760 |
| Tabla y coadición juntas | `p07.fits` | dme-master → dme-worker1 | 4 210 560 |
| Tabla y coadición juntas | `p08.fits` | dme-master → dme-worker1 | 4 210 560 |
| Tabla y coadición juntas | `p09.fits` | dme-master → dme-worker1 | 4 239 360 |
| Tabla y coadición juntas | `p10.fits` | dme-master → dme-worker1 | 4 222 080 |

Analyzer coincidió con la auditoría independiente en las tres ejecuciones. Se conciliaron 68 direcciones con residuo cero. Los datos binarios de las imágenes y las tarjetas FITS comparadas, incluida la geometría, coincidieron con la referencia local.

La agrupación de tabla y coadición minimizó el observado entre las configuraciones ensayadas. Se mantuvo la ruta del tutorial sin ajuste de fondo. El contraste no permite ordenar agrupaciones que quedaron fuera del diseño ni atribuir una mejora temporal a los bytes.
