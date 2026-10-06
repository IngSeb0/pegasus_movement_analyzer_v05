# Entorno Pegasus/HTCondor — captura desde el master

**Captura:** ClassAds desde `pegasus-master`, 2026-10-04 03:30:13 (UTC-05:00); inventario de guests de workers mediante jobs de solo lectura HTCondor el 4 de octubre de 2026. Las fuentes se distinguen por alcance: la propuesta oficial describe el equipo anfitrión; las capturas describen guests y recursos del pool.

## Equipo anfitrión declarado en la propuesta

La formulación oficial especifica Windows 11 Home Single Language, arquitectura de 64 bits, Intel Core i5-1235U (12.ª generación) y 8 GB de RAM. Estos son datos consignados en la propuesta del proyecto, no una nueva lectura de telemetría del host durante esta sesión.

## Componentes y configuración de la VM master

| Hecho | Captura/fuente |
|---|---|
| Host y rol | `pegasus-master` (`192.168.79.135`); Pegasus y daemons centrales HTCondor |
| OS/kernel/ISA | Ubuntu 26.04 LTS; Linux `7.0.0-31-generic`; `x86_64` |
| Virtualización | VMware, según captura previa de `lscpu` |
| CPU visible para VM | Intel Core i5-1235U reportado al guest; 1 CPU lógica/vCPU y 1 core/socket |
| Memoria VM | 1,671,811,072 bytes, `free -b` |
| Red | `ens33`, `192.168.79.135/24`; gateway `192.168.79.2` |
| Pegasus | 5.1.2 |
| HTCondor | 25.12.2; `X86_64-Ubuntu_26.04` |
| Runtime | Python 3.14.4; OpenJDK 25.0.4.1 |
| Servicios centrales | `MASTER`, `COLLECTOR`, `NEGOTIATOR`, `SCHEDD` |
| Configuración del pool | `COLLECTOR_HOST=pegasus-master`; `NETWORK_INTERFACE=192.168.79.135`; `DAEMON_LIST=MASTER,COLLECTOR,NEGOTIATOR,SCHEDD` |

## Workers: recursos del pool e inventario del guest

El collector publica un slot por worker. Además, se sometieron probes de solo lectura desde el master para consultar el entorno guest de cada worker, sin SSH directo.

| Rol/hostname | Guest y red | CPU / memoria guest | Software guest | Slot HTCondor |
|---|---|---|---|---|
| `pegasus-worker1` | Ubuntu 26.04 LTS; Linux `7.0.0-34-generic`; `x86_64`; VMware; `ens33`, `192.168.79.137/24` | Intel Core i5-1235U reportado al guest; 1 vCPU; RAM total visible `1,478,856,704` B; swap `4,294,963,200` B | Pegasus 5.1.2; HTCondor 25.12.2; Python 3.14.4; OpenJDK 25.0.4.1 | `slot1@pegasus-worker1`; ClassAds `StartD`, `DaemonMaster`, `Arch=X86_64`, `OpSys=LINUX`, `OpSysAndVer=Ubuntu26`; 1 CPU/1410 MiB; `Unclaimed/Idle` |
| `pegasus-worker2` | Ubuntu 26.04 LTS; Linux `7.0.0-34-generic`; `x86_64`; VMware; `ens33`, `192.168.79.139/24` | Intel Core i5-1235U reportado al guest; 1 vCPU; RAM total visible `1,478,864,896` B; swap `4,294,963,200` B | Pegasus 5.1.2; HTCondor 25.12.2; Python 3.14.4; OpenJDK 25.0.4.1 | `slot1@pegasus-worker2`; ClassAds `StartD`, `DaemonMaster`, `Arch=X86_64`, `OpSys=LINUX`, `OpSysAndVer=Ubuntu26`; 1 CPU/1410 MiB; `Unclaimed/Idle` |

`Memory=1410 MiB` y `Cpus=1` son recursos asignables anunciados por cada slot; no son la RAM total ni una afirmación de CPU física. El modelo de CPU es el que VMware expone al guest. Los guests comparten la subred observada `192.168.79.0/24`; no se midieron ancho de banda, latencia ni tráfico de paquetes.

## Datos que esta captura no determina

Hardware físico de cada worker por fuera de la VM, asignación de recursos del host anfitrión a cada guest, métricas de red (caudal, latencia, paquetes) y configuración local adicional no expuesta por estas consultas. No se infieren desde las ClassAds.

## Comandos de solo lectura para reproducir el estado del pool

Ejecutar en `pegasus-master`; consultan ClassAds y configuración, sin someter jobs:

```bash
date -Is
hostname -f
uname -a
cat /etc/os-release
lscpu
free -b
ip -br addr
ip route
pegasus-version
condor_version
python3 --version
java -version
condor_config_val DAEMON_LIST
condor_config_val COLLECTOR_HOST
condor_config_val NETWORK_INTERFACE
condor_status -af Name Machine MyAddress Arch OpSys OpSysAndVer Cpus Memory TotalSlotCpus TotalSlotMemory State Activity CondorVersion
condor_status -any -af MyType Name Machine MyAddress
```

Para confirmar solo slots de ejecución:

```bash
condor_status -startd -af Name Machine State Activity Cpus Memory OpSys Arch MyAddress CondorVersion
```
