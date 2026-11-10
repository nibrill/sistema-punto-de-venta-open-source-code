from decimal import Decimal, ROUND_HALF_UP


def decimal_seguro(valor):
    return Decimal(str(valor or 0))


def dinero(valor):
    return decimal_seguro(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def formatear_pesos(valor):
    valor = dinero(valor)
    return f"${int(valor):,}".replace(",", ".")


def formatear_decimal(valor, decimales=3):
    valor = decimal_seguro(valor)
    return f"{valor:.{decimales}f}"


def formatear_fecha(fecha):
    if fecha is None:
        return ""

    try:
        return fecha.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(fecha)


def limpiar_texto(texto):
    if texto is None:
        return ""

    return str(texto).strip()


def normalizar_codigo_barra(codigo):
    return limpiar_texto(codigo)


def normalizar_mayusculas(texto):
    return limpiar_texto(texto).upper()


def normalizar_usuario(usuario):
    return limpiar_texto(usuario).lower()