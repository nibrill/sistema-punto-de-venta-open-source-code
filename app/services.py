from decimal import Decimal

from app.database import obtener_conexion

from app.usuarios import (
    login_usuario,
    obtener_usuario,
    listar_usuarios,
    crear_usuario,
    cambiar_password,
    activar_usuario,
    desactivar_usuario
)

from app.productos import (
    buscar_producto_por_codigo,
    buscar_productos_por_nombre,
    listar_productos,
    crear_producto,
    productos_bajo_stock,
    desactivar_producto
)

from app.catalogos import (
    listar_categorias,
    crear_categoria,
    actualizar_categoria,
    activar_categoria,
    desactivar_categoria,
    listar_proveedores,
    crear_proveedor,
    actualizar_proveedor,
    activar_proveedor,
    desactivar_proveedor
)

from app.caja import (
    abrir_caja,
    cerrar_caja,
    obtener_caja_abierta,
    obtener_resumen_caja_actual,
    registrar_ingreso_extra,
    registrar_retiro
)

from app.ventas import (
    realizar_venta,
    listar_ventas_del_dia,
    obtener_venta,
    obtener_venta_por_numero,
    anular_venta
)

from app.tickets import generar_ticket_texto

from app.reportes import (
    ventas_del_dia,
    resumen_ventas_del_dia,
    ventas_por_rango,
    ganancia_por_rango,
    productos_mas_vendidos,
    movimientos_stock_producto,
    resumen_caja_actual
)

from app.inventario import (
    ingresar_stock,
    ajustar_stock,
    registrar_merma,
    actualizar_precio_producto,
    obtener_movimientos_stock,
    sugerir_reposicion_stock
)

from app.clientes import (
    listar_clientes,
    buscar_clientes,
    crear_cliente,
    actualizar_cliente,
    activar_cliente,
    desactivar_cliente
)

from app.compras import (
    registrar_compra,
    listar_compras,
    obtener_compra
)

from app.configuracion import (
    obtener_configuracion_negocio,
    crear_configuracion_negocio,
    actualizar_configuracion_negocio
)

from app.carrito import CarritoPOS

from app.permisos import (
    listar_permisos_rol
)

from app.dashboard import obtener_dashboard_principal

from app.formateadores import (
    formatear_pesos,
    formatear_fecha,
    decimal_seguro,
    dinero,
    limpiar_texto,
    normalizar_codigo_barra,
    normalizar_mayusculas,
    normalizar_usuario
)

from app.export_excel import (
    exportar_reporte_completo_excel,
    exportar_tabla_simple_excel
)

from app.security import tiene_permiso_accion, normalizar_rol


PERMISOS_EQUIVALENTES = {
    "realizar_venta": "crear_venta",
    "registrar_compra": "crear_compra",
    "ingresar_stock": "ajustar_stock",
    "generar_ticket": "crear_venta",
    "registrar_ingreso_extra": "abrir_caja",
    "registrar_retiro": "cerrar_caja",
}


class POSService:
    """
    Fachada principal del sistema POS.

    La interfaz visual debería usar principalmente esta clase,
    para no conectarse directamente con productos.py, caja.py, ventas.py, etc.
    """

    def __init__(self):
        self.usuario_actual = None
        self.auth = None
        self.carrito = CarritoPOS()

    # =====================================================
    # RESPUESTAS
    # =====================================================

    def _respuesta(self, ok, mensaje, data=None):
        return {
            "ok": ok,
            "mensaje": mensaje,
            "data": data
        }

    def set_usuario_actual(self, usuario):
        self.usuario_actual = usuario or {}

    def _requiere_sesion(self):
        if not self.usuario_actual:
            return self._respuesta(
                False,
                "Debe iniciar sesión para realizar esta acción.",
                None
            )

        return self._respuesta(True, "Sesión activa.", self.usuario_actual)

    def _validar_permiso_actual(self, permiso):
        sesion = self._requiere_sesion()

        if not sesion["ok"]:
            return sesion

        rol = normalizar_rol(self.usuario_actual.get("rol"))

        permiso = str(permiso or "").strip()
        permiso_equivalente = PERMISOS_EQUIVALENTES.get(permiso)

        if tiene_permiso_accion(rol, permiso):
            return self._respuesta(True, "Permiso autorizado.", None)

        if permiso_equivalente and tiene_permiso_accion(rol, permiso_equivalente):
            return self._respuesta(True, "Permiso autorizado.", None)

        return self._respuesta(
            False,
            f"No tiene permiso para realizar esta acción: {permiso}",
            None
        )

    def obtener_usuario_actual(self):
        if not self.usuario_actual:
            return self._respuesta(
                False,
                "No hay usuario conectado.",
                None
            )

        return self._respuesta(
            True,
            "Usuario actual obtenido correctamente.",
            self.usuario_actual
        )

    def obtener_usuario_id_actual(self):
        if not self.usuario_actual:
            return None

        return self.usuario_actual.get("id")

    def obtener_usuario_actual_id(self):
        return self.obtener_usuario_id_actual()

    def obtener_rol_actual(self):
        if not self.usuario_actual:
            return None

        return normalizar_rol(self.usuario_actual.get("rol"))

    # =====================================================
    # SISTEMA / CONEXIÓN
    # =====================================================

    def probar_conexion(self):
        conexion = obtener_conexion()

        if conexion is None:
            return self._respuesta(
                False,
                "No se pudo conectar a la base de datos.",
                None
            )

        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT DATABASE();")
            resultado = cursor.fetchone()

            cursor.close()
            conexion.close()

            return self._respuesta(
                True,
                "Conexión correcta a la base de datos.",
                {
                    "base_datos": resultado[0]
                }
            )

        except Exception as error:
            return self._respuesta(
                False,
                f"Error al probar conexión: {error}",
                None
            )

    def iniciar_sistema_modo_desarrollo(self, usuario_id=1):
        """
        Permite usar el sistema sin login visual todavía.
        Útil mientras se desarrolla la interfaz gráfica.
        """

        resultado = obtener_usuario(usuario_id)

        if not resultado["ok"]:
            return resultado

        self.usuario_actual = resultado["data"]

        return self._respuesta(
            True,
            "Sistema iniciado en modo desarrollo.",
            self.usuario_actual
        )

    # =====================================================
    # LOGIN / USUARIOS
    # =====================================================

    def iniciar_sesion(self, usuario, password):
        resultado = login_usuario(usuario, password)

        if not resultado["ok"]:
            return resultado

        self.usuario_actual = resultado["data"]

        return self._respuesta(
            True,
            "Sesión iniciada correctamente.",
            self.usuario_actual
        )

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.carrito.vaciar()

        return self._respuesta(
            True,
            "Sesión cerrada correctamente.",
            None
        )

    def crear_usuario_sistema(self, nombre, usuario, password, rol="VENDEDOR"):
        permiso = self._validar_permiso_actual("crear_usuario")

        if not permiso["ok"]:
            return permiso

        return crear_usuario(nombre, usuario, password, rol)

    def listar_usuarios_sistema(self):
        permiso = self._validar_permiso_actual("ver_usuarios")

        if not permiso["ok"]:
            return permiso

        return listar_usuarios()

    def cambiar_password_usuario(self, usuario_id, nuevo_password):
        permiso = self._validar_permiso_actual("editar_usuario")

        if not permiso["ok"]:
            return permiso

        return cambiar_password(usuario_id, nuevo_password)

    def activar_usuario_sistema(self, usuario_id):
        permiso = self._validar_permiso_actual("editar_usuario")

        if not permiso["ok"]:
            return permiso

        return activar_usuario(usuario_id)

    def desactivar_usuario_sistema(self, usuario_id):
        permiso = self._validar_permiso_actual("editar_usuario")

        if not permiso["ok"]:
            return permiso

        return desactivar_usuario(usuario_id)

    def permisos_usuario_actual(self):
        sesion = self._requiere_sesion()

        if not sesion["ok"]:
            return sesion

        try:
            return listar_permisos_rol(self.usuario_actual.get("rol"))
        except Exception:
            return self._respuesta(
                True,
                "Permisos cargados desde security.py.",
                []
            )

    def usuario_tiene_permiso(self, permiso):
        sesion = self._requiere_sesion()

        if not sesion["ok"]:
            return False

        rol = normalizar_rol(self.usuario_actual.get("rol"))

        permiso = str(permiso or "").strip()
        permiso_equivalente = PERMISOS_EQUIVALENTES.get(permiso)

        if tiene_permiso_accion(rol, permiso):
            return True

        if permiso_equivalente and tiene_permiso_accion(rol, permiso_equivalente):
            return True

        return False

    # =====================================================
    # PRODUCTOS
    # =====================================================

    def obtener_productos(self):
        permiso = self._validar_permiso_actual("ver_productos")

        if not permiso["ok"]:
            return permiso

        productos = listar_productos()

        return self._respuesta(
            True,
            "Productos obtenidos correctamente.",
            productos or []
        )

    def buscar_producto_codigo(self, codigo_barra):
        sesion = self._requiere_sesion()

        if not sesion["ok"]:
            return sesion

        codigo_barra = normalizar_codigo_barra(codigo_barra)

        producto = buscar_producto_por_codigo(codigo_barra)

        if not producto:
            return self._respuesta(
                False,
                "Producto no encontrado.",
                None
            )

        return self._respuesta(
            True,
            "Producto encontrado.",
            producto
        )

    def buscar_producto_nombre(self, texto):
        permiso = self._validar_permiso_actual("ver_productos")

        if not permiso["ok"]:
            return permiso

        texto = limpiar_texto(texto)

        productos = buscar_productos_por_nombre(texto)

        return self._respuesta(
            True,
            "Búsqueda realizada correctamente.",
            productos or []
        )

    def crear_producto_sistema(
        self,
        categoria_id,
        proveedor_id,
        codigo_barra,
        sku,
        nombre,
        descripcion,
        tipo_producto,
        unidad_medida,
        precio_compra,
        precio_venta,
        stock_actual,
        stock_minimo,
        permite_venta_sin_stock,
        requiere_mayoria_edad
    ):
        permiso = self._validar_permiso_actual("crear_producto")

        if not permiso["ok"]:
            return permiso

        resultado = crear_producto(
            categoria_id=categoria_id,
            proveedor_id=proveedor_id,
            codigo_barra=normalizar_codigo_barra(codigo_barra),
            sku=limpiar_texto(sku),
            nombre=limpiar_texto(nombre),
            descripcion=limpiar_texto(descripcion),
            tipo_producto=normalizar_mayusculas(tipo_producto),
            unidad_medida=normalizar_mayusculas(unidad_medida),
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            permite_venta_sin_stock=permite_venta_sin_stock,
            requiere_mayoria_edad=requiere_mayoria_edad
        )

        if not resultado:
            return self._respuesta(
                False,
                "No se pudo crear el producto.",
                None
            )

        return self._respuesta(
            True,
            "Producto creado correctamente.",
            {
                "producto_id": resultado
            }
        )

    def productos_con_bajo_stock(self):
        permiso = self._validar_permiso_actual("ver_productos")

        if not permiso["ok"]:
            return permiso

        productos = productos_bajo_stock()

        return self._respuesta(
            True,
            "Productos con bajo stock obtenidos correctamente.",
            productos or []
        )

    def desactivar_producto_sistema(self, producto_id):
        permiso = self._validar_permiso_actual("desactivar_producto")

        if not permiso["ok"]:
            return permiso

        resultado = desactivar_producto(producto_id)

        if resultado is None:
            return self._respuesta(
                False,
                "No se pudo desactivar el producto.",
                None
            )

        return self._respuesta(
            True,
            "Producto desactivado correctamente.",
            {
                "producto_id": producto_id
            }
        )

    # =====================================================
    # CATÁLOGOS
    # =====================================================

    def obtener_categorias(self, solo_activas=True):
        permiso = self._validar_permiso_actual("ver_productos")

        if not permiso["ok"]:
            return permiso

        return listar_categorias(solo_activas)

    def crear_categoria_sistema(self, nombre, descripcion=None):
        permiso = self._validar_permiso_actual("crear_producto")

        if not permiso["ok"]:
            return permiso

        return crear_categoria(nombre, descripcion)

    def actualizar_categoria_sistema(self, categoria_id, nombre, descripcion=None, activo=1):
        permiso = self._validar_permiso_actual("editar_producto")

        if not permiso["ok"]:
            return permiso

        return actualizar_categoria(categoria_id, nombre, descripcion, activo)

    def activar_categoria_sistema(self, categoria_id):
        permiso = self._validar_permiso_actual("editar_producto")

        if not permiso["ok"]:
            return permiso

        return activar_categoria(categoria_id)

    def desactivar_categoria_sistema(self, categoria_id):
        permiso = self._validar_permiso_actual("editar_producto")

        if not permiso["ok"]:
            return permiso

        return desactivar_categoria(categoria_id)

    def obtener_proveedores(self, solo_activos=True):
        permiso = self._validar_permiso_actual("ver_proveedores")

        if not permiso["ok"]:
            return permiso

        return listar_proveedores(solo_activos)

    def crear_proveedor_sistema(
        self,
        nombre,
        rut=None,
        contacto=None,
        telefono=None,
        email=None,
        direccion=None,
        notas=None
    ):
        permiso = self._validar_permiso_actual("crear_proveedor")

        if not permiso["ok"]:
            return permiso

        return crear_proveedor(
            nombre=nombre,
            rut=rut,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas
        )

    def actualizar_proveedor_sistema(
        self,
        proveedor_id,
        nombre,
        rut=None,
        contacto=None,
        telefono=None,
        email=None,
        direccion=None,
        notas=None,
        activo=1
    ):
        permiso = self._validar_permiso_actual("editar_proveedor")

        if not permiso["ok"]:
            return permiso

        return actualizar_proveedor(
            proveedor_id=proveedor_id,
            nombre=nombre,
            rut=rut,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
            activo=activo
        )

    def activar_proveedor_sistema(self, proveedor_id):
        permiso = self._validar_permiso_actual("editar_proveedor")

        if not permiso["ok"]:
            return permiso

        return activar_proveedor(proveedor_id)

    def desactivar_proveedor_sistema(self, proveedor_id):
        permiso = self._validar_permiso_actual("desactivar_proveedor")

        if not permiso["ok"]:
            return permiso

        return desactivar_proveedor(proveedor_id)

    # =====================================================
    # CAJA
    # =====================================================

    def abrir_caja_sistema(self, monto_inicial=0, observacion_apertura=None):
        permiso = self._validar_permiso_actual("abrir_caja")

        if not permiso["ok"]:
            return permiso

        return abrir_caja(
            usuario_id=self.obtener_usuario_id_actual(),
            monto_inicial=monto_inicial,
            observacion_apertura=observacion_apertura
        )

    def obtener_caja_abierta_sistema(self):
        permiso = self._validar_permiso_actual("ver_caja")

        if not permiso["ok"]:
            return permiso

        return obtener_caja_abierta()
    def obtener_resumen_caja(self):
            permiso = self._validar_permiso_actual("ver_caja")

            if not permiso["ok"]:
                return permiso

            return obtener_resumen_caja_actual()

    def registrar_ingreso_extra_caja(self, monto, descripcion=None):
        permiso = self._validar_permiso_actual("registrar_ingreso_extra")

        if not permiso["ok"]:
            return permiso

        return registrar_ingreso_extra(monto, descripcion)

    def registrar_retiro_caja(self, monto, descripcion=None):
        permiso = self._validar_permiso_actual("registrar_retiro")

        if not permiso["ok"]:
            return permiso

        return registrar_retiro(monto, descripcion)

    def cerrar_caja_sistema(self, monto_real_cierre, observacion_cierre=None):
        permiso = self._validar_permiso_actual("cerrar_caja")

        if not permiso["ok"]:
            return permiso

        return cerrar_caja(
            usuario_cierre_id=self.obtener_usuario_id_actual(),
            monto_real_cierre=monto_real_cierre,
            observacion_cierre=observacion_cierre
        )

    # =====================================================
    # CARRITO
    # =====================================================

    def carrito_agregar_producto(self, codigo_barra, cantidad=1, descuento_linea=0):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.agregar_producto(
            codigo_barra=codigo_barra,
            cantidad=cantidad,
            descuento_linea=descuento_linea
        )

    def carrito_eliminar_item(self, indice):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.eliminar_item(indice)

    def carrito_actualizar_cantidad(self, indice, cantidad):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.actualizar_cantidad(indice, cantidad)

    def carrito_actualizar_descuento_linea(self, indice, descuento_linea):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.actualizar_descuento_linea(indice, descuento_linea)

    def carrito_obtener_detalle(self):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self._respuesta(
            True,
            "Detalle de carrito obtenido correctamente.",
            self.carrito.obtener_detalle()
        )

    def carrito_obtener_resumen(self):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.obtener_resumen()

    def carrito_vaciar(self):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        return self.carrito.vaciar()

    # =====================================================
    # VENTAS
    # =====================================================

    def vender_carrito(
        self,
        metodo_pago="EFECTIVO",
        monto_efectivo=0,
        monto_tarjeta=0,
        monto_transferencia=0,
        tipo_documento="TICKET",
        numero_documento=None,
        descuento_total=0,
        observacion=None,
        confirmar_mayoria_edad=False
    ):
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        caja = self.obtener_caja_abierta_sistema()

        if not caja["ok"]:
            return self._respuesta(
                False,
                "Debe abrir caja antes de vender.",
                None
            )

        if self.carrito.esta_vacio():
            return self._respuesta(
                False,
                "No se puede vender porque el carrito está vacío.",
                None
            )

        resumen = self.carrito.obtener_resumen()

        if not resumen["ok"]:
            return resumen

        requiere_mayoria = resumen["data"].get("requiere_mayoria_edad", False)

        if requiere_mayoria and not confirmar_mayoria_edad:
            return self._respuesta(
                False,
                "La venta contiene productos que requieren mayoría de edad. Debe confirmar edad antes de continuar.",
                {
                    "requiere_mayoria_edad": True
                }
            )

        items = self.carrito.obtener_items_para_venta()

        resultado = realizar_venta(
            usuario_id=self.obtener_usuario_id_actual(),
            items=items,
            metodo_pago=normalizar_mayusculas(metodo_pago),
            monto_efectivo=monto_efectivo,
            monto_tarjeta=monto_tarjeta,
            monto_transferencia=monto_transferencia,
            tipo_documento=normalizar_mayusculas(tipo_documento),
            numero_documento=numero_documento,
            descuento_total=descuento_total,
            observacion=observacion
        )

        if resultado["ok"]:
            self.carrito.vaciar()

        return resultado

    def venta_directa(
        self,
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
        permiso = self._validar_permiso_actual("realizar_venta")

        if not permiso["ok"]:
            return permiso

        caja = self.obtener_caja_abierta_sistema()

        if not caja["ok"]:
            return self._respuesta(
                False,
                "Debe abrir caja antes de vender.",
                None
            )

        return realizar_venta(
            usuario_id=self.obtener_usuario_id_actual(),
            items=items,
            metodo_pago=normalizar_mayusculas(metodo_pago),
            monto_efectivo=monto_efectivo,
            monto_tarjeta=monto_tarjeta,
            monto_transferencia=monto_transferencia,
            tipo_documento=normalizar_mayusculas(tipo_documento),
            numero_documento=numero_documento,
            descuento_total=descuento_total,
            observacion=observacion
        )

    def obtener_ventas_hoy(self):
        permiso = self._validar_permiso_actual("ver_ventas")

        if not permiso["ok"]:
            return permiso

        return listar_ventas_del_dia()

    def buscar_venta_por_id(self, venta_id):
        permiso = self._validar_permiso_actual("ver_ventas")

        if not permiso["ok"]:
            return permiso

        return obtener_venta(venta_id)

    def buscar_venta_por_numero(self, numero_venta):
        permiso = self._validar_permiso_actual("ver_ventas")

        if not permiso["ok"]:
            return permiso

        return obtener_venta_por_numero(numero_venta)

    def anular_venta_sistema(self, venta_id, motivo, devolver_stock=True):
        permiso = self._validar_permiso_actual("anular_venta")

        if not permiso["ok"]:
            return permiso

        return anular_venta(
            venta_id=venta_id,
            usuario_id=self.obtener_usuario_id_actual(),
            motivo=motivo,
            devolver_stock=devolver_stock
        )

    def generar_ticket_venta(self, venta_id):
        permiso = self._validar_permiso_actual("generar_ticket")

        if not permiso["ok"]:
            return permiso

        return generar_ticket_texto(venta_id)

    def generar_ticket_por_numero_venta(self, numero_venta):
        permiso = self._validar_permiso_actual("generar_ticket")

        if not permiso["ok"]:
            return permiso

        venta = obtener_venta_por_numero(numero_venta)

        if not venta["ok"]:
            return venta

        return generar_ticket_texto(venta["data"]["id"])

    # =====================================================
    # INVENTARIO
    # =====================================================

    def ingresar_stock_producto(
        self,
        producto_id,
        cantidad,
        precio_compra=None,
        comentario="Ingreso de stock",
        actualizar_precio_compra=True
    ):
        permiso = self._validar_permiso_actual("ingresar_stock")

        if not permiso["ok"]:
            return permiso

        return ingresar_stock(
            producto_id=producto_id,
            usuario_id=self.obtener_usuario_id_actual(),
            cantidad=cantidad,
            precio_compra=precio_compra,
            comentario=comentario,
            actualizar_precio_compra=actualizar_precio_compra
        )

    def ajustar_stock_producto(
        self,
        producto_id,
        nuevo_stock,
        comentario="Ajuste manual de stock"
    ):
        permiso = self._validar_permiso_actual("ajustar_stock")

        if not permiso["ok"]:
            return permiso

        return ajustar_stock(
            producto_id=producto_id,
            usuario_id=self.obtener_usuario_id_actual(),
            nuevo_stock=nuevo_stock,
            comentario=comentario
        )

    def registrar_merma_producto(
        self,
        producto_id,
        cantidad,
        comentario="Merma de producto"
    ):
        permiso = self._validar_permiso_actual("ajustar_stock")

        if not permiso["ok"]:
            return permiso

        return registrar_merma(
            producto_id=producto_id,
            usuario_id=self.obtener_usuario_id_actual(),
            cantidad=cantidad,
            comentario=comentario
        )

    def actualizar_precio_producto_sistema(
        self,
        producto_id,
        nuevo_precio_venta,
        nuevo_precio_compra=None
    ):
        permiso = self._validar_permiso_actual("editar_producto")

        if not permiso["ok"]:
            return permiso

        return actualizar_precio_producto(
            producto_id=producto_id,
            nuevo_precio_venta=nuevo_precio_venta,
            nuevo_precio_compra=nuevo_precio_compra
        )

    def obtener_movimientos_inventario(self, producto_id=None, limite=100):
        permiso = self._validar_permiso_actual("ver_inventario")

        if not permiso["ok"]:
            return permiso

        return obtener_movimientos_stock(producto_id, limite)

    def obtener_sugerencia_reposicion(self):
        permiso = self._validar_permiso_actual("ver_inventario")

        if not permiso["ok"]:
            return permiso

        return sugerir_reposicion_stock()

    # =====================================================
    # REPORTES
    # =====================================================

    def obtener_dashboard(self):
        permiso = self._validar_permiso_actual("ver_dashboard")

        if not permiso["ok"]:
            return permiso

        return obtener_dashboard_principal()

    def reporte_ventas_del_dia(self):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return ventas_del_dia()

    def reporte_resumen_ventas_del_dia(self):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return resumen_ventas_del_dia()

    def reporte_ventas_por_rango(self, fecha_inicio, fecha_fin):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return ventas_por_rango(fecha_inicio, fecha_fin)

    def reporte_ganancia_por_rango(self, fecha_inicio, fecha_fin):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return ganancia_por_rango(fecha_inicio, fecha_fin)

    def reporte_productos_mas_vendidos(self, fecha_inicio, fecha_fin, limite=10):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return productos_mas_vendidos(fecha_inicio, fecha_fin, limite)

    def reporte_movimientos_stock_producto(self, producto_id):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return movimientos_stock_producto(producto_id)

    def reporte_resumen_caja_actual(self):
        permiso = self._validar_permiso_actual("ver_reportes")

        if not permiso["ok"]:
            return permiso

        return resumen_caja_actual()

    # =====================================================
    # CLIENTES
    # =====================================================

    def obtener_clientes(self, texto=None, solo_activos=True):
        permiso = self._validar_permiso_actual("ver_clientes")

        if not permiso["ok"]:
            return permiso

        if texto:
            return buscar_clientes(texto, solo_activos)

        return listar_clientes(solo_activos)

    def crear_cliente_sistema(
        self,
        nombre,
        rut=None,
        telefono=None,
        email=None,
        direccion=None,
        notas=None
    ):
        permiso = self._validar_permiso_actual("crear_cliente")

        if not permiso["ok"]:
            return permiso

        return crear_cliente(
            nombre=nombre,
            rut=rut,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas
        )

    def actualizar_cliente_sistema(
        self,
        cliente_id,
        nombre,
        rut=None,
        telefono=None,
        email=None,
        direccion=None,
        notas=None,
        activo=1
    ):
        permiso = self._validar_permiso_actual("editar_cliente")

        if not permiso["ok"]:
            return permiso

        return actualizar_cliente(
            cliente_id=cliente_id,
            nombre=nombre,
            rut=rut,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
            activo=activo
        )

    def activar_cliente_sistema(self, cliente_id):
        permiso = self._validar_permiso_actual("editar_cliente")

        if not permiso["ok"]:
            return permiso

        return activar_cliente(cliente_id)

    def desactivar_cliente_sistema(self, cliente_id):
        permiso = self._validar_permiso_actual("desactivar_cliente")

        if not permiso["ok"]:
            return permiso

        return desactivar_cliente(cliente_id)

    # =====================================================
    # COMPRAS
    # =====================================================

    def registrar_compra_sistema(
        self,
        proveedor_id=None,
        numero_documento=None,
        items=None,
        observacion=None
    ):
        permiso = self._validar_permiso_actual("registrar_compra")

        if not permiso["ok"]:
            return permiso

        return registrar_compra(
            usuario_id=self.obtener_usuario_id_actual(),
            proveedor_id=proveedor_id,
            numero_documento=numero_documento,
            items=items,
            observacion=observacion
        )

    def obtener_compras(self):
        permiso = self._validar_permiso_actual("ver_compras")

        if not permiso["ok"]:
            return permiso

        return listar_compras()

    def obtener_compra_sistema(self, compra_id):
        permiso = self._validar_permiso_actual("ver_compras")

        if not permiso["ok"]:
            return permiso

        return obtener_compra(compra_id)

    # =====================================================
    # CONFIGURACIÓN
    # =====================================================

    def obtener_configuracion(self):
        permiso = self._validar_permiso_actual("ver_configuracion")

        if not permiso["ok"]:
            return permiso

        return obtener_configuracion_negocio()

    def crear_configuracion(self, **kwargs):
        permiso = self._validar_permiso_actual("editar_configuracion")

        if not permiso["ok"]:
            return permiso

        return crear_configuracion_negocio(**kwargs)

    def actualizar_configuracion(self, **kwargs):
        permiso = self._validar_permiso_actual("editar_configuracion")

        if not permiso["ok"]:
            return permiso

        return actualizar_configuracion_negocio(**kwargs)

    # =====================================================
    # EXPORTACIÓN EXCEL
    # =====================================================

    def exportar_reporte_completo(
        self,
        ruta_archivo,
        fecha_inicio,
        fecha_fin
    ):
        permiso = self._validar_permiso_actual("exportar_reportes")

        if not permiso["ok"]:
            return permiso

        resumen = self.reporte_resumen_ventas_del_dia()
        ventas = self.reporte_ventas_por_rango(fecha_inicio, fecha_fin)
        productos = self.reporte_productos_mas_vendidos(fecha_inicio, fecha_fin, limite=50)
        ganancia = self.reporte_ganancia_por_rango(fecha_inicio, fecha_fin)
        caja = self.reporte_resumen_caja_actual()
        bajo_stock = self.productos_con_bajo_stock()

        if not resumen["ok"]:
            return resumen

        if not ventas["ok"]:
            return ventas

        if not productos["ok"]:
            return productos

        if not ganancia["ok"]:
            return ganancia

        if not caja["ok"]:
            return caja

        if not bajo_stock["ok"]:
            return bajo_stock

        return exportar_reporte_completo_excel(
            ruta_archivo=ruta_archivo,
            resumen=resumen["data"],
            ventas=ventas["data"],
            productos_mas_vendidos=productos["data"],
            ganancia=ganancia["data"],
            caja_actual=caja["data"],
            bajo_stock=bajo_stock["data"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

    def exportar_tabla_excel(self, ruta_archivo, nombre_hoja, headers, filas):
        permiso = self._validar_permiso_actual("exportar_reportes")

        if not permiso["ok"]:
            return permiso

        return exportar_tabla_simple_excel(
            ruta_archivo=ruta_archivo,
            nombre_hoja=nombre_hoja,
            headers=headers,
            filas=filas
        )

    # =====================================================
    # FORMATEADORES PARA LA INTERFAZ
    # =====================================================

    def formato_pesos(self, valor):
        return formatear_pesos(valor)

    def formato_fecha(self, fecha):
        return formatear_fecha(fecha)

    def formato_decimal(self, valor):
        return decimal_seguro(valor)

    def formato_dinero(self, valor):
        return dinero(valor)