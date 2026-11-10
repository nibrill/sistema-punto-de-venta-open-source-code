from decimal import Decimal

from app.ventas import obtener_venta
from app.configuracion import obtener_configuracion_negocio
from app.impuestos import IVA_PORCENTAJE_DEFECTO, decimal_seguro


def _formatear_pesos(valor):
    valor = Decimal(str(valor or 0))
    return f"${int(valor):,}".replace(",", ".")


def _formatear_porcentaje(valor):
    porcentaje = decimal_seguro(valor, IVA_PORCENTAJE_DEFECTO)
    if porcentaje == porcentaje.to_integral_value():
        return str(int(porcentaje))
    return f"{porcentaje:.2f}".rstrip("0").rstrip(".")


def _formatear_fecha(fecha):
    if fecha is None:
        return ""

    try:
        return fecha.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(fecha)


def generar_ticket_texto(venta_id):
    venta_resultado = obtener_venta(venta_id)

    if not venta_resultado["ok"]:
        return {
            "ok": False,
            "mensaje": venta_resultado["mensaje"],
            "data": None
        }

    config_resultado = obtener_configuracion_negocio()

    if config_resultado["ok"]:
        config = config_resultado["data"]
    else:
        config = {
            "nombre_negocio": "POS PYMES",
            "rut": "",
            "giro": "",
            "direccion": "",
            "comuna": "",
            "ciudad": "",
            "telefono": "",
            "impuesto_porcentaje": IVA_PORCENTAJE_DEFECTO,
            "mensaje_ticket": "Gracias por su compra"
        }

    venta = venta_resultado["data"]
    detalle = venta.get("detalle", [])

    impuesto_porcentaje = config.get("impuesto_porcentaje") or IVA_PORCENTAJE_DEFECTO
    subtotal = decimal_seguro(venta.get("subtotal"))
    descuento_total = decimal_seguro(venta.get("descuento_total"))
    impuesto_total = decimal_seguro(venta.get("impuesto_total"))
    neto_gravado = subtotal - descuento_total

    if neto_gravado < 0:
        neto_gravado = Decimal("0")

    lineas = []

    lineas.append("=" * 42)
    lineas.append(str(config.get("nombre_negocio") or "POS PYMES").center(42))

    if config.get("rut"):
        lineas.append(f"RUT: {config.get('rut')}".center(42))

    if config.get("giro"):
        lineas.append(str(config.get("giro")).center(42))

    direccion = " ".join([
        str(config.get("direccion") or ""),
        str(config.get("comuna") or ""),
        str(config.get("ciudad") or "")
    ]).strip()

    if direccion:
        lineas.append(direccion.center(42))

    if config.get("telefono"):
        lineas.append(f"Tel: {config.get('telefono')}".center(42))

    lineas.append("=" * 42)
    lineas.append(f"Venta: {venta.get('numero_venta')}")
    lineas.append(f"Fecha: {_formatear_fecha(venta.get('fecha_venta'))}")
    lineas.append(f"Cajero: {venta.get('usuario_nombre') or venta.get('nombre_usuario') or '-'}")
    lineas.append(f"Documento: {venta.get('tipo_documento')}")
    lineas.append("-" * 42)

    for item in detalle:
        nombre = str(item.get("nombre_producto") or "")[:28]
        cantidad = item.get("cantidad")
        precio = _formatear_pesos(item.get("precio_unitario"))
        subtotal_linea = _formatear_pesos(item.get("subtotal_linea"))

        lineas.append(nombre)
        lineas.append(f"{cantidad} x {precio}".ljust(22) + subtotal_linea.rjust(20))

    lineas.append("-" * 42)
    lineas.append("Subtotal neto:".ljust(22) + _formatear_pesos(subtotal).rjust(20))
    lineas.append("Descuento:".ljust(22) + _formatear_pesos(descuento_total).rjust(20))
    lineas.append("Neto gravado:".ljust(22) + _formatear_pesos(neto_gravado).rjust(20))
    lineas.append((f"IVA {_formatear_porcentaje(impuesto_porcentaje)}%:").ljust(22) + _formatear_pesos(impuesto_total).rjust(20))
    lineas.append("TOTAL:".ljust(22) + _formatear_pesos(venta.get("total")).rjust(20))
    lineas.append("-" * 42)
    lineas.append(f"Método pago: {venta.get('metodo_pago')}")
    lineas.append("Pagado:".ljust(22) + _formatear_pesos(venta.get("monto_pagado")).rjust(20))
    lineas.append("Vuelto:".ljust(22) + _formatear_pesos(venta.get("vuelto")).rjust(20))
    lineas.append("=" * 42)

    mensaje = config.get("mensaje_ticket") or "Gracias por su compra"
    lineas.append(mensaje.center(42))
    lineas.append("=" * 42)

    ticket = "\n".join(lineas)

    return {
        "ok": True,
        "mensaje": "Ticket generado correctamente.",
        "data": ticket
    }
