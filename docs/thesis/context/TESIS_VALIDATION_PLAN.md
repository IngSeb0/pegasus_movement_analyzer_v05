# TESIS — Plan de validación manual y controlada

**Versión:** 2026-09-25  
**Propósito:** documentar el oráculo manual, las fórmulas vigentes, los placements controlados y las campañas cerradas.

---

## 1. Orden de una prueba

1. fijar el workflow `WF=(Tasks,Deps)`;
2. fijar `SizeOf` para todos los datos científicos;
3. fijar el placement `PL` del caso controlado;
4. calcular `M_req` manualmente;
5. calcular `M_rec` manualmente a partir de las entradas/salidas científicas por job bajo `EM_HTC`;
6. ejecutar Pegasus/HTCondor con el placement forzado;
7. reconstruir el placement observado desde HTCondor;
8. ejecutar Analyzer v0.5.1;
9. comparar manual vs script en bytes y verificar el placement.

Criterio PASS:

```text
Delta_req = M_req_script - M_req_manual = 0
Delta_rec = M_rec_script - M_rec_manual = 0
placement_observado = placement_disenado
valid = True
```

No se usa tolerancia porcentual para esta validación determinista.

---

## 2. Fórmulas vigentes

Workflow:

```math
WF=(Tasks,Deps)
```

Dato interno y tamaño:

```math
Data_ij = dato producido por Ti y consumido por Tj
SizeOf(Data_ij) = tamaño en bytes
```

Placement:

```math
PL: Tasks -> Workers
PL(Ti)=Wk
```

Indicador de cambio de worker:

```math
ChangesWorker_ij(PL)=0 si PL(Ti)=PL(Tj)
ChangesWorker_ij(PL)=1 si PL(Ti)!=PL(Tj)
```

Referencia propuesta con placement fijo y reutilización local ideal en los workloads controlados (no equivale a lo factible dentro de `condorio`):

```math
M_req =
    sum ExternalInputs
  + sum_{(Ti,Tj) in Deps} SizeOf(Data_ij)*ChangesWorker_ij(PL)
  + sum FinalOutputs
```

Execution model estudiado:

```text
EM_HTC = condorio + HTCondor file transfer + sandbox aislado por job
```

Movimiento reconstruido bajo ese modelo:

```math
M_rec^HTC = sum por tarea de SizeOf(inputs cientificos) + SizeOf(outputs cientificos)
```

En los escenarios controlados, cambiar solamente `PL` no cambió `M_rec`, porque no cambió el contrato de I/O por job. Esta propiedad está limitada a `EM_HTC` y a lo que reconstruye el analizador. `M_obs` exige registros completos de transferencias realmente realizadas; las pruebas históricas no lo establecieron.

---

## 3. Oráculos manuales BALANCED-LOCAL para S=10 MiB

| Patrón | M_req manual | M_rec manual | Fórmula histórica |
|---|---:|---:|---|
| Process | 20 | 20 | `2S / 2S` |
| Pipeline | 30 | 60 | `3S / 6S` |
| Distribution | 25 | 40 | `2.5S / 4S` |
| Aggregation | 100 | 160 | `10S / 16S` |
| Redistribution | 120 | 320 | `12S / 32S` |

---

## 4. Matriz controlada vigente S=10 MiB

Formato: `M_req / M_rec` MiB. El antiguo rótulo `M_obs` corresponde a `M_rec` en esta tabla.

| Patrón | SAME | BALANCED-LOCAL | CROSS |
|---|---:|---:|---:|
| Process | 20 / 20 | 20 / 20 | — |
| Pipeline | 20 / 60 | 30 / 60 | 40 / 60 |
| Distribution | 20 / 40 | 25 / 40 | 30 / 40 |
| Aggregation | 80 / 160 | 100 / 160 | 120 / 160 |
| Redistribution | 80 / 320 | 120 / 320 | 200 / 320 |

---

## 5. Campañas cerradas

- `repro --reps 3`: 13 condiciones x 3 repeticiones = 39/39 PASS.
- `size-smoke`: 10/10 PASS; prueba preliminar, posteriormente supersedida por `size-full`.
- `size-full --reps 3`: 5 patrones x 3 tamaños x 3 repeticiones = 45/45 PASS.

---

## 6. Factores y niveles

| Factor | Niveles / valor |
|---|---|
| Patrón | process, pipeline, distribution, aggregation, redistribution |
| Placement | SAME, BALANCED-LOCAL, CROSS; process usa baseline same-w1 |
| Tamaño base S | 1, 10, 50 MiB |
| Branches | 4 cuando aplica |
| Stages pipeline | 3 |
| Repeticiones | 3 en campañas cerradas |
| Execution model | fijo: `EM_HTC` |

---

## 7. Regla de interpretación

- SAME, BALANCED-LOCAL y CROSS son placements controlados, no schedulers.
- `M_req` sí es sensible a `PL`.
- `M_rec` no fue sensible a `PL` en `EM_HTC` porque las entradas y salidas declaradas por job permanecieron fijas.
- La invariancia de `M_rec` no se presenta como propiedad universal de Pegasus/HTCondor ni de otros modelos de ejecución.
- `M_rec` es payload científico **reconstruido** de staging, no tráfico de red a nivel de paquetes ni `M_obs` confirmado.

## 8. Validaciones aún necesarias

La interpretación de `M_req` queda fijada como **lower bound lógico condicionado al placement**, bajo reutilización local y comunicación directa entre ubicaciones. Las validaciones pendientes son ahora:

1. **Observabilidad:** identificar evidencia por archivo, tramo, intento y corrida que permita confirmar `M_obs`; tratar cobertura incompleta como indeterminada.
2. **Equivalencia de frontera:** comprobar que `M_req` y `M_obs` usan los mismos archivos científicos, ubicaciones, tamaños y destinos antes de calcular `eta_move=M_req/M_obs`.
3. **Contraste reconstruido/observado:** comparar `M_rec` y `M_obs` cuando sea posible, incluyendo reintentos, duplicados y tamaños parciales.
4. **Sensibilidad estructural:** variar etapas de pipeline, fan-out, fan-in, redistribución y archivos compartidos, además del tamaño.
5. **No confusión con placement:** verificar que los reportes separen `M_req` como demanda de comunicación del placement de `eta_move` como eficiencia de materialización condicionada a ese placement.
6. **Aplicabilidad y overhead:** documentar cobertura, condiciones de aplicación, trazabilidad, costo de instrumentación y casos en los que la métrica debe reportarse como indeterminada.

Los PASS existentes verifican únicamente los oráculos de `M_req` y `M_rec` bajo las condiciones registradas. No validan `M_obs` ni `eta_move` observada.


---

## 9. Evidencia nueva de observabilidad — 26-09-2026

Dos pilotos a 50 MiB permiten elevar la validación desde reconstrucción pura a observación condicionada a nivel job.

| Caso | Placement observado | Intentos | `M_req` | payload científico observado reconciliado | Coverage |
| --- | --- | ---: | ---: | ---: | --- |
| Process same-w1 | W1 | 1 | 100 MiB | 100 MiB | `JOB_LEVEL_EXACT_RECONCILIATION` |
| Pipeline balanced-local | W1,W1,W2 | 1 por job | 150 MiB | 300 MiB | `JOB_LEVEL_EXACT_RECONCILIATION` |

Criterios mínimos para aceptar esta cobertura:

1. `TransferInputStats`/`TransferOutputStats` pertenecen al job científico correcto;
2. el placement real y el número de intentos están confirmados;
3. el `.sub` permite reconstruir el file-set del sandbox;
4. metadata o archivos preservados dan los tamaños científicos;
5. el total HTCondor se reconcilia con el conjunto transferido y los auxiliares quedan separados;
6. no queda residuo de bytes sin explicación relevante para la frontera científica.

Próxima validación: convertir estos criterios en una regla automática, probar un caso SAME y un caso CROSS adicionales, y después introducir un escenario con retry o evidencia incompleta para comprobar que la herramienta degrada coverage en vez de inventar `M_obs`.

## 9. Validación de placement con evidencia observada/reconciliada

Se fija un experimento controlado con pipeline de tres tareas y `S=10 MiB`: SAME (`W1,W1,W1`), BALANCED-LOCAL (`W1,W1,W2`) y CROSS (`W1,W2,W1`). Workflow, tamaño y execution model permanecen fijos. HTCondor confirma el placement observado y un único intento por job. La cobertura se clasifica `JOB_LEVEL_RECONCILED`.

Oráculo previo:

| Placement | M_req | M_obs científico esperado/confirmado | eta_move |
|---|---:|---:|---:|
| SAME | 20 MiB | 60 MiB | 0.3333 |
| BALANCED-LOCAL | 30 MiB | 60 MiB | 0.5000 |
| CROSS | 40 MiB | 60 MiB | 0.6667 |

Esta prueba valida sensibilidad al placement bajo el execution model estudiado y la política de observación reconciliada. No valida calidad de placement ni causalidad sobre makespan.


## 10. P2 congelado — validación obligatoria del Analyzer

La nomenclatura principal de validación desde el 26-09-2026 es `RequiredMovement`, `DeclaredMovement`, `ObservedMovement`, `Coverage` y `DME`.

### Oráculo piloto

| Placement | RequiredMovement | DeclaredMovement | ObservedMovement | Coverage | DME |
| --- | ---: | ---: | ---: | ---: | ---: |
| SAME | 20 MiB | 60 MiB | 60 MiB | 1 | 0.3333 |
| BALANCED-LOCAL | 30 MiB | 60 MiB | 60 MiB | 1 | 0.5000 |
| CROSS | 40 MiB | 60 MiB | 60 MiB | 1 | 0.6667 |

### Pruebas mínimas de P2

1. archivos auxiliares nunca suman al movimiento científico;
2. same-worker intermediate aporta 0 a RequiredMovement;
3. cross-worker intermediate aporta el tamaño del archivo;
4. fan-out se cuenta una vez por worker destino en RequiredMovement;
5. materializaciones repetidas sí pueden repetirse en ObservedMovement;
6. Coverage debe ser 1 para calcular DME;
7. evidencia incompleta produce ObservedMovement indeterminado y DME=N/A;
8. retry no reconciliable degrada Coverage;
9. `ObservedMovement < RequiredMovement` invalida el resultado;
10. `Required=Observed=0` produce DME=N/A; `Required=0, Observed>0` produce DME=0.

La validación histórica de `M_rec` se conserva como regresión, pero no reemplaza estas pruebas de observabilidad.

---

# Actualización 2026-09-30 — validación bloqueada por Gate I

La matriz experimental definitiva no se ejecutará hasta que el Analyzer nuevo cierre Gate I.

Antes de nuevas campañas deben existir:

- unit tests de modelo, RequiredMovement, manifests, reconciliación y DME;
- regression fixtures positivos y negativos;
- integración sobre runs históricos preservados;
- evidence mode explícito (`EXACT_BYTES` o `SUCCESSFUL_MANIFEST`) por fixture positivo;
- estados negativos `INCOMPLETE_EVIDENCE`, `UNSUPPORTED`, `INCONSISTENT` verificados.

Después de Gate I se ejecutarán los cinco patrones oficiales, repeticiones y sensibilidad estructural variando una condición primaria a la vez. La infraestructura oficial sigue siendo el testbed VMware definido en la propuesta.

---

<!-- SYNC_20260930_I13_GATEI -->
## Checkpoint previo a validación — 2026-09-30

La validación experimental nueva sigue **bloqueada**. Lo cerrado hasta ahora es verificación de implementación:

- I12 regression suite: CLOSED (`b5880d6`).
- I13 integration suite sobre runs reales preservados: CLOSED (`77c6ff6`).
- suite completa con integración: **142/142 PASS**.

Esto **no equivale a Gate V** ni autoriza campañas nuevas. El orden correcto es:

```text
Gate I closeout documental/CLI
→ suite final Gate I
→ Gate I CLOSED
→ I14 experiment runner
→ campañas de validación
→ Gate V
```

