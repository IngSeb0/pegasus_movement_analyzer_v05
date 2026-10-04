# Revisión académica pendiente — capítulos 1–6

**Corte:** 2026-10-04. `DONE` significa que el contenido técnico está sustentado y escrito en borrador; `PARTIAL` indica edición/integración necesaria; `BLOCKED` requiere datos nuevos o herramienta externa. Ningún capítulo contiene resultados finales Gate V.

| Capítulo | Estado | Base verificable | Revisión específica antes de congelar |
|---|---|---|---|
| 1 Introducción | PARTIAL | Objetivo oficial y pregunta del prompt/handoff, Requirements; alcance de Analyzer v1 | Integrar en estilo de la universidad y cotejar cita literal de la propuesta oficial en manuscrito maestro |
| 2 Estado del arte | PARTIAL | Artículos primarios de Deelman, Pietri/Sakellariou, DataLife, DaYu, DFTracer, WCP y Do et al. enlazados en el borrador | Completar ficha bibliográfica y citas en formato final; revisar alcance del gap sin afirmar primacía universal; verificar Tang et al. 2026 si se incorpora |
| 3 Sistema/ejecución | PARTIAL | Captura directa master y código del adapter; topología prevista de tres VMs | Capturar SO/hardware/versiones/configuración de worker1/2 cuando estén disponibles; separar la captura 3/10 de la futura línea base Gate V |
| 4 Métrica | DONE técnico, PARTIAL editorial | Requirements/Design congelados; `movement.py`, `metrics.py`, `reconciliation.py` | Revisar tipografía matemática y tabla de símbolos en el manuscrito; conservar los casos cero y `Coverage=1` sin reformular la métrica |
| 5 Arquitectura/implementación | DONE técnico, PARTIAL editorial | 13 dataclasses, módulos v1, pruebas y reporte Gate I; `CH5_TRACEABILITY_AUDIT.md` | Compilar el `.tex` abierto y revisar visualmente figuras/saltos; editor actual falla por plataforma; integrar al manuscrito sin duplicar capítulo |
| 6 Metodología | PARTIAL | Matriz de 129 workflows propuestos, generador leído en VM, oráculos, runbook | Medir presupuesto mediante piloto autorizado; fijar casos negativos y criterio de overhead; capturar pool completo; validar oráculos estructurales antes de ejecución |

## Afirmaciones que deben conservar su límite

- Los cinco runs preservados sustentan integración/regresión, no sensibilidad final ni repetibilidad de Gate V. Sus `Mobs` son reconciliados a nivel job bajo `SUCCESSFUL_MANIFEST`.
- El master tiene hechos de SO/CPU/RAM/versiones observados; los valores de workers permanecen desconocidos. No derivar propiedades de worker de `/etc/hosts`.
- Los PDF de figuras son heredados del handoff; la compilación actual del Capítulo 5 sigue sin verificarse.
- El generador histórico permite variar `--stages`/`--branches` con `same-w1`, pero restringe `balanced-local`; `run_controlled_case.sh` invoca Analyzer v0.5.1 y no debe servir como runner Gate V v1.
- No calcular DME para cobertura incompleta ni atribuirle tiempo, throughput, tráfico de red o ahorro realizable.

## Criterio para capítulos 7–9

Los capítulos de resultados, discusión y conclusiones empíricas permanecen `BLOCKED` hasta que Gate V genere runs nuevos auditables, oráculos independientes, fallos/negativos, sensibilidad y límites medidos. Se podrá preparar su estructura editorial, pero no escribir valores definitivos.
