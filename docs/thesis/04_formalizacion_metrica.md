# Capítulo 4 — Formalización de la métrica

**Estado:** formulación congelada en Requirements/Design; este texto explica su semántica y límites, sin redefinirla. Magnitudes en bytes de payload científico.

## 4.1 Objetos y fuentes

| Símbolo | Nombre y definición | Fuente | Interpretación |
|---|---|---|---|
| `WF=(Tasks,Deps)` | DAG lógico de tareas y dependencias | Workflow Pegasus/DAX | Estructura causal; no incorpora ubicación por sí sola |
| `R` | Ejecución concreta con jobs, intentos y artefactos | Directorio Pegasus + history acotado | Unidad de análisis |
| `PL_R(t)` | Worker observado de tarea `t` | HTCondor history unido al submit | Fija la referencia; no es una política óptima |
| `EM_R` | Perfil efectivo de ejecución/transferencia | Submits, configuración y history | Determina el adapter admisible |
| `Trace_R` | Conjunto de registros y procedencia | Artefactos Pegasus/HTCondor | Evidencia disponible, posiblemente incompleta |
| `F_sci(R)` | Archivos científicos con identidad y tamaño inequívocos | Workflow, submits, `.meta`, cache metadata | Frontera de bytes del estudio; excluye auxiliares |
| `Origin(f,R)` | Ubicación inicial modelada de `f` | Rol, productor y ubicaciones | Punto desde el cual se evalúa necesidad lógica |
| `RequiredLocations(f,R)` | Ubicaciones distintas requeridas por consumers/destino final | Dataflow + `PL_R` | Deduplica consumidores colocalizados |
| `D_sci(R)` | Ocurrencias científicas declaradas por manifests efectivos | Adapter de `EM_R` | Contrato de movimiento; no prueba ejecución |
| `E(R)` | Evidencia de transferencia | History, stats y job state | Insumo de reconciliación |
| `C_sci(R)` | Subconjunto de `D_sci` confirmado por reconciliación | Manifest + `E(R)` | Numerador de cobertura y movimiento observado |

El adapter conserva job, dirección e intento cuando este puede separarse. Una estadística agregada no se fracciona artificialmente en observaciones por archivo. La condición de éxito y la compatibilidad con manifest, worker y protocolo forman parte de la confirmación.

## 4.2 Movimiento requerido y declarado

`Mreq(R) = Σ_{f∈F_sci(R)} Size(f) · |RequiredLocations(f,R) ∖ {Origin(f,R)}|`.

Es un **lower bound lógico file-centric condicionado al placement observado**, bajo reutilización local ideal. Un input externo cuenta al llegar a un worker distinto; productor y consumidor en el mismo worker aportan cero; un archivo usado por varios consumers del mismo worker cuenta una copia; workers distintos cuentan cada uno; un output final cuenta si su destino es una ubicación nueva. No se fuerza al master como tránsito de intermediarios.

`Mrec(R) = Σ_{m∈D_sci(R)} Size(File(m))`.

Esta suma representa ocurrencias científicas **declaradas** por el contrato de transferencia del execution model. Se la nombra también `DeclaredMovement`; no equivale a bytes confirmados. En los workloads históricos con I/O por job fijo, `Mrec` no cambió por cambiar únicamente el placement; no se generaliza fuera de `EM_HTC`.

## 4.3 Reconciliación, cobertura y observación

`Coverage(R) = |C_sci(R)| / |D_sci(R)|` cuando `D_sci` no es vacío; la convención implementada fija `Coverage=1` cuando no hay ocurrencias declaradas. `ByteCoverage` es diagnóstico, no reemplaza la condición de cobertura por ocurrencia.

Si `Coverage=1`, `Mobs(R) = Σ_{m∈C_sci(R)} Size(File(m))`. Si `Coverage<1`, `Mobs=N/A` y `DME=N/A`. La ausencia de evidencia no equivale a transferencia de cero bytes. `JOB_LEVEL_RECONCILED` certifica las ocurrencias mediante manifest exitoso y evidencia compatible a nivel job; no se presenta como contador físico de bytes de cada archivo.

## 4.4 DME, dominios y casos límite

Con cobertura completa, `Mobs>0` y coherencia `Mobs≥Mreq`, `DME(R)=Mreq(R)/Mobs(R)`. La razón responde a la pregunta de qué fracción del movimiento científico confirmado era necesaria para ese placement. Si `Mreq=0<Mobs`, DME es 0; si ambos son cero, es no aplicable; si `Mobs<Mreq`, el estado es `INCONSISTENT/INVALID`, no una eficiencia superior a uno. `Mobs−Mreq` se llama **movimiento adicional respecto al lower bound lógico**, sin implicar ahorro realizable.

Las condiciones de aplicabilidad incluyen identidad y tamaño autoritativos, placement de las tareas, execution model soportado, manifest científico completo, éxito del workflow cuando procede, trazabilidad de intentos y reconciliación. Configuración desconocida o contradictoria, retries no separables, evidencia incompleta y tamaños en conflicto producen diagnóstico y fallan cerrado. DME no mide tiempo, throughput, bandwidth, costo, optimalidad del scheduler ni tráfico de red a nivel de paquetes.

## 4.5 Oráculos y verificabilidad

Para cada caso controlado, el oráculo manual enumera archivos, tamaños, origen y conjunto de ubicaciones distintas; después enumera los contratos de entrada/salida científicos por job. Las igualdades esperadas de `Mreq` y `Mrec` se evalúan en bytes exactos. La evidencia observada se valora por niveles `FILE_LEVEL_CONFIRMED`, `JOB_LEVEL_RECONCILED` e `INSUFFICIENT`. El procedimiento independiente está en `validation/ORACLE_PROTOCOL.md`.
