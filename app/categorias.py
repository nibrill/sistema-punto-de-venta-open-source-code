from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def _obtener_columnas(cursor):
    cursor.execute("SHOW COLUMNS FROM categorias;")
    filas = cursor.fetchall() or []

    columnas = set()

    for fila in filas:
        if isinstance(fila, dict):
            columnas.add(fila.get("Field"))
        else:
            columnas.add(fila[0])

    return columnas


def listar_categorias():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas(cursor)

        if "activo" in columnas:
            cursor.execute("""
                SELECT id, nombre
                FROM categorias
                WHERE activo = 1
                ORDER BY nombre ASC;
            """)
        else:
            cursor.execute("""
                SELECT id, nombre
                FROM categorias
                ORDER BY nombre ASC;
            """)

        return _respuesta(
            True,
            "Categorías obtenidas correctamente.",
            cursor.fetchall() or []
        )

    except Error as error:
        return _respuesta(False, f"Error al listar categorías: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def crear_categoria(nombre, descripcion=""):
    nombre = str(nombre or "").strip()
    descripcion = str(descripcion or "").strip()

    if not nombre:
        return _respuesta(False, "Debe ingresar el nombre de la categoría.")

    if len(nombre) < 2:
        return _respuesta(False, "El nombre de la categoría debe tener al menos 2 caracteres.")

    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas(cursor)

        filtro_activo = "AND activo = 1" if "activo" in columnas else ""

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
            {filtro_activo}
            LIMIT 1;
        """, (nombre,))

        existente = cursor.fetchone()

        if existente:
            return _respuesta(
                False,
                f"Ya existe una categoría con el nombre '{existente.get('nombre')}'."
            )

        campos = ["nombre"]
        valores = [nombre]
        placeholders = ["%s"]

        if "descripcion" in columnas:
            campos.append("descripcion")
            valores.append(descripcion)
            placeholders.append("%s")

        if "activo" in columnas:
            campos.append("activo")
            valores.append(1)
            placeholders.append("%s")

        if "created_at" in columnas:
            campos.append("created_at")
            placeholders.append("NOW()")

        if "updated_at" in columnas:
            campos.append("updated_at")
            placeholders.append("NOW()")

        consulta = f"""
            INSERT INTO categorias (
                {", ".join(campos)}
            ) VALUES (
                {", ".join(placeholders)}
            );
        """

        cursor.execute(consulta, tuple(valores))
        conexion.commit()

        return _respuesta(True, "Categoría creada correctamente.", {
            "id": cursor.lastrowid,
            "nombre": nombre
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_nombre_categoria(categoria_id, nuevo_nombre):
    nuevo_nombre = str(nuevo_nombre or "").strip()

    if not categoria_id:
        return _respuesta(False, "No se recibió el ID de la categoría.")

    if not nuevo_nombre:
        return _respuesta(False, "Debe ingresar el nuevo nombre de la categoría.")

    if len(nuevo_nombre) < 2:
        return _respuesta(False, "El nombre de la categoría debe tener al menos 2 caracteres.")

    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas(cursor)

        filtro_activo = "AND activo = 1" if "activo" in columnas else ""

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE id = %s
            {filtro_activo}
            LIMIT 1;
        """, (categoria_id,))

        categoria = cursor.fetchone()

        if not categoria:
            return _respuesta(False, "Categoría no encontrada o inactiva.")

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND id <> %s
            {filtro_activo}
            LIMIT 1;
        """, (nuevo_nombre, categoria_id))

        duplicada = cursor.fetchone()

        if duplicada:
            return _respuesta(
                False,
                f"Ya existe otra categoría con el nombre '{duplicada.get('nombre')}'."
            )

        sets = ["nombre = %s"]
        valores = [nuevo_nombre]

        if "updated_at" in columnas:
            sets.append("updated_at = NOW()")

        valores.append(categoria_id)

        cursor.execute(f"""
            UPDATE categorias
            SET {", ".join(sets)}
            WHERE id = %s;
        """, tuple(valores))

        conexion.commit()

        return _respuesta(True, "Nombre de categoría actualizado correctamente.", {
            "id": categoria_id,
            "nombre_anterior": categoria.get("nombre"),
            "nombre_nuevo": nuevo_nombre
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar categoría: {error}")

    finally:
        cursor.close()
        conexion.close()