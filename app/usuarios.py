import hashlib
import os
from mysql.connector import Error

from app.database import obtener_conexion


ROLES_VALIDOS = ["ADMIN", "CAJERO", "VENDEDOR"]


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def generar_hash_password(password):
    if not password or len(password.strip()) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")

    salt = os.urandom(16)
    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return f"{salt.hex()}${hash_password.hex()}"


def verificar_password(password, password_hash):
    try:
        if not password_hash or "$" not in password_hash:
            return False

        salt_hex, hash_guardado = password_hash.split("$")
        salt = bytes.fromhex(salt_hex)

        hash_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        ).hex()

        return hash_calculado == hash_guardado

    except Exception:
        return False


def crear_usuario(nombre, usuario, password, rol="CAJERO"):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        nombre = nombre.strip()
        usuario = usuario.strip().lower()
        rol = rol.upper().strip()

        if rol not in ROLES_VALIDOS:
            return _respuesta(False, "Rol inválido.")

        password_hash = generar_hash_password(password)

        cursor.execute("""
            INSERT INTO usuarios (
                nombre,
                usuario,
                password_hash,
                rol,
                activo
            ) VALUES (
                %s, %s, %s, %s, 1
            );
        """, (
            nombre,
            usuario,
            password_hash,
            rol
        ))

        conexion.commit()

        return _respuesta(True, "Usuario creado correctamente.", {
            "usuario_id": cursor.lastrowid,
            "nombre": nombre,
            "usuario": usuario,
            "rol": rol
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear usuario: {error}")

    except ValueError as error:
        conexion.rollback()
        return _respuesta(False, str(error))

    finally:
        cursor.close()
        conexion.close()


def login_usuario(usuario, password):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        usuario = usuario.strip().lower()

        cursor.execute("""
            SELECT
                id,
                nombre,
                usuario,
                password_hash,
                rol,
                activo
            FROM usuarios
            WHERE usuario = %s
            LIMIT 1;
        """, (usuario,))

        usuario_db = cursor.fetchone()

        if usuario_db is None:
            return _respuesta(False, "Usuario o contraseña incorrectos.")

        if int(usuario_db["activo"]) != 1:
            return _respuesta(False, "El usuario está desactivado.")

        password_ok = verificar_password(password, usuario_db["password_hash"])

        if not password_ok:
            return _respuesta(False, "Usuario o contraseña incorrectos.")

        cursor.execute("""
            UPDATE usuarios
            SET ultimo_login = NOW()
            WHERE id = %s;
        """, (usuario_db["id"],))

        conexion.commit()

        data = {
            "id": usuario_db["id"],
            "nombre": usuario_db["nombre"],
            "usuario": usuario_db["usuario"],
            "rol": usuario_db["rol"]
        }

        return _respuesta(True, "Login correcto.", data)

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al iniciar sesión: {error}")

    finally:
        cursor.close()
        conexion.close()


def listar_usuarios():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nombre,
                usuario,
                rol,
                activo,
                ultimo_login,
                created_at
            FROM usuarios
            ORDER BY nombre ASC;
        """)

        usuarios = cursor.fetchall()

        return _respuesta(True, "Usuarios obtenidos correctamente.", usuarios)

    except Error as error:
        return _respuesta(False, f"Error al listar usuarios: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def obtener_usuario(usuario_id):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nombre,
                usuario,
                rol,
                activo,
                ultimo_login,
                created_at
            FROM usuarios
            WHERE id = %s;
        """, (usuario_id,))

        usuario = cursor.fetchone()

        if usuario is None:
            return _respuesta(False, "Usuario no encontrado.")

        return _respuesta(True, "Usuario obtenido correctamente.", usuario)

    except Error as error:
        return _respuesta(False, f"Error al obtener usuario: {error}")

    finally:
        cursor.close()
        conexion.close()


def cambiar_password(usuario_id, nuevo_password):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        password_hash = generar_hash_password(nuevo_password)

        cursor.execute("""
            UPDATE usuarios
            SET password_hash = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            password_hash,
            usuario_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Usuario no encontrado.")

        return _respuesta(True, "Contraseña actualizada correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al cambiar contraseña: {error}")

    except ValueError as error:
        conexion.rollback()
        return _respuesta(False, str(error))

    finally:
        cursor.close()
        conexion.close()


def desactivar_usuario(usuario_id):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE usuarios
            SET activo = 0,
                updated_at = NOW()
            WHERE id = %s;
        """, (usuario_id,))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Usuario no encontrado.")

        return _respuesta(True, "Usuario desactivado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al desactivar usuario: {error}")

    finally:
        cursor.close()
        conexion.close()


def activar_usuario(usuario_id):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE usuarios
            SET activo = 1,
                updated_at = NOW()
            WHERE id = %s;
        """, (usuario_id,))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Usuario no encontrado.")

        return _respuesta(True, "Usuario activado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al activar usuario: {error}")

    finally:
        cursor.close()
        conexion.close()