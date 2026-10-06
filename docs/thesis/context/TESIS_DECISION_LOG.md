# TESIS — Decision log

**Propósito:** registro append-only de decisiones que cambian el diseño, alcance, definición formal o interpretación de resultados.

---

## 2026-09-25 — Adoptar `M_req` como communication lower bound condicionado al placement

**Estado:** aceptada como interpretación vigente de `M_req`; la confirmación de `M_obs` continúa pendiente.

**Decisión:** no se reemplaza la fórmula de `M_req`. Se redefine su descripción formal para evitar la expresión ambigua «ideal hipotético» como caracterización principal. `M_req` se presenta como **lower bound lógico del movimiento de payload científico requerido para satisfacer el dataflow bajo el placement observado**, suponiendo reutilización local y comunicación directa entre ubicaciones. El master conserva su papel cuando es origen de inputs o destino de outputs, pero no se impone como tránsito obligatorio de los intermedios.

**Regla de fan-out:** un archivo se cuenta por ubicaciones destino distintas. Varios consumidores en el mismo worker no generan varias copias requeridas.

**Métrica candidata:** cuando exista evidencia suficiente, `eta_move=M_req/M_obs` se interpreta como eficiencia de materialización **condicionada al placement**. No evalúa ni ordena la calidad de placements. Para comparar la demanda de comunicación entre placements se usa `M_req` manteniendo fijos workflow y tamaños. `M_obs/M_req` puede reportarse como factor auxiliar de amplificación.

**Estado de `M_rec`:** `eta_rec=M_req/M_rec` permanece como proxy reconstruido mientras `M_obs` no tenga cobertura suficiente. Los resultados históricos no cambian.

**Fundamento académico:** la decisión es coherente con trabajos que modelan costo de comunicación a partir de dependencias, archivos y colocación de tareas (Pietri y Sakellariou, 2018; Çatalyürek, Kaya y Uçar, 2011), con la metodología de communication lower bounds en HPC (Ballard et al., 2011) y con caracterización workflow-centric de productor/consumidor, reutilización y tamaño (Tang et al., 2026). No se afirma que estos trabajos propongan exactamente la métrica `M_req/M_obs`; la razón es una propuesta de esta tesis.

**Consecuencia:** el camino crítico deja de ser «decidir entre dos significados de `M_req`». El siguiente bloqueo es determinar la granularidad y cobertura real de `M_obs` en Pegasus/HTCondor.

---

## 2026-09-25 — Auditoría de la interpretación del cociente

**Estado:** hallazgo verificado sobre la fórmula candidata; la elección de la métrica principal continúa pendiente.

**Contraejemplo de interpretación:** para el mismo pipeline a 10 MiB, SAME, BALANCED-LOCAL y CROSS dan respectivamente `M_req/M_rec = 20/60`, `30/60` y `40/60`. `M_rec` no cambia, pero el cociente sube cuando crece el movimiento requerido por el placement. Por tanto, no usar «cociente mayor = menos bytes movidos» ni clasificar automáticamente estos placements como más eficientes por ese cociente. Véase `TESIS_FICHA_DECISION_METRICA_20260925.md`.

**Auditoría del código:** v0.5.1 crea `observed_transfers.tsv` a partir de las declaraciones `transfer_input_files`/`transfer_output_files` de `.sub` y tamaños en `.meta` o archivos físicos. El worker procede del historial, pero las filas no contienen eventos de transferencia con bytes efectivos o identificadores de intento. Esto fundamenta la reinterpretación de esas salidas como `M_rec`. No se han inspeccionado aún los directorios crudos de las corridas process y pipeline en la VM; el `M_obs` de ambas queda indeterminado. Véase `TESIS_AUDITORIA_EVIDENCIA_MOVIMIENTO_20260925.md`.

---

## 2026-09-25 — Distinguir propuesta aprobada, referencia hipotética y evidencia real

**Estado:** aceptada como regla de interpretación; la fórmula definitiva sigue pendiente.

**Hallazgo:** la propuesta oficial plantea diseñar y validar una métrica de eficiencia del movimiento de datos. No fija como problema central «contar bytes adicionales frente a un mínimo con placement fijo». La documentación de Pegasus confirma que `condorio` entrega inputs y recupera outputs de cada job a través del submit host; dos jobs en el mismo worker no obtienen automáticamente reutilización local del intermedio.

**Revisión de terminología:** el valor por suma de tamaños científicos de entradas/salidas por job que v0.5.1 y los documentos del 21 de septiembre llamaron `M_obs^HTC` se denomina desde ahora `M_rec`: reconstrucción condicionada por staging. `M_obs` se reserva para traslados confirmados por evidencia de ejecución con cobertura suficiente. Los resultados previos, tablas y archivos originales se preservan como hechos históricos; sus rótulos deben reinterpretarse, no transformarse en nuevas mediciones.

**Revisión del referente:** `M_req` con placement fijo y reutilización local ideal es un candidato de referencia entre mecanismos. No es el mínimo alcanzable dentro de `condorio` ordinario cuando esa configuración exige el recorrido por submit host. Se conserva la definición de trabajo para analizarla, pero no se declara aprobada como fórmula final de eficiencia.

**Pendiente explícito:** decidir si la pregunta operativa compara `condorio` con una ruta hipotética con reutilización local o si estudia eficiencia dentro de `condorio`, comprobar sensibilidad en ambos casos y verificar evidencia para `M_obs`. Esta entrada revisa solo las interpretaciones afectadas de 2026-09-21; mantiene sus decisiones sobre arquitectura, alcance, cinco patrones, placement controlado y separación del harness.

---

## 2026-09-21 — Fijar propuesta oficial y cerrar diseño técnico de semana 8

**Estado:** aceptada.

**Decisión 1 — fuente oficial:** `ppg_ls.contreras_202620 (2).pdf` es la única propuesta que debe usarse para determinar alcance, metodología y cronograma. Las versiones anteriores se conservan solo como historial.

**Decisión 2 — semana 8:** el hito vigente es `A7: diseño de arquitectura y modelo de datos`, no implementación de extracción. El producto es el diseño técnico.

**Arquitectura adoptada:** `extracción -> normalización -> integración -> cálculo -> validación -> resultados`.

**Modelo común:** `Run`, `Node`, `Task`, `File`, `TaskIO`, `Dependency`, `StagingEvent`, `RequiredMovement`, `MetricResult`.

**Separación:** los scripts que generan y ejecutan condiciones controladas forman el harness experimental y no deben confundirse con el núcleo de medición.

**Escalamiento:** 1, 2 o 4 nodos no constituyen por sí mismos un objetivo. Solo se incorporan cuando una hipótesis o condición de validación requiera variar el grado de distribución manteniendo controlado lo demás.

**Siguiente hito:** semana 9 implementa/separa formalmente extracción y normalización de Pegasus/HTCondor.

## 2026-09-21 — Simplificar la formalización y separar placement de execution model

**Estado:** aceptada; reemplaza la formalización del 2026-09-19.

**Decisión:** Se eliminan de la formulación principal `pi_A`, `Phi(A,G,W,R)`, `D+`, `Transfers` y una función separada `Payload`. El workflow se expresa como `WF=(Tasks,Deps)`, el placement como `PL: Tasks -> Workers`, y el tamaño de cada dato con `SizeOf`.

**Motivo:** La notación anterior introducía dependencias que no eran necesarias para calcular las métricas y podía confundirse con una evaluación de algoritmos de scheduling. También existían dos expresiones de `M_obs` con niveles de abstracción distintos y `EM` no estaba definido con suficiente precisión.

**Consecuencia para M_req:** `M_req(WF,SizeOf,PL)` suma inputs externos, datos intermedios que deben cambiar de worker bajo `PL` y outputs finales. La implementación general mantiene reutilización local ideal y cuenta una copia por worker destino distinto cuando un archivo tiene varios consumidores.

**Consecuencia para M_obs:** se fija explícitamente `EM_HTC = condorio + HTCondor file transfer + sandbox por job`. Bajo este modelo, `M_obs` se define una sola vez como la suma de los tamaños de inputs y outputs científicos materializados por cada job. `PL` no se usa como argumento de `M_obs` en los experimentos controlados porque cambiar solamente el worker no cambia el contrato de I/O.

**Límite:** la invariancia de `M_obs` frente a `PL` es específica del execution model estudiado y de esta definición basada en staging; no se generaliza a modelos con caché/reutilización local explícita ni se interpreta como tráfico packet-level.

---

## 2026-09-21 — Alinear la metodología con la tesis de referencia

**Estado:** aceptada.

**Decisión:** La sección experimental seguirá una separación análoga a Vivas: sistema, workloads, escenarios y métricas. La sección `Algorithms` de la tesis de referencia se sustituye por `Placement scenarios`, porque esta tesis no compara schedulers; SAME, BALANCED-LOCAL y CROSS son controles experimentales.

**Consecuencia:** La documentación mostrará explícitamente sistema/software, execution model, patrones, factores/niveles, repeticiones, métricas, criterio PASS y limitaciones antes de interpretar resultados.

---

## 2026-09-19 — Formalizar dependencia de la métrica en G, SizeOf, pi_A y E

**Estado:** reemplazada por la decisión del 2026-09-21.

**Decisión anterior:** se había adoptado `pi_A=Phi(A,G,W,R)` y `M=M(G,SizeOf,pi_A,E)`.

**Razón del reemplazo:** mezclaba la generación del placement con la definición de las métricas y añadía notación no necesaria para la validación actual.

---

## 2026-09-18 — BALANCED-LOCAL pasa de plan a evidencia validada

**Estado:** aceptada.

**Decisión:** `balanced-local` queda incorporado como escenario controlado validado, no como scheduler ni como placement óptimo.

**Evidencia:** process, pipeline, distribution, aggregation y redistribution coincidieron manual/script en `M_req`, `M_obs` y placement observado.

---

## 2026-09-18 — Size-full queda como evidencia cerrada

**Estado:** aceptada.

**Decisión:** La campaña `size-full` se considera cerrada porque alcanzó 45/45 PASS.

**Consecuencia:** La evidencia cerrada incluye repetibilidad a S=10 MiB y sensibilidad completa S=1,10,50 MiB.

---

## 2026-09-18 — Alinear sección experimental con Jain

**Estado:** aceptada.

**Decisión:** La presentación y el LaTeX deben mostrar explícitamente objetivos, sistema, workloads, factores, niveles, repeticiones, métricas, análisis y limitaciones.


---

## 2026-09-26 — Aceptar observabilidad a nivel job con reconciliación exacta como evidencia válida condicionada

**Estado:** aceptada de forma provisional para cerrar P2; falta convertirla en política de coverage general de la herramienta.

**Evidencia:** en las corridas piloto `process-same-w1-20260917-232331` y `pipeline-balanced-local-20260917-232616`, los ClassAds de HTCondor identifican un único intento por job, el worker real y los totales de transferencia del sandbox. Los `.sub` enumeran los archivos transferidos y los `.meta` de Pegasus preservan tamaños científicos. Para los cuatro jobs auditados, la suma del file-set de entrada coincide exactamente con `TransferInputStats.CedarSizeBytesTotal` / `BytesRecvd`. En salida, el total coincide con 50 MiB de output científico más los bytes auxiliares de stdout/stderr, con `CedarFilesCountTotal=3`.

**Decisión:** no exigir obligatoriamente un evento HTCondor separado por archivo para considerar observación válida. Se admite `M_obs` cuando existe una **reconciliación exacta y trazable a nivel job** que permita separar el payload científico de los artefactos auxiliares, siempre que:

1. la corrida y los jobs estén identificados inequívocamente;
2. el worker observado esté confirmado;
3. el intento o multiplicidad de intentos esté registrado;
4. el conjunto de archivos transferidos sea conocido;
5. los tamaños científicos estén preservados;
6. los bytes agregados de transferencia se reconcilien con ese conjunto sin residuo no explicado;
7. el boundary de `M_obs` sea idéntico al de `M_req`.

**Etiqueta provisional:** `JOB_LEVEL_EXACT_RECONCILIATION`.

**Consecuencia:** para process S=50 MiB se puede sostener provisionalmente `M_obs=100 MiB`; para pipeline BALANCED-LOCAL S=50 MiB, `M_obs=300 MiB`. La razón candidata produce respectivamente `eta_move=1.0` y `0.5`. Esto no implica granularidad de evento por archivo ni calidad del placement.

## 2026-09-26 — Aceptar `JOB_LEVEL_RECONCILED` como evidencia suficiente para `M_obs` científico en corridas controladas

**Estado:** aceptada para las corridas auditadas con cobertura explícita.

**Decisión:** `M_obs` puede declararse para una corrida cuando: (1) cada job científico está identificado y mapeado a su worker; (2) el job tiene un único intento o los intentos están explícitamente separados; (3) HTCondor registra bytes y conteos de transferencia a nivel job; (4) el `.sub` define el conjunto de archivos transferidos; (5) Pegasus conserva tamaños de los archivos científicos; y (6) la evidencia conjunta permite reconciliar el payload científico dentro del sandbox sin asignaciones proporcionales arbitrarias. Esta cobertura se etiqueta `JOB_LEVEL_RECONCILED`, no `FILE_LEVEL`.

**Aplicación:** en el trío pipeline de 10 MiB SAME/BALANCED/CROSS del 17-09-2026, `M_obs=60 MiB` en las tres corridas y `M_req={20,30,40} MiB`, dando `eta_move={1/3,1/2,2/3}`. La variación de `eta_move` refleja la demanda del placement condicionado; no se usa para ordenar placements.


## 2026-09-26 — Congelar P2 y adoptar DME

**Estado:** aceptada; reemplaza la nomenclatura candidata `eta_move` para documentos y código nuevos.

**Decisión:** la métrica principal se denomina `DME(R)` (`DataMovementEfficiency`) y se define como `RequiredMovement(R) / ObservedMovement(R)` solo cuando `Coverage(R)=1` y ambas cantidades usan el mismo alcance científico. `RequiredMovement=M_req`, `DeclaredMovement=M_rec` y `ObservedMovement=M_obs` se conservan como correspondencias con la notación histórica.

**Coverage:** no se usa la expresión vaga «coverage suficiente». La métrica principal exige confirmación de todos los movimientos científicos declarados por los jobs ejecutados. Si falta evidencia para alguno, `ObservedMovement` queda indeterminado para DME y no se sustituye por cero.

**Movimiento científico:** no significa toda transferencia de red. Es cada ocurrencia de entrada/salida de un archivo que pertenece al dataflow científico (input externo, intermediate u output final). Runtime, ejecutables, metadata, scripts, logs y stdout/stderr son auxiliares: sirven para reconciliar el sandbox, pero no suman a `ObservedMovement`.

**Implementación:** el Analyzer se divide en identificación de archivos científicos, extracción de placement/tamaños, cálculo de RequiredMovement, reconstrucción de movimientos declarados, recolección de evidencia, reconciliación, Coverage, ObservedMovement y DME. El contrato completo está en `TESIS_P2_CONTRATO_METRICA_ANALYZER_20260926.md`.

---

## 2026-09-30 — DEC-R1: Gate R cerrado

Se aprueba `TESIS_REQUIREMENTS_SPEC_20260930.md` como fuente canónica de requerimientos. Quedan congelados scope v1, payload semantics, Coverage, DME, retries/fallos, estados y política fail-closed. Ver `TESIS_GATE_R_CIERRE_20260930.md`.

## 2026-09-30 — DEC-D1: diseño file-centric y adapter-based

La herramienta se diseña alrededor de `ScientificFile`, identidad estable por corrida, `ExecutionModelProfile` y adapters. No se hardcodean pattern, placement ni rutas master/worker en el core.

## 2026-09-30 — DEC-D2: evidencia job-level con dos modos

`JOB_LEVEL_RECONCILED` se divide en:

- `EXACT_BYTES`: conteo y bytes del sandbox coinciden exactamente con el manifiesto completo;
- `SUCCESSFUL_MANIFEST`: transferencia exitosa de un manifiesto completo, conteo observado coincidente, tamaño científico autoritativo y ausencia de imputación proporcional.

Esta decisión permite representar con precisión la diferencia entre transfer-in exacto y outputs donde stdout/stderr auxiliares pudieron ser limpiados.

## 2026-09-30 — DEC-D3: Gate D cerrado

`TESIS_DESIGN_SPEC_20260930.md` y `TESIS_TRACEABILITY_MATRIX_20260930.md` cubren 80/80 requisitos. La implementación queda habilitada bajo `TESIS_IMPLEMENTATION_PLAN_20260930.md`. No se lanzan campañas experimentales nuevas hasta Gate I.

---

## 2026-09-30 — DEC-I1: extensiones de implementación sin cambiar semántica

Durante I1 se concretó `Diagnostic(status, reason_code, message, context, provenance)` y `MetricStatus = CALCULATED | NOT_APPLICABLE | INDETERMINATE | INVALID`. Estas estructuras operacionalizan el Design Spec; no cambian la definición de RequiredMovement, ObservedMovement, Coverage ni DME.

## 2026-09-30 — DEC-I4A: detección de execution model fail-closed

Los atributos necesarios para distinguir un modelo soportado de uno no soportado no se completan con defaults silenciosos. Si falta evidencia crítica, el perfil no selecciona adapter. Se añadieron reason codes de implementación para evidencia faltante/conflictiva y configuraciones/versiones no soportadas. Esto implementa la regla del Design Spec §10.

## 2026-09-30 — DEC-I4B: identificación de compute jobs por semántica Pegasus

Se descarta clasificar jobs científicos por nombre de archivo (`data_task_*`). En los submits Pegasus 5.x preservados, el builder exige `+pegasus_job_class = 1` y un `+pegasus_wf_dax_job_id` real, distinto de valores nulos. Los jobs auxiliares observados usan clases distintas (transfer, registration, create-dir, cleanup). La corrección fue necesaria porque `+pegasus_wf_dax_job_id = "null"` aparecía también en jobs auxiliares y una primera versión los clasificaba erróneamente como compute.

Smoke real posterior: `process-same-w1-20260917-222429` -> 1 compute job; `distribution-same-w1-20260917-181537` -> 5 compute jobs. Ambos reconstruyen `Pegasus 5.1.2`, `universe=vanilla`, `should_transfer_files=YES`, `when_to_transfer_output=ON_EXIT`, `clustered_jobs=False` y sin conflicto.

## 2026-09-30 — DEC-I4C: adapter sin inferencias implícitas

`CondorIOStandardAdapter.supports()` delega la validación al detector canónico y solo acepta un perfil explícitamente soportado y seleccionado para ese adapter. No rellena `condorio`, submit host, bypass/sharedfs ni versiones por suposición.

## 2026-09-30 — ACCIÓN ABIERTA I3B

La implementación actual de identidad de archivo permite fallback a `physical_path` cuando existe un único path. El Design Spec exige además una **relación semántica inequívoca dentro del run**. Antes de considerar I3 semánticamente cerrado y antes del commit final de I4 se debe endurecer este fallback y añadir prueba negativa `physical path alone is not sufficient identity`.

## 2026-09-30 — ESTADO DE IMPLEMENTACIÓN

Suite completa actual: **101/101 PASS**. I4A, I4B e I4C están cerrados; I4 global continúa abierto por evidencia crítica todavía no recuperada/demostrada (`data_configuration`, `submit_host`, `htcondor_version`, `bypass_enabled`, `shared_filesystem`) y por la verificación de separación submit-host/workers. El analyzer histórico conserva SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

---

## 2026-09-30 — DEC-I3B-CLOSE: identidad física fail-closed

Se cierra la deuda I3B. `physical_path` deja de ser suficiente por sí solo para resolver `file_id`: el fallback solo es válido cuando existe una relación semántica inequívoca dentro del run. La prueba negativa `physical_path_alone_is_not_sufficient_identity` queda verde. Commit: `1ebf309`.

## 2026-09-30 — DEC-I4D: execution model desde artefactos preservados

Los runs preservados contienen evidencia suficiente para completar el perfil v1 sin inferencias silenciosas: `*.metrics` aporta `data_config=condorio`; `braindump.yml` aporta `submit_hostname=pegasus-master`; `condor_history.long` aporta `CondorVersion=25.12.2`; `workflow.yml` aporta `sharedFileSystem=false`; la ausencia de habilitación de bypass se combina únicamente con el default documentado de Pegasus 5.x y se registra con provenance `derived`, no como hecho oculto. También se valida explícitamente `when_to_transfer_output=ON_EXIT` para el scope v1.

Smoke real: process y distribution seleccionan `CondorIOStandardAdapter`, sin razones de rechazo. Commit I4: `31f4244`.

## 2026-09-30 — DEC-I4-CLOSE: I4 cerrado

I4 queda cerrado después de 106/106 tests PASS, smoke real PASS en dos runs preservados y checksum legacy intacto. El siguiente frente es I5 Scientific Dataflow, seguido inmediatamente por I6 RequiredMovement e I7 DeclaredMovement.

---

## 2026-09-30 17:13 — DEC-I3B-CLOSE: identidad física fail-closed

Se cierra la deuda I3B. Un único path físico no constituye identidad suficiente. El fallback `PHYSICAL_PATH` solo se acepta cuando la relación semántica del archivo dentro de la corrida ha sido demostrada como inequívoca. Commit `1ebf309`.

## 2026-09-30 17:13 — DEC-I4D: evidencia preservada para execution model

Se incorporan como fuentes trazables del perfil v1 los artefactos preservados de la corrida: `.metrics` para `data_config=condorio`; `braindump.yml` para `submit_hostname`; `workflow.yml` para `sharedFileSystem`; `condor_history.long` para versión HTCondor; y submits científicos para `vanilla`, HTCondor file transfer y `ON_EXIT`.

La ausencia de bypass habilitado se representa únicamente bajo la regla implementada y trazable para el scope Pegasus 5.x; no se transforma en una inferencia silenciosa.

## 2026-09-30 17:13 — DEC-I4-CLOSE: Execution Model Detection cerrado

Se cierra I4 con commit `31f4244`. Los runs preservados de process y distribution seleccionan `CondorIOStandardAdapter` con `supported=True`. La suite completa queda `106/106 PASS`.

El siguiente bloque habilitado es I5 Scientific Dataflow.

---

<!-- SYNC_20260930_I13_GATEI -->
## Decisión operativa — 2026-09-30 después de I13

**Decisión:** no cerrar Gate I ni activar I14 todavía.

Razón:

1. I12 e I13 ya están cerrados y reproducibles (`b5880d6`, `77c6ff6`).
2. La auditoría de Gate I no encontró hardcodes de patrón/placement en el núcleo v1 y confirmó `schema_version = 1`.
3. Sin embargo, README/CLI todavía requieren sincronización explícita con la semántica v1 y la preservación histórica de v0.5.1.
4. Después de ese ajuste se exige **una única suite final**; solo si queda verde y el worktree queda limpio se emite el cierre formal de Gate I.

Cadena aprobada:

```text
I13 CLOSED
→ sincronización documental completa
→ README/CLI v1 + nota legacy
→ suite final Gate I
→ Gate I CLOSED
→ I14 ACTIVE
```


---

## Checkpoint de continuidad — 2026-10-03, Gate I

Este apéndice actualiza el **estado operativo** del documento histórico; no altera las fórmulas ni las decisiones cerradas de Requirements/Design. Gate R y Gate D siguen cerrados; I0–I13 siguen cerrados. **Gate I CLOSED** sobre el commit `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6` de `feat/analyzer-v1`: suite normal 142 pruebas correctas y una omitida; integración portable correcta (cinco runs); integración con directorios originales correcta (cinco runs); CLI smoke `VALID`, con 104857600 B para Mreq/Mrec/Mobs, Coverage=1 y DME=1. Los fixtures portables tienen manifiesto SHA-256 verificado (179 entradas). README, CHANGELOG y TEST_REPORT fueron actualizados; no cambió código funcional. El checkout del commit de cierre quedó limpio. Las ramas se publicaron en GitHub el 4/10/2026 desde Windows por HTTPS; PR pendiente de creación/revisión.

En la captura directa del master del 3/10, `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) no respondieron ping ni SSH y no anunciaron `startd`; su hardware/software no se ha medido. Esto no cambia la topología prevista de dos workers. I14 aún no se inicia; Gate V permanece pendiente. La matriz, oráculos y runbook preparados están en `docs/thesis/validation/`, con campaña larga sujeta a disponibilidad del pool y decisión posterior. El estado y la precedencia actuales están en `docs/thesis/CODEX_CONTEXT.md` y `CONTEXT_INDEX.md`.
