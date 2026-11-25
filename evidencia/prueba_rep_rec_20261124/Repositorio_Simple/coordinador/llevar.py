"""Lleva archivos entre tu PC y el coordinador (por SSH) y ejecuta comandos allá.

    python llevar.py subir  ARCHIVO_O_CARPETA...      copia a ~/trabajo/ del coordinador
    python llevar.py correr "COMANDO"                 ejecuta el comando en ~/trabajo/
    python llevar.py bajar  RUTA_REMOTA CARPETA_LOCAL descarga (ruta relativa a ~/trabajo/)

El coordinador se llama "dme-master" en tu ~/.ssh/config (HostName, User, IdentityFile),
o define otro nombre con la variable de entorno COORDINADOR.
"""
import os, subprocess, sys

HOST = os.environ.get("COORDINADOR", "dme-master")
SSH_CONFIG = os.environ.get("SSH_CONFIG")
SSH_OPTIONS = ["-F", SSH_CONFIG] if SSH_CONFIG else []
TRABAJO = "trabajo/prueba_rep_rec_20261124"


def ejecutar(*comando):
    if subprocess.run(comando).returncode:
        sys.exit("Falló: " + " ".join(comando))


accion, *args = sys.argv[1:]
if accion == "subir":
    ejecutar("ssh", *SSH_OPTIONS, HOST, f"mkdir -p ~/{TRABAJO}")
    ejecutar("scp", *SSH_OPTIONS, "-r", *args, f"{HOST}:{TRABAJO}/")
elif accion == "correr":
    ejecutar("ssh", *SSH_OPTIONS, HOST, f"cd ~/{TRABAJO} && {args[0]}")
elif accion == "bajar":
    ejecutar("scp", *SSH_OPTIONS, "-r", f"{HOST}:{TRABAJO}/{args[0]}", args[1])
else:
    sys.exit(__doc__)
