# Plan integral de continuidad — actualizado al 4 de octubre de 2026

La autoridad académica es `Propuesta_oficial_Data_Movement_Assessment_2026.md`. Gate I permanece cerrado en el HEAD validado del Analyzer. Gate V cuenta con campaña de 31 workflows en diez condiciones, análisis por réplicas y costos desagregados. El trabajo de esta etapa es editorial y de defensa: no cambia código, no inicia I14, no ejecuta workflows adicionales y no hace merge a `main`.

## 1. Productos listos

| Producto | Estado verificado | Archivo/evidencia |
|---|---|---|
| Semántica y arquitectura Analyzer v1 | Congeladas para el execution model `condorio`/HTCondor vanilla; código validado en `3f44f30` | `entregables/CAPITULO_5_ANALYZER_V1.tex`; `vm_repo/docs/thesis/05_arquitectura_implementacion.md` |
| Método y resultados Gate V | 31 workflows válidos, diez condiciones, ≥3 réplicas métricas por condición; costos temporales completos n=3 por condición | `vm_repo/docs/thesis/06_metodologia_experimental.md`, `07_resultados_gate_v.md`; `entregables/INFORME_VALIDACION_CONTROLADA_ANALYZER_V1_20261004.md` |
| Interpretación científica | Discusión, límites y conclusiones redactados a partir de los resultados obtenidos | `vm_repo/docs/thesis/08_discusion_y_amenazas.md`, `09_conclusiones.md` |
| Literatura | Estado del arte actualizado: autor, hallazgo, utilidad y diferencia frente a Analyzer; incluye fuente primaria de la disertación de Aurelio Antonio Vivas Meza | `vm_repo/docs/thesis/02_estado_del_arte.md`; `C:/Users/Acer/AppData/Local/Temp/08_vivas_meza_2026_dissertation_data_movement.md` |
| Presentación | 27 diapositivas editables; render completo revisado; slide 8 aclara la contribución de Vivas y slide 11 usa estilo azul para la precondición `Coverage=1` | `entregables/PRESENTACION_TESIS_DATA_MOVEMENT_MASTERCLASS_FINAL_20261004_REV17.pptx`; SHA-256 `e8de01e406658518facb4e7a39436d9ff6ba2bd0595a2138dbf2e4dedfb3b447` |
| Guion oral | REV7 mantiene la explicación conceptual. Una revisión cuantitativa nueva quedó como borrador y no se entrega porque el renderer DOCX no encontró LibreOffice en este runtime Windows | `entregables/GUION_PRESENTACION_TESIS_ANALYZER_V1_20261004_REV7.docx` |

## 2. Secuencia de cierre

| Orden | Acción | Criterio de cierre | Dependencia real |
|---|---|---|---|
| 1 | Acceder al proyecto maestro correcto de Overleaf | Proyecto aparece con fuente principal y archivos de bibliografía/figuras | La cuenta conectada actualmente muestra bienvenida sin proyecto. Se necesita abrir el proyecto correcto o compartir su URL con acceso |
| 2 | Integrar capítulos 1–9 y el capítulo 5 técnico | Una sola estructura de tesis; capítulos y figuras ubicados según el índice institucional, sin duplicados | Proyecto maestro accesible |
| 3 | Compilar el manuscrito completo a PDF | Compilación limpia con ecuaciones, citas y referencias resueltas | Punto 2; compilador del proyecto funcional |
| 4 | Revisar el PDF completo, página por página | Sin fórmulas cortadas, tablas desplazadas, referencias sin resolver, diagramas ilegibles ni capítulos repetidos | PDF del punto 3 |
| 5 | Cotejar claims, tablas y citas con evidencia | Números de Gate V iguales a CSV/JSON; límites y costos preservados; fuente primaria identificada | PDF y evidencia local, ya disponibles |
| 6 | Congelar paquete de entrega de tesis y defensa | PDF final, PPTX REV17, guion revisado visualmente, fuentes editables y lista de hashes/versión | Puntos 4–5 y acceso a renderer DOCX |

## 3. Revisión científica obligatoria al integrar

- Usar `Mreq` como lower bound lógico condicionado al placement observado; no llamarlo óptimo global ni mínimo de bytes físicos.
- Reportar `Mobs` y DME solo bajo `Coverage=1` y precondiciones válidas. La campaña no contiene casos empíricos válidos con cobertura parcial.
- Mantener `T_gen`, `T_collect`, `T_analyzer`, recursos offline y almacenamiento en apartados separados. No atribuir a Analyzer un porcentaje causal de runtime.
- Interpretar evidencia HTCondor a nivel job, no como captura de tráfico de red.
- Presentar tres réplicas por condición como estadística descriptiva; no derivar significancia ni generalización poblacional.
- Explicar la diferencia de objetivo entre scheduling NUMA de Vivas Meza, trazas de DFTracer, ciclo de vida de DataLife/DaYu, camino crítico WCP y DME.

## 4. Criterio de parada y futuras ampliaciones

La redacción de resultados disponibles puede cerrarse sin otra campaña. Solo una pregunta de investigación ampliada justificaría más ejecuciones —por ejemplo, otro modelo de transferencia, más workers, una condición empírica de cobertura incompleta o un control causal de instrumentación— y requeriría antes comprobar su alineación con la propuesta oficial y definir el protocolo correspondiente. La campaña de 129 casos y cualquier matriz de arquitecturas anterior no son requisitos automáticos.

No hacer merge a `main`, no iniciar I14 ni modificar el Analyzer para resolver tareas editoriales. No reconstruir información ya presente en `CODEX_CONTEXT.md`, el informe Gate V o los capítulos. El proyecto maestro de Overleaf es necesario para compilar la tesis; un renderer DOCX funcional es necesario antes de sustituir el guion REV7 por su borrador cuantitativo.
