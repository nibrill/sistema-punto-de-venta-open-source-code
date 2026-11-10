import hashlib
import hmac
import secrets


ROLES_DISPONIBLES = [
    "ADMIN",
    "VENDEDOR",
    "ENCARGADO_STOCK"
]


PERMISOS_POR_ROL = {
    "ADMIN": {
        "Dashboard",
        "Gráficos",
        "Ventas",
        "Productos",
        "Proveedores",
        "Clientes",
        "Compras",
        "Inventario",
        "Caja",
        "Reportes",
        "Configuración",
        "Usuarios"
    },

    "VENDEDOR": {
        "Dashboard",
        "Ventas",
        "Productos",
        "Clientes",
        "Caja"
    },

    "ENCARGADO_STOCK": {
        "Dashboard",
        "Gráficos",
        "Ventas",
        "Productos",
        "Proveedores",
        "Clientes",
        "Compras",
        "Inventario",
        "Caja",
        "Reportes"
    }
}


ACCIONES_POR_ROL = {
    "ADMIN": {
        "ver_dashboard",
        "ver_graficos",
        "ver_ventas",
        "crear_venta",
        "anular_venta",
        "ver_productos",
        "crear_producto",
        "editar_producto",
        "desactivar_producto",
        "ver_proveedores",
        "crear_proveedor",
        "editar_proveedor",
        "desactivar_proveedor",
        "ver_clientes",
        "crear_cliente",
        "editar_cliente",
        "desactivar_cliente",
        "ver_compras",
        "crear_compra",
        "ver_inventario",
        "ajustar_stock",
        "ver_caja",
        "abrir_caja",
        "cerrar_caja",
        "ver_reportes",
        "exportar_reportes",
        "ver_configuracion",
        "editar_configuracion",
        "ver_usuarios",
        "crear_usuario",
        "editar_usuario",
        "eliminar_usuario"
    },

    "VENDEDOR": {
        "ver_dashboard",
        "ver_ventas",
        "crear_venta",
        "ver_productos",
        "ver_clientes",
        "crear_cliente",
        "editar_cliente",
        "ver_caja",
        "abrir_caja",
        "cerrar_caja"
    },

    "ENCARGADO_STOCK": {
        "ver_dashboard",
        "ver_graficos",

        "ver_ventas",
        "crear_venta",
        "anular_venta",

        "ver_productos",
        "crear_producto",
        "editar_producto",
        "desactivar_producto",

        "ver_proveedores",
        "crear_proveedor",
        "editar_proveedor",
        "desactivar_proveedor",

        "ver_clientes",
        "crear_cliente",
        "editar_cliente",
        "desactivar_cliente",

        "ver_compras",
        "crear_compra",

        "ver_inventario",
        "ajustar_stock",

        "ver_caja",
        "abrir_caja",
        "cerrar_caja",

        "ver_reportes",
        "exportar_reportes"
    }
}


def normalizar_rol(rol):
    rol = str(rol or "").strip().upper()

    if rol == "CAJERO":
        return "VENDEDOR"

    if rol not in ROLES_DISPONIBLES:
        return "VENDEDOR"

    return rol


def tiene_permiso(rol, modulo):
    rol = normalizar_rol(rol)
    modulo = str(modulo or "").strip()

    return modulo in PERMISOS_POR_ROL.get(rol, set())


def tiene_permiso_accion(rol, accion):
    rol = normalizar_rol(rol)
    accion = str(accion or "").strip()

    return accion in ACCIONES_POR_ROL.get(rol, set())


def generar_hash_password(password):
    password = str(password or "")

    if len(password.strip()) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")

    salt = secrets.token_hex(16)

    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()

    return f"{salt}${hash_password}"


def verificar_password(password, password_hash):
    password = str(password or "")
    password_hash = str(password_hash or "")

    if not password or not password_hash:
        return False

    if "$" not in password_hash:
        return hmac.compare_digest(password, password_hash)

    try:
        salt, hash_guardado = password_hash.split("$", 1)

        hash_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000
        ).hex()

        return hmac.compare_digest(hash_calculado, hash_guardado)

    except Exception:
        return False


def es_hash_legacy(password_hash):
    password_hash = str(password_hash or "")
    return "$" not in password_hash