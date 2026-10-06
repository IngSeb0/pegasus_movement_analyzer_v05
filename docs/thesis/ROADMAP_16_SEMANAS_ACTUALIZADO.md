# Roadmap académico de 16 semanas — estado al 4 de octubre de 2026

Las semanas conservan las fases del plan académico aprobado, no representan fechas nuevas. La propuesta oficial mantiene autoridad sobre alcance y criterios. Gate V ya cuenta con una campaña independiente ejecutada; la actividad actual es cerrar consistencia editorial e integrar el manuscrito.

| Tramo | Actividad académica | Estado técnico y evidencia | Estado de documentos | Próximo paso de cierre |
|---|---|---|---|---|
| 1–4 · P1 | Fuentes, problema, variables, patrones y requisitos | Cinco patrones Pegasus/HTCondor definidos y evidencia de ejecución preservada | Capítulos 1–2; el capítulo 2 explica autores, hallazgos y utilidad | Verificar bibliografía final y mantener acotado el gap de literatura |
| 5–7 · P2 | Modelo de datos, semántica, métrica y oráculos | `Mreq`, `Mrec`, `Mobs`, Coverage y DME congelados; casos límite probados | Capítulo 4 redactado; fórmulas y figuras en revisión para el PDF maestro | Verificar tipografía matemática y símbolos en el PDF integrado |
| 8 · A7 | Arquitectura y modelo de datos | Analyzer v1 con 13 entidades normalizadas, trazable al código validado | Capítulo 5.1–5.12 en `.tex` independiente | Integrarlo sin duplicar y verificar figuras/paginación |
| 9–10 · P3 | Adquisición, normalización, análisis y pruebas | Gate I cerrado en HEAD `3f44f30`; suite 142 PASS/1 omitida, integración y CLI verificadas | Documentación de implementación en revisión editorial | Mantener PR/merge como decisión separada; no hacer merge en esta fase |
| 11–12 · A10–A11 | Patrones, placement, protocolo y oráculos | Cinco patrones, condiciones `same-w1`/`cross`, dos tamaños `process`; matriz ejecutada justificada | Capítulo 6 registra los diez tratamientos y el método realmente usado | Mantener el reporte ligado a cada run, sin extender la matriz automáticamente |
| 13–14 · A12–A13 | Validación, sensibilidad, consistencia y costos | Campaña de 31 workflows en diez condiciones; ≥3 por condición; costos temporales completos n=3 por condición | Capítulo 7 con resultados, ejemplo manual, sensibilidad, tiempos y recursos; informe/bundle preservados | Contrastar cifras finales al integrar el manuscrito; ninguna nueva campaña necesaria para describir estos datos |
| 15–16 · P4 | Discusión, conclusiones, defensa y depósito | Evidencia Gate V acotada al pool documentado; Analyzer offline sin instrumentación runtime adicional | Capítulos 8–9 redactados; presentación editable REV17 de 27 slides renderizada y revisada; guion REV7 disponible | Acceder al proyecto correcto de Overleaf, integrar, compilar PDF único y revisar página por página; actualizar visualmente el guion cuando haya un renderer Word disponible |

Los resultados no se extrapolan fuera del pool virtualizado de dos workers, Pegasus 5.1.2, HTCondor 25.12.2, jobs `vanilla` y `condorio`. La cobertura fue completa en los runs de Gate V; evidencia parcial se ejercitó en pruebas de software. No se formula causalidad sobre los logs nativos ni se atribuye a Analyzer un cambio en runtime.

## Restricciones de ejecución y publicación

- No se inicia I14 ni se ejecutan workflows adicionales como parte del cierre documental actual.
- No se hace merge a `main`; la revisión de PRs y cualquier integración quedan como decisión posterior.
- Las líneas futuras de validez externa o control causal son propuestas de investigación, no tareas ya autorizadas ni resultados de esta tesis.
