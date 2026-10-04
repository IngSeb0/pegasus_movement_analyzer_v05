# I14 y Gate V — estado de preparación (2026-10-03)

**Dependencia de implementación:** Gate I se cerró en `3f44f30a9540861fbe1eeb0e0a515a6f9d7d79e6`: 142 pruebas de la suite normal correctas (una omitida), integración portable y sobre runs originales correcta, CLI smoke `VALID`, árbol limpio. Este cierre habilita *planificar* I14; I14 no está implementado ni ejecutado. El commit ya está publicado en `origin/feat/analyzer-v1`.

| Precondición | Estado | Evidencia o acción |
|---|---|---|
| Semántica R/D congelada | Satisfecha | Requirements/Design Spec; Mreq, Mrec, Coverage, Mobs y DME sin cambios |
| Analyzer v1 y CLI auditados | Satisfecha | HEAD `3f44f30`, TEST_REPORT, runs preservados |
| Preservación de fuentes y provenance | Satisfecha en 5 runs existentes | `EXISTING_RUNS_IMPLEMENTATION_EVIDENCE.md` |
| Matriz y oráculos manuales | Borrador para revisión | `EXPERIMENT_MATRIX.md`, `ORACLE_PROTOCOL.md` |
| Runner I14 idempotente, con manifest y reanudación | Pendiente | No iniciarlo como parte de esta captura |
| Master y dos workers anunciados | Bloqueado por disponibilidad | `condor_status -startd` sin anuncios; worker1/2 inaccesibles el 3/10 |
| Snapshot por host y versiones | Parcial | Master capturado; workers pendientes |
| Presupuesto de tiempo/disco | Pendiente | Medir con piloto autorizado; no extrapolar del tamaño de payload |
| Aprobación de campaña larga | Pendiente | Presentar matriz, costo y estado de pool antes de iniciar 129 workflows propuestos |

La ausencia de SSH directo a un worker no impide por sí sola la ejecución vía HTCondor. La condición decisiva es disponer de `startd`/slots válidos en el collector y comprobar el placement realmente observado. No se ejecutaron nuevos workflows ni se cambió la configuración del pool en esta fase.
