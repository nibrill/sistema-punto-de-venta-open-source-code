from decimal import Decimal

from app.database import obtener_conexion


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


def _obtener_caja_abierta_cursor(cursor, bloquear=False):
    sql = """
        SELECT
            ct.id,
            ct.id AS caja_id,
            ct.id AS turno_id,
            ct.usuario_apertura_id,
            ua.nombre AS usuario_apertura,
            ct.usuario_cierre_id,
            uc.nombre AS usuario_cierre,
            ct.fecha_apertura,
            ct.fecha_cierre,
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
            ct.estado,
            ct.observacion_apertura,
            ct.observacion_cierre,
            ct.created_at
        FROM caja_turnos ct
        LEFT JOIN usuarios ua ON ua.id = ct.usuario_apertura_id
        LEFT JOIN usuarios uc ON uc.id = ct.usuario_cierre_id
        WHERE ct.estado = 'ABIERTA'
        ORDER BY ct.id DESC
        LIMIT 1
    """

    if bloquear:
        sql += " FOR UPDATE"

    cursor.execute(sql)
    return cursor.fetchone()


def _obtener_caja_por_id_cursor(cursor, caja_id):
    cursor.execute(
        """
        SELECT
            ct.id,
            ct.id AS caja_id,
            ct.id AS turno_id,
            ct.usuario_apertura_id,
            ua.nombre AS usuario_apertura,
            ct.usuario_cierre_id,
            uc.nombre AS usuario_cierre,
            ct.fecha_apertura,
            ct.fecha_cierre,
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
            ct.estado,
            ct.observacion_apertura,
            ct.observacion_cierre,
            ct.created_at
        FROM caja_turnos ct
        LEFT JOIN usuarios ua ON ua.id = ct.usuario_apertura_id
        LEFT JOIN usuarios uc ON uc.id = ct.usuario_cierre_id
        WHERE ct.id = %s
        LIMIT 1
        """,
        (caja_id,)
    )

    return cursor.fetchone()


def recalcular_totales_caja(caja_turno_id, conexion_externa=None):
    conexion = conexion_externa or obtener_conexion()
    cursor = None
    cerrar_conexion = conexion_externa is None

    try:
        cursor = _cursor_dict(conexion)

        cursor.execute(
            """
            SELECT
                IFNULL(SUM(total), 0) AS ventas_total,
                IFNULL(SUM(monto_efectivo - vuelto), 0) AS ventas_efectivo,
                IFNULL(SUM(monto_tarjeta), 0) AS ventas_tarjeta,
                IFNULL(SUM(monto_transferencia), 0) AS ventas_transferencia
            FROM ventas
            WHERE caja_turno_id = %s
            AND estado = 'PAGADA'
            """,
            (caja_turno_id,)
        )

        totales = cursor.fetchone() or {}

        ventas_total = _decimal(totales.get("ventas_total"))
        ventas_efectivo = _decimal(totales.get("ventas_efectivo"))
        ventas_tarjeta = _decimal(totales.get("ventas_tarjeta"))
        ventas_transferencia = _decimal(totales.get("ventas_transferencia"))

        cursor.execute(
            """
            SELECT
                monto_inicial,
                monto_ingresos_extra,
                monto_retiros
            FROM caja_turnos
            WHERE id = %s
            LIMIT 1
            """,
            (caja_turno_id,)
        )

        caja = cursor.fetchone()

        if not caja:
            return _respuesta(False, "Caja no encontrada.", None)

        monto_inicial = _decimal(caja.get("monto_inicial"))
        ingresos_extra = _decimal(caja.get("monto_ingresos_extra"))
        retiros = _decimal(caja.get("monto_retiros"))

        efectivo_esperado = monto_inicial + ventas_efectivo + ingresos_extra - retiros

        cursor.execute(
            """
            UPDATE caja_turnos
            SET
                monto_ventas_efectivo = %s,
                monto_ventas_tarjeta = %s,
                monto_ventas_transferencia = %s,
                monto_ventas_total = %s,
                monto_esperado_caja = %s
            WHERE id = %s
            """,
            (
                ventas_efectivo,
                ventas_tarjeta,
                ventas_transferencia,
                ventas_total,
                efectivo_esperado,
                caja_turno_id
            )
        )

        if cerrar_conexion:
            conexion.commit()

        return _respuesta(
            True,
            "Totales de caja recalculados.",
            {
                "caja_turno_id": caja_turno_id,
                "monto_ventas_efectivo": ventas_efectivo,
                "monto_ventas_tarjeta": ventas_tarjeta,
                "monto_ventas_transferencia": ventas_transferencia,
                "monto_ventas_total": ventas_total,
                "monto_esperado_caja": efectivo_esperado
            }
        )

    except Exception as error:
        if cerrar_conexion and conexion:
            conexion.rollback()

        return _respuesta(False, f"Error recalculando caja: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if cerrar_conexion and conexion:
            conexion.close()


def abrir_caja(usuario_id, monto_inicial=0, observacion_apertura=None):
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        caja_abierta = _obtener_caja_abierta_cursor(cursor, bloquear=True)

        if caja_abierta:
            conexion.rollback()
            return _respuesta(
                False,
                f"Ya existe una caja abierta. Turno actual ID: {caja_abierta.get('id')}",
                caja_abierta
            )

        monto_inicial = _decimal(monto_inicial)

        cursor.execute(
            """
            INSERT INTO caja_turnos
            (
                usuario_apertura_id,
                fecha_apertura,
                monto_inicial,
                monto_ventas_efectivo,
                monto_ventas_tarjeta,
                monto_ventas_transferencia,
                monto_ventas_total,
                monto_retiros,
                monto_ingresos_extra,
                monto_esperado_caja,
                estado,
                observacion_apertura
            )
            VALUES
            (
                %s,
                NOW(),
                %s,
                0,
                0,
                0,
                0,
                0,
                0,
                %s,
                'ABIERTA',
                %s
            )
            """,
            (
                usuario_id,
                monto_inicial,
                monto_inicial,
                observacion_apertura
            )
        )

        caja_id = cursor.lastrowid
        conexion.commit()

        return obtener_caja_por_id(caja_id)

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error abriendo caja: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def obtener_caja_abierta():
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)
        caja = _obtener_caja_abierta_cursor(cursor)

        if not caja:
            return _respuesta(False, "No hay caja abierta.", None)

        recalcular_totales_caja(caja["id"], conexion)

        caja = _obtener_caja_por_id_cursor(cursor, caja["id"])

        return _respuesta(
            True,
            "Caja abierta obtenida correctamente.",
            caja
        )

    except Exception as error:
        return _respuesta(False, f"Error obteniendo caja abierta: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def obtener_caja_por_id(caja_id):
    conexion = obtener_conexion()
    cursor = None

    try:
        cursor = _cursor_dict(conexion)

        caja = _obtener_caja_por_id_cursor(cursor, caja_id)

        if not caja:
            return _respuesta(False, "Caja no encontrada.", None)

        return _respuesta(True, "Caja obtenida correctamente.", caja)

    except Exception as error:
        return _respuesta(False, f"Error obteniendo caja: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def obtener_resumen_caja_actual():
    return obtener_caja_abierta()


def registrar_ingreso_extra(monto, descripcion=None):
    conexion = obtener_conexion()
    cursor = None

    try:
        monto = _decimal(monto)

        if monto <= 0:
            return _respuesta(False, "El monto del ingreso debe ser mayor a 0.", None)

        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        caja = _obtener_caja_abierta_cursor(cursor, bloquear=True)

        if not caja:
            conexion.rollback()
            return _respuesta(False, "Debe abrir caja antes de registrar ingresos.", None)

        caja_id = caja["id"]

        cursor.execute(
            """
            UPDATE caja_turnos
            SET monto_ingresos_extra = monto_ingresos_extra + %s
            WHERE id = %s
            """,
            (monto, caja_id)
        )

        recalcular_totales_caja(caja_id, conexion)

        conexion.commit()

        return obtener_caja_por_id(caja_id)

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error registrando ingreso extra: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def registrar_retiro(monto, descripcion=None):
    conexion = obtener_conexion()
    cursor = None

    try:
        monto = _decimal(monto)

        if monto <= 0:
            return _respuesta(False, "El monto del retiro debe ser mayor a 0.", None)

        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        caja = _obtener_caja_abierta_cursor(cursor, bloquear=True)

        if not caja:
            conexion.rollback()
            return _respuesta(False, "Debe abrir caja antes de registrar retiros.", None)

        caja_id = caja["id"]

        recalcular_totales_caja(caja_id, conexion)

        caja = _obtener_caja_por_id_cursor(cursor, caja_id)
        monto_esperado = _decimal(caja.get("monto_esperado_caja"))

        if monto > monto_esperado:
            conexion.rollback()
            return _respuesta(
                False,
                "No puedes retirar más dinero que el efectivo esperado en caja.",
                None
            )

        cursor.execute(
            """
            UPDATE caja_turnos
            SET monto_retiros = monto_retiros + %s
            WHERE id = %s
            """,
            (monto, caja_id)
        )

        recalcular_totales_caja(caja_id, conexion)

        conexion.commit()

        return obtener_caja_por_id(caja_id)

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error registrando retiro: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


def cerrar_caja(usuario_cierre_id, monto_real_cierre, observacion_cierre=None):
    conexion = obtener_conexion()
    cursor = None

    try:
        monto_real_cierre = _decimal(monto_real_cierre)

        cursor = _cursor_dict(conexion)
        conexion.start_transaction()

        caja = _obtener_caja_abierta_cursor(cursor, bloquear=True)

        if not caja:
            conexion.rollback()
            return _respuesta(False, "No hay caja abierta para cerrar.", None)

        caja_id = caja["id"]

        recalcular_totales_caja(caja_id, conexion)

        caja = _obtener_caja_por_id_cursor(cursor, caja_id)
        efectivo_esperado = _decimal(caja.get("monto_esperado_caja"))

        diferencia = monto_real_cierre - efectivo_esperado

        cursor.execute(
            """
            UPDATE caja_turnos
            SET
                usuario_cierre_id = %s,
                fecha_cierre = NOW(),
                monto_real_cierre = %s,
                diferencia = %s,
                estado = 'CERRADA',
                observacion_cierre = %s
            WHERE id = %s
            """,
            (
                usuario_cierre_id,
                monto_real_cierre,
                diferencia,
                observacion_cierre,
                caja_id
            )
        )

        conexion.commit()

        return obtener_caja_por_id(caja_id)

    except Exception as error:
        if conexion:
            conexion.rollback()

        return _respuesta(False, f"Error cerrando caja: {error}", None)

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()

