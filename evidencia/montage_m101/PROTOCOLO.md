# Sensibilidad de DME en un mosaico completo de M101

Se usa la rama de mosaico sin ajuste de fondo del [tutorial oficial de Montage](https://irsa.ipac.caltech.edu/Montage/docs/m101tutorial.html). El flujo comienza con diez imágenes 2MASS J y la cabecera suministrada. Termina con el mosaico FITS y su mapa de cobertura. Hay diez reproyecciones `mProject`, una tabla de las imágenes reproyectadas `mImgtbl` y una coadición `mAdd`. El grafo y los parámetros científicos se conservan en las tres condiciones.

| Condición | Intervención | Predicción por archivo |
| --- | --- | --- |
| Base | Un job por tarea. | La tabla y la coadición reciben por separado las diez imágenes reproyectadas. Cada reproyección recibe la cabecera. |
| Agrupar reproyecciones | Las dos primeras reproyecciones, por orden del nombre de entrada, comparten un job. | El job recibe la cabecera una sola vez. Mantiene los cuatro productos de ambas reproyecciones. |
| Agrupar tabla y coadición | Las dos tareas finales comparten un job. | Las diez imágenes reproyectadas llegan una vez al job. La tabla se consume en el mismo sandbox. El contrato CondorIO generado por Pegasus determina si queda un retorno de la tabla. |

Las reproyecciones se fijan en W2. La tabla y la coadición se fijan en W1. La ubicación observada debe coincidir en las tres condiciones. Cada agrupación reúne dos tareas y deja once jobs científicos frente a doce de la base. Se mantienen la versión del programa, las entradas, la cabecera, los recursos por job y las reglas del planificador. Se comparan las listas de archivos de los planes antes del envío. Un preflight científico ejecuta el mismo programa localmente para obtener tamaños reales y cotejar la salida. Sus bytes no se toman como transferencias observadas.

Una ejecución por condición. Se preservan entradas y finales, planes, historial y eventos. Se cotejan el requerido y el observado con un auditor separado, por archivo y destino. Se verifica la equivalencia del mosaico y del mapa de cobertura en las tres condiciones. La variante con menor observado entre las elegibles es la mejor de las tres por volumen. Con requerido común, también tiene el mayor DME. El tiempo es descriptivo y los resultados corresponden al grafo, ubicación y política ensayados.
