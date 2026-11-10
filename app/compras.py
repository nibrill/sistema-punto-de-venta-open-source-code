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


def registrar_compra(usuario_id, proveedor_id=None, numero_documento=None, items=None, observacion=None):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    if not items:
        return _respuesta(False, "La compra debe tener productos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        conexion.start_transaction()

        productos_compra = []
        subtotal = Decimal("0")

        for item in items:
            producto_id = item.get("producto_id")
            codigo_barra = item.get("codigo_barra")
            cantidad = _decimal(item.get("cantidad"))
            costo_unitario = _decimal(item.get("costo_unitario"))

            if cantidad <= 0:
                conexion.rollback()
                return _respuesta(False, "La cantidad debe ser mayor a cero.", item)

            if producto_id:
                cursor.execute("""
                    SELECT *
                    FROM productos
                    WHERE id = %s
                      AND activo = 1
                    FOR UPDATE;
                """, (producto_id,))
            else:
                cursor.execute("""
                    SELECT *
                    FROM productos
                    WHERE codigo_barra = %s
                      AND activo = 1
                    FOR UPDATE;
                """, (codigo_barra,))

            producto = cursor.fetchone()

            if producto is None:
                conexion.rollback()
                return _respuesta(False, "Producto no encontrado o inactivo.", item)

            if costo_unitario <= 0:
                costo_unitario = _decimal(producto["precio_compra"])

            total_linea = cantidad * costo_unitario
            subtotal += total_linea

            productos_compra.append({
                "producto": producto,
                "cantidad": cantidad,
                "costo_unitario": costo_unitario,
                "total_linea": total_linea,
                "stock_anterior": _decimal(producto["stock_actual"]),
                "stock_nuevo": _decimal(producto["stock_actual"]) + cantidad
            })

        total = subtotal

        cursor.execute("""
            INSERT INTO compras (
                proveedor_id,
                usuario_id,
                numero_documento,
                fecha_compra,
                subtotal,
                total,
                estado,
                observacion
            ) VALUES (
                %s, %s, %s, NOW(), %s, %s, 'RECIBIDA', %s
            );
        """, (
            proveedor_id,
            usuario_id,
            numero_documento,
            subtotal,
            total,
            observacion
        ))

        compra_id = cursor.lastrowid

        for item in productos_compra:
            producto = item["producto"]

            cursor.execute("""
                INSERT INTO compra_detalle (
                    compra_id,
                    producto_id,
                    codigo_barra,
                    nombre_producto,
                    cantidad,
                    costo_unitario,
                    total_linea
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                );
            """, (
                compra_id,
                producto["id"],
                producto["codigo_barra"],
                producto["nombre"],
                item["cantidad"],
                item["costo_unitario"],
                item["total_linea"]
            ))

            cursor.execute("""
                UPDATE productos
                SET
                    stock_actual = stock_actual + %s,
                    precio_compra = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                item["cantidad"],
                item["costo_unitario"],
                producto["id"]
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
                producto["id"],
                usuario_id,
                item["stock_anterior"],
                item["cantidad"],
                item["stock_nuevo"],
                item["costo_unitario"],
                f"COMPRA {compra_id}",
                observacion or "Ingreso por compra"
            ))

        conexion.commit()

        return _respuesta(True, "Compra registrada correctamente.", {
            "compra_id": compra_id,
            "subtotal": subtotal,
            "total": total
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al registrar compra: {error}")

    finally:
        cursor.close()
        conexion.close()


def listar_compras():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                c.id,
                c.numero_documento,
                c.fecha_compra,
                c.subtotal,
                c.total,
                c.estado,
                c.observacion,
                p.nombre AS proveedor,
                u.nombre AS usuario
            FROM compras c
            LEFT JOIN proveedores p
                ON p.id = c.proveedor_id
            INNER JOIN usuarios u
                ON u.id = c.usuario_id
            ORDER BY c.fecha_compra DESC;
        """)

        return _respuesta(True, "Compras obtenidas correctamente.", cursor.fetchall())

    except Error as error:
        return _respuesta(False, f"Error al listar compras: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def obtener_compra(compra_id):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                c.*,
                p.nombre AS proveedor,
                u.nombre AS usuario
            FROM compras c
            LEFT JOIN proveedores p
                ON p.id = c.proveedor_id
            INNER JOIN usuarios u
                ON u.id = c.usuario_id
            WHERE c.id = %s;
        """, (compra_id,))

        compra = cursor.fetchone()

        if compra is None:
            return _respuesta(False, "Compra no encontrada.")

        cursor.execute("""
            SELECT *
            FROM compra_detalle
            WHERE compra_id = %s
            ORDER BY id ASC;
        """, (compra_id,))

        compra["detalle"] = cursor.fetchall()

        return _respuesta(True, "Compra obtenida correctamente.", compra)

    except Error as error:
        return _respuesta(False, f"Error al obtener compra: {error}")

    finally:
        cursor.close()
        conexion.close()