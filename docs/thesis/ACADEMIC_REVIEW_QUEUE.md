# Revisión académica — estado de los capítulos

**Corte:** 4 de octubre de 2026. `Sustentado` indica que el contenido técnico está redactado con evidencia identificada; `Edición final` indica que falta integrar, compilar o revisar el manuscrito completo, no que se deban inventar resultados. La propuesta oficial gobierna el alcance.

| Capítulo | Contenido disponible | Revisión concreta de cierre |
|---|---|---|
| 1 Introducción | Pregunta, objetivo, problema y contribuciones alineados con Analyzer v1 y Gate V | Ajustar al formato institucional e integrar al manuscrito maestro |
| 2 Estado del arte | Autores, hallazgos y utilidad explicados para Pegasus/workflows, scheduling, DataLife, DaYu, DFTracer, WCP, Do et al. y Vivas | Verificar bibliografía final contra fuentes primarias; conservar la delimitación de novedad como revisión acotada |
| 3 Sistema y execution model | Pool master + dos workers, Pegasus 5.1.2, HTCondor 25.12.2, `vanilla`, `condorio`; datos de entorno y límites | Integrar snapshot con procedencia y no confundir recursos ClassAd del slot con hardware físico |
| 4 Formalización | Semántica congelada de `Mreq`, `Mrec`, `Mobs`, `Coverage` y DME, con precondiciones | Revisar notación, consistencia de símbolos y paginación en el PDF maestro |
| 5 Arquitectura e implementación | Capítulo técnico 5.1–5.12 en `.tex`, trazable al código v1; resultados experimentales fuera del capítulo | Integrar sin duplicación y revisar compilación y figuras en el manuscrito completo |
| 6 Metodología | Matriz ejecutada de diez condiciones, 31 workflows, oráculos, réplicas y costos separados | Verificar que tablas y referencias del manuscrito reproduzcan el protocolo ejecutado |
| 7 Resultados | Tabla por condición, cálculo manual, sensibilidad, tiempos y recursos/almacenamiento | Contrastar cada cifra con los CSV/JSON fuente al integrar; conservar unidades y `n` |
| 8 Discusión | Interpretación, literatura, costo post-mortem y amenazas a la validez | Revisión de continuidad y citas en el PDF completo |
| 9 Conclusiones | Respuesta acotada a la pregunta, contribución, utilidad y líneas futuras | Revisión final de alcance y correspondencia con capítulos 7–8 |

## Límites de interpretación que deben conservarse

- La campaña Gate V validó 31 workflows en diez condiciones del pool de dos workers. Tres réplicas por condición permiten describir resultados y dispersión, no inferencia poblacional.
- Todas las ejecuciones Gate V tuvieron `Coverage=1`. Los escenarios de evidencia incompleta o contradictoria se ejercitaron en pruebas de software, no como condición empírica de la campaña.
- `Mreq` es una referencia lógica file-centric condicionada; `Mobs` se apoya en manifests e HTCondor history a nivel job. No son paquetes ni medición física de red.
- `T_gen` es duración observada que incluye cómputo científico y logs nativos, no overhead atribuible al Analyzer. Los costos post-mortem, recursos medidos y almacenamiento están desagregados en el capítulo 7.
- No se afirma efecto causal del logging basal. Analyzer no añade tracer, profiler ni logger dentro de los jobs.
- No generalizar a más nodos, otros execution models, `sharedfs`, otros schedulers ni sistemas físicos distintos.

## Cierre editorial

El contenido de los capítulos 1–9 está redactado como capítulos Markdown derivados, y el capítulo 5 existe además como `.tex` independiente. Falta el proyecto maestro de Overleaf: la cuenta conectada solo muestra la bienvenida y no presenta proyecto/editor. Con el proyecto correcto accesible, integrar los capítulos, compilar el PDF único y hacer revisión página por página de ecuaciones, tablas, referencias, diagramas, folios y cortes. No hace falta ejecutar más workflows para cerrar la redacción de los resultados ya obtenidos.
