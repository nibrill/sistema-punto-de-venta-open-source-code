from decimal import Decimal, ROUND_HALF_UP

IVA_PORCENTAJE_DEFECTO = Decimal("19")


def decimal_seguro(valor, defecto="0"):
    try:
        if valor is None or valor == "":
            return Decimal(str(defecto))
        return Decimal(str(valor))
    except Exception:
        return Decimal(str(defecto))


def dinero(valor):
    return decimal_seguro(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def obtener_porcentaje_impuesto_defecto():
    """
    Lee el impuesto desde negocio_config. Si la configuración no existe,
    usa IVA chileno por defecto: 19%.
    """
    try:
        from app.configuracion import obtener_configuracion_negocio

        resultado = obtener_configuracion_negocio()
        if resultado.get("ok"):
            porcentaje = decimal_seguro(
                (resultado.get("data") or {}).get("impuesto_porcentaje"),
                IVA_PORCENTAJE_DEFECTO
            )
            if porcentaje >= 0:
                return porcentaje
    except Exception:
        pass

    return IVA_PORCENTAJE_DEFECTO


def calcular_totales_venta(subtotal, descuento_total=0, impuesto_porcentaje=None):
    """
    Calcula totales para una venta usando precios netos.

    subtotal: suma antes de descuentos e impuesto.
    descuento_total: descuentos de línea + descuento global.
    impuesto_total: IVA calculado sobre el neto gravado.
    total: neto gravado + impuesto_total.
    """
    subtotal = dinero(subtotal)
    descuento_total = dinero(descuento_total)

    if descuento_total < 0:
        descuento_total = Decimal("0")

    if descuento_total > subtotal:
        descuento_total = subtotal

    neto_gravado = dinero(subtotal - descuento_total)

    if impuesto_porcentaje is None:
        impuesto_porcentaje = obtener_porcentaje_impuesto_defecto()
    else:
        impuesto_porcentaje = decimal_seguro(impuesto_porcentaje, IVA_PORCENTAJE_DEFECTO)

    if impuesto_porcentaje < 0:
        impuesto_porcentaje = Decimal("0")

    impuesto_total = dinero(neto_gravado * impuesto_porcentaje / Decimal("100"))
    total = dinero(neto_gravado + impuesto_total)

    return {
        "subtotal": subtotal,
        "descuento_total": descuento_total,
        "neto_gravado": neto_gravado,
        "impuesto_porcentaje": impuesto_porcentaje,
        "impuesto_total": impuesto_total,
        "total": total,
    }
