"""Edición comunitaria: sin licenciamiento, todos los módulos habilitados."""

MODULOS = [
    "ventas", "productos", "proveedores", "clientes", "compras",
    "inventario", "caja", "reportes", "configuracion",
]


def validate_license(license_text=None):
    return {
        "valid": True,
        "message": "Edición comunitaria (código abierto).",
        "payload": {"estado": "ACTIVA", "modulos": list(MODULOS)},
    }


def has_module(module_name):
    return module_name in MODULOS
