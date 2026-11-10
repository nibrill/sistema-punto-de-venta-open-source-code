"""Genera el hash de una contraseña para el usuario admin inicial.

Uso:  python scripts/generar_hash.py
Pegue el resultado en sql/99_datos_iniciales.sql reemplazando @@ADMIN_HASH@@.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.security import generar_hash_password

print(generar_hash_password(getpass.getpass("Contraseña para admin: ")))
