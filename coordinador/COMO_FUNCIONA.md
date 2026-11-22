# Cómo se lleva al coordinador lo que necesita

## Dos lugares

| Lugar | Qué hay | Qué se hace ahí |
|---|---|---|
| **Tu PC** | `llevar.py` y tus carpetas | Subir archivos, lanzar comandos, bajar resultados. |
| **Coordinador** (`dme-master`) | Pegasus 5.1.2, HTCondor 26.0.1, Python con `Pegasus.api` y `PyYAML`, `gcc` | Crear el flujo, planificarlo, ejecutarlo y guardar la evidencia. |

Los cuatro workers (`dme-worker1…4`) no se tocan a mano: HTCondor les envía lo que cada job necesita. Desde tu PC solo se llega a ellos pasando por el coordinador (`ProxyJump dme-master`).

## `llevar.py`: tres acciones

```
python llevar.py subir  flujos analyzer                 # tu PC -> ~/trabajo/ del coordinador
python llevar.py correr "COMANDO"                       # ejecuta el comando en ~/trabajo/
python llevar.py bajar  caso1 .                         # coordinador -> tu PC
```

Usa `ssh` y `scp` con el nombre `dme-master` de tu `~/.ssh/config` (`HostName`, `User dmeadmin`, `IdentityFile`). Para otro nombre: variable de entorno `COORDINADOR`.

## Una corrida completa

```
python llevar.py subir flujos analyzer
python llevar.py correr "python3 flujos/crear_flujo.py flujos/especificaciones.json DISTRIBUTION-W2 caso1"
python llevar.py correr "python3 flujos/ejecutar_flujo.py caso1"
python llevar.py correr "python3 analyzer/analyzer.py <run0001> caso1/history.long -v"
python llevar.py bajar caso1 .
```

`<run0001>` es la ruta que imprime `ejecutar_flujo.py` al terminar.

## Qué viaja y qué no

- **Se sube desde tu PC (menos de 100 KB):** el código de `flujos/`, `analyzer.py` y `especificaciones.json`.
- **No se sube el archivo inicial de 200 MiB.** `crear_flujo.py` lo genera en el coordinador (paso 2 del script). Subirlo por SSH no aportaría nada y mediría la red de tu casa.
- **Montage (147 fotos):** las fotos FITS se descargan **desde el coordinador**, con `curl`, del servicio SIA de IRSA (2MASS, banda J, 2° × 2° alrededor de M101), antes de que empiece el flujo: lo hace `flujos/montage.py`. Como no es una tarea del flujo, no cuenta en DME. Después, Pegasus las trata como archivos iniciales del coordinador y CondorIO se las envía al worker que corre cada alineación. MontagePy viaja empaquetado dentro de `tarea_montage.py`.

## Cuántos workers usa una corrida

El flujo no dice en qué máquina corre cada tarea (el `.sub` solo exige `DMEStudyEligible == true`); lo decide HTCondor entre los workers elegibles. Para correr con 2 o con 4 workers se activa esa marca solo en los que se quieren, con un archivo de configuración en cada worker (`/etc/condor/config.d/99-dme.conf`) y `condor_reconfig`:

```
NUM_CPUS = 1
NUM_SLOTS = 1
NUM_SLOTS_TYPE_1 = 1
SLOT_TYPE_1 = cpus=1
SLOT_TYPE_1_PARTITIONABLE = TRUE
DMEStudyEligible = TRUE          # FALSE en los workers que no se usan
STARTD_ATTRS = $(STARTD_ATTRS), DMEStudyEligible
```

Ver el estado: `condor_status -constraint 'DMEStudyEligible == true'` y `condor_q -allusers`.

## Encender y apagar las máquinas

Las VMs están en Azure y cobran mientras estén encendidas:

```
az vm start      -g GRUPO --name dme-master      # repetir con cada máquina
az vm deallocate -g GRUPO --name dme-master --no-wait
```

Siempre `deallocate` al terminar (apagar desde dentro de la máquina no deja de cobrar). El `cloud.py` anterior, además, abría el puerto 22 solo para tu IP y apagaba todo al llegar la hora límite de la sesión.

## Qué reemplaza a los scripts anteriores

| Antes (`remote.py`, `cloud.py`, `run_study.py`) | Ahora |
|---|---|
| `upload` (paquete `.tar.gz` con verificación de hashes) | `llevar.py subir` |
| `two`, `four`, `preflight`, `status` | `llevar.py correr "…"` con los comandos de arriba |
| `download` (cápsulas `.tar.xz` verificadas) | `llevar.py bajar` |
| `start`, `close`, `guard` | `az vm start` y `az vm deallocate` |

Se omiten a propósito la verificación de hashes, el libro de registro y las auditorías automáticas de las sesiones anteriores. El código exacto que corrió los 30 experimentos sigue en `05_Registros/Intensivo_20261122/intensivo_20261122_resultados.zip`.
