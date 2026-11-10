from decimal import Decimal
from mysql.connector import Error

from app.database import obtener_conexion


def _decimal(valor):
    return Decimal(str(valor or 0))


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def ingresar_stock(
    producto_id,
    usuario_id,
    cantidad,
    precio_compra=None,
    comentario="Ingreso de stock",
    actualizar_precio_compra=True
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cantidad = _decimal(cantidad)

        if cantidad <= 0:
            return _respuesta(False, "La cantidad debe ser mayor a cero.")

        conexion.start_transaction()

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id = %s
              AND activo = 1
            FOR UPDATE;
        """, (producto_id,))

        producto = cursor.fetchone()

        if producto is None:
            conexion.rollback()
            return _respuesta(False, "Producto no encontrado o inactivo.")

        stock_anterior = _decimal(producto["stock_actual"])
        stock_nuevo = stock_anterior + cantidad

        if precio_compra is None:
            precio_compra_final = _decimal(producto["precio_compra"])
        else:
            precio_compra_final = _decimal(precio_compra)

        if actualizar_precio_compra:
            cursor.execute("""
                UPDATE productos
                SET
                    stock_actual = %s,
                    precio_compra = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                stock_nuevo,
                precio_compra_final,
                producto_id
            ))
        else:
            cursor.execute("""
                UPDATE productos
                SET
                    stock_actual = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                stock_nuevo,
                producto_id
            ))

        cursor.execute("""
            INSERT INTO movimientos_stock (
                producto_id,
                usuario_id,
                tipo_movimiento,
                cantidad_anterior,
                cantidad_movimiento,
                cantidad_nueva,
                precio_compra,
                referencia,
                comentario
            ) VALUES (
                %s, %s, 'ENTRADA', %s, %s, %s, %s, %s, %s
            );
        """, (
            producto_id,
            usuario_id,
            stock_anterior,
            cantidad,
            stock_nuevo,
            precio_compra_final,
            "INGRESO-STOCK",
            comentario
        ))

        conexion.commit()

        return _respuesta(True, "Stock ingresado correctamente.", {
            "producto_id": producto_id,
            "producto": producto["nombre"],
            "stock_anterior": stock_anterior,
            "cantidad_ingresada": cantidad,
            "stock_nuevo": stock_nuevo,
            "precio_compra": precio_compra_final
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al ingresar stock: {error}")

    finally:
        cursor.close()
        conexion.close()


def ajustar_stock(
    producto_id,
    usuario_id,
    nuevo_stock,
    comentario="Ajuste manual de stock"
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        nuevo_stock = _decimal(nuevo_stock)

        if nuevo_stock < 0:
            return _respuesta(False, "El nuevo stock no puede ser negativo.")

        conexion.start_transaction()

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id = %s
              AND activo = 1
            FOR UPDATE;
        """, (producto_id,))

        producto = cursor.fetchone()

        if producto is None:
            conexion.rollback()
            return _respuesta(False, "Producto no encontrado o inactivo.")

        stock_anterior = _decimal(producto["stock_actual"])
        diferencia = nuevo_stock - stock_anterior

        if diferencia == 0:
            conexion.rollback()
            return _respuesta(False, "El nuevo stock es igual al stock actual. No hay cambios.")

        if diferencia > 0:
            tipo_movimiento = "AJUSTE_POSITIVO"
        else:
            tipo_movimiento = "AJUSTE_NEGATIVO"

        cursor.execute("""
            UPDATE productos
            SET
                stock_actual = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            nuevo_stock,
            producto_id
        ))

        cursor.execute("""
            INSERT INTO movimientos_stock (
                producto_id,
                usuario_id,
                tipo_movimiento,
                cantidad_anterior,
                cantidad_movimiento,
                cantidad_nueva,
                precio_compra,
                referencia,
                comentario
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """, (
            producto_id,
            usuario_id,
            tipo_movimiento,
            stock_anterior,
            diferencia,
            nuevo_stock,
            producto["precio_compra"],
            "AJUSTE-STOCK",
            comentario
        ))

        conexion.commit()

        return _respuesta(True, "Stock ajustado correctamente.", {
            "producto_id": producto_id,
            "producto": producto["nombre"],
            "stock_anterior": stock_anterior,
            "stock_nuevo": nuevo_stock,
            "diferencia": diferencia,
            "tipo_movimiento": tipo_movimiento
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al ajustar stock: {error}")

    finally:
        cursor.close()
        conexion.close()


def registrar_merma(
    producto_id,
    usuario_id,
    cantidad,
    comentario="Merma de producto"
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cantidad = _decimal(cantidad)

        if cantidad <= 0:
            return _respuesta(False, "La cantidad debe ser mayor a cero.")

        conexion.start_transaction()

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id = %s
              AND activo = 1
            FOR UPDATE;
        """, (producto_id,))

        producto = cursor.fetchone()

        if producto is None:
            conexion.rollback()
            return _respuesta(False, "Producto no encontrado o inactivo.")

        stock_anterior = _decimal(producto["stock_actual"])

        if cantidad > stock_anterior:
            conexion.rollback()
            return _respuesta(False, "La merma no puede ser mayor al stock actual.", {
                "stock_actual": stock_anterior,
                "cantidad_merma": cantidad
            })

        stock_nuevo = stock_anterior - cantidad

        cursor.execute("""
            UPDATE productos
            SET
                stock_actual = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            stock_nuevo,
            producto_id
        ))

        cursor.execute("""
            INSERT INTO movimientos_stock (
                producto_id,
                usuario_id,
                tipo_movimiento,
                cantidad_anterior,
                cantidad_movimiento,
                cantidad_nueva,
                precio_compra,
                referencia,
                comentario
            ) VALUES (
                %s, %s, 'MERMA', %s, %s, %s, %s, %s, %s
            );
        """, (
            producto_id,
            usuario_id,
            stock_anterior,
            cantidad * Decimal("-1"),
            stock_nuevo,
            producto["precio_compra"],
            "MERMA",
            comentario
        ))

        conexion.commit()

        return _respuesta(True, "Merma registrada correctamente.", {
            "producto_id": producto_id,
            "producto": producto["nombre"],
            "stock_anterior": stock_anterior,
            "cantidad_merma": cantidad,
            "stock_nuevo": stock_nuevo
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al registrar merma: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_precio_producto(
    producto_id,
    nuevo_precio_venta,
    nuevo_precio_compra=None
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        nuevo_precio_venta = _decimal(nuevo_precio_venta)

        if nuevo_precio_venta < 0:
            return _respuesta(False, "El precio de venta no puede ser negativo.")

        conexion.start_transaction()

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id = %s
              AND activo = 1
            FOR UPDATE;
        """, (producto_id,))

        producto = cursor.fetchone()

        if producto is None:
            conexion.rollback()
            return _respuesta(False, "Producto no encontrado o inactivo.")

        if nuevo_precio_compra is None:
            cursor.execute("""
                UPDATE productos
                SET
                    precio_venta = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                nuevo_precio_venta,
                producto_id
            ))
        else:
            nuevo_precio_compra = _decimal(nuevo_precio_compra)

            if nuevo_precio_compra < 0:
                conexion.rollback()
                return _respuesta(False, "El precio de compra no puede ser negativo.")

            cursor.execute("""
                UPDATE productos
                SET
                    precio_venta = %s,
                    precio_compra = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                nuevo_precio_venta,
                nuevo_precio_compra,
                producto_id
            ))

        conexion.commit()

        return _respuesta(True, "Precio actualizado correctamente.", {
            "producto_id": producto_id,
            "producto": producto["nombre"],
            "precio_venta_anterior": producto["precio_venta"],
            "precio_venta_nuevo": nuevo_precio_venta
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar precio: {error}")

    finally:
        cursor.close()
        conexion.close()


def obtener_movimientos_stock(producto_id=None, limite=100):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        if producto_id:
            cursor.execute("""
                SELECT
                    ms.id,
                    ms.producto_id,
                    p.nombre AS producto,
                    ms.tipo_movimiento,
                    ms.cantidad_anterior,
                    ms.cantidad_movimiento,
                    ms.cantidad_nueva,
                    ms.precio_compra,
                    ms.referencia,
                    ms.comentario,
                    ms.created_at,
                    u.nombre AS usuario
                FROM movimientos_stock ms
                INNER JOIN productos p
                    ON p.id = ms.producto_id
                INNER JOIN usuarios u
                    ON u.id = ms.usuario_id
                WHERE ms.producto_id = %s
                ORDER BY ms.created_at DESC
                LIMIT %s;
            """, (
                producto_id,
                limite
            ))
        else:
            cursor.execute("""
                SELECT
                    ms.id,
                    ms.producto_id,
                    p.nombre AS producto,
                    ms.tipo_movimiento,
                    ms.cantidad_anterior,
                    ms.cantidad_movimiento,
                    ms.cantidad_nueva,
                    ms.precio_compra,
                    ms.referencia,
                    ms.comentario,
                    ms.created_at,
                    u.nombre AS usuario
                FROM movimientos_stock ms
                INNER JOIN productos p
                    ON p.id = ms.producto_id
                INNER JOIN usuarios u
                    ON u.id = ms.usuario_id
                ORDER BY ms.created_at DESC
                LIMIT %s;
            """, (
                limite,
            ))

        movimientos = cursor.fetchall()

        return _respuesta(True, "Movimientos obtenidos correctamente.", movimientos)

    except Error as error:
        return _respuesta(False, f"Error al obtener movimientos: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def sugerir_reposicion_stock():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.id,
                p.codigo_barra,
                p.nombre,
                c.nombre AS categoria,
                p.stock_actual,
                p.stock_minimo,
                CASE
                    WHEN p.stock_minimo <= 0 THEN 0
                    ELSE (p.stock_minimo * 2) - p.stock_actual
                END AS cantidad_sugerida
            FROM productos p
            LEFT JOIN categorias c
                ON c.id = p.categoria_id
            WHERE p.activo = 1
              AND p.stock_actual <= p.stock_minimo
            ORDER BY p.stock_actual ASC;
        """)

        productos = cursor.fetchall()

        return _respuesta(True, "Sugerencia de reposición generada correctamente.", productos)

    except Error as error:
        return _respuesta(False, f"Error al generar sugerencia de reposición: {error}", [])

    finally:
        cursor.close()
        conexion.close()