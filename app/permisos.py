PERMISOS_POR_ROL = {
    "ADMIN": [
        "abrir_caja",
        "cerrar_caja",
        "realizar_venta",
        "anular_venta",
        "crear_producto",
        "editar_producto",
        "desactivar_producto",
        "ingresar_stock",
        "ajustar_stock",
        "ver_reportes",
        "crear_usuario",
        "editar_usuario",
        "ver_configuracion",
        "editar_configuracion",
        "registrar_retiro",
        "registrar_ingreso_extra",
         "generar_ticket",
         "crear_cliente",
         "editar_cliente",
         "registrar_compra",
         "ver_compras"
    ],
    "CAJERO": [
        "abrir_caja",
        "cerrar_caja",
        "realizar_venta",
        "ver_productos",
        "ver_caja",
        "generar_ticket"
    ],
    "VENDEDOR": [
        "realizar_venta",
        "ver_productos",
        "generar_ticket"
    ]
}


def tiene_permiso(rol, permiso):
    rol = str(rol or "").upper()
    permiso = str(permiso or "").strip()

    permisos = PERMISOS_POR_ROL.get(rol, [])

    return permiso in permisos


def validar_permiso(rol, permiso):
    if tiene_permiso(rol, permiso):
        return {
            "ok": True,
            "mensaje": "Permiso autorizado.",
            "data": None
        }

    return {
        "ok": False,
        "mensaje": f"No tiene permiso para realizar esta acción: {permiso}",
        "data": {
            "rol": rol,
            "permiso": permiso
        }
    }


def listar_permisos_rol(rol):
    rol = str(rol or "").upper()

    return {
        "ok": True,
        "mensaje": "Permisos obtenidos correctamente.",
        "data": PERMISOS_POR_ROL.get(rol, [])
    }

