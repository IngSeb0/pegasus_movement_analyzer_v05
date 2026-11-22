## Corrección vigente de signos — 8 de noviembre de 2026

Los signos de apertura se escriben con `\textquestiondown{}` y `\textexclamdown{}` al compilar con Tectonic y fuentes T1. La prueba visual confirmó que el carácter literal de interrogación se dibujaba como libra; modificar solo ToUnicode corregía la extracción, no ese dibujo. La versión vigente compila con los signos correctos sin posprocesar el PDF. Las instrucciones siguientes sobre el corrector corresponden a versiones anteriores.

# Procedencia y adaptación de la plantilla

La portada y el estilo de capítulos se basan en TiCSw/Uniandes-thesis-template-es.latex, revisión 9a7f35147ac9866e4b57f01aae81058108522b6c. Esta revisión conserva clase report de 11 puntos, papel A4, márgenes, estilo de capítulos y logotipo. La maquetación a una cara reduce las páginas en blanco. El formato de referencias usa autor y año.

El archivo uniandestitlepage.sty conserva su autoría y aviso GPL versión 2 o posterior. La licencia se incluye en COPYING. La procedencia del estilo no atribuye al repositorio la autoría del contenido científico.

Los objetivos provienen literalmente de la entrega Uniandes del 3 de noviembre de 2026. La versión del 6 de noviembre reorganiza y abrevia la tesis. Los resultados incluidos se toman de la selección documentada del bloque A. Las cifras de la campaña se conservan en las fuentes históricas.

Para compilar desde esta carpeta, use `tectonic -X compile main.tex`. Se incluyen los archivos requeridos por el documento. La primera compilación fuera de esta estación puede necesitar el paquete de recursos de Tectonic.

## Extracción de texto del PDF con Tectonic

En la versión de Tectonic usada en esta revisión, los signos de interrogación de apertura se dibujan correctamente y pueden copiarse como «£». Para conservar la extracción de texto de la entrega, después de compilar instala pypdf 6.10.0 y ejecuta:

    python corregir_texto_pdf.py main.pdf tesis.pdf

El paso ajusta únicamente el mapa de texto de las fuentes Latin Modern afectadas. El diseño, los glifos visibles y la paginación se conservan.
