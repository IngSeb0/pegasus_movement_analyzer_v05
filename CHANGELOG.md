# v0.5.0

- M_req simplificado a una única referencia: placement observado + reutilización local ideal.
- Entrada directa `runXXXX`.
- Placement desde TSV, snapshot `condor_history -long` o `condor_history` vivo.
- Trazabilidad byte a byte mediante `observed_transfers.tsv` y `required_movement.tsv`.
- Ya no se presenta M_req*, M_req^(pi,E) ni EMD como definiciones principales del analizador.
- Fixture de Distribution reconstruida desde evidencia real del proyecto.
