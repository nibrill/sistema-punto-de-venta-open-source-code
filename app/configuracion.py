from mysql.connector import Error

from app.database import obtener_conexion


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data
    }


def obtener_configuracion_negocio():
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nombre_negocio,
                rut,
                giro,
                direccion,
                comuna,
                ciudad,
                telefono,
                email,
                logo_url,
                moneda,
                impuesto_porcentaje,
                mensaje_ticket,
                created_at,
                updated_at
            FROM negocio_config
            ORDER BY id ASC
            LIMIT 1;
        """)

        config = cursor.fetchone()

        if config is None:
            return _respuesta(False, "No existe configuración del negocio.")

        return _respuesta(True, "Configuración obtenida correctamente.", config)

    except Error as error:
        return _respuesta(False, f"Error al obtener configuración: {error}")

    finally:
        cursor.close()
        conexion.close()


def crear_configuracion_negocio(
    nombre_negocio,
    rut=None,
    giro=None,
    direccion=None,
    comuna=None,
    ciudad=None,
    telefono=None,
    email=None,
    logo_url=None,
    moneda="CLP",
    impuesto_porcentaje=19,
    mensaje_ticket="Gracias por su compra"
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id
            FROM negocio_config
            LIMIT 1;
        """)

        existe = cursor.fetchone()

        if existe:
            return _respuesta(False, "Ya existe una configuración del negocio. Use actualizar_configuracion_negocio().")

        cursor.execute("""
            INSERT INTO negocio_config (
                nombre_negocio,
                rut,
                giro,
                direccion,
                comuna,
                ciudad,
                telefono,
                email,
                logo_url,
                moneda,
                impuesto_porcentaje,
                mensaje_ticket
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """, (
            nombre_negocio,
            rut,
            giro,
            direccion,
            comuna,
            ciudad,
            telefono,
            email,
            logo_url,
            moneda,
            impuesto_porcentaje,
            mensaje_ticket
        ))

        conexion.commit()

        return _respuesta(True, "Configuración creada correctamente.", {
            "configuracion_id": cursor.lastrowid
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear configuración: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_configuracion_negocio(
    nombre_negocio,
    rut=None,
    giro=None,
    direccion=None,
    comuna=None,
    ciudad=None,
    telefono=None,
    email=None,
    logo_url=None,
    moneda="CLP",
    impuesto_porcentaje=19,
    mensaje_ticket="Gracias por su compra"
):
    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id
            FROM negocio_config
            ORDER BY id ASC
            LIMIT 1;
        """)

        config = cursor.fetchone()

        if config is None:
            conexion.rollback()
            return crear_configuracion_negocio(
                nombre_negocio=nombre_negocio,
                rut=rut,
                giro=giro,
                direccion=direccion,
                comuna=comuna,
                ciudad=ciudad,
                telefono=telefono,
                email=email,
                logo_url=logo_url,
                moneda=moneda,
                impuesto_porcentaje=impuesto_porcentaje,
                mensaje_ticket=mensaje_ticket
            )

        cursor.execute("""
            UPDATE negocio_config
            SET
                nombre_negocio = %s,
                rut = %s,
                giro = %s,
                direccion = %s,
                comuna = %s,
                ciudad = %s,
                telefono = %s,
                email = %s,
                logo_url = %s,
                moneda = %s,
                impuesto_porcentaje = %s,
                mensaje_ticket = %s,
                updated_at = NOW()
            WHERE id = %s;
        """, (
            nombre_negocio,
            rut,
            giro,
            direccion,
            comuna,
            ciudad,
            telefono,
            email,
            logo_url,
            moneda,
            impuesto_porcentaje,
            mensaje_ticket,
            config["id"]
        ))

        conexion.commit()

        return _respuesta(True, "Configuración actualizada correctamente.", {
            "configuracion_id": config["id"]
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al actualizar configuración: {error}")

    finally:
        cursor.close()
        conexion.close()