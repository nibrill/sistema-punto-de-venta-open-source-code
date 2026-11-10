from pathlib import Path
import os
import sys

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


def obtener_ruta_env():
    r"""
    Busca el archivo .env en orden de prioridad.

    1. C:\ProgramData\CorePOS\.env
       Esta es la ruta usada por el instalador.

    2. Carpeta raíz del proyecto
       Esta sirve cuando ejecutas desde VS Code.

    3. Carpeta donde está el .exe
       Esta sirve si en algún momento dejas el .env junto al ejecutable.
    """

    rutas = []

    program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    rutas.append(Path(program_data) / "CorePOS" / ".env")

    base_dir = Path(__file__).resolve().parent.parent
    rutas.append(base_dir / ".env")

    if getattr(sys, "frozen", False):
        rutas.append(Path(sys.executable).resolve().parent / ".env")

    rutas.append(Path.cwd() / ".env")

    for ruta in rutas:
        if ruta.exists():
            return ruta

    return None


ENV_PATH = obtener_ruta_env()

if ENV_PATH:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    print("ADVERTENCIA: No se encontró archivo .env. Se usarán valores por defecto.")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", 3307)),
    "user": os.getenv("DB_USER", "pos_user"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "pos_pymes"),
}


def obtener_conexion():
    if not DB_CONFIG["password"]:
        print("ERROR: DB_PASSWORD no está configurado. Revise el archivo .env "
              r"(C:\ProgramData\CorePOS\.env).")
        return None

    try:
        conexion = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )

        return conexion

    except Error as error:
        print("Error al conectar a MySQL:")
        print(error)
        print("Configuración usada:")
        print(f"HOST: {DB_CONFIG['host']}")
        print(f"PORT: {DB_CONFIG['port']}")
        print(f"DB: {DB_CONFIG['database']}")
        print(f"USER: {DB_CONFIG['user']}")
        return None


def ejecutar_consulta(consulta, parametros=None, obtener_uno=False, obtener_todos=False):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, parametros or ())

        if obtener_uno:
            resultado = cursor.fetchone()
        elif obtener_todos:
            resultado = cursor.fetchall()
        else:
            conexion.commit()
            resultado = cursor.lastrowid

        return resultado

    except Error as error:
        conexion.rollback()
        print("Error en consulta SQL:")
        print(error)
        return None

    finally:
        cursor.close()
        conexion.close()