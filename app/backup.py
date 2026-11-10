"""Respaldo automático de la base de datos CorePOS (mysqldump)."""
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from app.database import DB_CONFIG

MAX_RESPALDOS = 14
CREATE_NO_WINDOW = 0x08000000


def _ruta_mysqldump():
    candidatos = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "CorePOS" / "mysql" / "mysql-8.4.9-winx64" / "bin" / "mysqldump.exe",
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return None


def carpeta_respaldos():
    base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "CorePOS" / "backups"
    base.mkdir(parents=True, exist_ok=True)
    return base


def respaldar_base_datos(forzar=False):
    """Genera un .sql comprimible. Máximo un respaldo por día salvo forzar=True."""
    dump = _ruta_mysqldump()
    if dump is None or not DB_CONFIG["password"]:
        return {"ok": False, "mensaje": "mysqldump o credenciales no disponibles."}

    carpeta = carpeta_respaldos()
    hoy = datetime.now().strftime("%Y%m%d")

    if not forzar and any(carpeta.glob(f"pos_pymes_{hoy}_*.sql")):
        return {"ok": True, "mensaje": "Ya existe un respaldo de hoy."}

    destino = carpeta / f"pos_pymes_{datetime.now():%Y%m%d_%H%M%S}.sql"
    entorno = dict(os.environ, MYSQL_PWD=str(DB_CONFIG["password"]))

    try:
        with open(destino, "wb") as salida:
            proceso = subprocess.run(
                [str(dump), "-h", str(DB_CONFIG["host"]), "-P", str(DB_CONFIG["port"]),
                 "-u", str(DB_CONFIG["user"]), "--single-transaction",
                 "--routines", DB_CONFIG["database"]],
                stdout=salida, stderr=subprocess.PIPE, env=entorno,
                creationflags=CREATE_NO_WINDOW, timeout=300,
            )
        if proceso.returncode != 0:
            destino.unlink(missing_ok=True)
            return {"ok": False, "mensaje": proceso.stderr.decode(errors="replace")[:300]}
    except Exception as error:
        destino.unlink(missing_ok=True)
        return {"ok": False, "mensaje": str(error)}

    for viejo in sorted(carpeta.glob("pos_pymes_*.sql"))[:-MAX_RESPALDOS]:
        viejo.unlink(missing_ok=True)

    return {"ok": True, "mensaje": f"Respaldo creado: {destino.name}"}


def respaldar_en_segundo_plano():
    threading.Thread(target=respaldar_base_datos, daemon=True).start()
