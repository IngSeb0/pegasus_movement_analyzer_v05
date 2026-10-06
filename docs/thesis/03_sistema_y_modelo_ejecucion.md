# Capítulo 3 — Sistema y modelo de ejecución

Ver la captura vigente y su alcance por fuente en `environment/ENVIRONMENT_SNAPSHOT.md`.

## 3.1 Infraestructura

El testbed usa VMware, `pegasus-master` (`192.168.79.135`), `pegasus-worker1` (`192.168.79.137`) y `pegasus-worker2` (`192.168.79.139`) en la red observada `192.168.79.0/24`. En la consulta desde el master del 4/10/2026 a las 03:30:13 (UTC-05:00), HTCondor publicó un slot en cada worker. Los datos de recursos se reportan como atributos ClassAd por slot, no como inventario físico completo. La descripción del host Windows procede de la formulación oficial del proyecto.

## 3.2 Plataforma distribuida

Pegasus 5.1.2 gestiona la planificación/ejecución de workflows. HTCondor 25.12.2 ofrece en el master `Collector`, `Negotiator` y `Schedd`; el collector anuncia `startd` y slots de ambos workers. El estado se consulta desde el master mediante ClassAds, sin acceso SSH interactivo directo a cada worker. Las ClassAds anuncian plataforma `X86_64`/`Ubuntu26`, HTCondor 25.12.2 y un slot de 1 CPU/1410 MiB por worker; no exponen el inventario físico completo.

## 3.3 Modelo formal de la ejecución

El workflow es `WF=(Tasks,Deps)` con archivos científicos identificables, tamaño en bytes, productores y consumidores. Una ejecución `R` instancia tareas en jobs, intentos, ubicaciones y estados. `PL_R: Tasks→Workers` es el placement observado en history; SAME, BALANCED-LOCAL y CROSS son escenarios controlados, no algoritmos de scheduling. En v1, el execution model soportado es Pegasus `condorio` con jobs HTCondor `vanilla`, sandbox por job y transferencia administrada de entradas y salidas. Los contratos de archivo pertenecen al job, mientras el lower bound `Mreq` corresponde al dataflow y a las ubicaciones. Por ello el master no se impone como tránsito lógico de intermediarios en `Mreq`, aunque los manifests del modelo `condorio` reflejen staging por job.

## 3.4 Modelo de traza y Analyzer

La traza disponible combina `workflow.yml`, DAG, submits, `.meta`, metadatos Pegasus y un archivo history HTCondor acotado al run. Estas fuentes no tienen granularidad homogénea: un manifest declara archivos; las estadísticas de history pueden estar agregadas por job/dirección. Analyzer v1 opera offline, identifica archivos científicos, normaliza nombres/ubicaciones, construye movimientos y reconcilia evidencia. Si una identidad, tamaño, worker, intento o protocolo no puede sostenerse, emite diagnóstico y omite métricas dependientes. `Mobs` reconciliado a nivel job no equivale a tráfico de red ni a observación directa file-level.

## 3.5 Límites y supuestos

La frontera científica excluye ejecutables, logs y metadatos auxiliares. El tamaño debe provenir de fuente asociable sin ambigüedad a un archivo lógico. Se asume reutilización local ideal para el límite requerido, manteniendo placement. El adapter no extiende su interpretación a `sharedfs`, `bypass`, plugins o jobs agrupados. Los cinco runs históricos se emplean como evidencia de implementación; sus estados de ejecución no sustituyen una caracterización actual del pool.
