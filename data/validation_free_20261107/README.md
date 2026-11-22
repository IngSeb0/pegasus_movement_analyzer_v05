# Validación con ubicación libre — 7 de noviembre

Nueve comparaciones L01/GL2/GL3, tres por configuración, y un piloto GL2 separado. Cada archivo científico mide 10 MiB. HTCondor elige el worker; no se afirma asignación aleatoria.

Desde la raíz del repositorio: python analysis/rebuild_free_validation.py. Recalcula el requerido con las ubicaciones, suma entregas del cotejo extraído y verifica la razón exacta y los residuos. Los datos compactos permiten repetir esas operaciones; no sustituyen las diez cápsulas nativas preservadas fuera de Git. No se incluyen scripts que enciendan VMs.

El archivo A–H histórico es una cohorte distinta. No sumar sus casos como repeticiones de este contraste.
