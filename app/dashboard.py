from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def obtener_dashboard_principal():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        data = {}

        cursor.execute("""
            SELECT
                id,
                fecha_apertura,
                monto_inicial,
                monto_ventas_total,
                monto_ventas_efectivo,
                monto_ventas_tarjeta,
                monto_ventas_transferencia,
                monto_esperado_caja,
                estado
            FROM caja_turnos
            WHERE estado = 'ABIERTA'
            ORDER BY id DESC
            LIMIT 1;
        """)

        data["caja_actual"] = cursor.fetchone()

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

        data["ventas_hoy"] = cursor.fetchone()

        cursor.execute("""
            SELECT
                COUNT(*) AS productos_bajo_stock
            FROM productos
            WHERE activo = 1
              AND stock_actual <= stock_minimo;
        """)

        data["bajo_stock"] = cursor.fetchone()

        cursor.execute("""
            SELECT
                id,
                numero_venta,
                fecha_venta,
                metodo_pago,
                impuesto_total,
                total,
                estado
            FROM ventas
            WHERE DATE(fecha_venta) = CURDATE()
            ORDER BY fecha_venta DESC
            LIMIT 5;
        """)

        data["ultimas_ventas"] = cursor.fetchall()

        cursor.execute("""
            SELECT
                vd.producto_id,
                vd.nombre_producto,
                SUM(vd.cantidad) AS cantidad_vendida,
                SUM(vd.subtotal_linea) AS total_vendido
            FROM venta_detalle vd
            INNER JOIN ventas v
                ON v.id = vd.venta_id
            WHERE DATE(v.fecha_venta) = CURDATE()
              AND v.estado = 'PAGADA'
            GROUP BY
                vd.producto_id,
                vd.nombre_producto
            ORDER BY cantidad_vendida DESC
            LIMIT 5;
        """)

        data["productos_mas_vendidos_hoy"] = cursor.fetchall()

        return _respuesta(True, "Dashboard generado correctamente.", data)

    except Error as error:
        return _respuesta(False, f"Error al obtener dashboard: {error}")

    finally:
        cursor.close()
        conexion.close()