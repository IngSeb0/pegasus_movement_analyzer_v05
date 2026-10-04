# Contexto autosuficiente — tesis y Analyzer v1

**Fecha de checkpoint:** 2026-10-03. **Proyecto:** Data Movement Assessment in Scientific Workflows. **Repositorio:** `IngSeb0/pegasus_movement_analyzer_v05`. **VM autoritativa:** `luis@192.168.79.135`, checkout `/home/luis/pegasus_movement_analyzer_v05`; runs originales en `/home/luis/pegasus-lab/pegasus_avance_semana_1_6/experiments`. Windows se usa para edición de tesis, presentación y handoff. Este archivo resume el estado actual; las fuentes primarias siguen siendo los artefactos citados.

## Git y gates

- `main`: `8269f0b222805efd3191a41f94d4ee0f6cf03856`, baseline v0.5.1. No hacer merge a `main` sin decisión posterior.
- `feat/analyzer-v1`: commit de cierre `3f44f30a9540861fbe1eb0e0a515a6f9d7d79e6`, publicado en GitHub el 4/10/2026; padre `5600ee17f5da7e48d46689cb8bf0b4e74cbfe158`. El cierre solo cambió README, CHANGELOG y TEST_REPORT. El checkout quedó limpio.
- `docs/thesis-v1`: rama de documentación creada desde `3f44f30`, con commit `79bd80cd5070fe2e8bff94a67635fe45601799ea` publicado en GitHub el 4/10/2026. Confirmar HEAD/estado antes de continuar; no usar la copia Windows del repo como verdad Git porque SCP altera bits ejecutables.
- Gate R, Gate D e I0–I13: cerrados según handoff. **Gate I: CLOSED en `3f44f30`**, con suite normal 142 correctas y 1 omitida, integración portable y con cinco runs originales, CLI smoke `VALID`, hashes de 179 archivos portables correctos. Logs finales: `/tmp/gate_i_final_*_3f44f30.log` en master. I14 aún no iniciado; Gate V pendiente.
- El remoto GitHub se actualizó desde Windows por HTTPS sin force push, usando un bundle Git creado en la VM. La VM no tiene autenticación GitHub funcional; `git fetch origin` por SSH falló por `Permission denied (publickey)`. Las ramas publicadas son `feat/analyzer-v1` y `docs/thesis-v1`. No se hizo merge. La integración GitHub disponible devolvió HTTP 403 al intentar crear un PR; queda pendiente abrirlo desde una sesión con permiso de PR.

## Topología y entorno

Testbed previsto de tres VMs VMware: `pegasus-master` `192.168.79.135`, `pegasus-worker1` `192.168.79.137`, `pegasus-worker2` `192.168.79.139`. En la captura 3/10, master responde SSH y HTCondor anuncia componentes centrales; ambos workers no respondieron ping/SSH y `condor_status -startd` no mostró slots. Se desconoce la causa y el hardware/software de workers. Master: Ubuntu 26.04 LTS, kernel 7.0.0-31, 1 vCPU, 1,671,811,072 B RAM, Pegasus 5.1.2, HTCondor 25.12.2, Python 3.14.4, Java 25.0.4.1. Ver `environment/ENVIRONMENT_SNAPSHOT.md` para fuente y comandos read-only.

## Semántica que no se debe cambiar

`Mreq=Σ_f Size(f)×|RequiredLocations(f,R)∖{Origin(f,R)}|`: límite lógico file-centric con placement **observado** y reutilización local ideal. `Mrec` suma ocurrencias científicas **declaradas** por el contrato del execution model. Manifest no es observación. `Coverage=|C_sci|/|D_sci|`, con convención 1 para denominador cero. `Mobs` solo existe con `Coverage=1` y suma tamaños de movimientos confirmados. `DME=Mreq/Mobs` si aplica; cero/cero es N/A, cero/positivo es 0, `Mobs<Mreq` es inconsistente. `Mobs−Mreq` se denomina movimiento adicional respecto al límite lógico; no se llama desperdicio. Analyzer v1 soporta Pegasus 5.x `condorio`, HTCondor vanilla y managed file transfer en su perfil verificado. Nunca describir v0.5 v35/v36 como implementación v1.

## Evidencia y artefactos

Los cinco runs originales preservados son process 50 MiB, pipeline 50 MiB balanced-local y pipeline 10 MiB same/balanced/cross. Analyzer `v1@3f44f30` los reportó `VALID`, `Coverage=1`, `SUCCESSFUL_MANIFEST`, `JOB_LEVEL_RECONCILED`; valores y rutas están en `validation/EXISTING_RUNS_IMPLEMENTATION_EVIDENCE.md` y TSV/JSON adjuntos. Son evidencia de integración, no campaña Gate V. La presentación Windows tiene 20 slides editables; el Capítulo 5 LaTeX tiene 5.1–5.12 y tres TikZ. La compilación integrada falló por entorno (`Unable to find standard directories for platform`), así que no existe PDF validado.

## Trabajo siguiente

1. Confirmar y recuperar disponibilidad de workers por el administrador/usuario; luego capturar hechos por worker y comprobar startd/slots, sin alterar red ni servicios desde este trabajo.
2. Revisar matriz de 117 casos y presupuesto con un piloto autorizado; decidir activación de I14 y campaña Gate V. I14 no se inicia automáticamente por haberse cerrado Gate I.
3. Abrir para revisión un PR de `feat/analyzer-v1` hacia `main` y otro de `docs/thesis-v1` hacia `feat/analyzer-v1` si procede, sin merge automático.
4. Integrar capítulos 1–6 al manuscrito, resolver compilador LaTeX del editor y completar capítulos 7–9 tras Gate V.

**Precedencia:** Requirements cerrados → Design Spec cerrado → decisiones posteriores explícitas → implementación real verificada → evidencia experimental → documentos académicos derivados → históricos. Si dos registros discrepan, localizar fecha y commit antes de adoptar uno.
