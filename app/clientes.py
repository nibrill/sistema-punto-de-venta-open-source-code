from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def listar_clientes(solo_activos=True):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        if solo_activos:
            cursor.execute("""
                SELECT *
                FROM clientes
                WHERE activo = 1
                ORDER BY nombre ASC;
            """)
        else:
            cursor.execute("""
                SELECT *
                FROM clientes
                ORDER BY nombre ASC;
            """)

        return _respuesta(True, "Clientes obtenidos correctamente.", cursor.fetchall())

    except Error as error:
        return _respuesta(False, f"Error al listar clientes: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def buscar_clientes(texto, solo_activos=True):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        filtro = f"%{texto}%"

        if solo_activos:
            cursor.execute("""
                SELECT *
                FROM clientes
                WHERE activo = 1
                  AND (
                    nombre LIKE %s OR
                    rut LIKE %s OR
                    telefono LIKE %s OR
                    email LIKE %s
                  )
                ORDER BY nombre ASC;
            """, (filtro, filtro, filtro, filtro))
        else:
            cursor.execute("""
                SELECT *
                FROM clientes
                WHERE nombre LIKE %s OR
                      rut LIKE %s OR
                      telefono LIKE %s OR
                      email LIKE %s
                ORDER BY nombre ASC;
            """, (filtro, filtro, filtro, filtro))

        return _respuesta(True, "Búsqueda de clientes realizada correctamente.", cursor.fetchall())

    except Error as error:
        return _respuesta(False, f"Error al buscar clientes: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def crear_cliente(nombre, rut=None, telefono=None, email=None, direccion=None, notas=None):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        if not nombre or not nombre.strip():
            return _respuesta(False, "El nombre del cliente es obligatorio.")

        cursor.execute("""
            INSERT INTO clientes (
                nombre,
                rut,
                telefono,
                email,
                direccion,
                notas,
                activo
            ) VALUES (
                %s, %s, %s, %s, %s, %s, 1
            );
        """, (
            nombre.strip(),
            rut,
            telefono,
            email,
            direccion,
            notas
        ))

        conexion.commit()

        return _respuesta(True, "Cliente creado correctamente.", {
            "cliente_id": cursor.lastrowid
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear cliente: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_cliente(cliente_id, nombre, rut=None, telefono=None, email=None, direccion=None, notas=None, activo=1):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE clientes
            SET
                nombre = %s,
                rut = %s,
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
            telefono,
            email,
            direccion,
            notas,
            activo,
            cliente_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Cliente no encontrado.")

        return _respuesta(True, "Cliente actualizado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar cliente: {error}")

    finally:
        cursor.close()
        conexion.close()


def activar_cliente(cliente_id):
    return actualizar_estado_cliente(cliente_id, 1)


def desactivar_cliente(cliente_id):
    return actualizar_estado_cliente(cliente_id, 0)


def actualizar_estado_cliente(cliente_id, activo):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE clientes
            SET activo = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            activo,
            cliente_id
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            return _respuesta(False, "Cliente no encontrado.")

        return _respuesta(True, "Estado del cliente actualizado correctamente.")

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar cliente: {error}")

    finally:
        cursor.close()
        conexion.close()