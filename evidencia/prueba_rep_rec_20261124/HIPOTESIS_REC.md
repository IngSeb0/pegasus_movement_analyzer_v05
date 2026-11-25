# Predicciones REP-REC

R1. El requerido de REP-REC es igual al de REP: 1887436800 bytes.
R2. El observado de REP-REC es 1887436800 bytes (DME = 1); en REP es 2097152000 bytes. La diferencia es exactamente 209715200 bytes en cada repetición.
R3. En cada repetición, el tramo de transferencia de REP-REC es menor que el de REP, del orden de 200 MiB divididos por el ancho medido (unos 18 s a 11,8 MB/s). Se considera cumplida si el promedio de la diferencia es negativo y su magnitud está entre 9 y 27 s.
R4. Sin predicción de dirección para la duración total. P+C1 es un solo job, así que g llega al coordinador cuando termina C1, y C2, C3 y C4 esperan ese cómputo extra. Solo se reporta la diferencia y su desviación.
