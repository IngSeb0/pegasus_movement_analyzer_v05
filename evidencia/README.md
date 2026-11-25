# Evidencia de las pruebas de la tesis

## Conjuntos

### intensivo_20261122

Cinco patrones sintéticos con dos y cuatro workers, y contraste entre agrupación y reparto. El ZIP de resultados se publica descomprimido.

- [HIPOTESIS.md](intensivo_20261122/HIPOTESIS.md)
- [HIPOTESIS.sha256](intensivo_20261122/HIPOTESIS.sha256)
- [RESULTADOS/BYTES.csv](intensivo_20261122/RESULTADOS/BYTES.csv)

### montage_intensivo_20261122

Montage de 147 imágenes de M101. Incluye el piloto a 100 Mbit/s, la ronda enmendada a 50 Mbit/s y el diagnóstico de M4.

- [RESULTADOS/HIPOTESIS.md](montage_intensivo_20261122/RESULTADOS/HIPOTESIS.md)
- [RESULTADOS/HIPOTESIS.sha256](montage_intensivo_20261122/RESULTADOS/HIPOTESIS.sha256)
- [RESULTADOS/PLAN_ACCOUNTS.json](montage_intensivo_20261122/RESULTADOS/PLAN_ACCOUNTS.json)
- [ronda2_50mbit/BYTES.csv](montage_intensivo_20261122/ronda2_50mbit/BYTES.csv)
- [ronda2_50mbit/CAUSA_M4/CAUSA_M4.md](montage_intensivo_20261122/ronda2_50mbit/CAUSA_M4/CAUSA_M4.md)

### montage_m101

Montage de diez imágenes de M101. Compara la ejecución separada y las variantes de agrupación.

- [PROTOCOLO.md](montage_m101/PROTOCOLO.md)
- [RESULTADOS_M101.md](montage_m101/RESULTADOS_M101.md)
- [evidence/PLAN_ACCOUNTS.json](montage_m101/evidence/PLAN_ACCOUNTS.json)

### prueba_rep_rec_20261124

Validación de la recomendación de agrupar P y C1 en W1. Hay dos pares válidos y un tercer REP interrumpido.

- [HIPOTESIS_REC.md](prueba_rep_rec_20261124/HIPOTESIS_REC.md)
- [HIPOTESIS_REC.sha256](prueba_rep_rec_20261124/HIPOTESIS_REC.sha256)
- [RESULTADOS_REC.md](prueba_rep_rec_20261124/RESULTADOS_REC.md)
- [CAMINO_CRITICO.md](prueba_rep_rec_20261124/CAMINO_CRITICO.md)

## Integridad y datos de Azure

El identificador de suscripción y la dirección IP pública del coordinador se reemplazaron por `<omitido>` en los textos. Las rutas de credenciales y configuraciones privadas se excluyeron. Los contenedores internos se listan entre los omitidos porque pueden encapsular archivos sin depurar. El ZIP de Intensivo se recorrió por entrada.

Los sellos siguientes se cotejaron con los bytes publicados:

- [intensivo_20261122/HIPOTESIS.sha256](intensivo_20261122/HIPOTESIS.sha256)
- [intensivo_20261122/RESULTADOS/HIPOTESIS.sha256](intensivo_20261122/RESULTADOS/HIPOTESIS.sha256)
- [montage_intensivo_20261122/HIPOTESIS.sha256](montage_intensivo_20261122/HIPOTESIS.sha256)
- [montage_intensivo_20261122/RESULTADOS/ANEXO_RONDA2_50MBIT_20261122.sha256](montage_intensivo_20261122/RESULTADOS/ANEXO_RONDA2_50MBIT_20261122.sha256)
- [montage_intensivo_20261122/RESULTADOS/HIPOTESIS.sha256](montage_intensivo_20261122/RESULTADOS/HIPOTESIS.sha256)
- [montage_intensivo_20261122/RESULTADOS/HIPOTESIS_ANEXO_SIA_20261122.sha256](montage_intensivo_20261122/RESULTADOS/HIPOTESIS_ANEXO_SIA_20261122.sha256)
- [montage_intensivo_20261122/ronda2_50mbit/ANEXO_RONDA2_50MBIT_20261122.sha256](montage_intensivo_20261122/ronda2_50mbit/ANEXO_RONDA2_50MBIT_20261122.sha256)
- [prueba_rep_rec_20261124/HIPOTESIS_REC.sha256](prueba_rep_rec_20261124/HIPOTESIS_REC.sha256)

## Archivos omitidos con huella

El límite se interpreta como 50 000 000 bytes. Las exclusiones por ruta privada y los cachés no se enumeran.

| Ruta | Bytes | SHA-256 | Motivo |
| --- | ---: | --- | --- |
| `montage_intensivo_20261122/montage_intensivo_20261122_preparacion.zip` | 26661 | `663495d69e2e33aafd1546c4170298044ffa2968fb2b76c550bb4156137cd619` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/Montage_M101_SIA_20261122.zip` | 8621479 | `e5b2d4e22ec4b8eb7ba4b3a57e8ddb641b0e9c9a9356415ee42b6ee61ed1ce04` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/preparacion_planes.tar.gz` | 6535546 | `8893708b8bc3a3d004c110b2a4a77c9f215dc4966edc08194f17b328904ada84` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/RESULTADOS/planes_nativos.tar.gz` | 360623 | `fa05d168d149584f2695504baaa427649869c856b6ace551fcb5023952d822e4` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/ronda2_50mbit/Montage_M101_Ronda2_50Mbit_20261122.zip` | 19676121 | `2d6ef3b1b519e5b7c9a6b3f2b4e5694144c3964f926517d016d4747ab3016279` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/ronda2_50mbit/payload.tar.gz` | 6535810 | `9ff179901193aad7e2cbdc28882c22bed4e4ba78e335ff968141b4f51fa00df8` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/ronda2_50mbit/sesion09/evidencia.tar.gz` | 6567448 | `8c47321d05510b236e6b5d91fe79af9e2aa6f47c241767de78522cd677aa31d1` | Contenedor empaquetado sin publicación directa |
| `montage_intensivo_20261122/sesion07/evidencia.tar.gz` | 941345 | `e40e10fd843e57c3153e17d1a2ec310926865ae9a8babffa08e43b718cead645` | Contenedor empaquetado sin publicación directa |
| `montage_m101/evidence/capsules/M101-BASE.tar.xz` | 124215044 | `b22f01c8d9f6c351eae9f9540dd37f8b621099c92e2f85d7af0fdddf5d80ad86` | Mayor de 50 MB |
| `montage_m101/evidence/capsules/M101-FINAL.tar.xz` | 124202584 | `d0c7f17f779accb0e5eea92cb7a304258758ae856de0a5890c661c2e0bcca340` | Mayor de 50 MB |
| `montage_m101/evidence/capsules/M101-PROJ.tar.xz` | 124220276 | `b5e63bde46168df4bc61456666fa42ac47f5141dfa5815323d446a3ee21e369d` | Mayor de 50 MB |
| `montage_m101/evidence/compact.tar.gz` | 32095 | `059f1d1235ab3c64870d059c3810fb1d3de9a5ebabd46dc82c18d98a4e8d4a3e` | Contenedor empaquetado sin publicación directa |
| `montage_m101/evidence/evidence.tar` | 372756480 | `13495f51c9145632b703377abcbcd8cd94aefdea45313e9714de2a155e35b513` | Mayor de 50 MB |
| `montage_m101/payload/montage_assets/montage_task.py` | 8575333 | `c1023c1a4124dc5f557a1754da2db096f09f21638960b3d4e35c9c9b9b72b127` | Patrón de credencial en contenido |
| `montage_m101/payload.tar.gz` | 22245266 | `87e99c193bf27c2fd93c6b526b7928dbed76bc9f10c8d0c89cae4e251bdc47b2` | Contenedor empaquetado sin publicación directa |
| `prueba_rep_rec_20261124/PLAN_NATIVO/pegasus-worker-5.1.2-x86_64_ubuntu_24.tar.gz` | 18251217 | `b1d82cc0c6b2c26bfa308c51e7eeb661a48691af2355ad4755f0c5262d5e4cc1` | Contenedor empaquetado sin publicación directa |
| `prueba_rep_rec_20261124/rep_r1/run0001/pegasus-worker-5.1.2-x86_64_ubuntu_24.tar.gz` | 18251217 | `b1d82cc0c6b2c26bfa308c51e7eeb661a48691af2355ad4755f0c5262d5e4cc1` | Contenedor empaquetado sin publicación directa |
| `prueba_rep_rec_20261124/rep_r2/run0001/pegasus-worker-5.1.2-x86_64_ubuntu_24.tar.gz` | 18251217 | `b1d82cc0c6b2c26bfa308c51e7eeb661a48691af2355ad4755f0c5262d5e4cc1` | Contenedor empaquetado sin publicación directa |
| `prueba_rep_rec_20261124/reprec_r1/run0001/pegasus-worker-5.1.2-x86_64_ubuntu_24.tar.gz` | 18251217 | `b1d82cc0c6b2c26bfa308c51e7eeb661a48691af2355ad4755f0c5262d5e4cc1` | Contenedor empaquetado sin publicación directa |
| `prueba_rep_rec_20261124/reprec_r2/run0001/pegasus-worker-5.1.2-x86_64_ubuntu_24.tar.gz` | 18251217 | `b1d82cc0c6b2c26bfa308c51e7eeb661a48691af2355ad4755f0c5262d5e4cc1` | Contenedor empaquetado sin publicación directa |

## Nota sobre las huellas de las hipótesis

El 25 de noviembre de 2026, después de las pruebas, se cambió en los archivos `HIPOTESIS.md` de `intensivo_20261122` y `montage_intensivo_20261122` (y en sus copias de `RESULTADOS/`) solo el título del documento, una línea inicial con instrucciones de trabajo y el nombre del archivo de resumen de resultados al que remiten, que ahora se llama `RESUMEN_RESULTADOS.md`. No se modificó ninguna hipótesis, valor esperado ni criterio. En los registros también se reemplazó la ruta de la carpeta local del autor por `<carpeta local>`. Por eso sus archivos `.sha256` se recalcularon. Las huellas originales, registradas antes de medir, eran:

| Archivo | Huella original (SHA-256) |
|---|---|
| `intensivo_20261122/HIPOTESIS.md` | `f663a80ed64475248c2aff11f6ee819aa0cfe34cee5429b7c2ba062c095bfae1` |
| `montage_intensivo_20261122/HIPOTESIS.md` | `d48b4aedebc08a5180e804d3c43390b2a18e156152ad17a28475b9c49c1911d3` |

Los archivos `HIPOTESIS_REC.md` (REP-REC) y `HIPOTESIS_ANEXO_SIA_20261122.md` no cambiaron y conservan su huella original.
