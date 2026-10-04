# Capítulo 2 — Estado del arte y delimitación del aporte

**Estado:** borrador comparativo. Se cotejaron título y contribución de las fuentes primarias enlazadas; la bibliografía final y revisión sistemática permanecen pendientes. No se afirma prioridad universal.

## 2.1 Gestión de workflows y Pegasus

Deelman et al. describen Pegasus como WMS que transforma descripciones abstractas en planes ejecutables sobre infraestructura distribuida. Este antecedente justifica distinguir workflow lógico, ejecución concreta y artefactos de planificación. La tesis usa esa separación para reconstruir archivos, jobs y ubicaciones, sin atribuir a Pegasus una medición directa de DME. [Artículo de los autores, FGCS 2015](https://deelman.isi.edu/wordpress/wp-content/papercite-data/pdf/deelman-fgcs-2015.pdf).

## 2.2 Scheduling, placement y localidad

Pietri y Sakellariou proponen aumentar el peso de la comunicación al construir un schedule para acercar tareas que intercambian archivos y estudiar el intercambio con tiempo de ejecución. Esta línea optimiza una asignación. Aquí se mantiene fija la asignación **observada** y se mide una corrida post-mortem; DME no selecciona el scheduler. [Artículo de los autores, SSDBM 2018](https://www.cs.man.ac.uk/~rizos/papers/ssdbm2018.pdf).

## 2.3 Dataflow, I/O y trazas

DataLife enriquece el DAG de tareas con objetos y propiedades de datos, analiza ciclos de vida y razona sobre colocación y movimiento. Confirma la importancia de representar explícitamente productores, consumidores y reutilización. DaYu conecta semántica de dataflow con comportamiento de I/O para diagnosticar y orientar optimizaciones. DFTracer provee trazas de flujo de datos a varios niveles. Estas contribuciones motivan la integración de fuentes y provenance, pero no sustituyen una regla explícita que compare referencia lógica y movimiento confirmado de la **misma** ejecución. [DataLife, SC'23](https://cs.iit.edu/~scs/assets/files/lee2023data.pdf); [DaYu, CLUSTER 2024](https://cs.iit.edu/~scs/assets/files/tang2024dayu.pdf); [DFTracer, SC'24](https://akougkas.io/assets/pdf/dftracer.pdf).

## 2.4 Métricas a nivel workflow

Workflow Critical Path modela estados y mutaciones de datos para calcular un camino crítico a través de un workflow HPC. Do et al. definen una métrica de eficiencia de recursos para workflows *in situ* sobre un execution model explícito. Ambos demuestran que la utilidad de una métrica depende de su unidad, modelo y precondiciones; sus magnitudes y preguntas difieren del cociente de bytes científicos de esta tesis. [Nguyen y Karavanic, 2021](https://www.sciencedirect.com/science/article/pii/S2772485921000016); [Do et al., 2021](https://www.sciencedirect.com/science/article/pii/S1877750320305573).

## 2.5 Síntesis y gap acotado

| Línea | Aporte documentado | Diferencia con DME |
|---|---|---|
| WMS/Pegasus | Planificación y ejecución | La tesis integra evidencia para medir una corrida |
| Scheduling/localidad | Optimización de ubicación/comunicación | `Mreq` condiciona el placement observado; no lo optimiza |
| Dataflow/I/O/tracing | Representación y observación | DME exige referencia lógica, frontera científica y cobertura |
| Métricas workflow | Tiempo/camino crítico/recursos | DME expresa razón de payload científico en bytes |

En la literatura revisada **no se identificó, dentro del conjunto de fuentes analizado**, una métrica con la misma semántica operacional: límite lógico file-centric condicionado al placement observado frente a payload científico confirmado para esa ejecución, con `Coverage=1` como precondición del cociente. Esta es una conclusión de alcance documental, no la afirmación de que no existan trabajos relacionados ni una revisión sistemática exhaustiva. El registro comparativo histórico del handoff amplía la lista de referencias; cada cita que pase al manuscrito definitivo debe verificarse contra la fuente primaria.
