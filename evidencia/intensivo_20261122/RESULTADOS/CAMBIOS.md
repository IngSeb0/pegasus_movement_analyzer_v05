# Cambios de la campaña

Los trece grafos reutilizan la especificación FMA. Todos los archivos científicos pasan de 10 a 200 MiB, exactamente 209 715 200 B por archivo. Todas las tareas ejecutan el presupuesto F_patrones de 1 766 799 020 FLOPs. El binario FMA viaja como auxiliar.

El cotejo local usa Pegasus 5.1.2. Los planes de plantilla de patrones fijan las ubicaciones declaradas en el grafo base. En nube, el lanzador de patrones conserva la selección nativa de HTCondor sobre el conjunto elegible de dos o cuatro workers. La matriz de contraste conserva su asignación a máquinas. El conteo científico se verifica antes del envío y después mediante Analyzer y el auditor.

El límite de espera por workflow sube a 1800 s en ambos lanzadores. Los archivos científicos locales de cada corrida se retiran después de la auditoría, y se conserva la evidencia administrativa y sus resultados. Se omite el caché de archivos científicos del lanzador de patrones para liberar el espacio realmente usado. HTCondor conserva la limpieza habitual del sandbox del worker.

Para el límite bidireccional de 100 Mbit/s, el coordinador comparte una cola TBF para el destino 10.42.1.0/24. En cada worker la cola TBF aplica al destino 10.42.0.4. Se usa un filtro por destino para conservar el acceso de administración. Se registra la cola antes, durante y después en cada nodo. Una guarda local y un temporizador por nodo cubren la ventana de cinco horas.

La predicción D3 usa las tasas medidas en ambas direcciones y suma bytes de cada dirección divididos por su tasa. Se comparte el enlace del coordinador, con actividad que puede solaparse entre sentidos. El tramo temporal se asigna por prioridad, y su comparación con esa suma se interpreta bajo esa convención. Los casos con una ubicación que no aparece en FMA usan la reconstrucción de 10 MiB sobre la ubicación efectiva.
