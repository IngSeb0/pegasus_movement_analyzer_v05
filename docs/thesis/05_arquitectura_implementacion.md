# Capítulo 5 — Especificación técnica de Pegasus Data Movement Analyzer v1

**Estado:** borrador técnico para revisión académica. Describe la implementación inspeccionada en `feat/analyzer-v1`; no contiene resultados experimentales finales.

## Base de verificación y alcance

La inspección funcional se realizó en `pegasus-master` el 2026-10-03 sobre `feat/analyzer-v1` en `5600ee17f5da7e48d46689cb8bf0b4e74cbfe158`. El cierre documental y las pruebas finales de Gate I se verificaron en el commit `3f44f30a9540861fbe1eeb0e0a515a6f9d7d79e6`, que solo cambió README, CHANGELOG y TEST_REPORT; no cambió módulos funcionales. El commit se publicó en `origin/feat/analyzer-v1` el 4/10/2026.

Gate R, Gate D, I0–I13 y Gate I están **CLOSED** para la revisión validada `3f44f30`. La suite normal, la integración portable y con runs originales, y el CLI smoke pasaron sobre ese HEAD. I14 no se inició. La campaña de Gate V se ejecutó después con 31 workflows independientes en diez condiciones; sus resultados se presentan en el capítulo 7 y no cambian la descripción funcional de Analyzer v1.

La especificación se basa en los requisitos, diseño, matriz de trazabilidad, log y plan de implementación, estado maestro, estructura de tesis/presentación, y en el código v1 de `pegasus_movement/` y `tools/analyze_run_v1.py`. Las afirmaciones históricas de v35/v36 no se usan como descripción actual cuando difieren del Analyzer v1.

## 5.1 Arquitectura general de Analyzer v1

Analyzer v1 analiza un run preservado de Pegasus junto con un archivo de historial de HTCondor proporcionado explícitamente. Integra artefactos del run —workflow, submits y metadatos— con registros de `condor_history -long`. La canalización es offline: no consulta el pool vivo ni modifica las fuentes analizadas.

El flujo implementado es:

1. Descubrir y leer fuentes del run e historial.
2. Detectar y validar el modelo efectivo de ejecución.
3. Normalizar identidades de jobs, tareas, archivos y ubicaciones.
4. Reconstruir el dataflow científico.
5. Derivar movimientos requeridos usando ubicaciones observadas.
6. Construir manifests de transferencia para el adapter soportado.
7. Derivar movimientos declarados de entradas científicas del manifest.
8. Reconciliar declaraciones con evidencia de HTCondor.
9. Calcular métricas bajo las condiciones de cobertura y consistencia.
10. Serializar informes, procedencia y diagnósticos.

El objeto `RunExecution` integra las entidades del análisis. La implementación distingue el movimiento **requerido** por el dataflow, el movimiento **declarado** por el modelo efectivo y el movimiento **confirmado** por la evidencia. Un manifest representa una expectativa de sandbox y no demuestra, por sí mismo, que una transferencia ocurrió.

## 5.2 Modelo de datos normalizado

Las entidades son clases del dominio realmente implementadas. Los campos de la tabla son conceptualmente relevantes y no pretenden enumerar cada detalle de serialización.

| Entidad | Responsabilidad y campos conceptuales | Fuente de información | Relaciones | Etapa de métrica |
|---|---|---|---|---|
| `RunExecution` | Contenedor del análisis: `run_id`, ruta, workflow, contexto del patrón, parámetros, colecciones normalizadas, resultado y diagnósticos. | `workflow.yml`, artefactos del run, history y datos derivados. | Contiene tareas, archivos, ubicaciones, perfil, manifests, evidencias, verificaciones y movimientos. | Integra y reporta el análisis completo. |
| `Location` | Ubicación canónica: ID, tipo (submit host, worker, sitio externo o destino final), valores crudos y procedencia. | Host observado en history; host de envío derivado de fuentes del modelo; sitios del workflow. | Referenciada por tareas, archivos y extremos de movimientos. | Define extremos para RequiredMovement y DeclaredMovement. |
| `TaskExecution` | Ejecución observada de una tarea Pegasus: IDs Pegasus/DAG y job HTCondor, worker, estado, código de salida, contadores de ejecución/inicios, éxito y procedencia. | IDs Pegasus de submits y estado/ubicación del job en HTCondor history. | Une tarea lógica con job observado y worker; vincula productores/consumidores de archivos. | Aporta placement, asociación de evidencia y validación de éxito/reintentos. |
| `ScientificFile` | Archivo científico lógico: ID/nombre, referencias físicas, roles, tamaño y procedencia, productor, consumidores, origen y destinos finales. | Workflow/DAX, submits Pegasus, `.meta`/cache, referencias físicas y tamaños resolubles. | Conecta productores y consumidores; se referencia en manifests y movimientos. | Reconstruye dataflow y alimenta movimientos y bytes. |
| `ExecutionModelProfile` | Modelo efectivo: versiones, configuración de datos, universe, submit host, políticas de transferencia, bypass/plugins, clustering/filesystem compartido, adapter, soporte y razones. | Evidencia de submits, history, configuración y artefactos del run. | Perfil asociado al run; selecciona o rechaza el adapter. | Puerta de alcance previa al cálculo de movimientos. |
| `ManifestFile` | Archivo físico esperado por job/dirección: identidad lógica opcional, ruta, basename, clasificación científica/auxiliar, tamaño, protocolo y remap. | Atributos de transferencia del submit, archivos científicos normalizados y tamaños conocidos. | Entrada de `JobTransferManifest`; puede referir un `ScientificFile`. | Define ocurrencias esperadas que se contrastan con evidencia. |
| `JobTransferManifest` | Conjunto esperado por job, dirección e intento: archivos, conteos, bytes, subtotales científicos y completitud. | Submit efectivo del job y contexto de intento separable. | Agrupa `ManifestFile`; se coteja con evidencia y da lugar a movimientos declarados. | Base de DeclaredMovement y reconciliation. |
| `TransferEvidence` | Estadísticas observadas por job/dirección/intento: worker, métodos, contadores/bytes, valores crudos y tiempos. | Atributos de HTCondor history, incluidas estadísticas anidadas de transferencia. | Se empareja con manifest y ejecución del job. | Puede confirmar ocurrencias declaradas. |
| `MovementVerification` | Resultado de reconciliación: nivel, modo, confirmado, razón, conteos/bytes esperados y observados, bytes inexplicados e IDs científicos confirmados. | Comparación entre manifest y evidencia, éxito del job y separabilidad del intento. | Resume la comparación por job/dirección/intento y afecta los movimientos declarados. | Decide qué ocurrencias cuentan para Coverage y ObservedMovement. |
| `RequiredMovementRecord` | Bytes requeridos para un archivo desde origen hasta una ubicación necesaria, incluyendo razón `input`, `consumer` o `final_destination`. | Dataflow, tamaños y workers observados. | Referencia archivo y ubicaciones origen/destino. | Suma de RequiredMovement. |
| `DeclaredMovementRecord` | Ocurrencia declarada: ID, job/intento, archivo, dirección, extremos, tamaño, nivel/estado y razón de verificación. | Manifest científico, worker y submit host del perfil. | Relaciona archivo, manifest, job e ubicaciones; reconciliation actualiza su confirmación. | Suma de DeclaredMovement; determina cobertura y movimiento observado confirmado. |
| `MetricResult` | Bytes requeridos/declarados/observados, Coverage, ByteCoverage, DME, diferencia, estados, razones y niveles de evidencia. | Movimientos requeridos y declarados tras reconciliation. | Pertenece al run y se reporta junto con diagnósticos/procedencia asociada. | Contiene magnitudes derivadas del Analyzer. |
| `ProvenanceRef` | Referencia de fuente: tipo, ruta, atributo, hash opcional y notas. | Artefactos parseados y evidencias derivadas. | Asociada al run y a datos de ubicación, tarea, archivo, tamaño, perfil y evidencia. | Permite rastrear datos y decisiones. |

## 5.3 Adquisición de fuentes Pegasus/HTCondor

El descubridor del run recoge determinísticamente archivos `.sub`, `.meta`, metadatos de cache, `.dag`, propiedades/configuración, braindumps y logs dentro del directorio. El workflow se lee desde `workflow.yml`; la CLI recibe por separado la ruta de un archivo HTCondor history mediante `--history-file`.

El parser de submit conserva atributos duplicados, valores crudos, directivas y líneas de origen; no reduce rutas a basenames al leer. El parser de history conserva orden, atributos desconocidos, duplicados, valores ClassAd anidados y procedencia por línea. La interpretación semántica y la normalización se realizan en etapas posteriores.

La adquisición v1 se basa en archivos preservados. No consulta en vivo `condor_status` ni obtiene directamente del pool las estadísticas del job. Esta diferencia debe mantenerse al describir la captura del entorno y el análisis de los runs.

## 5.4 Normalización e integración

Después del parsing, el Analyzer acota history al run analizado, normaliza identidades y relaciona IDs Pegasus con jobs HTCondor. Normaliza los hosts observados como ubicaciones worker e identifica el submit host desde la evidencia del modelo de ejecución.

La identidad lógica de archivos se basa en nombres Pegasus explícitos y referencias físicas resolubles; los IDs explícitos emplean `lfn:`. El basename aislado no constituye identidad. El tamaño se acepta cuando está asociado a una fuente identificable y se conserva su procedencia. Identidades ambiguas, productores múltiples, tamaños ausentes/conflictivos y placements no resueltos generan diagnósticos.

## 5.5 Reconstrucción del dataflow científico

El módulo de dataflow integra workflow/DAX, submits de cómputo y metadatos Pegasus para reconstruir archivos científicos, productor, consumidores, roles y referencias físicas. Los roles implementados distinguen entrada externa, intermedio y salida final. La identidad de la tarea se relaciona con los IDs DAX/DAG disponibles en los submits.

El tamaño se incorpora solo cuando existe una fuente que lo sustenta para la identidad correspondiente. Origen y destinos dependen de los roles y ubicaciones disponibles. Si una identidad o relación no se resuelve sin ambigüedad, el Analyzer emite diagnósticos y puede detener las etapas que dependan de ella.

## 5.6 Adapter de modelo de ejecución condorio

`CondorIOStandardAdapter` delega la validación al detector canónico del modelo de ejecución. No rellena evidencia faltante ni decide por inferencia silenciosa que el run es soportado. El perfil puede registrar versiones Pegasus/HTCondor, configuración de datos, universe, submit host, políticas de transferencia, bypass, plugins, filesystem compartido y jobs agrupados.

El alcance v1 descrito en las especificaciones corresponde a Pegasus 5.x con condorio, HTCondor vanilla y transferencia de archivos HTCondor bajo las condiciones documentadas. El submit host debe identificarse y ser distinto del worker científico. Modelos fuera de alcance, evidencia insuficiente o evidencia contradictoria producen estados/razones explícitos antes del cálculo.

## 5.7 RequiredMovement y DeclaredMovement

**RequiredMovement** se deriva del grafo científico y del placement observado. Para cada archivo se consideran ubicaciones distintas que requieren el archivo, excluyendo el origen; cada ubicación necesaria aporta el tamaño del archivo. La repetición de consumers en el mismo worker no duplica esa ubicación. No se inserta tránsito por el master de forma predeterminada; se cuenta el destino final solo cuando es una ubicación nueva requerida.

**DeclaredMovement** se construye de las entradas científicas de los manifests de input y output asociados a jobs científicos. Input representa submit host → worker; output representa worker → submit host. Cada ocurrencia conserva job e intento; materializaciones repetidas pueden ser ocurrencias declaradas distintas. Los archivos auxiliares pueden pertenecer al sandbox manifest, pero no son movimiento científico ni entran en esas magnitudes.

El manifest representa el conjunto esperado según la semántica efectiva del submit. No demuestra una transferencia física y no equivale a ObservedMovement.

## 5.8 TransferEvidence y reconciliation

La evidencia se extrae por job, dirección y contexto de intento desde el history. Reconciliation contrasta esa evidencia con el manifest completo, la ubicación worker, el protocolo y el estado exitoso del job.

Los modos implementados son `EXACT_BYTES` y `SUCCESSFUL_MANIFEST`; los niveles son `FILE_LEVEL_CONFIRMED`, `JOB_LEVEL_RECONCILED` e `INSUFFICIENT`. Para la confirmación por manifest exitoso se requieren conjunto efectivo completo, identidad de ejecución y estadísticas compatibles. La implementación no distribuye proporcionalmente bytes agregados entre archivos. Intentos no separables, protocolo no contabilizado, conteos discordantes, manifest incompleto o job fallido impiden confirmar la ocurrencia afectada.

## 5.9 Coverage, ObservedMovement y DME

Coverage se cuenta por ocurrencias declaradas confirmadas:

\[
Coverage = \frac{\text{ocurrencias declaradas confirmadas}}{\text{ocurrencias declaradas}}
\]

Un conjunto declarado vacío usa la convención implementada de Coverage igual a 1. Los movimientos de cero bytes también cuentan como ocurrencias. `ByteCoverage` es un indicador diagnóstico y no reemplaza Coverage.

`ObservedMovement` suma tamaños de ocurrencias científicas declaradas y confirmadas. Solo se define con Coverage completa; con Coverage menor que 1 queda indeterminado. Excluye transferencia auxiliar de sandbox.

DME se calcula únicamente con sus precondiciones de movimiento requerido y observado. Si ambos son cero, es no aplicable; si el requerido es cero y el observado positivo, DME es cero. Si el observado es menor que el requerido, la combinación se marca inconsistente y no se produce una DME válida. La métrica no clasifica placements ni mide tiempo, latencia, red o coste.

## 5.10 Reporting y provenance

El documento JSON canónico incluye versión de esquema, `RunExecution`, contexto del patrón, parámetros experimentales, modelo de ejecución, fuentes, ubicaciones, tareas, archivos, manifests, movimientos, evidencias, verificaciones, métricas y diagnósticos. Se producen también reportes tabulares y un resumen CLI con estado y magnitudes si están disponibles. Para interpretar cada resultado conforme a la propuesta, el protocolo debe asociar al run el planner Pegasus detallado y el snapshot del entorno; estos elementos no son campos normalizados completos ni se capturan automáticamente en el modelo.

`ProvenanceRef` conserva tipo de fuente, ruta, atributo y notas; el hash es opcional. Por ello, la descripción académica habla de referencias de procedencia, sin afirmar que todo dato siempre lleva hash criptográfico calculado. El estado global y código de salida derivan de los diagnósticos y del resultado del análisis.

## 5.11 Política fail-closed y diagnósticos

El flujo bloquea etapas posteriores cuando el modelo no está soportado o cuando hay diagnósticos bloqueantes. No convierte ausencia de evidencia en confirmación ni resuelve identidades científicas solo por basename. Tamaños no autoritativos, intentos no separables, manifests incompletos y contradicciones entre expectativa y observación dejan ocurrencias sin confirmar y las métricas dependientes indeterminadas o inválidas.

Los códigos distinguen falta/conflicto de evidencia del modelo, semántica fuera de alcance, identidad/placement/tamaño ambiguo, productores múltiples, reintento no separable, transferencia parcial o discordante, protocolo no contabilizado, job científico fallido y observado menor al requerido.

## 5.12 Estrategia de pruebas de implementación

La suite está organizada en pruebas unitarias por módulos (parsing, normalización, modelo de ejecución, dataflow, movements, reconciliación, métricas y reporting), regresiones con oráculos auditados e integración con runs preservados. La descripción de la estrategia debe cubrir:

- preservación de valores crudos, duplicados y procedencia en parsers;
- identidad normalizada e inequívoca de jobs, tareas, archivos y ubicaciones;
- aceptación/rechazo del adapter ante evidencia del modelo;
- reconstrucción de dataflow y selección de tamaños;
- derivación de manifests, RequiredMovement y DeclaredMovement;
- reconciliation positiva y negativa, incluidos intentos no separables y evidencia incompleta;
- reglas de Coverage, ObservedMovement y DME para cero bytes, no aplicabilidad e inconsistencia;
- estructura y determinismo de informes y diagnósticos.

Esta sección describe la estrategia de pruebas de implementación de Gate I; no incluye resultados experimentales finales.

## Anexo A — Entorno Pegasus/HTCondor

La información combina la formulación oficial del proyecto y consultas de solo lectura efectuadas desde `pegasus-master` el 4 de octubre de 2026 a las 03:30:13 (UTC-05:00). El host Windows se atribuye a la propuesta; las propiedades del master corresponden a la VM; los recursos de workers son ClassAds de slots.

| Componente | Datos documentados |
|---|---|
| Equipo anfitrión según propuesta | Windows 11 Home Single Language; Intel Core i5-1235U; 8 GB RAM; x64. |
| `pegasus-master` | Ubuntu 26.04 LTS; kernel `7.0.0-31-generic`; x86_64; VMware; CPU Intel Core i5-1235U visible al guest, 1 vCPU; RAM VM 1,671,811,072 bytes. |
| Software master | Pegasus 5.1.2; HTCondor 25.12.2; Python 3.14.4; OpenJDK 25.0.4.1. |
| Red y daemons master | `ens33`, `192.168.79.135/24`, gateway `192.168.79.2`; `MASTER`, `COLLECTOR`, `NEGOTIATOR`, `SCHEDD`. |
| `pegasus-worker1` | `192.168.79.137`; ClassAd `X86_64`, `LINUX/Ubuntu26`; HTCondor 25.12.2; slot: 1 CPU, 1410 MiB, `Unclaimed/Idle`. |
| `pegasus-worker2` | `192.168.79.139`; ClassAd `X86_64`, `LINUX/Ubuntu26`; HTCondor 25.12.2; slot: 1 CPU, 1410 MiB, `Unclaimed/Idle`. |

Los recursos de worker son valores publicados por slot y no capacidad física total del host. Los ClassAds de ambos workers se consultaron desde el master; para comprobar el estado del pool no se necesita SSH directo a los workers.

Comandos reproducibles de solo lectura, para ejecutar en el master:

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

## Anexo B — Material visual de la presentación

| Componente | Representación editable |
|---|---|
| Infraestructura y execution model | Diagrama de pool con roles, versiones y ClassAds capturadas; distingue VM/host de recursos por slot. |
| Arquitectura Analyzer v1 | Fuentes → normalización/dataflow → adapter → movimientos → reconciliation → resultado. |
| Modelo de datos | Dos vistas con las entidades normalizadas de ejecución, dataflow, manifiestos, evidencia y métricas. |
| Evidencia/reconciliation | JobTransferManifest, TransferEvidence y MovementVerification, con niveles de confirmación y límites. |
| Métrica y alcance | Fórmulas, condición de Coverage y referencia conceptual worker-to-worker frente a ruta condorio. |
