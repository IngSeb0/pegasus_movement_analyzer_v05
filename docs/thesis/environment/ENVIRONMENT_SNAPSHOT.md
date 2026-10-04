# Entorno Pegasus/HTCondor — captura de infraestructura

**Captura:** 2026-10-03, `pegasus-master`. **Naturaleza:** consultas de solo lectura. Este documento distingue el diseño previsto de lo que estaba anunciado y accesible durante la captura; los runs de septiembre se interpretan con sus propios artefactos preservados.

## Topología prevista

| Rol | Nombre | Dirección mapeada en `/etc/hosts` del master | Estado observado |
|---|---|---|---|
| Master, collector y schedd | `pegasus-master` | `192.168.79.135` | SSH operativo; HTCondor anuncia Collector, Scheduler, DaemonMaster y Negotiator |
| Worker | `pegasus-worker1` | `192.168.79.137` | `ping` devuelve `Destination Host Unreachable`; SSH/22 agota tiempo; sin anuncio `startd`/slot |
| Worker | `pegasus-worker2` | `192.168.79.139` | `ping` devuelve `Destination Host Unreachable`; SSH/22 agota tiempo; sin anuncio `startd`/slot |

El usuario confirma que el entorno previsto incluye ambos workers. La ausencia de anuncios en esta captura no demuestra que la arquitectura sea de un solo host ni identifica por sí sola la causa de la desconexión. `ip neigh` informó `FAILED` para ambas direcciones.

**Seguimiento 2026-10-04:** desde el master, `condor_status -startd -af Name Machine State Activity Cpus Memory` continuó sin mostrar slots. Un `ping` a cada dirección de worker (`.137` y `.139`) tuvo 100 % de pérdida. En este seguimiento no se repitió SSH a los workers; los intentos SSH fallidos corresponden a la captura del 2026-10-03. No se modificó la infraestructura.

## Hechos confirmados en master

| Dato | Observación y fuente |
|---|---|
| OS/kernel/ISA | Ubuntu 26.04 LTS, kernel `7.0.0-31-generic`, `x86_64` (`/etc/os-release`, `uname -a`) |
| Virtualización | VMware según `lscpu` |
| CPU visible | Intel Core i5-1235U presentado a la VM; 1 CPU lógica/vCPU, 1 core/socket (`lscpu`, `nproc`) |
| Memoria total | 1,671,811,072 B (`free -b`) |
| Almacenamiento | `sda` 60 G; partición `sda2` ext4 montada en `/` (`lsblk`) |
| Red | `ens33` `192.168.79.135/24`; gateway `192.168.79.2` (`ip -br addr`, `ip route`) |
| Pegasus | 5.1.2 (`pegasus-version`) |
| HTCondor | 25.12.2, plataforma `X86_64-Ubuntu_26.04` (`condor_version`) |
| Python y Java | Python 3.14.4; OpenJDK 25.0.4.1 |
| Git | 2.53.0 |
| Configuración de pool | `COLLECTOR_HOST=pegasus-master`; `NETWORK_INTERFACE=192.168.79.135`; `SCHEDD_HOST` no definido explícitamente; `DAEMON_LIST=MASTER,COLLECTOR,NEGOTIATOR,SCHEDD` |
| Anuncios HTCondor | `condor_status -schedd` y `-collector` muestran el master; `condor_status -startd` no muestra execution points |

Las cifras de CPU/RAM pertenecen a la VM, no al host físico VMware completo.

## Datos pendientes de cada worker

SO, kernel, CPU/vCPU, RAM, disco, interfaces/rutas, Pegasus si existe, HTCondor, Python, Java, `DAEMON_LIST`, estado del servicio Condor y recursos de slots. No se trasladan automáticamente los valores del master a los workers.

Cuando vuelvan a estar accesibles, consultar en cada host sin cambiar configuración:

```bash
hostnamectl --static
hostname -f
uname -a
cat /etc/os-release
lscpu
nproc
free -b
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
ip -br addr
ip route
pegasus-version
condor_version
python3 --version
java -version
condor_config_val DAEMON_LIST
systemctl is-active condor
```

Desde master, confirmar disponibilidad de ejecución con `condor_status -startd -af Name Machine State Activity Cpus Memory OpSys Arch MyAddress`. Restaurar energía, servicio o red de las VMs exige una intervención de infraestructura separada; aquí no se hizo.
