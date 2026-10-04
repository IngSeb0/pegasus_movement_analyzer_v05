# Capítulo 3 — Sistema y modelo de ejecución

**Estado:** modelo redactado; el inventario directo de workers permanece pendiente. Ver `environment/ENVIRONMENT_SNAPSHOT.md`.

## 3.1 Infraestructura

El testbed previsto usa VMware, `pegasus-master` (`192.168.79.135`), `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) en la red observada `192.168.79.0/24`. Es una topología **prevista** y confirmada por el usuario, no una inferencia de disponibilidad. En la captura del 3/10 el master respondió, los workers no respondieron a ping/SSH y no aparecieron slots `startd`. Por ello se documentan por separado la estructura del testbed y el estado de una captura.

## 3.2 Plataforma distribuida

Pegasus 5.1.2 gestiona la planificación/ejecución de workflows. HTCondor 25.12.2 ofrece en el master `Collector`, `Negotiator` y `Schedd`; los workers previstos deben publicar `startd` para ejecutar jobs científicos. Una sesión SSH desde Windows al master no constituye una sesión SSH a los workers. La ejecución distribuida a través de HTCondor puede funcionar sin SSH interactivo a cada worker siempre que sus slots estén anunciados y sean compatibles. Las versiones aquí citadas son las capturadas en master; las de workers se desconocen.

## 3.3 Modelo formal de la ejecución

El workflow es `WF=(Tasks,Deps)` con archivos científicos identificables, tamaño en bytes, productores y consumidores. Una ejecución `R` instancia tareas en jobs, intentos, ubicaciones y estados. `PL_R: Tasks→Workers` es el placement observado en history; SAME, BALANCED-LOCAL y CROSS son escenarios controlados, no algoritmos de scheduling. En v1, el execution model soportado es Pegasus `condorio` con jobs HTCondor `vanilla`, sandbox por job y transferencia administrada de entradas y salidas. Los contratos de archivo pertenecen al job, mientras el lower bound `Mreq` corresponde al dataflow y a las ubicaciones. Por ello el master no se impone como tránsito lógico de intermediarios en `Mreq`, aunque los manifests del modelo `condorio` reflejen staging por job.

## 3.4 Modelo de traza y Analyzer

La traza disponible combina `workflow.yml`, DAG, submits, `.meta`, metadatos Pegasus y un archivo history HTCondor acotado al run. Estas fuentes no tienen granularidad homogénea: un manifest declara archivos; las estadísticas de history pueden estar agregadas por job/dirección. Analyzer v1 opera offline, identifica archivos científicos, normaliza nombres/ubicaciones, construye movimientos y reconcilia evidencia. Si una identidad, tamaño, worker, intento o protocolo no puede sostenerse, emite diagnóstico y omite métricas dependientes. `Mobs` reconciliado a nivel job no equivale a tráfico de red ni a observación directa file-level.

## 3.5 Límites y supuestos

La frontera científica excluye ejecutables, logs y metadatos auxiliares. El tamaño debe provenir de fuente asociable sin ambigüedad a un archivo lógico. Se asume reutilización local ideal para el límite requerido, manteniendo placement. El adapter no extiende su interpretación a `sharedfs`, `bypass`, plugins o jobs agrupados. Los cinco runs históricos se emplean como evidencia de implementación; sus estados de ejecución no sustituyen una caracterización actual del pool.
