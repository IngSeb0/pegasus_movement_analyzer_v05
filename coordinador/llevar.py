"""Lleva archivos entre tu PC y el coordinador (por SSH) y ejecuta comandos allá.

    python llevar.py subir  ARCHIVO_O_CARPETA...      copia a ~/trabajo/ del coordinador
    python llevar.py correr "COMANDO"                 ejecuta el comando en ~/trabajo/
    python llevar.py bajar  RUTA_REMOTA CARPETA_LOCAL descarga (ruta relativa a ~/trabajo/)

El coordinador se llama "dme-master" en tu ~/.ssh/config (HostName, User, IdentityFile),
o define otro nombre con la variable de entorno COORDINADOR.
"""
import os, subprocess, sys

HOST = os.environ.get("COORDINADOR", "dme-master")


def ejecutar(*comando):
    if subprocess.run(comando).returncode:
        sys.exit("Falló: " + " ".join(comando))


accion, *args = sys.argv[1:]
if accion == "subir":
    ejecutar("ssh", HOST, "mkdir -p ~/trabajo")
    ejecutar("scp", "-r", *args, f"{HOST}:trabajo/")
elif accion == "correr":
    ejecutar("ssh", HOST, f"cd ~/trabajo && {args[0]}")
elif accion == "bajar":
    ejecutar("scp", "-r", f"{HOST}:trabajo/{args[0]}", args[1])
else:
    sys.exit(__doc__)
