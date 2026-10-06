# Capítulo 1 — Introducción y formulación del problema

**Estado:** borrador académico sustentado en la propuesta y las especificaciones congeladas; falta integración editorial al manuscrito final.

## 1.1 Contexto y motivación

Un workflow científico coordina tareas con dependencias y archivos de datos. En una plataforma distribuida, la ubicación de cada tarea y las reglas de transferencia determinan dónde deben materializarse esos archivos. Pegasus planifica y ejecuta workflows sobre infraestructuras como HTCondor; sus artefactos describen workflow, submits, jobs y parte de las transferencias. Sin embargo, la pregunta de cuántos bytes científicos fueron necesarios para satisfacer un dataflow concreto no se responde leyendo aisladamente un log de ejecución o un manifiesto.

## 1.2 Problema y pregunta de investigación

El problema de esta tesis es **definir y calcular una medida trazable** que relacione el movimiento científico indispensable para un workflow y placement observados con el movimiento científico confirmado durante esa ejecución. Las fuentes están distribuidas entre representación del workflow, archivos Pegasus, contratos de sandbox e historial HTCondor; sus niveles de granularidad difieren. La ausencia de evidencia de transferencia no autoriza a registrar cero bytes.

**Pregunta:** para una ejecución concreta de un workflow científico, ¿qué fracción del movimiento científico confirmado era necesaria para satisfacer el dataflow manteniendo el placement observado?

## 1.3 Objetivos

**Objetivo general oficial:** diseñar, implementar y validar una herramienta que permita calcular una métrica para evaluar la eficiencia del movimiento de datos durante la ejecución de flujos de trabajo gestionados por Pegasus, utilizando los patrones process, pipeline, data aggregation, data distribution y data redistribution para evaluar la sensibilidad de la métrica bajo condiciones controladas de ejecución.

Objetivos específicos operacionalizados:

1. Caracterizar fuentes, archivos científicos, ubicaciones, placement y modelo de transferencia.
2. Formalizar `RequiredMovement`, `DeclaredMovement`, `Coverage`, `ObservedMovement` y `DME`, incluyendo casos límite y política de evidencia.
3. Construir Analyzer v1 con extracción, normalización, reconciliación y procedencia auditables.
4. Diseñar y ejecutar una validación controlada con oráculos independientes, patrones, placements, tamaños y repeticiones; la campaña de Gate V cubrió diez condiciones en el pool disponible.

## 1.4 Alcance, exclusiones y contribución

La unidad de análisis es una ejecución preservada de Pegasus con jobs `condorio`/HTCondor vanilla y transferencia administrada. La referencia `Mreq` conserva el placement observado y supone reutilización local ideal. `Mobs` exige reconciliación completa de ocurrencias científicas declaradas. La contribución comprende la semántica formal, Analyzer v1 —que integra fuentes dispersas, discrimina evidencia y falla cerrado— y la validación controlada de cinco patrones en diez condiciones con 31 workflows independientes. La evidencia empírica queda limitada a las configuraciones y al pool medidos.

La tesis no diseña un scheduler, no busca placement global óptimo y no mide tráfico de paquetes, latencia, makespan, ancho de banda ni ahorro realizable. `Mobs−Mreq` es movimiento adicional frente al límite lógico condicionado, no una estimación automática de desperdicio o bytes evitables. Otros modelos de ejecución requieren adapters y validación propios.

## 1.5 Organización

El capítulo 2 contrasta trabajos relacionados; el 3 fija el sistema y el execution model; el 4 formaliza la métrica; el 5 describe Analyzer v1; el 6 documenta el método ejecutado; el 7 presenta los resultados; el 8 los discute frente a la literatura y sus límites; y el 9 resume conclusiones y trabajo futuro.
