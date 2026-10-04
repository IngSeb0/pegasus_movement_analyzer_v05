# Matriz propuesta para Gate V

**Unidad experimental:** una ejecución nueva de un workflow controlado, con directorio Pegasus y history preservados, analizada con un commit fijo de Analyzer v1. La matriz principal propuesta contiene **13 condiciones patrón–placement × 3 tamaños × 3 repeticiones = 117 runs**. La cifra es una propuesta de diseño, no una campaña ejecutada. Casos negativos y variaciones estructurales se presupuestarán aparte tras el piloto.

| Patrón | Placements propuestos | Condiciones por tamaño | Parámetros que deben fijarse |
|---|---|---:|---|
| process | same-w1 | 1 | un job científico, input/output |
| pipeline | same-w1, balanced-local, cross | 3 | 3 etapas y dependencias |
| distribution | same-w1, balanced-local, cross | 3 | 4 ramas, fan-out |
| aggregation | same-w1, balanced-local, cross | 3 | 4 ramas, fan-in |
| redistribution | same-w1, balanced-local, cross | 3 | 4 ramas y redistribución |

Tamaños base: `1, 10, 50 MiB`; repeticiones: `1, 2, 3`. Una fila concreta de la matriz es la tupla `(pattern, placement, size_mib, replicate, workflow_parameters, analyzer_commit, Pegasus_version, HTCondor_version, environment_snapshot_id)`. El `run_id` se asigna al ejecutar, nunca se inventa. Los parámetros de generador y seeds deben persistirse en el manifest del runner I14. `same-w2` o `natural` pueden ser controles adicionales, pero **no** integran las 117 filas base sin una decisión documentada.

| Campo de resultado requerido por fila | Regla |
|---|---|
| `run_path`, `history_path`, `output_path` | Rutas absolutas preservadas y verificadas |
| `expected_RequiredMovement_B` | Oráculo independiente calculado antes del run, según DAG, tamaños y placement diseñado; repetir con placement observado |
| `expected_qualitative_behavior` | Mreq cambia con destinos; Mrec puede ser invariante al placement si I/O por job fijo; Mobs solo con evidencia |
| `observed_placement` | Derivado de history, comparado con placement diseñado |
| `Coverage` | Cobertura por ocurrencia; `1` para habilitar Mobs y DME |
| `DME_validity` | Aplicar precondiciones y casos cero de Design Spec |
| `PASS/FAIL` | Igualdad exacta en bytes para oráculos deterministas y placement; estado e invariantes de evidencia |
| `diagnostics`, `exit_code`, `source_hashes` | Guardar íntegros; fallos no se recodifican como cero |

**Coste:** 117 procesos de workflow, más preparación y análisis. El tiempo y consumo de disco por caso no están medidos de modo comparable para esta matriz; permanecerán `PENDING_ESTIMATE` hasta un piloto corto autorizado con workers disponibles. No se ejecutará la campaña larga desde este plan.
