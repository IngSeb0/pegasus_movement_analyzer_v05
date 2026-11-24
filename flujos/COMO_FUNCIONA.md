# Cómo se hace un flujo y cómo se ejecuta

```
especificaciones.json ──crear_flujo.py──▶ workflow.yml + pegasus.properties
                                            │ pegasus-plan
                                            ▼
                                  .dag + un .sub por job
                                            │ pegasus-run (DAGMan + HTCondor)
                                            ▼
                                  history.long ──▶ analyzer.py ──▶ DME
```

## 1. La especificación

`especificaciones.json` tiene 13 condiciones: `PROCESS`, `PIPELINE`, `AGGREGATION`, `DISTRIBUTION`, `REDISTRIBUTION` con 2 y 4 workers (`-W2`, `-W4`) y las de contraste `REP`, `W2-SEP`, `W2-AGR`. Todos los archivos son de 200 MiB. Cada condición dice solo qué hay que calcular:

```
tareas   T1: lee A, escribe g       T2: lee g, escribe B1   …
archivos A (200 MiB, entrada)       g (intermedio)          B1…B5 (finales)
```

**Ubicación.** Una tarea sin campo `maquina` la ubica HTCondor entre los workers elegibles (`TARGET.DMEStudyEligible == true`): así corrieron los diez patrones. Una tarea con `maquina` queda fija (`TARGET.Machine == "dme-worker2"`): así corrieron las tres de contraste (`REP`, `W2-SEP`, `W2-AGR`) y todo Montage. Una condición puede traer `groups`: tareas que Pegasus junta en un solo job (`W2-AGR`).

## 2. `workflow.yml` (lo escribe `crear_flujo.py`)

Es la descripción abstracta del flujo, en YAML. Sus secciones:

| Sección | Qué dice | Dónde se arma (`crear_flujo.py`) |
|---|---|---|
| `siteCatalog` | Dos lugares: `local` (el coordinador, con carpetas `scratch` y `outputs`) y `condorpool` (los workers). | líneas 42–51 |
| `replicaCatalog` | Dónde está cada archivo inicial (`A` en `inputs/`). | líneas 53–56 |
| `transformationCatalog` | El programa que ejecutan los jobs: `campaign_task` = `tarea.py`. | líneas 57–69 |
| `jobs` | Un job por tarea con sus argumentos, sus archivos (`uses`) y su requisito de máquina. | líneas 70–83 |
| `jobDependencies` | Quién espera a quién: T2…T6 esperan a T1 porque leen `g`. | líneas 84–89 |

Un job real, recortado:

```yaml
- type: job
  name: campaign_task
  id: T2
  arguments: [--task-id, T2, --flops, '1766799020', --input, g, '209715200', --output, B1, '209715200']
  uses:
  - {lfn: g,  type: input}
  - {lfn: B1, type: output, stageOut: true}      # stageOut: true = resultado final, vuelve al coordinador
  profiles:
    condor: {requirements: TARGET.DMEStudyEligible == true, request_cpus: '1', request_memory: 256}
```

`uses` es lo que el Analyzer lee en el paso 2: de ahí salen el productor y los lectores de cada archivo. El kernel de cómputo no aparece: no es un dato del flujo.

## 3. `pegasus.properties`

```
pegasus.data.configuration=condorio      # los archivos viajan con HTCondor, pasando por el coordinador
pegasus.selector.site=RoundRobin         # reparto de jobs entre sites
dagman.retry=0                           # sin reintentos: un fallo detiene la corrida
```

**CondorIO** es la clave: cada job recibe sus entradas desde el coordinador y devuelve sus salidas al coordinador. Un archivo que va de un worker a otro pasa siempre por el coordinador. Eso es lo que DME mide.

## 4. `pegasus-plan`: del flujo abstracto a archivos de HTCondor

Deja una carpeta `submit/…/run0001/` con:

| Archivo | Qué es |
|---|---|
| `*.dag` | El orden de ejecución, para DAGMan. |
| `00/00/campaign_task_T4.sub` | El contrato de ese job para HTCondor. |
| `00/00/campaign_task_T4.sh` | El script que corre en el worker y lanza `tarea.py`. |
| `00/00/*.meta` | Tamaños y datos de cada archivo. |
| `braindump.yml` | Identificadores de la corrida (`root_wf_uuid`). |

Las líneas del `.sub` que importan (job T4, recortado):

```
requirements          = TARGET.DMEStudyEligible == true
transfer_input_files  = g, campaign_task, <paquete de Pegasus>, <.meta>, <scripts>, …/fma_kernel
transfer_output_files = B3
```

`g` y `B3` son archivos científicos. Todo lo demás (el programa, el paquete de Pegasus, scripts, `.meta`, el kernel) es auxiliar y no cuenta en DME.

## 5. `ejecutar_flujo.py`: de los `.sub` a la evidencia

1. **`pegasus-plan`** (líneas 22–30): genera `run0001`. Si el flujo trae grupos, añade `--cluster label`.
2. **Kernel** (31–38, solo en los sintéticos): añade `fma_kernel` a `transfer_input_files` de cada `.sub` de tarea. Pegasus solo envía lo declarado como entrada, y el kernel es una herramienta de medición, no un dato del flujo.
3. **`pegasus-run`** (39–41): entrega el `.dag` a DAGMan, que va enviando cada job a HTCondor cuando sus padres terminan. Responde al instante.
4. **Espera** (43–54): hasta 45 minutos, hasta que DAGMan escribe `EXITING WITH STATUS 0`.
5. **`condor_history`** (55–57): guarda en `history.long` en qué máquina corrió cada job.

## 6. `tarea.py` y `fma_kernel.c`: lo que corre cada job

`tarea.py` lee cada entrada completa, ejecuta el kernel y escribe cada salida con su tamaño exacto.

`fma_kernel.c` (17 líneas de código) es la carga de cómputo. Su única operación es:

```c
x = fma(x, 0.999999999999, 0.125);      // x*a + b en una sola instrucción
```

**FMA** (*fused multiply-add*) multiplica y suma en una sola instrucción de la CPU. Cuenta como 2 operaciones de punto flotante (FLOP). Cada vuelta usa el `x` de la anterior, así la CPU no puede adelantar ni omitir trabajo, y `printf` del resultado evita que el compilador elimine el bucle. Con `--flops 1766799020` hace 883 399 510 vueltas, unos 1,1 a 1,4 s de CPU según la máquina. Se compila con `-mfma` para que sea la instrucción de hardware (`vfmadd`) y no una función lenta por software.

La misma carga en todas las tareas hace que la diferencia entre corridas sea el movimiento de datos. El tiempo de CPU de cada tarea no lo mide el kernel: lo registran Pegasus (Kickstart) y HTCondor.

## 7. Montage (M101, 147 fotos de 2° × 2°)

Se crea con el **mismo** `crear_flujo.py`: solo cambia quién escribe la especificación. Para los patrones es `especificaciones.json`; para Montage, `montage.py`:

```
python3 montage.py montage_m101                                          # descarga y escribe la especificación
python3 crear_flujo.py montage_m101/especificaciones.json MG-BASE  flujo_base
python3 ejecutar_flujo.py flujo_base
```

**`montage.py`** (92 líneas, en el coordinador, antes del flujo; no cuenta en DME):

| Paso | Líneas | Qué hace |
|---|---|---|
| 1 | 27–52 | Pregunta a IRSA (servicio SIA de 2MASS) qué fotos de la banda J cubren el cuadrado de 2° alrededor de M101, y baja cada una con `curl`. Con ellas quedan en `entradas/`. |
| 2 | 54–67 | Baja MontagePy (la rueda), crea con `mMakeHdr` la cabecera común `template.hdr`, y mete la rueda dentro de `tarea_montage.py` para que los workers no instalen nada. |
| 3 | 69–92 | Escribe `especificaciones.json` con dos condiciones. |

**El grafo**: una tarea `P##` por foto (`mProjectPP` la alinea a la cabecera común), `TABLE` (`mImgtbl` indexa las alineadas) y `ADD` (`mAdd` suma todo en `m101.fits`). Las `P##` se reparten por turnos entre `dme-worker2`, `3` y `4`; `TABLE` y `ADD` van en `dme-worker1`. Aquí la máquina **sí** va fija en cada job (`requirements = TARGET.Machine == "dme-worker2"`), a diferencia de los patrones.

**Las dos condiciones**:

| Condición | Qué cambia |
|---|---|
| `MG-BASE` | `TABLE` y `ADD` son jobs separados: las alineadas viajan al job de `TABLE` y otra vez al de `ADD`. |
| `MG-FINAL` | `TABLE` y `ADD` van en `groups`: `crear_flujo.py` les pone la misma etiqueta, `ejecutar_flujo.py` planifica con `--cluster label` y Pegasus los junta en un solo job (`merge_group_1`). Las alineadas llegan una sola vez. |

**`tarea_montage.py`** (43 líneas) es lo que corre cada job: según el `--task-id` llama a `mProjectPP`, `mImgtbl` o `mAdd`. El tamaño `0` en un argumento significa «desconocido, no comprobar»: los tamaños de los archivos intermedios no se conocen hasta que corre el flujo, y el Analyzer los lee después de los `.meta`.

**En la sustentación**: la red de las corridas de Montage se limita con `tc tbf` (50 Mbit/s en la segunda ronda) para que la transferencia sea el tramo mayor; eso lo hace el procedimiento de la ronda, no estos scripts.

## Qué se comprobó de este código

- `crear_flujo.py` produce un `workflow.yml` con los mismos jobs, argumentos, archivos (`uses`) y requisitos que los de las corridas reales.
- `tarea.py`, `fma_kernel.c` y `ejecutar_flujo.py` se probaron: la tarea con el kernel compilado y el script con comandos de Pegasus y HTCondor simulados.
- Montage: con 4 fotos sintéticas, `montage.py` crea la cabecera y la especificación; `crear_flujo.py` produce `MG-BASE` y `MG-FINAL` (este con la etiqueta `group_1` y `seqexec`, y la máquina fija por job); y las tareas ejecutadas en orden producen `m101.fits`.
- **No se probó** la descarga desde IRSA (la red de esta sesión no llega a ese servidor): se probó con fotos ya puestas en `entradas/`. Tampoco se ejecutó `pegasus-plan`, ni con grupos.
- El `.sub` real de Montage (corrida de ejemplo M101-FINAL) pasa por el Analyzer y por `tiempos.py` sin que se active ningún control.
- No se ejecutó `pegasus-plan` sobre este `workflow.yml`: Pegasus y HTCondor solo están en el coordinador.

## Montage reducido y SIA

- **Qué es real:** las 147 fotos (2MASS, banda J, de IRSA) y las herramientas (`mProjectPP`, `mImgtbl`, `mAdd` de MontagePy 2.3.0). **Qué es nuestro:** el diagrama, reducido a alinear → tabla → mosaico, sin `mDiffFit`, `mConcatFit`, `mBgModel`, `mBackground`, `mShrink` ni `mJPEG` (corrección de fondo y vistas previas). Razón: la comparación es dónde corren la tabla y el mosaico y si las alineadas viajan una o dos veces, y `mDiffFit` multiplicaría las tareas (una por par de fotos que se traslapan). Límite: es Montage reducido, no el completo.
- **SIA (Simple Image Access):** estándar de IVOA para consultar un archivo de imágenes por posición y tamaño; devuelve una tabla con los enlaces. `montage.py` usa el SIA v1 de IRSA con `POS` = centro de M101, `SIZE` = 2° y banda J.
- **Bloques:** una ronda en la que corren BASE y FINAL una vez cada una, con el orden rotado entre rondas.
