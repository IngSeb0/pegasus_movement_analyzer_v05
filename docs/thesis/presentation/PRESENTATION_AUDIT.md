# Auditoría de la presentación

**Entrega vigente:** `PRESENTACION_DATA_MOVEMENT_CLARA_20261005.pptx`  
**Diseño:** presentación nueva de 14 diapositivas; objetos de texto, flechas, diagramas y gráfico editables en PowerPoint.  
**Propósito:** explicar la pregunta, el problema, las definiciones, un ejemplo calculado y los resultados en lenguaje simple.

## Hilo narrativo

1. Portada con la pregunta exacta de investigación.
2. Problema de dependencia de archivos y posible cuello de botella en workflows intensivos en datos.
3. Autores y enfoques relacionados; explica que aportan evidencias distintas y no responde cada uno la misma pregunta.
4. Pregunta y contribución del estudio.
5. `M_req`, `M_rec`, `M_obs` y `Coverage`, distinguiendo evidencia.
6. Fórmulas explicadas en palabras sencillas, con definición de `C_sci` y `D_sci`.
7. Despliegue master/two workers y análisis post-mortem separado.
8. Cinco patrones de workflow con flechas de dependencia en sentido correcto.
9. Método, oráculos y réplicas de Gate V.
10. Cálculo manual de un pipeline para placement local y distribuido.
11. Gráfico editable de DME para cuatro patrones.
12. Costo de preparación, análisis offline y preservación; limita las afirmaciones de overhead.
13. Utilidad práctica y límites de lo medido.
14. Referencias consultadas.

## Revisión de calidad

- Se generaron PNG de las 14 diapositivas y se revisó visualmente el deck completo.
- Se corrigió la dirección de las flechas de los diagramas y se ordenó el despliegue en el pool.
- El ejemplo manual incluye `M_obs = 6 × 10 MiB = 60 MiB`, `M_req = 20/40 MiB` y `DME = 0.33/0.67` según placement.
- El texto diferencia dependencia lógica de ruta de red y evidencia HTCondor por job de captura física de bytes.
- El gráfico es un objeto nativo de PowerPoint; los diagramas usan formas y conectores editables.
- Integridad de paquete: 14 diapositivas, 1 gráfico nativo, 0 hallazgos.
- Geometría: tamaño 16:9, 0 hallazgos y 0 advertencias.
- La exportación oficial del finalizador tuvo una falla de permisos al lanzar Python desde Node. La presentación se exportó y se revisó con los dos validadores directos; las validaciones no simulan apertura en PowerPoint de escritorio.

Las presentaciones REV16/REV17 quedan como antecedentes archivados. La presentación nueva de 14 diapositivas es el archivo de trabajo para revisión con el usuario y sus profesores.
