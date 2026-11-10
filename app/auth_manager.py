import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

from app.security import (
    generar_hash_password,
    verificar_password,
    es_hash_legacy,
    normalizar_rol
)


def obtener_ruta_env():
    """
    Busca el archivo .env en orden de prioridad.

    1. C:\\ProgramData\\CorePOS\\.env
       Ruta usada por el instalador.

    2. Raíz del proyecto
       Ruta usada cuando ejecutas desde VS Code.

    3. Carpeta del .exe
       Ruta alternativa si dejas el .env junto al ejecutable.

    4. Carpeta actual
       Respaldo final.
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
    print("ADVERTENCIA: No se encontró archivo .env en AuthManager. Se usarán valores por defecto.")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", 3307)),
    "user": os.getenv("DB_USER", "pos_user"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "pos_pymes"),
}


class AuthManager:
    def conectar(self):
        return mysql.connector.connect(**DB_CONFIG)

    def respuesta(self, ok, mensaje="", data=None):
        return {
            "ok": ok,
            "mensaje": mensaje,
            "data": data
        }

    def login(self, usuario, password):
        usuario = str(usuario or "").strip()
        password = str(password or "").strip()

        if not usuario or not password:
            return self.respuesta(False, "Debe ingresar usuario y contraseña.")

        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, nombre, usuario, password_hash, rol, activo
                FROM usuarios
                WHERE usuario = %s
                LIMIT 1
                """,
                (usuario,)
            )

            fila = cursor.fetchone()

            if not fila:
                return self.respuesta(False, "Usuario o contraseña incorrectos.")

            if int(fila.get("activo") or 0) != 1:
                return self.respuesta(False, "Este usuario está desactivado.")

            password_hash = fila.get("password_hash")

            if not verificar_password(password, password_hash):
                return self.respuesta(False, "Usuario o contraseña incorrectos.")

            if es_hash_legacy(password_hash):
                nuevo_hash = generar_hash_password(password)

                cursor.execute(
                    """
                    UPDATE usuarios
                    SET password_hash = %s
                    WHERE id = %s
                    """,
                    (nuevo_hash, fila["id"])
                )

            cursor.execute(
                """
                UPDATE usuarios
                SET ultimo_login = NOW()
                WHERE id = %s
                """,
                (fila["id"],)
            )

            conexion.commit()

            usuario_logueado = {
                "id": fila["id"],
                "nombre": fila["nombre"],
                "usuario": fila["usuario"],
                "rol": normalizar_rol(fila["rol"]),
                "activo": fila["activo"]
            }

            return self.respuesta(True, "Login correcto.", usuario_logueado)

        except Exception as error:
            if conexion:
                conexion.rollback()

            return self.respuesta(
                False,
                f"Error en login: {error}\n"
                f"Conexión usada: {DB_CONFIG['host']}:{DB_CONFIG['port']} / "
                f"BD: {DB_CONFIG['database']} / Usuario MySQL: {DB_CONFIG['user']}"
            )

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()

    def listar_usuarios(self, texto="", incluir_inactivos=True):
        texto = str(texto or "").strip()

        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            sql = """
                SELECT id, nombre, usuario, rol, activo, ultimo_login, created_at
                FROM usuarios
                WHERE 1 = 1
            """

            params = []

            if texto:
                sql += """
                    AND (
                        nombre LIKE %s
                        OR usuario LIKE %s
                        OR rol LIKE %s
                    )
                """
                like = f"%{texto}%"
                params.extend([like, like, like])

            if not incluir_inactivos:
                sql += " AND activo = 1 "

            sql += " ORDER BY activo DESC, nombre ASC "

            cursor.execute(sql, tuple(params))
            usuarios = cursor.fetchall() or []

            for usuario in usuarios:
                usuario["rol"] = normalizar_rol(usuario.get("rol"))

            return self.respuesta(True, "Usuarios cargados.", usuarios)

        except Exception as error:
            return self.respuesta(False, f"Error cargando usuarios: {error}")

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()

    def crear_usuario(self, nombre, usuario, password, rol):
        nombre = str(nombre or "").strip()
        usuario = str(usuario or "").strip()
        password = str(password or "").strip()
        rol = normalizar_rol(rol)

        if not nombre:
            return self.respuesta(False, "Debe ingresar el nombre.")

        if not usuario:
            return self.respuesta(False, "Debe ingresar el usuario.")

        if not password:
            return self.respuesta(False, "Debe ingresar una contraseña.")

        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            password_hash = generar_hash_password(password)

            cursor.execute(
                """
                INSERT INTO usuarios
                (nombre, usuario, password_hash, rol, activo)
                VALUES (%s, %s, %s, %s, 1)
                """,
                (nombre, usuario, password_hash, rol)
            )

            conexion.commit()

            return self.respuesta(True, "Usuario creado correctamente.")

        except mysql.connector.IntegrityError:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, "Ya existe un usuario con ese nombre de acceso.")

        except Exception as error:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, f"Error creando usuario: {error}")

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()

    def actualizar_usuario(self, usuario_id, nombre, usuario, rol, activo, password=None):
        usuario_id = int(usuario_id)
        nombre = str(nombre or "").strip()
        usuario = str(usuario or "").strip()
        rol = normalizar_rol(rol)
        activo = 1 if activo else 0
        password = str(password or "").strip()

        if not nombre:
            return self.respuesta(False, "Debe ingresar el nombre.")

        if not usuario:
            return self.respuesta(False, "Debe ingresar el usuario.")

        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            if password:
                password_hash = generar_hash_password(password)

                cursor.execute(
                    """
                    UPDATE usuarios
                    SET nombre = %s,
                        usuario = %s,
                        password_hash = %s,
                        rol = %s,
                        activo = %s
                    WHERE id = %s
                    """,
                    (nombre, usuario, password_hash, rol, activo, usuario_id)
                )

            else:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET nombre = %s,
                        usuario = %s,
                        rol = %s,
                        activo = %s
                    WHERE id = %s
                    """,
                    (nombre, usuario, rol, activo, usuario_id)
                )

            conexion.commit()

            return self.respuesta(True, "Usuario actualizado correctamente.")

        except mysql.connector.IntegrityError:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, "Ya existe otro usuario con ese nombre de acceso.")

        except Exception as error:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, f"Error actualizando usuario: {error}")

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()

    def activar_usuario(self, usuario_id):
        return self.cambiar_estado_usuario(usuario_id, 1)

    def desactivar_usuario(self, usuario_id):
        return self.cambiar_estado_usuario(usuario_id, 0)

    def eliminar_usuario_definitivo(self, usuario_id):
        usuario_id = int(usuario_id)

        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, nombre, usuario, rol
                FROM usuarios
                WHERE id = %s
                LIMIT 1
                """,
                (usuario_id,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                return self.respuesta(False, "El usuario no existe.")

            if usuario.get("rol") == "ADMIN":
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total_admins
                    FROM usuarios
                    WHERE rol = 'ADMIN'
                    AND activo = 1
                    AND id <> %s
                    """,
                    (usuario_id,)
                )

                data_admins = cursor.fetchone()
                total_admins = int(data_admins.get("total_admins") or 0)

                if total_admins == 0:
                    return self.respuesta(
                        False,
                        "No puedes eliminar el último administrador activo del sistema."
                    )

            cursor.execute(
                """
                DELETE FROM usuarios
                WHERE id = %s
                """,
                (usuario_id,)
            )

            conexion.commit()

            return self.respuesta(
                True,
                f"Usuario '{usuario.get('usuario')}' eliminado definitivamente."
            )

        except mysql.connector.IntegrityError:
            if conexion:
                conexion.rollback()

            return self.respuesta(
                False,
                "No se puede eliminar este usuario porque tiene ventas, caja o movimientos asociados. "
                "Para mantener el historial del POS, desactívalo en vez de eliminarlo."
            )

        except Exception as error:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, f"Error eliminando usuario: {error}")

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()

    def cambiar_estado_usuario(self, usuario_id, activo):
        conexion = None
        cursor = None

        try:
            conexion = self.conectar()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute(
                """
                UPDATE usuarios
                SET activo = %s
                WHERE id = %s
                """,
                (1 if activo else 0, int(usuario_id))
            )

            conexion.commit()

            return self.respuesta(True, "Estado del usuario actualizado.")

        except Exception as error:
            if conexion:
                conexion.rollback()

            return self.respuesta(False, f"Error cambiando estado: {error}")

        finally:
            if cursor:
                cursor.close()

            if conexion:
                conexion.close()