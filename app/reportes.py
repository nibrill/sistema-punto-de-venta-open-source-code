from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def ventas_del_dia():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                v.id,
                v.numero_venta,
                v.fecha_venta,
                u.nombre AS cajero,
                v.metodo_pago,
                v.subtotal,
                v.descuento_total,
                v.impuesto_total,
                v.total,
                v.monto_pagado,
                v.vuelto,
                v.estado
            FROM ventas v
            INNER JOIN usuarios u
                ON u.id = v.usuario_id
            WHERE DATE(v.fecha_venta) = CURDATE()
            ORDER BY v.fecha_venta DESC;
        """)

        ventas = cursor.fetchall()

        return _respuesta(True, "Ventas del día obtenidas correctamente.", ventas)

    except Error as error:
        return _respuesta(False, f"Error al obtener ventas del día: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def resumen_ventas_del_dia():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS cantidad_ventas,
                COALESCE(SUM(subtotal - descuento_total), 0) AS total_neto,
                COALESCE(SUM(impuesto_total), 0) AS total_impuesto,
                COALESCE(SUM(total), 0) AS total_vendido,
                COALESCE(SUM(monto_efectivo - vuelto), 0) AS total_efectivo,
                COALESCE(SUM(monto_tarjeta), 0) AS total_tarjeta,
                COALESCE(SUM(monto_transferencia), 0) AS total_transferencia
            FROM ventas
            WHERE DATE(fecha_venta) = CURDATE()
              AND estado = 'PAGADA';
        """)

        resumen = cursor.fetchone()

        return _respuesta(True, "Resumen de ventas del día obtenido correctamente.", resumen)

    except Error as error:
        return _respuesta(False, f"Error al obtener resumen: {error}")

    finally:
        cursor.close()
        conexion.close()


def ventas_por_rango(fecha_inicio, fecha_fin):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                v.id,
                v.numero_venta,
                v.fecha_venta,
                u.nombre AS cajero,
                v.metodo_pago,
                v.subtotal,
                v.descuento_total,
                v.impuesto_total,
                v.total,
                v.monto_efectivo,
                v.monto_tarjeta,
                v.monto_transferencia,
                v.vuelto,
                v.estado
            FROM ventas v
            INNER JOIN usuarios u
                ON u.id = v.usuario_id
            WHERE DATE(v.fecha_venta) BETWEEN %s AND %s
            ORDER BY v.fecha_venta DESC;
        """, (
            fecha_inicio,
            fecha_fin
        ))

        ventas = cursor.fetchall()

        return _respuesta(True, "Ventas por rango obtenidas correctamente.", ventas)

    except Error as error:
        return _respuesta(False, f"Error al obtener ventas por rango: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def ganancia_por_rango(fecha_inicio, fecha_fin):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS cantidad_ventas,
                COALESCE(SUM(v.total), 0) AS total_vendido,
                COALESCE(SUM(v.subtotal - v.descuento_total), 0) AS total_neto,
                COALESCE(SUM(v.impuesto_total), 0) AS impuesto_total,
                COALESCE(SUM(costos.costo_total), 0) AS costo_total,
                COALESCE(SUM((v.subtotal - v.descuento_total) - IFNULL(costos.costo_total, 0)), 0) AS ganancia_estimada
            FROM ventas v
            LEFT JOIN (
                SELECT
                    venta_id,
                    SUM(precio_compra_unitario * cantidad) AS costo_total
                FROM venta_detalle
                GROUP BY venta_id
            ) costos
                ON costos.venta_id = v.id
            WHERE DATE(v.fecha_venta) BETWEEN %s AND %s
              AND v.estado = 'PAGADA';
        """, (
            fecha_inicio,
            fecha_fin
        ))

        resumen = cursor.fetchone()

        return _respuesta(True, "Ganancia por rango obtenida correctamente.", resumen)

    except Error as error:
        return _respuesta(False, f"Error al obtener ganancia por rango: {error}")

    finally:
        cursor.close()
        conexion.close()


def productos_mas_vendidos(fecha_inicio, fecha_fin, limite=10):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                vd.producto_id,
                vd.codigo_barra,
                vd.nombre_producto,
                SUM(vd.cantidad) AS cantidad_vendida,
                SUM(vd.subtotal_linea) AS total_vendido,
                SUM(vd.subtotal_linea - (vd.precio_compra_unitario * vd.cantidad)) AS ganancia_estimada
            FROM venta_detalle vd
            INNER JOIN ventas v
                ON v.id = vd.venta_id
            WHERE DATE(v.fecha_venta) BETWEEN %s AND %s
              AND v.estado = 'PAGADA'
            GROUP BY
                vd.producto_id,
                vd.codigo_barra,
                vd.nombre_producto
            ORDER BY cantidad_vendida DESC
            LIMIT %s;
        """, (
            fecha_inicio,
            fecha_fin,
            limite
        ))

        productos = cursor.fetchall()

        return _respuesta(True, "Productos más vendidos obtenidos correctamente.", productos)

    except Error as error:
        return _respuesta(False, f"Error al obtener productos más vendidos: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def productos_bajo_stock():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.id,
                p.codigo_barra,
                p.sku,
                p.nombre,
                c.nombre AS categoria,
                p.stock_actual,
                p.stock_minimo,
                p.precio_venta,
                p.activo
            FROM productos p
            LEFT JOIN categorias c
                ON c.id = p.categoria_id
            WHERE p.stock_actual <= p.stock_minimo
              AND p.activo = 1
            ORDER BY p.stock_actual ASC;
        """)

        productos = cursor.fetchall()

        return _respuesta(True, "Productos con bajo stock obtenidos correctamente.", productos)

    except Error as error:
        return _respuesta(False, f"Error al obtener bajo stock: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def movimientos_stock_producto(producto_id):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.", [])

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                ms.id,
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
            INNER JOIN usuarios u
                ON u.id = ms.usuario_id
            WHERE ms.producto_id = %s
            ORDER BY ms.created_at DESC;
        """, (producto_id,))

        movimientos = cursor.fetchall()

        return _respuesta(True, "Movimientos de stock obtenidos correctamente.", movimientos)

    except Error as error:
        return _respuesta(False, f"Error al obtener movimientos de stock: {error}", [])

    finally:
        cursor.close()
        conexion.close()


def resumen_caja_actual():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                ct.id,
                ct.fecha_apertura,
                ct.fecha_cierre,
                ua.nombre AS usuario_apertura,
                uc.nombre AS usuario_cierre,
                ct.monto_inicial,
                ct.monto_ventas_efectivo,
                ct.monto_ventas_tarjeta,
                ct.monto_ventas_transferencia,
                ct.monto_ventas_total,
                ct.monto_retiros,
                ct.monto_ingresos_extra,
                ct.monto_esperado_caja,
                ct.monto_real_cierre,
                ct.diferencia,
                ct.estado
            FROM caja_turnos ct
            INNER JOIN usuarios ua
                ON ua.id = ct.usuario_apertura_id
            LEFT JOIN usuarios uc
                ON uc.id = ct.usuario_cierre_id
            WHERE ct.estado = 'ABIERTA'
            ORDER BY ct.id DESC
            LIMIT 1;
        """)

        caja = cursor.fetchone()

        if caja is None:
            return _respuesta(True, "No hay caja abierta.", None)

        return _respuesta(True, "Resumen de caja obtenido correctamente.", caja)

    except Error as error:
        return _respuesta(False, f"Error al obtener resumen de caja: {error}")

    finally:
        cursor.close()
        conexion.close()