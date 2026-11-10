from decimal import Decimal

from app.services import POSService


pos = POSService()


# =========================================================
# UTILIDADES GENERALES
# =========================================================

def pausar():
    input("\nPresione ENTER para continuar...")


def limpiar():
    print("\n" * 2)


def titulo(texto):
    print("\n" + "=" * 80)
    print(texto.center(80))
    print("=" * 80)


def leer_texto(mensaje, obligatorio=True):
    while True:
        valor = input(mensaje).strip()

        if valor or not obligatorio:
            return valor

        print("Este campo es obligatorio.")


def leer_decimal(mensaje, obligatorio=True, valor_default=0):
    while True:
        valor = input(mensaje).strip()

        if not valor and not obligatorio:
            return Decimal(str(valor_default))

        try:
            return Decimal(valor)
        except Exception:
            print("Ingrese un número válido.")


def leer_entero(mensaje, obligatorio=True, valor_default=None):
    while True:
        valor = input(mensaje).strip()

        if not valor and not obligatorio:
            return valor_default

        try:
            return int(valor)
        except Exception:
            print("Ingrese un número entero válido.")


def mostrar_respuesta(resultado):
    print(resultado.get("mensaje"))

    if not resultado.get("ok") and resultado.get("data") is not None:
        print(resultado.get("data"))


def pesos(valor):
    return pos.formato_pesos(valor)


def fecha(valor):
    return pos.formato_fecha(valor)


# =========================================================
# INICIO DE SISTEMA
# =========================================================

def iniciar_sistema():
    titulo("INICIANDO SISTEMA POS PYMES")

    conexion = pos.probar_conexion()
    mostrar_respuesta(conexion)

    if not conexion["ok"]:
        return False

    resultado = pos.iniciar_sistema_modo_desarrollo(usuario_id=1)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        print("No se pudo cargar el usuario administrador.")
        return False

    usuario = resultado["data"]

    print(f"Usuario activo: {usuario.get('nombre')} | Rol: {usuario.get('rol')}")

    return True


# =========================================================
# DASHBOARD
# =========================================================

def menu_dashboard():
    titulo("DASHBOARD PRINCIPAL")

    resultado = pos.obtener_dashboard()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    data = resultado["data"]

    caja = data.get("caja_actual")
    ventas = data.get("ventas_hoy") or {}
    bajo_stock = data.get("bajo_stock") or {}
    ultimas = data.get("ultimas_ventas") or []
    top_productos = data.get("productos_mas_vendidos_hoy") or []

    print("\nCAJA ACTUAL")
    print("-" * 80)

    if caja:
        print(f"Estado: {caja.get('estado')}")
        print(f"Fecha apertura: {fecha(caja.get('fecha_apertura'))}")
        print(f"Monto inicial: {pesos(caja.get('monto_inicial'))}")
        print(f"Ventas total: {pesos(caja.get('monto_ventas_total'))}")
        print(f"Monto esperado caja: {pesos(caja.get('monto_esperado_caja'))}")
    else:
        print("No hay caja abierta.")

    print("\nVENTAS DE HOY")
    print("-" * 80)
    print(f"Cantidad ventas: {ventas.get('cantidad_ventas')}")
    print(f"Total vendido: {pesos(ventas.get('total_vendido'))}")
    print(f"Efectivo: {pesos(ventas.get('total_efectivo'))}")
    print(f"Tarjeta: {pesos(ventas.get('total_tarjeta'))}")
    print(f"Transferencia: {pesos(ventas.get('total_transferencia'))}")

    print("\nSTOCK")
    print("-" * 80)
    print(f"Productos bajo stock: {bajo_stock.get('productos_bajo_stock')}")

    print("\nÚLTIMAS VENTAS")
    print("-" * 80)

    if not ultimas:
        print("No hay ventas recientes.")
    else:
        for venta in ultimas:
            print(
                f"{venta.get('numero_venta')} | "
                f"{fecha(venta.get('fecha_venta'))} | "
                f"{venta.get('metodo_pago')} | "
                f"{pesos(venta.get('total'))} | "
                f"{venta.get('estado')}"
            )

    print("\nPRODUCTOS MÁS VENDIDOS HOY")
    print("-" * 80)

    if not top_productos:
        print("No hay datos de productos vendidos.")
    else:
        for producto in top_productos:
            print(
                f"{producto.get('nombre_producto')} | "
                f"Cantidad: {producto.get('cantidad_vendida')} | "
                f"Total: {pesos(producto.get('total_vendido'))}"
            )


# =========================================================
# PRODUCTOS
# =========================================================

def menu_productos():
    while True:
        titulo("MÓDULO PRODUCTOS")
        print("1. Listar productos")
        print("2. Buscar por código de barra")
        print("3. Buscar por nombre")
        print("4. Crear producto")
        print("5. Productos bajo stock")
        print("6. Desactivar producto")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            productos_listar()

        elif opcion == "2":
            productos_buscar_codigo()

        elif opcion == "3":
            productos_buscar_nombre()

        elif opcion == "4":
            productos_crear()

        elif opcion == "5":
            productos_bajo_stock()

        elif opcion == "6":
            productos_desactivar()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def productos_listar():
    titulo("LISTADO DE PRODUCTOS")

    resultado = pos.obtener_productos()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    productos = resultado["data"]

    if not productos:
        print("No hay productos registrados.")
        return

    for p in productos:
        print(
            f"ID: {p.get('id')} | "
            f"Código: {p.get('codigo_barra')} | "
            f"Nombre: {p.get('nombre')} | "
            f"Precio: {pesos(p.get('precio_venta'))} | "
            f"Stock: {p.get('stock_actual')}"
        )


def productos_buscar_codigo():
    titulo("BUSCAR PRODUCTO POR CÓDIGO")

    codigo = leer_texto("Ingrese código de barra: ")

    resultado = pos.buscar_producto_codigo(codigo)
    mostrar_respuesta(resultado)

    if resultado["ok"]:
        mostrar_producto(resultado["data"])


def productos_buscar_nombre():
    titulo("BUSCAR PRODUCTO POR NOMBRE")

    texto = leer_texto("Ingrese nombre o parte del nombre: ")

    resultado = pos.buscar_producto_nombre(texto)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    productos = resultado["data"]

    if not productos:
        print("No se encontraron productos.")
        return

    for p in productos:
        print(
            f"ID: {p.get('id')} | "
            f"Código: {p.get('codigo_barra')} | "
            f"Nombre: {p.get('nombre')} | "
            f"Precio: {pesos(p.get('precio_venta'))} | "
            f"Stock: {p.get('stock_actual')}"
        )


def mostrar_producto(producto):
    print("-" * 80)
    print(f"ID: {producto.get('id')}")
    print(f"Código barra: {producto.get('codigo_barra')}")
    print(f"SKU: {producto.get('sku')}")
    print(f"Nombre: {producto.get('nombre')}")
    print(f"Categoría: {producto.get('categoria')}")
    print(f"Proveedor: {producto.get('proveedor')}")
    print(f"Tipo: {producto.get('tipo_producto')}")
    print(f"Unidad: {producto.get('unidad_medida')}")
    print(f"Precio compra: {pesos(producto.get('precio_compra'))}")
    print(f"Precio venta: {pesos(producto.get('precio_venta'))}")
    print(f"Stock actual: {producto.get('stock_actual')}")
    print(f"Stock mínimo: {producto.get('stock_minimo')}")
    print(f"Mayoría edad: {producto.get('requiere_mayoria_edad')}")
    print("-" * 80)


def productos_crear():
    titulo("CREAR PRODUCTO")

    print("\nCategorías disponibles:")
    categorias = pos.obtener_categorias()

    if categorias["ok"]:
        for c in categorias["data"]:
            print(f"{c.get('id')} - {c.get('nombre')}")

    categoria_id = leer_entero("ID categoría: ", obligatorio=False)

    print("\nProveedores disponibles:")
    proveedores = pos.obtener_proveedores()

    if proveedores["ok"]:
        for p in proveedores["data"]:
            print(f"{p.get('id')} - {p.get('nombre')}")

    proveedor_id = leer_entero("ID proveedor: ", obligatorio=False)

    codigo_barra = leer_texto("Código de barra: ")
    sku = leer_texto("SKU: ", obligatorio=False)
    nombre = leer_texto("Nombre producto: ")
    descripcion = leer_texto("Descripción: ", obligatorio=False)

    print("\nTipos válidos:")
    print("ALCOHOL | BEBIDA | CIGARRO | SNACK | ABARROTE | OTRO")
    tipo_producto = leer_texto("Tipo producto: ").upper()

    print("\nUnidades válidas:")
    print("UNIDAD | PACK | CAJA | KG | LITRO")
    unidad_medida = leer_texto("Unidad medida: ").upper()

    precio_compra = leer_decimal("Precio compra: ")
    precio_venta = leer_decimal("Precio venta: ")
    stock_actual = leer_decimal("Stock inicial: ")
    stock_minimo = leer_decimal("Stock mínimo: ")

    permite_sin_stock = leer_entero("¿Permite venta sin stock? 1=Sí / 0=No: ")
    requiere_edad = leer_entero("¿Requiere mayoría de edad? 1=Sí / 0=No: ")

    resultado = pos.crear_producto_sistema(
        categoria_id=categoria_id,
        proveedor_id=proveedor_id,
        codigo_barra=codigo_barra,
        sku=sku,
        nombre=nombre,
        descripcion=descripcion,
        tipo_producto=tipo_producto,
        unidad_medida=unidad_medida,
        precio_compra=precio_compra,
        precio_venta=precio_venta,
        stock_actual=stock_actual,
        stock_minimo=stock_minimo,
        permite_venta_sin_stock=permite_sin_stock,
        requiere_mayoria_edad=requiere_edad
    )

    mostrar_respuesta(resultado)


def productos_bajo_stock():
    titulo("PRODUCTOS BAJO STOCK")

    resultado = pos.productos_con_bajo_stock()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    productos = resultado["data"]

    if not productos:
        print("No hay productos con bajo stock.")
        return

    for p in productos:
        print(
            f"ID: {p.get('id')} | "
            f"Código: {p.get('codigo_barra')} | "
            f"Nombre: {p.get('nombre')} | "
            f"Stock: {p.get('stock_actual')} | "
            f"Mínimo: {p.get('stock_minimo')}"
        )


def productos_desactivar():
    titulo("DESACTIVAR PRODUCTO")

    producto_id = leer_entero("ID producto: ")

    resultado = pos.desactivar_producto_sistema(producto_id)
    mostrar_respuesta(resultado)


# =========================================================
# CAJA
# =========================================================

def menu_caja():
    while True:
        titulo("MÓDULO CAJA")
        print("1. Abrir caja")
        print("2. Ver caja abierta")
        print("3. Resumen de caja")
        print("4. Registrar ingreso extra")
        print("5. Registrar retiro")
        print("6. Cerrar caja")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            caja_abrir()

        elif opcion == "2":
            caja_ver_abierta()

        elif opcion == "3":
            caja_resumen()

        elif opcion == "4":
            caja_ingreso_extra()

        elif opcion == "5":
            caja_retiro()

        elif opcion == "6":
            caja_cerrar()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def caja_abrir():
    titulo("ABRIR CAJA")

    monto = leer_decimal("Monto inicial: ")
    observacion = leer_texto("Observación: ", obligatorio=False)

    resultado = pos.abrir_caja_sistema(
        monto_inicial=monto,
        observacion_apertura=observacion
    )

    mostrar_respuesta(resultado)


def caja_ver_abierta():
    titulo("CAJA ABIERTA")

    resultado = pos.obtener_caja_abierta_sistema()
    mostrar_respuesta(resultado)

    if resultado["ok"] and resultado["data"]:
        c = resultado["data"]
        print(f"ID: {c.get('id')}")
        print(f"Fecha apertura: {fecha(c.get('fecha_apertura'))}")
        print(f"Monto inicial: {pesos(c.get('monto_inicial'))}")
        print(f"Estado: {c.get('estado')}")


def caja_resumen():
    titulo("RESUMEN CAJA")

    resultado = pos.obtener_resumen_caja()
    mostrar_respuesta(resultado)

    if not resultado["ok"] or not resultado["data"]:
        return

    c = resultado["data"]

    print(f"ID caja: {c.get('caja_turno_id')}")
    print(f"Fecha apertura: {fecha(c.get('fecha_apertura'))}")
    print(f"Monto inicial: {pesos(c.get('monto_inicial'))}")
    print(f"Ventas efectivo: {pesos(c.get('ventas_efectivo'))}")
    print(f"Ventas tarjeta: {pesos(c.get('ventas_tarjeta'))}")
    print(f"Ventas transferencia: {pesos(c.get('ventas_transferencia'))}")
    print(f"Ventas total: {pesos(c.get('ventas_total'))}")
    print(f"Ingresos extra: {pesos(c.get('ingresos_extra'))}")
    print(f"Retiros: {pesos(c.get('retiros'))}")
    print(f"Monto esperado: {pesos(c.get('monto_esperado_caja'))}")
    print(f"Estado: {c.get('estado')}")


def caja_ingreso_extra():
    titulo("INGRESO EXTRA")

    monto = leer_decimal("Monto: ")
    descripcion = leer_texto("Descripción: ", obligatorio=False)

    resultado = pos.registrar_ingreso_extra_caja(monto, descripcion)
    mostrar_respuesta(resultado)


def caja_retiro():
    titulo("RETIRO DE CAJA")

    monto = leer_decimal("Monto retiro: ")
    descripcion = leer_texto("Descripción: ", obligatorio=False)

    resultado = pos.registrar_retiro_caja(monto, descripcion)
    mostrar_respuesta(resultado)


def caja_cerrar():
    titulo("CERRAR CAJA")

    monto_real = leer_decimal("Monto real contado: ")
    observacion = leer_texto("Observación cierre: ", obligatorio=False)

    resultado = pos.cerrar_caja_sistema(
        monto_real_cierre=monto_real,
        observacion_cierre=observacion
    )

    mostrar_respuesta(resultado)

    if resultado["ok"]:
        d = resultado["data"]
        print(f"Monto esperado: {pesos(d.get('monto_esperado_caja'))}")
        print(f"Monto real: {pesos(d.get('monto_real_cierre'))}")
        print(f"Diferencia: {pesos(d.get('diferencia'))}")


# =========================================================
# VENTAS / CARRITO
# =========================================================

def menu_ventas():
    while True:
        titulo("MÓDULO VENTAS")
        print("1. Agregar producto al carrito")
        print("2. Ver carrito")
        print("3. Cambiar cantidad de item")
        print("4. Eliminar item del carrito")
        print("5. Vaciar carrito")
        print("6. Cobrar carrito")
        print("7. Ventas del día")
        print("8. Buscar venta por número")
        print("9. Generar ticket por número")
        print("10. Anular venta")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            venta_agregar_producto()

        elif opcion == "2":
            venta_ver_carrito()

        elif opcion == "3":
            venta_cambiar_cantidad()

        elif opcion == "4":
            venta_eliminar_item()

        elif opcion == "5":
            resultado = pos.carrito_vaciar()
            mostrar_respuesta(resultado)

        elif opcion == "6":
            venta_cobrar_carrito()

        elif opcion == "7":
            venta_listar_hoy()

        elif opcion == "8":
            venta_buscar_numero()

        elif opcion == "9":
            venta_generar_ticket()

        elif opcion == "10":
            venta_anular()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def venta_agregar_producto():
    titulo("AGREGAR PRODUCTO AL CARRITO")

    codigo = leer_texto("Código de barra: ")
    cantidad = leer_decimal("Cantidad: ")

    resultado = pos.carrito_agregar_producto(codigo, cantidad)
    mostrar_respuesta(resultado)

    if resultado["ok"]:
        item = resultado["data"]
        print(f"Producto: {item.get('nombre')}")
        print(f"Cantidad: {item.get('cantidad')}")
        print(f"Subtotal: {pesos(item.get('subtotal_linea'))}")


def venta_ver_carrito():
    titulo("CARRITO ACTUAL")

    detalle = pos.carrito_obtener_detalle()
    resumen = pos.carrito_obtener_resumen()

    if not detalle["ok"]:
        mostrar_respuesta(detalle)
        return

    items = detalle["data"]

    if not items:
        print("El carrito está vacío.")
        return

    for i, item in enumerate(items):
        print(
            f"[{i}] "
            f"{item.get('nombre')} | "
            f"Código: {item.get('codigo_barra')} | "
            f"Cantidad: {item.get('cantidad')} | "
            f"Precio: {pesos(item.get('precio_unitario'))} | "
            f"Subtotal: {pesos(item.get('subtotal_linea'))}"
        )

    print("-" * 80)

    if resumen["ok"]:
        r = resumen["data"]
        print(f"Items: {r.get('cantidad_items')}")
        print(f"Unidades: {r.get('total_unidades')}")
        print(f"Subtotal neto: {pesos(r.get('subtotal'))}")
        print(f"Descuento: {pesos(r.get('descuento_total'))}")
        print(f"IVA {r.get('impuesto_porcentaje', 19)}%: {pesos(r.get('impuesto_total'))}")
        print(f"Total: {pesos(r.get('total'))}")
        print(f"Requiere mayoría edad: {r.get('requiere_mayoria_edad')}")


def venta_cambiar_cantidad():
    titulo("CAMBIAR CANTIDAD")

    venta_ver_carrito()

    indice = leer_entero("Índice del item: ")
    cantidad = leer_decimal("Nueva cantidad: ")

    resultado = pos.carrito_actualizar_cantidad(indice, cantidad)
    mostrar_respuesta(resultado)


def venta_eliminar_item():
    titulo("ELIMINAR ITEM")

    venta_ver_carrito()

    indice = leer_entero("Índice del item a eliminar: ")

    resultado = pos.carrito_eliminar_item(indice)
    mostrar_respuesta(resultado)


def venta_cobrar_carrito():
    titulo("COBRAR CARRITO")

    venta_ver_carrito()

    print("\nMétodos de pago:")
    print("EFECTIVO | TARJETA | TRANSFERENCIA | MIXTO")

    metodo = leer_texto("Método de pago: ").upper()

    monto_efectivo = Decimal("0")
    monto_tarjeta = Decimal("0")
    monto_transferencia = Decimal("0")

    if metodo == "EFECTIVO":
        monto_efectivo = leer_decimal("Monto recibido en efectivo: ")

    elif metodo == "TARJETA":
        pass

    elif metodo == "TRANSFERENCIA":
        pass

    elif metodo == "MIXTO":
        monto_efectivo = leer_decimal("Monto efectivo: ")
        monto_tarjeta = leer_decimal("Monto tarjeta: ")
        monto_transferencia = leer_decimal("Monto transferencia: ")

    else:
        print("Método de pago inválido.")
        return

    confirmar_edad = leer_entero(
        "¿Confirma mayoría de edad si aplica? 1=Sí / 0=No: ",
        obligatorio=False,
        valor_default=1
    )

    resultado = pos.vender_carrito(
        metodo_pago=metodo,
        monto_efectivo=monto_efectivo,
        monto_tarjeta=monto_tarjeta,
        monto_transferencia=monto_transferencia,
        confirmar_mayoria_edad=bool(confirmar_edad)
    )

    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    venta = resultado["data"]

    print(f"Número venta: {venta.get('numero_venta')}")
    print(f"Subtotal neto: {pesos(venta.get('subtotal'))}")
    print(f"IVA {venta.get('impuesto_porcentaje', 19)}%: {pesos(venta.get('impuesto_total'))}")
    print(f"Total: {pesos(venta.get('total'))}")
    print(f"Pagado: {pesos(venta.get('monto_pagado'))}")
    print(f"Vuelto: {pesos(venta.get('vuelto'))}")

    ticket = pos.generar_ticket_venta(venta.get("venta_id"))

    if ticket["ok"]:
        print("\n")
        print(ticket["data"])
    else:
        print(ticket["mensaje"])


def venta_listar_hoy():
    titulo("VENTAS DEL DÍA")

    resultado = pos.obtener_ventas_hoy()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    ventas = resultado["data"]

    if not ventas:
        print("No hay ventas registradas hoy.")
        return

    for v in ventas:
        print(
            f"ID: {v.get('id')} | "
            f"Número: {v.get('numero_venta')} | "
            f"Fecha: {fecha(v.get('fecha_venta'))} | "
            f"Cajero: {v.get('cajero')} | "
            f"Pago: {v.get('metodo_pago')} | "
            f"Total: {pesos(v.get('total'))} | "
            f"Estado: {v.get('estado')}"
        )


def venta_buscar_numero():
    titulo("BUSCAR VENTA")

    numero = leer_texto("Número de venta: ")

    resultado = pos.buscar_venta_por_numero(numero)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    venta = resultado["data"]

    print(f"ID: {venta.get('id')}")
    print(f"Número: {venta.get('numero_venta')}")
    print(f"Fecha: {fecha(venta.get('fecha_venta'))}")
    print(f"Cajero: {venta.get('nombre_usuario')}")
    print(f"Total: {pesos(venta.get('total'))}")
    print(f"Estado: {venta.get('estado')}")

    print("\nDetalle:")

    for item in venta.get("detalle", []):
        print(
            f"{item.get('nombre_producto')} | "
            f"Cantidad: {item.get('cantidad')} | "
            f"Precio: {pesos(item.get('precio_unitario'))} | "
            f"Subtotal: {pesos(item.get('subtotal_linea'))}"
        )


def venta_generar_ticket():
    titulo("GENERAR TICKET")

    numero = leer_texto("Número de venta: ")

    resultado = pos.generar_ticket_por_numero_venta(numero)

    if resultado["ok"]:
        print(resultado["data"])
    else:
        mostrar_respuesta(resultado)


def venta_anular():
    titulo("ANULAR VENTA")

    numero = leer_texto("Número de venta: ")

    venta = pos.buscar_venta_por_numero(numero)

    if not venta["ok"]:
        mostrar_respuesta(venta)
        return

    data = venta["data"]

    print(f"Venta: {data.get('numero_venta')}")
    print(f"Total: {pesos(data.get('total'))}")
    print(f"Estado: {data.get('estado')}")

    motivo = leer_texto("Motivo anulación: ")
    devolver = leer_entero("¿Devolver stock? 1=Sí / 0=No: ")

    resultado = pos.anular_venta_sistema(
        venta_id=data.get("id"),
        motivo=motivo,
        devolver_stock=bool(devolver)
    )

    mostrar_respuesta(resultado)


# =========================================================
# INVENTARIO
# =========================================================

def menu_inventario():
    while True:
        titulo("MÓDULO INVENTARIO")
        print("1. Ingresar stock")
        print("2. Ajustar stock")
        print("3. Registrar merma")
        print("4. Actualizar precio producto")
        print("5. Ver movimientos de stock")
        print("6. Sugerencia de reposición")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            inventario_ingresar_stock()

        elif opcion == "2":
            inventario_ajustar_stock()

        elif opcion == "3":
            inventario_merma()

        elif opcion == "4":
            inventario_actualizar_precio()

        elif opcion == "5":
            inventario_movimientos()

        elif opcion == "6":
            inventario_reposicion()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def inventario_ingresar_stock():
    titulo("INGRESAR STOCK")

    producto_id = leer_entero("ID producto: ")
    cantidad = leer_decimal("Cantidad a ingresar: ")
    precio_compra = leer_decimal("Precio compra, ENTER para mantener actual: ", obligatorio=False, valor_default=0)

    usar_precio = input("¿Actualizar precio compra? 1=Sí / 0=No: ").strip()

    if usar_precio == "1":
        precio_final = precio_compra
        actualizar_precio = True
    else:
        precio_final = None
        actualizar_precio = False

    comentario = leer_texto("Comentario: ", obligatorio=False)

    resultado = pos.ingresar_stock_producto(
        producto_id=producto_id,
        cantidad=cantidad,
        precio_compra=precio_final,
        comentario=comentario,
        actualizar_precio_compra=actualizar_precio
    )

    mostrar_respuesta(resultado)


def inventario_ajustar_stock():
    titulo("AJUSTAR STOCK")

    producto_id = leer_entero("ID producto: ")
    nuevo_stock = leer_decimal("Nuevo stock físico: ")
    comentario = leer_texto("Comentario: ", obligatorio=False)

    resultado = pos.ajustar_stock_producto(
        producto_id=producto_id,
        nuevo_stock=nuevo_stock,
        comentario=comentario
    )

    mostrar_respuesta(resultado)


def inventario_merma():
    titulo("REGISTRAR MERMA")

    producto_id = leer_entero("ID producto: ")
    cantidad = leer_decimal("Cantidad merma: ")
    comentario = leer_texto("Comentario: ", obligatorio=False)

    resultado = pos.registrar_merma_producto(
        producto_id=producto_id,
        cantidad=cantidad,
        comentario=comentario
    )

    mostrar_respuesta(resultado)


def inventario_actualizar_precio():
    titulo("ACTUALIZAR PRECIO")

    producto_id = leer_entero("ID producto: ")
    nuevo_precio_venta = leer_decimal("Nuevo precio venta: ")

    cambiar_compra = input("¿Actualizar también precio compra? 1=Sí / 0=No: ").strip()

    if cambiar_compra == "1":
        nuevo_precio_compra = leer_decimal("Nuevo precio compra: ")
    else:
        nuevo_precio_compra = None

    resultado = pos.actualizar_precio_producto_sistema(
        producto_id=producto_id,
        nuevo_precio_venta=nuevo_precio_venta,
        nuevo_precio_compra=nuevo_precio_compra
    )

    mostrar_respuesta(resultado)


def inventario_movimientos():
    titulo("MOVIMIENTOS DE STOCK")

    producto_id = leer_entero("ID producto, ENTER para todos: ", obligatorio=False)
    limite = leer_entero("Límite registros: ", obligatorio=False, valor_default=50)

    resultado = pos.obtener_movimientos_inventario(producto_id, limite)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    movimientos = resultado["data"]

    if not movimientos:
        print("No hay movimientos.")
        return

    for m in movimientos:
        print(
            f"{fecha(m.get('created_at'))} | "
            f"{m.get('producto')} | "
            f"{m.get('tipo_movimiento')} | "
            f"Anterior: {m.get('cantidad_anterior')} | "
            f"Mov: {m.get('cantidad_movimiento')} | "
            f"Nuevo: {m.get('cantidad_nueva')} | "
            f"Usuario: {m.get('usuario')}"
        )


def inventario_reposicion():
    titulo("SUGERENCIA DE REPOSICIÓN")

    resultado = pos.obtener_sugerencia_reposicion()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    productos = resultado["data"]

    if not productos:
        print("No hay productos para reponer.")
        return

    for p in productos:
        print(
            f"ID: {p.get('id')} | "
            f"{p.get('nombre')} | "
            f"Stock: {p.get('stock_actual')} | "
            f"Mínimo: {p.get('stock_minimo')} | "
            f"Sugerido: {p.get('cantidad_sugerida')}"
        )


# =========================================================
# REPORTES
# =========================================================

def menu_reportes():
    while True:
        titulo("REPORTES")
        print("1. Resumen ventas del día")
        print("2. Ventas del día detalladas")
        print("3. Ganancia por rango")
        print("4. Productos más vendidos")
        print("5. Resumen caja actual")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            reporte_resumen_dia()

        elif opcion == "2":
            reporte_ventas_dia()

        elif opcion == "3":
            reporte_ganancia()

        elif opcion == "4":
            reporte_productos_mas_vendidos()

        elif opcion == "5":
            reporte_caja()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def reporte_resumen_dia():
    titulo("RESUMEN VENTAS DEL DÍA")

    resultado = pos.reporte_resumen_ventas_del_dia()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    d = resultado["data"]

    print(f"Cantidad ventas: {d.get('cantidad_ventas')}")
    print(f"Total neto: {pesos(d.get('total_neto'))}")
    print(f"IVA: {pesos(d.get('total_impuesto'))}")
    print(f"Total vendido: {pesos(d.get('total_vendido'))}")
    print(f"Efectivo: {pesos(d.get('total_efectivo'))}")
    print(f"Tarjeta: {pesos(d.get('total_tarjeta'))}")
    print(f"Transferencia: {pesos(d.get('total_transferencia'))}")


def reporte_ventas_dia():
    titulo("VENTAS DEL DÍA DETALLADAS")

    resultado = pos.reporte_ventas_del_dia()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    for v in resultado["data"]:
        print(
            f"{v.get('numero_venta')} | "
            f"{fecha(v.get('fecha_venta'))} | "
            f"{v.get('cajero')} | "
            f"{v.get('metodo_pago')} | "
            f"{pesos(v.get('total'))} | "
            f"{v.get('estado')}"
        )


def reporte_ganancia():
    titulo("GANANCIA POR RANGO")

    inicio = leer_texto("Fecha inicio YYYY-MM-DD: ")
    fin = leer_texto("Fecha fin YYYY-MM-DD: ")

    resultado = pos.reporte_ganancia_por_rango(inicio, fin)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    d = resultado["data"]

    print(f"Ventas: {d.get('cantidad_ventas')}")
    print(f"Total vendido: {pesos(d.get('total_vendido'))}")
    print(f"Costo total: {pesos(d.get('costo_total'))}")
    print(f"Ganancia estimada: {pesos(d.get('ganancia_estimada'))}")


def reporte_productos_mas_vendidos():
    titulo("PRODUCTOS MÁS VENDIDOS")

    inicio = leer_texto("Fecha inicio YYYY-MM-DD: ")
    fin = leer_texto("Fecha fin YYYY-MM-DD: ")
    limite = leer_entero("Límite: ", obligatorio=False, valor_default=10)

    resultado = pos.reporte_productos_mas_vendidos(inicio, fin, limite)
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    productos = resultado["data"]

    if not productos:
        print("No hay datos.")
        return

    for p in productos:
        print(
            f"{p.get('nombre_producto')} | "
            f"Cantidad: {p.get('cantidad_vendida')} | "
            f"Total: {pesos(p.get('total_vendido'))} | "
            f"Ganancia: {pesos(p.get('ganancia_estimada'))}"
        )


def reporte_caja():
    titulo("REPORTE CAJA ACTUAL")

    resultado = pos.reporte_resumen_caja_actual()
    mostrar_respuesta(resultado)

    if not resultado["ok"] or not resultado["data"]:
        return

    c = resultado["data"]

    print(f"ID caja: {c.get('id')}")
    print(f"Usuario apertura: {c.get('usuario_apertura')}")
    print(f"Fecha apertura: {fecha(c.get('fecha_apertura'))}")
    print(f"Monto inicial: {pesos(c.get('monto_inicial'))}")
    print(f"Ventas total: {pesos(c.get('monto_ventas_total'))}")
    print(f"Monto esperado: {pesos(c.get('monto_esperado_caja'))}")
    print(f"Estado: {c.get('estado')}")


# =========================================================
# CONFIGURACIÓN
# =========================================================

def menu_configuracion():
    while True:
        titulo("CONFIGURACIÓN")
        print("1. Ver configuración negocio")
        print("2. Actualizar configuración negocio")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            config_ver()

        elif opcion == "2":
            config_actualizar()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def config_ver():
    titulo("CONFIGURACIÓN DEL NEGOCIO")

    resultado = pos.obtener_configuracion()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    c = resultado["data"]

    print(f"Nombre: {c.get('nombre_negocio')}")
    print(f"RUT: {c.get('rut')}")
    print(f"Giro: {c.get('giro')}")
    print(f"Dirección: {c.get('direccion')}")
    print(f"Comuna: {c.get('comuna')}")
    print(f"Ciudad: {c.get('ciudad')}")
    print(f"Teléfono: {c.get('telefono')}")
    print(f"Email: {c.get('email')}")
    print(f"Moneda: {c.get('moneda')}")
    print(f"Mensaje ticket: {c.get('mensaje_ticket')}")


def config_actualizar():
    titulo("ACTUALIZAR CONFIGURACIÓN")

    nombre = leer_texto("Nombre negocio: ")
    rut = leer_texto("RUT: ", obligatorio=False)
    giro = leer_texto("Giro: ", obligatorio=False)
    direccion = leer_texto("Dirección: ", obligatorio=False)
    comuna = leer_texto("Comuna: ", obligatorio=False)
    ciudad = leer_texto("Ciudad: ", obligatorio=False)
    telefono = leer_texto("Teléfono: ", obligatorio=False)
    email = leer_texto("Email: ", obligatorio=False)
    mensaje = leer_texto("Mensaje ticket: ", obligatorio=False)

    resultado = pos.actualizar_configuracion(
        nombre_negocio=nombre,
        rut=rut,
        giro=giro,
        direccion=direccion,
        comuna=comuna,
        ciudad=ciudad,
        telefono=telefono,
        email=email,
        moneda="CLP",
        impuesto_porcentaje=19,
        mensaje_ticket=mensaje or "Gracias por su compra"
    )

    mostrar_respuesta(resultado)


# =========================================================
# USUARIOS
# =========================================================

def menu_usuarios():
    while True:
        titulo("USUARIOS")
        print("1. Listar usuarios")
        print("2. Crear usuario")
        print("3. Cambiar contraseña")
        print("4. Activar usuario")
        print("5. Desactivar usuario")
        print("0. Volver")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            usuarios_listar()

        elif opcion == "2":
            usuarios_crear()

        elif opcion == "3":
            usuarios_cambiar_password()

        elif opcion == "4":
            usuarios_activar()

        elif opcion == "5":
            usuarios_desactivar()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")

        pausar()


def usuarios_listar():
    titulo("LISTAR USUARIOS")

    resultado = pos.listar_usuarios_sistema()
    mostrar_respuesta(resultado)

    if not resultado["ok"]:
        return

    for u in resultado["data"]:
        print(
            f"ID: {u.get('id')} | "
            f"Nombre: {u.get('nombre')} | "
            f"Usuario: {u.get('usuario')} | "
            f"Rol: {u.get('rol')} | "
            f"Activo: {u.get('activo')}"
        )


def usuarios_crear():
    titulo("CREAR USUARIO")

    nombre = leer_texto("Nombre: ")
    usuario = leer_texto("Usuario: ")
    password = leer_texto("Contraseña: ")

    print("Roles válidos: ADMIN | CAJERO | VENDEDOR")
    rol = leer_texto("Rol: ").upper()

    resultado = pos.crear_usuario_sistema(nombre, usuario, password, rol)
    mostrar_respuesta(resultado)


def usuarios_cambiar_password():
    titulo("CAMBIAR CONTRASEÑA")

    usuario_id = leer_entero("ID usuario: ")
    nueva = leer_texto("Nueva contraseña: ")

    resultado = pos.cambiar_password_usuario(usuario_id, nueva)
    mostrar_respuesta(resultado)


def usuarios_activar():
    titulo("ACTIVAR USUARIO")

    usuario_id = leer_entero("ID usuario: ")

    resultado = pos.activar_usuario_sistema(usuario_id)
    mostrar_respuesta(resultado)


def usuarios_desactivar():
    titulo("DESACTIVAR USUARIO")

    usuario_id = leer_entero("ID usuario: ")

    resultado = pos.desactivar_usuario_sistema(usuario_id)
    mostrar_respuesta(resultado)


# =========================================================
# MENÚ PRINCIPAL
# =========================================================

def menu_principal():
    while True:
        usuario = pos.obtener_usuario_actual().get("data") or {}

        titulo("SISTEMA POS PYMES")
        print(f"Usuario: {usuario.get('nombre')} | Rol: {usuario.get('rol')}")
        print("=" * 80)
        print("1. Dashboard")
        print("2. Productos")
        print("3. Caja")
        print("4. Ventas / Carrito")
        print("5. Inventario")
        print("6. Reportes")
        print("7. Configuración")
        print("8. Usuarios")
        print("9. Probar conexión")
        print("0. Salir")
        print("=" * 80)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            menu_dashboard()
            pausar()

        elif opcion == "2":
            menu_productos()

        elif opcion == "3":
            menu_caja()

        elif opcion == "4":
            menu_ventas()

        elif opcion == "5":
            menu_inventario()

        elif opcion == "6":
            menu_reportes()

        elif opcion == "7":
            menu_configuracion()

        elif opcion == "8":
            menu_usuarios()

        elif opcion == "9":
            resultado = pos.probar_conexion()
            mostrar_respuesta(resultado)
            pausar()

        elif opcion == "0":
            print("Cerrando sistema POS Pymes...")
            break

        else:
            print("Opción inválida.")
            pausar()


def main():
    limpiar()

    if not iniciar_sistema():
        return

    menu_principal()


if __name__ == "__main__":
    main()