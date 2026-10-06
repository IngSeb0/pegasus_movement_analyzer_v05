# Matriz candidata de validación para Gate V

**Autoridad:** formulación oficial del proyecto. Esta es una alternativa operativa interna, no una cantidad fijada por la propuesta ni un protocolo aprobado. La matriz candidata contiene **13 condiciones patrón–placement × 3 tamaños × 3 repeticiones = 117 runs**. Un bloque candidato de sensibilidad estructural agrega **4 condiciones × 3 repeticiones = 12 runs**. **Total de esta alternativa: 129 workflows nuevos**, ninguno ejecutado. Los casos negativos se diseñan como análisis offline separados y no aumentan el conteo de workflows.

Las **129 filas explícitas** están en `experiment_cases_proposed.csv`. Todos sus `workflow_run_status` son `NOT_RUN` y los campos de rutas, snapshot de entorno y oráculo numérico están vacíos a propósito: deben llenarse con evidencia antes y después de cada ejecución, nunca por suposición. El CSV identifica cada caso de forma estable para el futuro runner I14.

| Patrón | Placements propuestos | Condiciones por tamaño | Parámetros que deben fijarse |
|---|---|---:|---|
| process | same-w1 | 1 | un job científico, input/output |
| pipeline | same-w1, balanced-local, cross | 3 | 3 etapas y dependencias |
| data aggregation | same-w1, balanced-local, cross | 3 | 4 ramas, fan-in |
| data distribution | same-w1, balanced-local, cross | 3 | 4 ramas, fan-out |
| data redistribution | same-w1, balanced-local, cross | 3 | 4 ramas y redistribución |

El CSV mantiene `aggregation`, `distribution` y `redistribution` como identificadores técnicos cortos del generador; corresponden, respectivamente, a los nombres completos oficiales anteriores.

Tamaños base: `1, 10, 50 MiB`; repeticiones: `1, 2, 3`. Una fila concreta de la matriz es la tupla `(pattern, placement, size_mib, replicate, workflow_parameters, analyzer_commit, Pegasus_version, HTCondor_version, environment_snapshot_id)`. El `run_id` se asigna al ejecutar, nunca se inventa. Los parámetros de generador y seeds deben persistirse en el manifest del runner I14. `same-w2` o `natural` pueden ser controles adicionales, pero **no** integran las 117 filas base sin una decisión documentada.

## Bloque candidato de sensibilidad estructural

| Patrón | Placement | Tamaño | Baseline comparado | Perturbación propuesta | Repeticiones | Runs nuevos |
|---|---|---:|---|---|---:|---:|
| pipeline | same-w1 | 10 MiB | 3 etapas de la matriz base | 4 etapas | 3 | 3 |
| data aggregation | same-w1 | 10 MiB | 4 ramas | 6 ramas (fan-in) | 3 | 3 |
| data distribution | same-w1 | 10 MiB | 4 ramas | 6 ramas (fan-out) | 3 | 3 |
| data redistribution | same-w1 | 10 MiB | 4 ramas | 6 ramas | 3 | 3 |

La elección de `same-w1` es operativa: el generador preservado `workflow_controlled.py` admite `--stages` y `--branches`, mientras que **rechaza** `balanced-local` con pipeline distinto de 3 etapas o con distribution/aggregation/redistribution distintos de 4 ramas. Se verificó leyendo el generador en la VM el 4/10; no se ejecutó. Cada perturbación compara con su baseline `same-w1,10 MiB` de la matriz de 117, manteniendo tamaño y placement. Los oráculos exactos para la estructura nueva se calcularán independientemente antes de cualquier run.

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

**Casos negativos:** al menos ocho entradas de análisis offline preservadas para tamaño ausente, tamaño conflictivo, productor ambiguo, placement ausente, job fallido, retry no separable, manifest incompleto y protocolo no soportado; cada una debe tener estado y razón esperados. No se los contará como workflows nuevos. **Overhead:** medir tiempo y memoria del análisis v1 sobre artefactos preservados; si se añade instrumentación al workflow, el número adicional de runs debe presupuestarse explícitamente.

**Coste de esta alternativa:** 129 workflows nuevos, más preparación y análisis offline. El tiempo y consumo de disco por caso no están medidos de modo comparable para esta matriz. El script histórico `run_controlled_case.sh` invoca Analyzer v0.5.1 y no es un runner válido para Gate V; cualquier método futuro deberá invocar la versión v1 acordada y preservar provenance. Esta matriz no autoriza la ejecución.

El piloto de presupuesto de tres filas concretas, sus medidas y reglas de recuperación están en `PILOT_BUDGET_PLAN.md`. Su ejecución requiere una decisión separada de la autorización de la campaña larga.
