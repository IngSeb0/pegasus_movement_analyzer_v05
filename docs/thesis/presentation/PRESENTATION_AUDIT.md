# Auditoría de la presentación

**Presentación vigente:** `PRESENTACION_DATA_MOVEMENT_PROBLEMA_CLARO_20261005.pptx`

**Extensión:** 14 diapositivas.
**Pregunta:** dado un workflow y el worker donde corrió cada tarea, ¿cuánto movimiento exigen sus dependencias y cuánto payload científico declara y confirma la ejecución?

## Secuencia

1. Pregunta de investigación.
2. Problema de transferir archivos entre máquinas; ejemplo hipotético de 500 GB frente a 300 GB requeridos.
3. Qué miden los bytes, el ancho de banda y el tiempo; aportes de Bharathi, Deelman, Pietri y Sakellariou, Lee, Tang, Devarajan y Vivas Meza.
4. Definición sencilla: ubicación de una tarea es el worker donde se ejecutó.
5. `M_req`, `M_rec`, `M_obs` y `Coverage`, con sus límites de conteo.
6. Fórmulas de `M_req`, `Coverage`, `M_obs` y DME; definiciones de `D_sci` y `C_sci`.
7. Ejemplo calculado de pipeline: tareas en W1 frente a W1/W2.
8. Patrones process, pipeline, distribución, agregación y redistribución.
9. Despliegue Pegasus/HTCondor en master y dos workers; Analyzer post-mortem.
10. Validación con oráculos y réplicas independientes.
11. Gráfico editable de DME para cuatro patrones.
12. Recolección, análisis offline y almacenamiento de evidencia.
13. Utilidad potencial y límites de la métrica.
14. Conclusión práctica para el cliente.

## Límites de interpretación

- El contraste de 500 GB/300 GB es ilustrativo, no un resultado experimental.
- La ubicación de cada tarea significa el worker donde se ejecutó.
- `M_req` cuenta destinos lógicos; `M_obs` suma ocurrencias científicas declaradas en manifiestos y reconciliadas con evidencia HTCondor a nivel de job. Son reglas de conteo diferentes.
- `M_obs` no es una captura de paquetes, bytes totales de red ni prueba de bytes evitables.
- La DME compara volúmenes; no demuestra mejora de runtime, ancho de banda ni costo.
- El ejemplo manual muestra `M_req = 20/40 MiB`, `M_obs = 60 MiB`, `Coverage = 1` y DME de `0.33/0.67` para el patrón y las ubicaciones ensayadas.
- El análisis de costos separa preparación, Analyzer post-mortem y preservación. No atribuye porcentaje del runtime a Analyzer.
- Las fuentes y DOI completos están en las notas de presentador de las diapositivas 3 y 14.

## Revisión del archivo

- Integridad del paquete: 14 diapositivas, 1 gráfico nativo, 0 hallazgos.
- Geometría: 16:9, 0 hallazgos y 0 advertencias.
- Gráfico nativo: diapositiva 11, ocho valores numéricos editables; verificación de título sin hallazgos.
- Se renderizaron y revisaron visualmente las 14 diapositivas; el ejemplo central y el despliegue usan conectores editables.
- El finalizador integrado no pudo iniciar el validador Python desde Node en este entorno (`spawnSync ... EPERM`). Los mismos validadores empaquetados se ejecutaron directamente y pasaron. No se verificó apertura en PowerPoint de escritorio.

La presentación anterior `PRESENTACION_DATA_MOVEMENT_CLARA_20261005.pptx` queda como antecedente. La presentación indicada arriba es la vigente para revisión.
