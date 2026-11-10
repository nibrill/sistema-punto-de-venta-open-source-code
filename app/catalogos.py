from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


# =========================================================
# CATEGORÍAS
# =========================================================

def listar_categorias(solo_activas=True):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        if solo_activas:
            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    descripcion,
                    activo,
                    created_at
                FROM categorias
                WHERE activo = 1
                ORDER BY nombre ASC;
            """)
        else:
            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    descripcion,
                    activo,
                    created_at
                FROM categorias
                ORDER BY nombre ASC;
            """)

        categorias = cursor.fetchall()

        return _respuesta(True, "Categorías obtenidas correctamente.", categorias)

    except Error as error:
        return _respuesta(False, f"Error al listar categorías: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def crear_categoria(nombre, descripcion=None):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        nombre = nombre.strip()

        if not nombre:
            return _respuesta(False, "El nombre de la categoría es obligatorio.")

        cursor.execute("""
            INSERT INTO categorias (
                nombre,
                descripcion,
                activo
            ) VALUES (
                %s, %s, 1
            );
        """, (
            nombre,
            descripcion
        ))

        conexion.commit()

        return _respuesta(True, "Categoría creada correctamente.", {
            "categoria_id": cursor.lastrowid,
            "nombre": nombre
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_categoria(categoria_id, nombre, descripcion=None, activo=1):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE categorias
            SET
                nombre = %s,
                descripcion = %s,
                activo = %s
            WHERE id = %s;
        """, (
            nombre.strip(),
            descripcion,
            activo,
            categoria_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Categoría no encontrada.")

        return _respuesta(True, "Categoría actualizada correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


def desactivar_categoria(categoria_id):
    return actualizar_estado_categoria(categoria_id, 0)


def activar_categoria(categoria_id):
    return actualizar_estado_categoria(categoria_id, 1)


def actualizar_estado_categoria(categoria_id, activo):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE categorias
            SET activo = %s
            WHERE id = %s;
        """, (
            activo,
            categoria_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Categoría no encontrada.")

        return _respuesta(True, "Estado de categoría actualizado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar estado de categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


# =========================================================
# PROVEEDORES
# =========================================================

def listar_proveedores(solo_activos=True):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        if solo_activos:
            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    rut,
                    contacto,
                    telefono,
                    email,
                    direccion,
                    notas,
                    activo,
                    created_at,
                    updated_at
                FROM proveedores
                WHERE activo = 1
                ORDER BY nombre ASC;
            """)
        else:
            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    rut,
                    contacto,
                    telefono,
                    email,
                    direccion,
                    notas,
                    activo,
                    created_at,
                    updated_at
                FROM proveedores
                ORDER BY nombre ASC;
            """)

        proveedores = cursor.fetchall()

        return _respuesta(True, "Proveedores obtenidos correctamente.", proveedores)

    except Error as error:
        return _respuesta(False, f"Error al listar proveedores: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def crear_proveedor(nombre, rut=None, contacto=None, telefono=None, email=None, direccion=None, notas=None):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        nombre = nombre.strip()

        if not nombre:
            return _respuesta(False, "El nombre del proveedor es obligatorio.")

        cursor.execute("""
            INSERT INTO proveedores (
                nombre,
                rut,
                contacto,
                telefono,
                email,
                direccion,
                notas,
                activo
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, 1
            );
        """, (
            nombre,
            rut,
            contacto,
            telefono,
            email,
            direccion,
            notas
        ))

        conexion.commit()

        return _respuesta(True, "Proveedor creado correctamente.", {
            "proveedor_id": cursor.lastrowid,
            "nombre": nombre
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear proveedor: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_proveedor(
    proveedor_id,
    nombre,
    rut=None,
    contacto=None,
    telefono=None,
    email=None,
    direccion=None,
    notas=None,
    activo=1
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE proveedores
            SET
                nombre = %s,
                rut = %s,
                contacto = %s,
                telefono = %s,
                email = %s,
                direccion = %s,
                notas = %s,
                activo = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            nombre.strip(),
            rut,
            contacto,
            telefono,
            email,
            direccion,
            notas,
            activo,
            proveedor_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Proveedor no encontrado.")

        return _respuesta(True, "Proveedor actualizado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar proveedor: {error}")

    finally:
        cursor.close()
        conexion.close()


def desactivar_proveedor(proveedor_id):
    return actualizar_estado_proveedor(proveedor_id, 0)


def activar_proveedor(proveedor_id):
    return actualizar_estado_proveedor(proveedor_id, 1)


def actualizar_estado_proveedor(proveedor_id, activo):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE proveedores
            SET
                activo = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            activo,
            proveedor_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Proveedor no encontrado.")

        return _respuesta(True, "Estado de proveedor actualizado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar estado del proveedor: {error}")

    finally:
        cursor.close()
        conexion.close()