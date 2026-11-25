# Resultados REP-REC · 24 de noviembre de 2026

Versiones y slots en POOL_3.txt. Ventana en INICIO_UTC_3.txt y CIERRE_UTC_3.txt.
Comandos en los registros por paso y corrida. Cambios en CAMBIOS.diff.
Estado de red en TC_ANTES_3.txt, TC_DURANTE_3.txt, TC_QUITAR_3.txt y TC_FINAL_3.txt.
Calibración HTCondor de entrada en ANCHO_DE_BANDA.json: {
  "bytes": 1073741824,
  "segundos": 91,
  "MB_s": 11.799360703296705
}

| repeticion | condicion | requerido | observado | DME | duracion | ejecucion | transferencia | auxiliares | cola | cierre | dagman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REP | 1887436800 | 2097152000 | 0.9 | 252.4 | 75 | 74 | 45 | 20 | 17 | 21 |
| 1 | REP-REC | 1887436800 | 1887436800 | 1.0 | 250.3 | 31 | 117 | 55 | 8 | 19 | 21 |
| 2 | REP | 1887436800 | 2097152000 | 0.9 | 266.4 | 31 | 118 | 50 | 27 | 19 | 21 |
| 2 | REP-REC | 1887436800 | 1887436800 | 1.0 | 255.3 | 27 | 122 | 55 | 16 | 15 | 21 |

R1 y R2 se confirmaron en los dos pares válidos. La tercera repetición queda pendiente. R3 no se cumplió en los datos disponibles. R4 queda reportada para dos pares, sin predicción direccional.

## Incidencia del intento 2

El supervisor agotó su espera de 120 s durante red.py limitar. Se verificó la limpieza y la desasignación. Registro íntegro en INCIDENCIA_INTENTO_2.md.

## Incidencias del intento 3

rep_r3.txt: 1: El flujo terminó con error (ver el .dagman.out en /mnt/prueba_rep_rec_20261124/rep_r3/submit/dmeadmin/pegasus/flujo-rep/run0001)
Falló: ssh -F <carpeta local>\azure_cloud_20261025\.local\ssh_config dme-master cd ~/trabajo/prueba_rep_rec_20261124 && python3 flujos/ejecutar_flujo.py rep_r3
 
Cierre pendiente: CIERRE_3.txt: 1: Exception: C:\Defensa\Sustentacion_DME\10_Preparacion_Final\prueba_rep_rec_20261124\Control-Cluster.ps1:90
Line |
  90 |  … LED\s*$') { throw 'No se confirmo cola vacia; desasignacion cancelada …
     |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | No se confirmo cola vacia; desasignacion cancelada.
 

## Resultados parciales · dos pares

Ancho de banda de entrada medido con 1 GiB de HTCondor en 91 s: 11,79936 MB/s. El orden de magnitud para 200 MiB es 17,8 s.

| Medida | REP, media ± DE | REP-REC, media ± DE |
| --- | ---: | ---: |
| requerido | 1887436800.000000 ± 0.000000 | 1887436800.000000 ± 0.000000 |
| observado | 2097152000.000000 ± 0.000000 | 1887436800.000000 ± 0.000000 |
| DME | 0.900000 ± 0.000000 | 1.000000 ± 0.000000 |
| duracion | 259.400000 ± 9.899495 | 252.800000 ± 3.535534 |
| ejecucion | 53.000000 ± 31.112698 | 29.000000 ± 2.828427 |
| transferencia | 96.000000 ± 31.112698 | 119.500000 ± 3.535534 |
| auxiliares | 47.500000 ± 3.535534 | 55.000000 ± 0.000000 |
| cola | 23.500000 ± 4.949747 | 12.000000 ± 5.656854 |
| cierre | 18.000000 ± 1.414214 | 17.000000 ± 2.828427 |
| dagman | 21.000000 ± 0.000000 | 21.000000 ± 0.000000 |

| Diferencia REP-REC menos REP | Par 1 (s) | Par 2 (s) | Media ± DE (s) |
| --- | ---: | ---: | ---: |
| transferencia | +43.0 | +4.0 | +23.50 ± 27.58 |
| duracion | -2.1 | -11.1 | -6.60 ± 6.36 |

R1: 1 887 436 800 B requeridos en los cuatro registros. R2: ahorro observado de 209 715 200 B en cada par y DME de 0,90 a 1,00. R3: transferencia subió en ambos pares. R4: duración total bajó en ambos pares, sin inferir un efecto general.

REP r3 fue cancelada tras el apagado del startd de W3, que interrumpió una transferencia activa de C3. El registro del starter no establece qué originó la detención. No se ejecutó REP-REC r3. Ver W3_STARTER_REP_R3.txt, OBSERVACION_REP_R3.txt, DAGMAN_REP_R3_PARCIAL.txt y CANCELACION_REP_R3.txt.

## Recomendador sobre el primer par guardado

~~~text
python -B C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/Repositorio_Simple/analyzer/recomendar.py C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/rep_r1/run0001 C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/rep_r1/history.long --ancho 11.799360703296705
Observado actual:   2097152000 B
  1. En dme-worker1: juntar [C1] con [P]  evita 209715200 B
Observado previsto: 1887436800 B   (evita 209715200 B, 10.00 %)
Orden de magnitud del ahorro de transferencia: 17.8 s
Jobs: 5 -> 4
~~~

~~~text
python -B C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/Repositorio_Simple/analyzer/recomendar.py C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/reprec_r1/run0001 C:/Defensa/Sustentacion_DME/10_Preparacion_Final/prueba_rep_rec_20261124/reprec_r1/history.long --ancho 11.799360703296705
Observado actual:   1887436800 B
Observado previsto: 1887436800 B   (evita 0 B, 0.00 %)
Orden de magnitud del ahorro de transferencia: 0.0 s
Jobs: 4 -> 4
~~~

TC_FINAL_3.txt confirma los cinco nodos sin prio ni tbf.

## Cierre confirmado

La primera comprobación de cola encontró una sola entrada residual de C3 en estado Removed. Se retiró esa entrada del DAG ya cancelado y se comprobó que la cola quedó en cero. No se repitió ninguna corrida. Azure confirmó las cinco VMs en VM deallocated. Inicio UTC: 2026-11-24T16:07:06.381473+00:00. Cierre UTC: 2026-11-24T16:53:48.1941065+00:00. Evidencia en COLA_FINAL_3.txt, CIERRE_3_REINTENTO.txt y ESTADO_FINAL_3.json.
