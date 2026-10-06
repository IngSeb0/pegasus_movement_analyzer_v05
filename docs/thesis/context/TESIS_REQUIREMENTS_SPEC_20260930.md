# TESIS — Requirements Specification

**Proyecto:** Data Movement Assessment in Scientific Workflows  
**Autor:** Luis Sebastián Contreras Díaz  
**Versión:** 1.1 — 30 de septiembre de 2026  
**Estado:** **CONGELADO — Gate R cerrado**  
**Propósito:** definir **qué debe hacer** la métrica, la herramienta y el protocolo experimental antes de diseñar o implementar software nuevo.

---

## 0. Regla de trabajo del proyecto

El desarrollo seguirá cuatro fases secuenciales con gates explícitos:

```text
REQUERIMIENTOS
      ↓  Gate R
DISEÑO COMPLETO
      ↓  Gate D
IMPLEMENTACIÓN
      ↓  Gate I
PRUEBAS Y VALIDACIÓN
      ↓  Gate V
```

No se modifica el código para resolver un requisito aún ambiguo. No se diseña una solución cuyo requisito no esté identificado. No se valida una implementación contra resultados que no tengan un oráculo o criterio de aceptación definido.

---

# 1. Fuente de verdad y alcance

## 1.1 Fuente de alcance

La propuesta oficial `ppg_ls.contreras_202620 (2)(1).pdf` gobierna:

- problema;
- justificación;
- objetivo general y objetivos específicos;
- alcance;
- metodología;
- ambiente experimental;
- patrones de validación;
- criterios de validación.

La tesis tiene como producto central una **herramienta de medición**, no un scheduler, un sistema de staging nuevo ni una comparación exhaustiva de algoritmos de planificación.

## 1.2 Objetivo funcional de la herramienta

Para una ejecución concreta de un workflow gestionado por Pegasus/HTCondor, la herramienta deberá:

1. reconstruir el dataflow científico relevante;
2. recuperar el placement realmente ejecutado;
3. identificar el movimiento de datos requerido por workflow + placement;
4. reconstruir el movimiento científico declarado por los jobs;
5. recopilar evidencia de transferencia producida por la ejecución;
6. decidir qué movimientos declarados pueden confirmarse;
7. calcular `ObservedMovement` únicamente con evidencia completa;
8. calcular `DME` únicamente cuando se cumplan sus precondiciones;
9. conservar trazabilidad hacia las fuentes originales.

---

# 2. Vocabulario normativo

Los documentos, el código y la presentación deberán usar estos nombres como terminología principal.

| Concepto | Nombre principal | Alias corto permitido |
|---|---|---|
| movimiento lógico requerido | `RequiredMovement` | `M_req` |
| movimiento declarado/reconstruido | `DeclaredMovement` | `M_rec` |
| movimiento científico confirmado | `ObservedMovement` | `M_obs` |
| cobertura de evidencia | `Coverage` | — |
| eficiencia de movimiento | `DataMovementEfficiency` | `DME` |

La notación `eta_move` queda deprecada para documentos nuevos.

---

# 3. Definiciones del fenómeno medido

## 3.1 Archivo científico

Un **archivo científico** es un archivo cuyo contenido forma parte del dataflow de la aplicación científica. Puede ser:

- `input`: entrada externa consumida por una o más tareas;
- `intermediate`: resultado de una tarea consumido por otra(s);
- `output`: resultado final declarado del workflow.

No son payload científico:

- ejecutables;
- wrappers;
- Pegasus worker packages;
- scripts de Pegasus/PegasusLite;
- archivos `.meta`;
- stdout/stderr;
- logs;
- archivos de control de DAGMan/HTCondor;
- otros artefactos auxiliares sin semántica de dato científico.

**REQ-DATA-01.** La clasificación debe derivarse de la semántica del workflow/ejecución, no de heurísticas basadas únicamente en extensión o nombre de archivo.

## 3.2 Ubicación

Una **ubicación** es la unidad usada para decidir si un dato cambió de lugar.

En el testbed actual:

```text
SubmitHost = pegasus-master
Worker1    = pegasus-worker1
Worker2    = pegasus-worker2
```

**REQ-LOC-01.** La identidad de ubicación debe ser explícita y consistente en numerador y denominador.  
**REQ-LOC-02.** La herramienta no debe asumir que todo input proviene siempre del SubmitHost ni que todo output termina siempre allí; debe usar el origen/destino efectivo cuando esa información esté disponible.  
**REQ-LOC-03.** Si la configuración usa un mecanismo cuyo origen/destino no puede determinarse con la evidencia disponible, el caso se reporta como no soportado o con evidencia insuficiente.

## 3.3 Movimiento científico

Un movimiento científico representa que un archivo científico de tamaño conocido pasa de una ubicación a otra como parte de la ejecución.

Cada movimiento debe poder representarse, como mínimo, mediante:

```text
archivo
rol científico
bytes de payload
origen
Destino
job/tarea asociada
sentido (input/output)
intento de ejecución cuando aplique
fuente de evidencia
estado de verificación
```

La tesis mide **bytes de payload científico**, no paquetes Ethernet, bytes de protocolo, headers, cifrado o tráfico total de red.

---

# 4. RequiredMovement

## 4.1 Significado

`RequiredMovement(R)` es el volumen mínimo de payload científico que debe alcanzar ubicaciones nuevas para satisfacer el dataflow de una ejecución `R`, manteniendo fijo el placement observado.

No optimiza el placement y no modela la ruta concreta de `condorio`.

## 4.2 Regla general por archivo

Para cada archivo científico se determina:

1. su ubicación inicial:
   - origen externo, si es input;
   - worker productor, si es intermediate/output;
2. el conjunto de ubicaciones que deben disponer del archivo:
   - workers consumidores;
   - destino final, si el archivo debe conservarse como output.

El archivo aporta su tamaño **una vez por cada ubicación nueva distinta** que deba alcanzar.

Esto evita doble conteo cuando varios consumidores están en el mismo worker.

## 4.3 Requerimientos

**REQ-RM-01.** Un consumo en la misma ubicación que el productor aporta `0` bytes requeridos.  
**REQ-RM-02.** Un consumo en una ubicación distinta aporta el tamaño completo del archivo.  
**REQ-RM-03.** Un archivo compartido por varios consumidores en el mismo worker se cuenta una sola vez para ese worker.  
**REQ-RM-04.** Si el archivo debe alcanzar varios workers distintos, se cuenta una copia por ubicación destino distinta.  
**REQ-RM-05.** Un output final agrega movimiento solo si su destino final es distinto de una ubicación que ya dispone del archivo.  
**REQ-RM-06.** Inputs externos y outputs finales deben usar origen/destino declarados; no se representan como tareas ficticias.  
**REQ-RM-07.** `RequiredMovement` debe expresarse internamente en bytes enteros no negativos.  
**REQ-RM-08.** La fórmula debe ser independiente de los nombres SAME/BALANCED/CROSS y de los cinco patrones experimentales.

---

# 5. DeclaredMovement

## 5.1 Significado

`DeclaredMovement(R)` es el volumen de archivos científicos que los jobs **realmente pertenecientes a la ejecución** declaran como parte de sus transferencias de input/output bajo el execution model estudiado.

No significa que la transferencia esté confirmada; describe el contrato de transferencia del job.

## 5.2 Requerimientos

**REQ-DM-01.** Solo se consideran jobs científicos; jobs auxiliares de Pegasus deben separarse.  
**REQ-DM-02.** Debe conservarse el sentido del movimiento: input o output.  
**REQ-DM-03.** Debe conservarse el job/tarea y, si existe más de un intento, la multiplicidad relevante.  
**REQ-DM-04.** Los archivos auxiliares del sandbox no se suman a `DeclaredMovement` científico.  
**REQ-DM-05.** La herramienta debe conservar el file-set auxiliar para poder reconciliar el total de sandbox con la evidencia HTCondor.  
**REQ-DM-06.** Si el job usa una semántica de transferencia no soportada por el modelo vigente, debe detectarse y reportarse; nunca debe interpretarse silenciosamente como `condorio` estándar.

---

# 6. ObservedMovement

## 6.1 Significado

`ObservedMovement(R)` es el volumen de payload científico perteneciente a movimientos declarados cuya ocurrencia puede **confirmarse con evidencia de la ejecución**.

La palabra “observed” no significa packet-level. En esta tesis significa **movimiento de payload científico confirmado a la granularidad disponible y documentada**.

## 6.2 Evidencia mínima aceptada en el piloto actual

La cobertura `JOB_LEVEL_RECONCILED` es aceptable cuando, para cada job relevante:

1. el job está identificado inequívocamente;
2. la tarea científica asociada está identificada;
3. el worker realmente usado está identificado;
4. el número de intentos está conocido;
5. el conjunto de archivos transferidos está conocido;
6. el tamaño de cada archivo científico está conocido;
7. HTCondor reporta estadísticas de transferencia del sandbox;
8. existe una reconciliación suficiente del sandbox por una de estas dos vías:
   - **exact-byte reconciliation:** el file-set, conteo y total de bytes observados coinciden con el manifiesto completo y sus tamaños; o
   - **successful-manifest reconciliation:** el manifiesto efectivo está completo, la transferencia de la dirección terminó exitosamente, el conteo observado coincide con el manifiesto, no hay errores de transferencia, el intento es conocido y cada archivo científico tiene tamaño autoritativo; los bytes auxiliares no se imputan al archivo científico;
9. la dirección de la transferencia está determinada;
10. no existe ambigüedad de retries, remaps, plugins o transferencias parciales que impida atribuir el movimiento científico.

## 6.3 Requerimientos

**REQ-OM-01.** `BytesRecvd`, `BytesSent`, `TransferInputStats` o `TransferOutputStats` no son por sí solos `ObservedMovement` científico.  
**REQ-OM-02.** Los bytes agregados de sandbox deben separarse de runtime, scripts, metadata, stdout/stderr y demás auxiliares.  
**REQ-OM-03.** Está prohibido distribuir proporcionalmente un total agregado entre archivos.  
**REQ-OM-04.** Si la reconciliación no es exacta bajo la política de evidencia declarada, el movimiento afectado queda no verificado.  
**REQ-OM-05.** Si existe evidencia directa por archivo en una futura configuración, podrá usarse como nivel más fuerte de evidencia sin cambiar la semántica de `ObservedMovement`.  
**REQ-OM-06.** La herramienta debe registrar el nivel de evidencia usado en cada resultado.  
**REQ-OM-07.** `TransferInputSizeMB` no se acepta como prueba de bytes efectivamente transferidos; HTCondor lo define como tamaño de inputs a transferir y además puede excluir transferencias vía plugins.  
**REQ-OM-08.** Las estadísticas por protocolo de HTCondor deberán preservarse; no se asumirá que toda transferencia usa Cedar si aparecen plugins.

---

# 7. Coverage

## 7.1 Definición principal

```text
Coverage = movimientos científicos confirmados / movimientos científicos declarados
```

`Coverage` se usa como precondición de validez, no como aproximación de DME.

**REQ-COV-01.** La métrica principal solo se calcula cuando `Coverage = 1`.  
**REQ-COV-02.** Si `Coverage < 1`, `ObservedMovement` completo y `DME` se reportan como `N/A`/indeterminados.  
**REQ-COV-03.** Ausencia de evidencia nunca equivale a cero bytes.  
**REQ-COV-04.** Se podrá reportar adicionalmente cobertura por bytes declarados como diagnóstico, pero no reemplaza la condición de cobertura completa por movimientos.

---

# 8. DataMovementEfficiency (DME)

## 8.1 Fórmula

Cuando la ejecución cumple las precondiciones:

```text
DME(R) = RequiredMovement(R) / ObservedMovement(R)
```

## 8.2 Interpretación

`DME` es la fracción del movimiento científico confirmado que corresponde al movimiento mínimo exigido por el dataflow **para ese mismo placement y esas mismas ubicaciones**.

## 8.3 Requerimientos

**REQ-DME-01.** `RequiredMovement` y `ObservedMovement` deben medir el mismo conjunto de archivos científicos y la misma noción de ubicación.  
**REQ-DME-02.** Si `ObservedMovement > 0` y las precondiciones son válidas, el valor esperado está entre `0` y `1`.  
**REQ-DME-03.** Si `RequiredMovement = 0` y `ObservedMovement > 0`, `DME = 0`.  
**REQ-DME-04.** Si `RequiredMovement = 0` y `ObservedMovement = 0`, `DME = N/A` porque el cociente no informa eficiencia de movimiento.  
**REQ-DME-05.** Si `ObservedMovement < RequiredMovement`, el resultado se marca inválido y debe investigarse la evidencia o los supuestos.  
**REQ-DME-06.** Un DME mayor no significa automáticamente un placement mejor, menor tiempo total ni mejor scheduler.  
**REQ-DME-07.** `ObservedMovement - RequiredMovement` podrá reportarse como exceso respecto al lower bound lógico, pero no como “bytes necesariamente ahorrables” sin demostrar un execution model alternativo que los evite.

---

# 9. Execution model soportado

## 9.1 Scope v1

La primera versión validada de la herramienta tendrá como execution model objetivo:

```text
Pegasus 5.x
pegasus.data.configuration = condorio
HTCondor vanilla universe
HTCondor-managed file transfer
jobs científicos en workers separados del submit host
```

El testbed oficial permanece en VMs Linux sobre host Windows, de acuerdo con la propuesta.

## 9.2 Requerimientos

**REQ-EM-01.** La herramienta debe identificar y registrar el execution model antes de calcular las métricas.  
**REQ-EM-02.** Configuraciones `sharedfs`, bypass de inputs, transfer plugins, múltiples staging sites u otros modelos no se interpretarán como `condorio` estándar sin soporte explícito.  
**REQ-EM-03.** Un modo no soportado produce un diagnóstico explícito, no un resultado aparentemente válido.  
**REQ-EM-04.** La arquitectura futura debe permitir agregar adapters de execution model sin cambiar la definición central de las métricas.

---

# 10. Fuentes de información y trazabilidad

La herramienta deberá poder relacionar cada valor con sus fuentes.

Fuentes actuales:

- DAG / estructura de ejecución Pegasus;
- `.sub` de jobs;
- `.meta` / cache metadata;
- replica/output metadata cuando aplique;
- `condor_history -long` / ClassAds;
- job event logs;
- archivos físicos preservados, cuando existan;
- configuración del experimento;
- versiones de Pegasus, HTCondor y Analyzer.

**REQ-TRACE-01.** Cada tamaño debe almacenar su `size_source`.  
**REQ-TRACE-02.** Cada placement debe almacenar su fuente de evidencia.  
**REQ-TRACE-03.** Cada movimiento observado debe poder remontarse a job, archivo y evidencia.  
**REQ-TRACE-04.** Cada resultado final debe incluir run id/path, configuración, versiones y versión/commit del Analyzer.  
**REQ-TRACE-05.** Si dos fuentes discrepan, la discrepancia debe aparecer en el reporte y el resultado no debe resolverla silenciosamente.

---

# 11. Requerimientos funcionales de la herramienta

**REQ-F-01.** Cargar una ejecución existente sin modificar sus artefactos.  
**REQ-F-02.** Detectar tareas científicas y excluir auxiliares.  
**REQ-F-03.** Identificar archivos científicos y roles.  
**REQ-F-04.** Obtener tamaños en bytes con procedencia.  
**REQ-F-05.** Construir productor(es), consumidores, origen y destino final.  
**REQ-F-06.** Extraer placement observado.  
**REQ-F-07.** Construir los registros que componen `RequiredMovement`.  
**REQ-F-08.** Construir los movimientos declarados por los jobs.  
**REQ-F-09.** Obtener estadísticas reales de transferencia HTCondor.  
**REQ-F-10.** Reconciliar evidencia de cada job/dirección.  
**REQ-F-11.** Calcular `Coverage`.  
**REQ-F-12.** Calcular `ObservedMovement` solo con cobertura completa.  
**REQ-F-13.** Validar precondiciones e invariantes.  
**REQ-F-14.** Calcular `DME` cuando sea válido.  
**REQ-F-15.** Generar salidas legibles por humanos y por programas.  
**REQ-F-16.** Reportar explícitamente cualquier dato faltante, caso no soportado o inconsistencia.

---

# 12. Salidas requeridas

Como mínimo, cada análisis debe producir:

```text
run identifier
workflow/pattern (contexto)
execution model
observed placement
scientific files + roles + sizes + provenance
RequiredMovement total + detalle
DeclaredMovement total + detalle
transfer evidence por job/dirección
Coverage
ObservedMovement o N/A
DME o N/A
evidence level
valid / invalid
reasons / warnings
software versions
```

Formatos mínimos:

- JSON canónico;
- TSV/CSV para análisis tabular;
- reporte de texto legible.

---

# 13. Requerimientos no funcionales

**REQ-NF-01 — Determinismo.** Mismos artefactos de entrada deben producir el mismo cálculo.  
**REQ-NF-02 — Reproducibilidad.** Deben conservarse configuración, versión de software y fuentes utilizadas.  
**REQ-NF-03 — Trazabilidad.** Ningún valor agregado puede existir sin detalle recuperable.  
**REQ-NF-04 — Fail closed.** Ante evidencia ambigua, el sistema prefiere `N/A` antes que un número no sustentado.  
**REQ-NF-05 — Independencia del patrón.** El núcleo no contiene fórmulas hardcoded para process/pipeline/distribution/aggregation/redistribution.  
**REQ-NF-06 — Independencia del placement experimental.** SAME/BALANCED/CROSS son datos de entrada/contexto, no ramas especiales de cálculo.  
**REQ-NF-07 — N workers.** El modelo no debe limitarse conceptualmente a dos workers.  
**REQ-NF-08 — Unidades.** El almacenamiento canónico usa bytes; MiB es solo presentación (`1 MiB = 1,048,576 bytes`).  
**REQ-NF-09 — No invasividad.** El análisis debe ser post-mortem siempre que la evidencia existente lo permita; cualquier instrumentación adicional deberá medirse como overhead.  
**REQ-NF-10 — Compatibilidad histórica.** Los resultados v0.5.1 deben preservarse como evidencia histórica, pero su columna histórica `M_obs` se interpreta como `DeclaredMovement/M_rec` y no se sobreescribe.

---

# 14. Edge cases que deben estar contemplados desde requisitos

La implementación no puede considerarse completa mientras no exista una decisión explícita para cada caso.

| Caso | Política requerida |
|---|---|
| retries / re-ejecuciones | incluir movimiento repetido solo con atribución exacta por intento; si es ambiguo, `Coverage < 1` |
| job fallido | no producir DME de workflow completo; permitir diagnóstico parcial separado |
| transferencia parcial/fallida | no contar como movimiento completo salvo evidencia inequívoca del payload transferido |
| shared input a varios jobs mismo worker | `RequiredMovement`: una ubicación; `ObservedMovement`: todas las materializaciones verificadas |
| fan-out a varios workers | una copia requerida por worker destino distinto |
| varios archivos entre mismo productor/consumidor | tratarlos por identidad de archivo; no colapsarlos salvo agregación explícita y trazable |
| archivo intermediate y final output | construir conjunto de destinos y evitar doble conteo de una ubicación ya alcanzada |
| archivo de tamaño 0 | movimiento puede existir como evento, pero aporta 0 bytes; cuidar DME 0/0 |
| nombres lógicos duplicados | exigir identidad inequívoca/versionada; si no, invalidar |
| producer múltiple para mismo archivo lógico | no asumir cuál es el origen; invalidar o requerir versión explícita |
| archivo físico limpiado | usar metadata preservada si su identidad/tamaño son trazables |
| archivo físico actual modificado | no usarlo como prueba histórica si no puede ligarse a la corrida |
| paths con remaps/renames | preservar LFN y path físico; aplicar remap explícito |
| directorios transferidos | expandir con manifiesto exacto o marcar no soportado |
| `condorio` con bypass | origen puede no ser SubmitHost; detectar y modelar o marcar no soportado |
| transfer plugins (HTTP/S3/etc.) | preservar protocolo y estadísticas específicas; no sumar solo Cedar |
| `sharedfs` | execution model distinto; no aplicar reglas condorio |
| output transfer on eviction | puede producir múltiples outputs; requiere atribución por intento |
| HTCondor history purgado | evidencia insuficiente salvo fuente equivalente preservada |
| ClassAds ausentes | no inferir valores desde secuencia temporal si la identificación no es inequívoca |
| jobs clustered / multiple tasks per job | detectar; soportar explícitamente o rechazar en v1 |
| caching/deduplicación | no inferir transferencia por mera declaración; usar evidencia real |
| compresión | DME sigue definido sobre payload científico, no wire bytes; reconciliación debe declarar qué representa la estadística observada |

---

# 15. Requerimientos experimentales

La validación utilizará los cinco patrones oficiales:

1. process;
2. pipeline;
3. data aggregation;
4. data distribution;
5. data redistribution.

**REQ-EXP-01.** Cada caso debe tener parámetros conocidos y oráculo manual cuando sea razonable.  
**REQ-EXP-02.** Las variaciones deben cambiar una condición primaria a la vez cuando se busque sensibilidad causal de la métrica.  
**REQ-EXP-03.** Deben conservarse artefactos crudos y resultados procesados.  
**REQ-EXP-04.** Cada resultado debe estar ligado a run, patrón, placement, tamaño/configuración y versiones.  
**REQ-EXP-05.** Deben existir pruebas de repetibilidad.  
**REQ-EXP-06.** Deben existir pruebas de sensibilidad estructural: tamaño, número de etapas, fan-out/fan-in y redistribución, según el patrón.  
**REQ-EXP-07.** Debe evaluarse overhead de cualquier instrumentación adicional.  
**REQ-EXP-08.** La validación oficial permanece en el ambiente virtualizado definido en la propuesta; moverla a cloud sería un cambio metodológico que requiere aprobación.

---

# 16. Criterios de aceptación del producto

El Gate R se considera cerrado cuando:

- no quedan términos centrales ambiguos;
- todos los edge cases tienen política o están explícitamente fuera de alcance;
- se ha decidido qué evidencia habilita `ObservedMovement` y DME;
- se ha decidido qué execution models soporta v1;
- existen criterios observables para `valid`, `N/A` e `invalid`;
- la lista de outputs obligatorios está cerrada;
- la matriz de validación requerida está definida a nivel de factores, no necesariamente ejecutada.

El Gate D posterior exigirá un diseño completo que trace **cada requisito** a:

```text
componente
modelo de datos
algoritmo
fuente de información
interfaz
error/diagnóstico
test futuro
```

---

# 17. Oráculos actualmente aceptados

Para pipeline de tres tareas con archivos de 10 MiB:

```text
SAME:      RequiredMovement = 20 MiB
BALANCED:  RequiredMovement = 30 MiB
CROSS:     RequiredMovement = 40 MiB
```

En el piloto `condorio` auditado:

```text
DeclaredMovement = 60 MiB
ObservedMovement = 60 MiB
Coverage         = 1
```

por tanto:

```text
DME(SAME)     = 20/60 = 0.3333
DME(BALANCED) = 30/60 = 0.5000
DME(CROSS)    = 40/60 = 0.6667
```

Estos valores son oráculos de regresión del piloto, no una afirmación de que CROSS sea un mejor placement.

---

# 18. Contraste con literatura y documentación técnica

1. **Pegasus** separa el workflow abstracto del entorno de ejecución y coordina tanto tareas como datos; esta separación respalda mantener workflow, placement y execution model como conceptos distintos.  
   Deelman et al., 2015. DOI: `10.1016/j.future.2014.10.008`.

2. La documentación de **Pegasus condorio** indica que, en un pool sin filesystem compartido, el submit host y HTCondor file transfer participan en la materialización de datos; también documenta bypass y otras configuraciones que impiden hardcodear universalmente `master -> worker`.  
   Pegasus WMS User Guide, *Data Transfers*: https://pegasus.isi.edu/documentation/user-guide/data-transfers.html

3. La documentación de **HTCondor** distingue `TransferInputSizeMB` —tamaño de inputs a transferir— de `TransferInputStats`/`TransferOutputStats`, que describen transferencias administradas por HTCondor y agregan información sobre intentos. Esto justifica no tratar `TransferInputSizeMB` como observación real y obliga a manejar retries/protocolos.  
   HTCondor Job ClassAd Attributes: https://htcondor.readthedocs.io/en/latest/classad-attributes/job-classad-attributes.html

4. La literatura de data placement y workflow scheduling representa archivos, dependencias, tareas y ubicaciones como elementos centrales del costo de comunicación. Esto respalda que `RequiredMovement` dependa de dataflow + placement, sin convertir la tesis en un problema de scheduling.  
   Yuan et al., 2010. DOI: `10.1016/j.future.2010.02.004`.  
   Çatalyürek, Kaya & Uçar, 2011. DOI: `10.1145/1996014.1996022`.

5. Los communication lower bounds son una referencia conceptual válida para comparar movimiento observado contra una cantidad mínima, pero **no demuestran nuestra fórmula particular**. Nuestra definición debe defenderse por sus supuestos y por validación experimental.  
   Ballard, Demmel & Gearhart, 2011, UCB/EECS-2011-13.

6. Dai et al. muestran que workflows tradicionales pueden mover intermedios repetidamente entre cómputo y almacenamiento, reforzando la relevancia de distinguir movimiento inherente al dataflow de movimiento inducido por la materialización.  
   Dai et al., 2018. DOI: `10.48550/arXiv.1805.06167`.

7. Bharathi et al. sustentan el uso de estructuras recurrentes de workflow para construir casos controlados.  
   DOI: `10.1109/WORKS.2008.4723958`.

---

# 19. Decisiones de Gate R — APROBADAS

Gate R se cerró el 30 de septiembre de 2026 con las siguientes decisiones normativas:

1. **Scope v1:** `condorio` + HTCondor file transfer estándar del testbed actual; otros execution models requieren adapter explícito.
2. **Evidence policy:** `JOB_LEVEL_RECONCILED` es suficiente para DME cuando el file-set y la ejecución se reconcilian completamente, por igualdad exacta de bytes del sandbox o por confirmación inequívoca de un manifiesto completo transferido exitosamente; nunca mediante imputación proporcional.
3. **Retries:** DME solo se calcula si la multiplicidad de movimientos puede atribuirse sin ambigüedad; en caso contrario, `Coverage < 1`.
4. **Failed workflow:** no hay DME global; solo diagnóstico parcial etiquetado.
5. **Payload semantics:** DME mide bytes de payload científico lógico, no bytes físicos de red.
6. **Core independence:** patrón y placement son contexto/datos, no ramas especiales de cálculo.
7. **Unsupported policy:** `sharedfs`, bypass/plugins no soportados, clustered jobs y directorios sin manifiesto exacto fallan de forma explícita.
8. **Estados:** se distinguen `VALID`, `NOT_APPLICABLE`, `INCOMPLETE_EVIDENCE`, `UNSUPPORTED`, `INCONSISTENT`, `FAILED_WORKFLOW` y `ERROR`.
9. **Coverage:** `Coverage == 1` sigue siendo la condición de validez; `ByteCoverage` es solo diagnóstico.

Documento de decisión: `TESIS_GATE_R_CIERRE_20260930.md`.

---

# 20. Freeze de requisitos

Desde Gate R, una modificación que cambie la semántica de `RequiredMovement`, `DeclaredMovement`, `ObservedMovement`, `Coverage`, `DME`, el scope v1 o los criterios de validez requiere:

1. registrar el cambio como requisito;
2. analizar impacto en diseño, código, tests y resultados históricos;
3. actualizar la matriz de trazabilidad;
4. no reinterpretar silenciosamente resultados previos.

El siguiente artefacto normativo es `TESIS_DESIGN_SPEC_20260930.md`.

---

<!-- SYNC_20260930_I13_GATEI -->
## Checkpoint sincronizado — 2026-09-30 después de I13

Este bloque actualiza el **estado operativo** y no redefine requisitos, diseño ni fórmulas congeladas.

```text
Gate R — Requirements      CLOSED
Gate D — Design            CLOSED
I0–I13 — Implementation   CLOSED
Gate I — Implementation    ACTIVE: cierre documental/CLI pendiente
I14 — Experiment runner    BLOCKED hasta Gate I
Gate V — Validation        BLOCKED hasta Gate I
```

Evidencia verificada:

- `55712ed` — orquestación end-to-end Analyzer v1.
- `b5880d6` — regresiones auditadas I12.
- `77c6ff6` — integración I13 con runs preservados.
- suite con integración: **142/142 PASS**.
- runs reales preservados: process 50 MiB, pipeline 50 MiB BALANCED y pipeline 10 MiB SAME/BALANCED/CROSS.
- `schema_version = 1`.
- auditoría de hardcodes: no hay ramas de cálculo dependientes de SAME/BALANCED/CROSS ni de los cinco patrones en el núcleo v1.
- analyzer histórico `pegasus_movement/analyzer.py` preservado con SHA-256 `d3dda7a10e2fff5be0fee56655a9f42b67646edada53b4415db37207b264baf2`.

**Cadena correcta desde este punto:** sincronizar evidencia y documentación siguiendo el protocolo, terminar README/CLI de v1, ejecutar una única suite final de Gate I, cerrar Gate I formalmente y solo entonces activar I14.

