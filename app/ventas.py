from decimal import Decimal
from datetime import datetime
import random

from app.database import obtener_conexion
from app.caja import recalcular_totales_caja
from app.impuestos import calcular_totales_venta, dinero


def _respuesta(ok, mensaje="", data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def _decimal(valor):
    try:
        return Decimal(str(valor or 0))
    except Exception:
        return Decimal("0")


def _cursor_dict(conexion):
    return conexion.cursor(dictionary=True)


def _generar_numero_venta():
    fecha = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(100, 999)
    return f"V-{fecha}-{random_num}"


def _obtener_caja_abierta(cursor):
    cursor.execute(
        """
        SELECT *
        FROM caja_turnos
        WHERE estado = 'ABIERTA'
        ORDER BY id DESC
        LIMIT 1
        FOR UPDATE
        """
    )
    return cursor.fetchone()


def _obtener_producto_para_venta(cursor, item):
    producto_id = item.get("producto_id") or item.get("id")
    codigo_barra = item.get("codigo_barra")

    if producto_id:
        cursor.execute(
            """
            SELECT *
            FROM productos
            WHERE id = %s
            AND activo = 1
            LIMIT 1
            FOR UPDATE
            """,
            (producto_id,)
        )
        return cursor.fetchone()

    if codigo_barra:
        cursor.execute(
            """
            SELECT *
            FROM productos
            WHERE codigo_barra = %s
            AND activo = 1
            LIMIT 1
            FOR UPDATE
            """,
            (codigo_barra,)
        )
        return cursor.fetchone()

    return None


def _normalizar_item(cursor, item):
    producto = _obtener_producto_para_venta(cursor, item)

    if not producto:
        return None, "Producto no encontrado o inactivo."

    cantidad = _decimal(item.get("cantidad"))
    precio_unitario = _decimal(item.get("precio_unitario") or producto.get("precio_venta"))
    precio_compra = _decimal(item.get("precio_compra_unitario") or producto.get("precio_compra"))
    descuento_linea = _decimal(item.get("descuento_linea"))
    subtotal_bruto_linea = dinero(cantidad * precio_unitario)

    if cantidad <= 0:
        return None, f"Cantidad inválida para {producto.get('nombre')}."

    if descuento_linea < 0:
        return None, f"El descuento no puede ser negativo para {producto.get('nombre')}."

    if descuento_linea > subtotal_bruto_linea:
        return None, f"El descuento no puede superar el subtotal de {producto.get('nombre')}."

    subtotal_linea = dinero(subtotal_bruto_linea - descuento_linea)

    stock_actual = _decimal(producto.get("stock_actual"))
    permite_sin_stock = int(producto.get("permite_venta_sin_stock") or 0) == 1

    if not permite_sin_stock and cantidad > stock_actual:
        return None, (
            f"Stock insuficiente para {producto.get('nombre')}. "
            f"Stock actual: {stock_actual}"
        )

    item_normalizado = {
        "producto": producto,
        "producto_id": producto["id"],
        "codigo_barra": producto["codigo_barra"],
        "nombre_producto": producto["nombre"],
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "precio_compra_unitario": precio_compra,
        "descuento_linea": descuento_linea,
        "subtotal_linea": subtotal_linea,
        "stock_anterior": stock_actual,
        "stock_nuevo": stock_actual - cantidad
    }

    return item_normalizado, None


def _calcular_pago(total, metodo_pago, monto_efectivo, monto_tarjeta, monto_transferencia):
    metodo_pago = str(metodo_pago or "EFECTIVO").upper()

    monto_efectivo = _decimal(monto_efectivo)
    monto_tarjeta = _decimal(monto_tarjeta)
    monto_transferencia = _decimal(monto_transferencia)

    if metodo_pago == "EFECTIVO":
        monto_tarjeta = Decimal("0")
        monto_transferencia = Decimal("0")

    elif metodo_pago == "TARJETA":
        monto_efectivo = Decimal("0")
        monto_tarjeta = total
        monto_transferencia = Decimal("0")

    elif metodo_pago == "TRANSFERENCIA":
        monto_efectivo = Decimal("0")
        monto_tarjeta = Decimal("0")
        monto_transferencia = total

    elif metodo_pago == "MIXTO":
        pass

    else:
        metodo_pago = "EFECTIVO"
        monto_tarjeta = Decimal("0")
        monto_transferencia = Decimal("0")

    monto_pagado = monto_efectivo + monto_tarjeta + monto_transferencia

    if monto_pagado < total:
        return None, "El monto pagado es menor al total de la venta."

    vuelto = monto_pagado - total

    if vuelto > monto_efectivo:
        return None, "El vuelto no puede ser mayor que el efectivo recibido."

    efectivo_neto = monto_efectivo - vuelto

    return {
        "metodo_pago": metodo_pago,
        "monto_efectivo": monto_efectivo,
        "monto_tarjeta": monto_tarjeta,
        "monto_transferencia": monto_transferencia,
        "monto_pagado": monto_pagado,
        "vuelto": vuelto,
        "efectivo_neto": efectivo_neto
    }, None


def realizar_venta(
    usuario_id,
    items,
    metodo_pago="EFECTIVO",
    monto_efectivo=0,
    monto_tarjeta=0,
    monto_transferencia=0,
    tipo_documento="TICKET",
    numero_documento=None,
    descuento_total=0,
    observacion=None
):
    conexion = obtener_conexion()
    cursor = None

    try:
        if not items:
            return _respuesta(False, "No hay productos para vender.", None)

        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        caja = _obtener_caja_abierta(cursor)

        if not caja:
            conexion.rollback()
            return _respuesta(False, "Debe abrir caja antes de realizar una venta.", None)

        caja_turno_id = caja["id"]

        items_normalizados = []
        errores = []

        for item in items:
            item_normalizado, error = _normalizar_item(cursor, item)

            if error:
                errores.append(error)
            else:
                items_normalizados.append(item_normalizado)

        if errores:
            conexion.rollback()
            return _respuesta(False, "\n".join(errores), None)

        subtotal = sum(dinero(item["cantidad"] * item["precio_unitario"]) for item in items_normalizados)
        descuento_lineas = sum(item["descuento_linea"] for item in items_normalizados)
        descuento_total = _decimal(descuento_total) + descuento_lineas

        totales_venta = calcular_totales_venta(
            subtotal=subtotal,
            descuento_total=descuento_total
        )

        subtotal = totales_venta["subtotal"]
        descuento_total = totales_venta["descuento_total"]
        neto_gravado = totales_venta["neto_gravado"]
        impuesto_total = totales_venta["impuesto_total"]
        impuesto_porcentaje = totales_venta["impuesto_porcentaje"]
        total = totales_venta["total"]

        if total <= 0:
            conexion.rollback()
            return _respuesta(False, "El total de la venta debe ser mayor a 0.", None)

        pago, error_pago = _calcular_pago(
            total=total,
            metodo_pago=metodo_pago,
            monto_efectivo=monto_efectivo,
            monto_tarjeta=monto_tarjeta,
            monto_transferencia=monto_transferencia
        )

        if error_pago:
            conexion.rollback()
            return _respuesta(False, error_pago, None)

        numero_venta = _generar_numero_venta()
        tipo_documento = str(tipo_documento or "TICKET").upper()

        if tipo_documento not in ["TICKET", "BOLETA", "FACTURA"]:
            tipo_documento = "TICKET"

        cursor.execute(
            """
            INSERT INTO ventas
            (
                caja_turno_id,
                usuario_id,
                numero_venta,
                tipo_documento,
                numero_documento,
                fecha_venta,
                subtotal,
                descuento_total,
                impuesto_total,
                total,
                metodo_pago,
                monto_efectivo,
                monto_tarjeta,
                monto_transferencia,
                monto_pagado,
                vuelto,
                estado,
                observacion
            )
            VALUES
            (
                %s, %s, %s, %s, %s, NOW(),
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                'PAGADA',
                %s
            )
            """,
            (
                caja_turno_id,
                usuario_id,
                numero_venta,
                tipo_documento,
                numero_documento,
                subtotal,
                descuento_total,
                impuesto_total,
                total,
                pago["metodo_pago"],
                pago["monto_efectivo"],
                pago["monto_tarjeta"],
                pago["monto_transferencia"],
                pago["monto_pagado"],
                pago["vuelto"],
                observacion
            )
        )

        venta_id = cursor.lastrowid

        for item in items_normalizados:
            producto = item["producto"]

            cursor.execute(
                """
                INSERT INTO venta_detalle
                (
                    venta_id,
                    producto_id,
                    codigo_barra,
                    nombre_producto,
                    cantidad,
                    precio_unitario,
                    precio_compra_unitario,
                    descuento_linea,
                    subtotal_linea
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    venta_id,
                    item["producto_id"],
                    item["codigo_barra"],
                    item["nombre_producto"],
                    item["cantidad"],
                    item["precio_unitario"],
                    item["precio_compra_unitario"],
                    item["descuento_linea"],
                    item["subtotal_linea"]
                )
            )

            if int(producto.get("permite_venta_sin_stock") or 0) == 0:
                cursor.execute(
                    """
                    UPDATE productos
                    SET stock_actual = stock_actual - %s
                    WHERE id = %s
                    """,
                    (item["cantidad"], item["producto_id"])
                )

                cursor.execute(
                    """
                    INSERT INTO movimientos_stock
                    (
                        producto_id,
                        usuario_id,
                        tipo_movimiento,
                        cantidad_anterior,
                        cantidad_movimiento,
                        cantidad_nueva,
                        precio_compra,
                        referencia,
                        comentario
                    )
                    VALUES
                    (%s, %s, 'VENTA', %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        item["producto_id"],
                        usuario_id,
                        item["stock_anterior"],
                        item["cantidad"],
                        item["stock_nuevo"],
                        item["precio_compra_unitario"],
                        f"VENTA {numero_venta}",
                        "Salida de stock por venta"
                    )
                )

        recalcular_totales_caja(caja_turno_id, conexion)

        conexion.commit()

        return _respuesta(
            True,
            "Venta realizada correctamente.",
            {
                "venta_id": venta_id,
                "id": venta_id,
                "caja_turno_id": caja_turno_id,
                "numero_venta": numero_venta,
                "subtotal": subtotal,
                "descuento_total": descuento_total,
                "impuesto_porcentaje": impuesto_porcentaje,
                "impuesto_total": impuesto_total,
                "neto_gravado": neto_gravado,
                "total": total,
                "metodo_pago": pago["metodo_pago"],
                "monto_efectivo": pago["monto_efectivo"],
                "monto_tarjeta": pago["monto_tarjeta"],
                "monto_transferencia": pago["monto_transferencia"],
                "monto_pagado": pago["monto_pagado"],
                "vuelto": pago["vuelto"]
            }
        )

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error realizando venta: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def obtener_venta(venta_id):
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)

        cursor.execute(
            """
            SELECT
                v.*,
                u.nombre AS usuario_nombre,
                ct.fecha_apertura AS caja_fecha_apertura
            FROM ventas v
            LEFT JOIN usuarios u ON u.id = v.usuario_id
            LEFT JOIN caja_turnos ct ON ct.id = v.caja_turno_id
            WHERE v.id = %s
            LIMIT 1
            """,
            (venta_id,)
        )

        venta = cursor.fetchone()

        if not venta:
            return _respuesta(False, "Venta no encontrada.", None)

        cursor.execute(
            """
            SELECT *
            FROM venta_detalle
            WHERE venta_id = %s
            ORDER BY id ASC
            """,
            (venta_id,)
        )

        detalle = cursor.fetchall() or []
        venta["detalle"] = detalle

        return _respuesta(True, "Venta obtenida correctamente.", venta)

    except Exception as error:
        return _respuesta(False, f"Error obteniendo venta: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def obtener_venta_por_numero(numero_venta):
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)

        cursor.execute(
            """
            SELECT id
            FROM ventas
            WHERE numero_venta = %s
            LIMIT 1
            """,
            (numero_venta,)
        )

        venta = cursor.fetchone()

        if not venta:
            return _respuesta(False, "Venta no encontrada.", None)

        return obtener_venta(venta["id"])

    except Exception as error:
        return _respuesta(False, f"Error buscando venta: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def listar_ventas_del_dia():
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)

        cursor.execute(
            """
            SELECT
                v.*,
                u.nombre AS usuario_nombre
            FROM ventas v
            LEFT JOIN usuarios u ON u.id = v.usuario_id
            WHERE DATE(v.fecha_venta) = CURDATE()
            ORDER BY v.fecha_venta DESC
            """
        )

        ventas = cursor.fetchall() or []

        return _respuesta(True, "Ventas del día obtenidas correctamente.", ventas)

    except Exception as error:
        return _respuesta(False, f"Error listando ventas del día: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def anular_venta(venta_id, usuario_id, motivo, devolver_stock=True):
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        cursor.execute(
            """
            SELECT *
            FROM ventas
            WHERE id = %s
            FOR UPDATE
            """,
            (venta_id,)
        )

        venta = cursor.fetchone()

        if not venta:
            conexion.rollback()
            return _respuesta(False, "Venta no encontrada.", None)

        if venta.get("estado") != "PAGADA":
            conexion.rollback()
            return _respuesta(False, "Solo se pueden anular ventas pagadas.", None)

        cursor.execute(
            """
            UPDATE ventas
            SET estado = 'ANULADA',
                motivo_anulacion = %s
            WHERE id = %s
            """,
            (motivo, venta_id)
        )

        if devolver_stock:
            cursor.execute(
                """
                SELECT *
                FROM venta_detalle
                WHERE venta_id = %s
                """,
                (venta_id,)
            )

            detalles = cursor.fetchall() or []

            for detalle in detalles:
                cursor.execute(
                    """
                    SELECT stock_actual, precio_compra
                    FROM productos
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (detalle["producto_id"],)
                )

                producto = cursor.fetchone()

                if not producto:
                    continue

                stock_anterior = _decimal(producto.get("stock_actual"))
                cantidad = _decimal(detalle.get("cantidad"))
                stock_nuevo = stock_anterior + cantidad

                cursor.execute(
                    """
                    UPDATE productos
                    SET stock_actual = stock_actual + %s
                    WHERE id = %s
                    """,
                    (cantidad, detalle["producto_id"])
                )

                cursor.execute(
                    """
                    INSERT INTO movimientos_stock
                    (
                        producto_id,
                        usuario_id,
                        tipo_movimiento,
                        cantidad_anterior,
                        cantidad_movimiento,
                        cantidad_nueva,
                        precio_compra,
                        referencia,
                        comentario
                    )
                    VALUES
                    (%s, %s, 'DEVOLUCION', %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        detalle["producto_id"],
                        usuario_id,
                        stock_anterior,
                        cantidad,
                        stock_nuevo,
                        producto.get("precio_compra"),
                        f"ANULACION VENTA {venta.get('numero_venta')}",
                        motivo or "Anulación de venta"
                    )
                )

        recalcular_totales_caja(venta["caja_turno_id"], conexion)

        conexion.commit()

        return _respuesta(
            True,
            "Venta anulada correctamente.",
            {
                "venta_id": venta_id,
                "caja_turno_id": venta["caja_turno_id"]
            }
        )

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error anulando venta: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()