from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QAbstractSpinBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.compras import registrar_compra, listar_compras, obtener_compra
from app.productos import buscar_producto_por_codigo
from app.database import ejecutar_consulta


class ComprasServiceAdapter:
    def __init__(self, usuario_id=1):
        self.usuario_id = usuario_id

    def _normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return {
            "ok": True,
            "mensaje": mensaje_ok,
            "data": resultado,
        }

    def formato_pesos(self, valor):
        try:
            valor = int(Decimal(str(valor or 0)))
            return f"${valor:,.0f}".replace(",", ".")
        except Exception:
            return "$0"

    def formato_fecha(self, fecha):
        if not fecha:
            return "-"

        try:
            return fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(fecha)

    def obtener_proveedores(self):
        try:
            resultado = ejecutar_consulta(
                """
                SELECT id, nombre
                FROM proveedores
                WHERE activo = 1
                ORDER BY nombre ASC;
                """,
                obtener_todos=True,
            )
        except Exception:
            try:
                resultado = ejecutar_consulta(
                    """
                    SELECT id, nombre
                    FROM proveedores
                    ORDER BY nombre ASC;
                    """,
                    obtener_todos=True,
                )
            except Exception:
                resultado = []

        return self._normalizar_respuesta(
            resultado,
            "Proveedores obtenidos correctamente.",
        )

    def buscar_producto_codigo(self, codigo):
        resultado = buscar_producto_por_codigo(codigo)
        return self._normalizar_respuesta(
            resultado,
            "Producto encontrado correctamente.",
        )

    def registrar_compra_sistema(
        self,
        proveedor_id=None,
        numero_documento=None,
        items=None,
        observacion=None,
    ):
        return registrar_compra(
            usuario_id=self.usuario_id,
            proveedor_id=proveedor_id,
            numero_documento=numero_documento,
            items=items,
            observacion=observacion,
        )

    def obtener_compras(self):
        return listar_compras()

    def obtener_compra_sistema(self, compra_id):
        return obtener_compra(compra_id)


class ComprasPage(QWidget):
    def __init__(self, pos_service=None, usuario_id=1):
        super().__init__()

        self.backend = ComprasServiceAdapter(usuario_id=usuario_id)
        self.pos = pos_service or self.backend

        self.items = []
        self.compras_cache = []
        self.compras_visibles = []

        self.actualizando_compras = False
        self.timer_compras = None

        self.combo_proveedor = QComboBox()
        self.input_documento = QLineEdit()
        self.input_codigo = QLineEdit()
        self.input_cantidad = QDoubleSpinBox()
        self.input_costo = QDoubleSpinBox()
        self.input_observacion = QTextEdit()
        self.input_busqueda_historial = QLineEdit()

        self.tabla_items = QTableWidget()
        self.tabla_compras = QTableWidget()

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.labels = {}
        self.cards = {}

        self.btn_quitar = None
        self.btn_limpiar = None
        self.btn_registrar = None
        self.btn_ver_detalle = None
        self.btn_copiar = None

        self.construir_interfaz()
        self.cargar_datos(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    # ============================================================
    # ACTUALIZACIÓN AUTOMÁTICA
    # ============================================================

    def iniciar_actualizacion_automatica(self):
        self.timer_compras = QTimer(self)
        self.timer_compras.timeout.connect(self.cargar_datos_automatico)
        self.timer_compras.start(10000)

    def cargar_datos_automatico(self):
        if self.actualizando_compras:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_datos(mostrar_mensaje=False)

    def actualizar_label_ultima_actualizacion(self):
        if self.label_ultima_actualizacion is None:
            return

        hora_actual = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora_actual}")

    # ============================================================
    # INTERFAZ
    # ============================================================

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()
        textos.setSpacing(6)

        titulo = QLabel("Compras")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Registra compras a proveedores, actualiza stock automáticamente y mantiene historial de ingreso."
        )
        subtitulo.setObjectName("subtituloPagina")
        subtitulo.setWordWrap(True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        estado_actualizacion = QVBoxLayout()
        estado_actualizacion.setSpacing(4)
        estado_actualizacion.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        label_auto = QLabel("Actualización automática")
        label_auto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_auto.setStyleSheet("""
            QLabel {
                color: #166534;
                font-size: 13px;
                font-weight: 800;
                background-color: #DCFCE7;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
                padding: 8px 14px;
            }
        """)

        self.label_ultima_actualizacion = QLabel("Última revisión: --:--:--")
        self.label_ultima_actualizacion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_ultima_actualizacion.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 12px;
                font-weight: 600;
                background-color: transparent;
            }
        """)

        estado_actualizacion.addWidget(label_auto)
        estado_actualizacion.addWidget(self.label_ultima_actualizacion)

        encabezado.addLayout(textos, 1)
        encabezado.addStretch()
        encabezado.addLayout(estado_actualizacion)

        layout.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["items_actuales"] = self.crear_card(
            cards, 0, 0,
            key="items_actuales",
            titulo="Items en compra",
            valor="0",
            detalle="Productos agregados al ingreso actual",
            tipo="azul",
        )

        self.labels["total_actual"] = self.crear_card(
            cards, 0, 1,
            key="total_actual",
            titulo="Total compra actual",
            valor="$0",
            detalle="Monto pendiente por registrar",
            tipo="verde",
        )

        self.labels["compras_hoy"] = self.crear_card(
            cards, 0, 2,
            key="compras_hoy",
            titulo="Compras de hoy",
            valor="0",
            detalle="Compras registradas en el día",
            tipo="neutro",
        )

        self.labels["total_hoy"] = self.crear_card(
            cards, 0, 3,
            key="total_hoy",
            titulo="Total comprado hoy",
            valor="$0",
            detalle="Suma de compras recibidas hoy",
            tipo="morado",
        )

        self.labels["total_historial"] = self.crear_card(
            cards, 1, 0,
            key="total_historial",
            titulo="Historial total",
            valor="0",
            detalle="Compras cargadas en historial",
            tipo="neutro",
        )

        self.labels["total_general"] = self.crear_card(
            cards, 1, 1,
            key="total_general",
            titulo="Total histórico",
            valor="$0",
            detalle="Suma total de compras cargadas",
            tipo="neutro",
        )

        self.labels["proveedores"] = self.crear_card(
            cards, 1, 2,
            key="proveedores",
            titulo="Proveedores activos",
            valor="0",
            detalle="Disponibles para asociar compras",
            tipo="azul",
        )

        self.labels["ultima_compra"] = self.crear_card(
            cards, 1, 3,
            key="ultima_compra",
            titulo="Última compra",
            valor="-",
            detalle="Registro más reciente",
            tipo="alerta",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando estado de compras...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_alertas)

        # ============================================================
        # PANEL NUEVA COMPRA
        # ============================================================

        panel_compra = QFrame()
        panel_compra.setObjectName("panelCompra")

        panel_layout = QVBoxLayout(panel_compra)
        panel_layout.setContentsMargins(18, 16, 18, 18)
        panel_layout.setSpacing(14)

        titulo_panel = QLabel("Nueva compra a proveedor")
        titulo_panel.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 18px;
                font-weight: 900;
                background: transparent;
            }
        """)

        ayuda_panel = QLabel(
            "Selecciona proveedor, ingresa documento y escanea productos. "
            "Al registrar la compra, el stock aumenta automáticamente."
        )
        ayuda_panel.setWordWrap(True)
        ayuda_panel.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                background: transparent;
            }
        """)

        panel_layout.addWidget(titulo_panel)
        panel_layout.addWidget(ayuda_panel)

        fila_datos = QHBoxLayout()
        fila_datos.setSpacing(12)

        self.combo_proveedor.setMinimumHeight(42)

        self.input_documento.setPlaceholderText("Número de documento, factura o guía")
        self.input_documento.setMinimumHeight(42)

        fila_datos.addWidget(QLabel("Proveedor:"))
        fila_datos.addWidget(self.combo_proveedor, 1)
        fila_datos.addWidget(QLabel("Documento:"))
        fila_datos.addWidget(self.input_documento, 2)

        panel_layout.addLayout(fila_datos)

        fila_producto = QHBoxLayout()
        fila_producto.setSpacing(12)

        self.input_codigo.setPlaceholderText("Código de barra del producto")
        self.input_codigo.setMinimumHeight(46)
        self.input_codigo.returnPressed.connect(self.agregar_producto)

        self.configurar_spinbox_compra(
            self.input_cantidad,
            decimales=3,
            minimo=0.001,
            maximo=999999999,
            paso=1,
            prefijo="",
            ancho=95,
        )
        self.input_cantidad.setValue(1)
        self.input_cantidad.setToolTip(
            "Ej: 1 unidad | 0.500 medio kilo | 1.250 kilo y cuarto"
        )

        self.configurar_spinbox_compra(
            self.input_costo,
            decimales=0,
            minimo=0,
            maximo=999999999,
            paso=100,
            prefijo="$ ",
            ancho=115,
        )
        self.input_costo.setValue(0)
        self.input_costo.setToolTip(
            "Si lo dejas en $0, se usa el precio de compra actual del producto."
        )

        control_cantidad = self.crear_control_spinbox(self.input_cantidad)
        control_costo = self.crear_control_spinbox(self.input_costo)

        btn_agregar = QPushButton("Agregar producto")
        btn_agregar.setObjectName("botonPrincipal")
        btn_agregar.setMinimumHeight(46)
        btn_agregar.setFixedWidth(190)
        btn_agregar.clicked.connect(self.agregar_producto)

        fila_producto.addWidget(self.input_codigo, 2)
        fila_producto.addWidget(QLabel("Cantidad:"))
        fila_producto.addWidget(control_cantidad)
        fila_producto.addWidget(QLabel("Costo:"))
        fila_producto.addWidget(control_costo)
        fila_producto.addWidget(btn_agregar)

        panel_layout.addLayout(fila_producto)

        self.tabla_items.setColumnCount(6)
        self.tabla_items.setHorizontalHeaderLabels([
            "Código",
            "Producto",
            "Cantidad",
            "Costo unitario",
            "Total línea",
            "Producto ID",
        ])
        self.preparar_tabla(self.tabla_items)
        self.tabla_items.setMinimumHeight(220)
        self.tabla_items.setColumnHidden(5, True)

        panel_layout.addWidget(self.tabla_items)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(12)

        self.btn_quitar = QPushButton("Quitar item")
        self.btn_quitar.setMinimumHeight(44)
        self.btn_quitar.clicked.connect(self.quitar_item)

        self.btn_limpiar = QPushButton("Limpiar compra")
        self.btn_limpiar.setMinimumHeight(44)
        self.btn_limpiar.clicked.connect(self.limpiar_compra)

        self.btn_registrar = QPushButton("Registrar compra")
        self.btn_registrar.setObjectName("botonPrincipal")
        self.btn_registrar.setMinimumHeight(46)
        self.btn_registrar.setFixedWidth(190)
        self.btn_registrar.clicked.connect(self.registrar_compra)

        fila_acciones.addWidget(self.btn_quitar)
        fila_acciones.addWidget(self.btn_limpiar)
        fila_acciones.addStretch()
        fila_acciones.addWidget(self.btn_registrar)

        panel_layout.addLayout(fila_acciones)

        self.input_observacion.setPlaceholderText(
            "Observación opcional: condición de entrega, descuento, responsable, etc."
        )
        self.input_observacion.setFixedHeight(70)

        panel_layout.addWidget(self.input_observacion)

        layout.addWidget(panel_compra)

        # ============================================================
        # HISTORIAL
        # ============================================================

        panel_historial = QFrame()
        panel_historial.setObjectName("panelHistorialCompras")

        historial_layout = QVBoxLayout(panel_historial)
        historial_layout.setContentsMargins(18, 16, 18, 18)
        historial_layout.setSpacing(14)

        titulo_historial = QLabel("Historial de compras")
        titulo_historial.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)

        barra_historial = QHBoxLayout()
        barra_historial.setSpacing(12)

        self.input_busqueda_historial.setPlaceholderText(
            "Buscar por proveedor, documento, estado, usuario o ID..."
        )
        self.input_busqueda_historial.setMinimumHeight(44)
        self.input_busqueda_historial.textChanged.connect(self.aplicar_filtro_historial)

        btn_limpiar_historial = QPushButton("Limpiar")
        btn_limpiar_historial.setMinimumHeight(44)
        btn_limpiar_historial.setFixedWidth(140)
        btn_limpiar_historial.clicked.connect(self.limpiar_filtro_historial)

        barra_historial.addWidget(self.input_busqueda_historial, 1)
        barra_historial.addWidget(btn_limpiar_historial)

        self.tabla_compras.setColumnCount(7)
        self.tabla_compras.setHorizontalHeaderLabels([
            "ID",
            "Fecha",
            "Proveedor",
            "Documento",
            "Total",
            "Estado",
            "Usuario",
        ])
        self.preparar_tabla(self.tabla_compras)
        self.tabla_compras.setMinimumHeight(310)
        self.tabla_compras.itemSelectionChanged.connect(self.actualizar_botones_historial)

        acciones_historial = QHBoxLayout()
        acciones_historial.setSpacing(12)

        self.btn_ver_detalle = QPushButton("Ver detalle")
        self.btn_ver_detalle.setMinimumHeight(44)
        self.btn_ver_detalle.clicked.connect(self.ver_detalle_compra)

        self.btn_copiar = QPushButton("Copiar resumen")
        self.btn_copiar.setMinimumHeight(44)
        self.btn_copiar.clicked.connect(self.copiar_resumen_compra)

        acciones_historial.addWidget(self.btn_ver_detalle)
        acciones_historial.addWidget(self.btn_copiar)
        acciones_historial.addStretch()

        historial_layout.addWidget(titulo_historial)
        historial_layout.addLayout(barra_historial)
        historial_layout.addWidget(self.tabla_compras)
        historial_layout.addLayout(acciones_historial)

        layout.addWidget(panel_historial)

        self.label_estado_operacion = QLabel("Compras listas para registrar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_estado_operacion)

        self.aplicar_estilos()
        self.actualizar_tabla_items()
        self.actualizar_botones_historial()

    def configurar_spinbox_compra(
        self,
        spinbox,
        decimales=0,
        minimo=0,
        maximo=999999999,
        paso=1,
        prefijo="",
        ancho=120,
    ):
        spinbox.setMinimum(minimo)
        spinbox.setMaximum(maximo)
        spinbox.setDecimals(decimales)
        spinbox.setSingleStep(paso)
        spinbox.setPrefix(prefijo)
        spinbox.setFixedWidth(ancho)
        spinbox.setMinimumHeight(38)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setAccelerated(True)
        spinbox.setKeyboardTracking(False)
        spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                color: #0F172A;
                font-size: 14px;
                font-weight: 800;
            }

            QDoubleSpinBox:focus {
                background-color: #FFFFFF;
            }
        """)

    def crear_control_spinbox(self, spinbox):
        contenedor = QFrame()
        contenedor.setObjectName("controlSpinCompra")
        contenedor.setFixedHeight(46)

        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(4)

        btn_menos = QPushButton("−")
        btn_menos.setObjectName("botonMiniSpin")
        btn_menos.setFixedSize(34, 36)
        btn_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menos.clicked.connect(lambda: spinbox.stepDown())

        btn_mas = QPushButton("+")
        btn_mas.setObjectName("botonMiniSpin")
        btn_mas.setFixedSize(34, 36)
        btn_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_mas.clicked.connect(lambda: spinbox.stepUp())

        layout.addWidget(btn_menos)
        layout.addWidget(spinbox)
        layout.addWidget(btn_mas)

        return contenedor

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardCompra")
        card.setProperty("tipo", tipo)
        card.setMinimumHeight(126)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("cardTitulo")
        label_titulo.setWordWrap(True)

        label_valor = QLabel(valor)
        label_valor.setObjectName("cardValor")

        label_detalle = QLabel(detalle)
        label_detalle.setObjectName("cardDetalle")
        label_detalle.setWordWrap(True)

        layout.addWidget(label_titulo)
        layout.addStretch()
        layout.addWidget(label_valor)
        layout.addWidget(label_detalle)

        grid.addWidget(card, fila, columna)
        self.cards[key] = card

        return label_valor

    def preparar_tabla(self, tabla):
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setShowGrid(True)

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def cargar_datos(self, mostrar_mensaje=False):
        if self.actualizando_compras:
            return

        self.actualizando_compras = True
        compra_id_anterior = self.obtener_id_compra_seleccionada_silencioso()

        try:
            self.cargar_proveedores()
            self.cargar_compras()

            self.restaurar_seleccion_compra(compra_id_anterior)
            self.actualizar_resumen_historial()
            self.actualizar_alertas()

            if mostrar_mensaje:
                self.actualizar_estado_operacion(
                    "Compras cargadas correctamente.",
                    "ok",
                )

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar compras automáticamente: {error}",
                "error",
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_compras = False
            self.actualizar_botones_historial()

    def cargar_proveedores(self):
        proveedor_actual = self.combo_proveedor.currentData()

        self.combo_proveedor.blockSignals(True)
        self.combo_proveedor.clear()
        self.combo_proveedor.addItem("Sin proveedor", None)

        resultado = self.obtener_proveedores()

        if resultado.get("ok"):
            proveedores = resultado.get("data") or []

            for proveedor in proveedores:
                self.combo_proveedor.addItem(
                    str(proveedor.get("nombre") or "Sin nombre"),
                    proveedor.get("id"),
                )

            self.labels["proveedores"].setText(str(len(proveedores)))

        index = self.combo_proveedor.findData(proveedor_actual)

        if index >= 0:
            self.combo_proveedor.setCurrentIndex(index)

        self.combo_proveedor.blockSignals(False)

    def obtener_proveedores(self):
        metodo = getattr(self.pos, "obtener_proveedores", None)

        if callable(metodo):
            try:
                resultado = metodo(solo_activos=True)
            except TypeError:
                resultado = metodo()
            except Exception:
                resultado = None

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            if resultado is not None:
                return {
                    "ok": True,
                    "mensaje": "Proveedores obtenidos correctamente.",
                    "data": resultado or [],
                }

        return self.backend.obtener_proveedores()

    def cargar_compras(self):
        resultado = self.obtener_compras()

        if not resultado.get("ok"):
            self.compras_cache = []
            self.compras_visibles = []
            self.cargar_tabla_compras([])
            self.actualizar_estado_operacion(
                resultado.get("mensaje", "No se pudieron cargar las compras."),
                "error",
            )
            return

        self.compras_cache = resultado.get("data") or []
        self.compras_visibles = self.filtrar_compras_local(
            self.compras_cache,
            self.input_busqueda_historial.text().strip(),
        )

        self.cargar_tabla_compras(self.compras_visibles)

    def obtener_compras(self):
        posibles_metodos = [
            "obtener_compras",
            "listar_compras_sistema",
            "obtener_compras_sistema",
            "listar_compras",
        ]

        ultimo_error = None

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo()
            except Exception as error:
                ultimo_error = error
                continue

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            return {
                "ok": True,
                "mensaje": "Compras obtenidas correctamente.",
                "data": resultado or [],
            }

        try:
            return self.backend.obtener_compras()
        except Exception as error:
            ultimo_error = error

        mensaje = "No existe método para listar compras."

        if ultimo_error is not None:
            mensaje += f" Último error: {ultimo_error}"

        return {
            "ok": False,
            "mensaje": mensaje,
            "data": [],
        }

    # ============================================================
    # PRODUCTOS EN COMPRA
    # ============================================================

    def agregar_producto(self):
        codigo = self.input_codigo.text().strip()

        if not codigo:
            QMessageBox.warning(
                self,
                "Código requerido",
                "Ingresa o escanea el código de barra del producto.",
            )
            self.input_codigo.setFocus()
            return

        resultado = self.buscar_producto(codigo)

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Producto no encontrado",
                resultado.get("mensaje", "No se encontró el producto."),
            )
            self.input_codigo.selectAll()
            self.input_codigo.setFocus()
            return

        producto = resultado.get("data")

        if not isinstance(producto, dict):
            QMessageBox.warning(
                self,
                "Producto inválido",
                "La búsqueda no devolvió un producto válido.",
            )
            return

        cantidad = Decimal(str(self.input_cantidad.value()))
        costo = Decimal(str(self.input_costo.value()))

        if cantidad <= 0:
            QMessageBox.warning(
                self,
                "Cantidad inválida",
                "La cantidad debe ser mayor a 0.",
            )
            return

        if costo <= 0:
            costo = Decimal(str(producto.get("precio_compra") or 0))

        if costo <= 0:
            QMessageBox.warning(
                self,
                "Costo requerido",
                "Ingresa un costo de compra válido o define precio de compra en el producto.",
            )
            self.input_costo.setFocus()
            return

        item_nuevo = {
            "producto_id": producto.get("id"),
            "codigo_barra": producto.get("codigo_barra"),
            "nombre": producto.get("nombre"),
            "cantidad": cantidad,
            "costo_unitario": costo,
            "total_linea": cantidad * costo,
        }

        self.agregar_o_sumar_item(item_nuevo)

        self.input_codigo.clear()
        self.input_cantidad.setValue(1)
        self.input_costo.setValue(0)
        self.input_codigo.setFocus()

        self.actualizar_tabla_items()
        self.actualizar_estado_operacion(
            "Producto agregado correctamente a la compra.",
            "ok",
        )

    def buscar_producto(self, codigo):
        posibles_metodos = [
            "buscar_producto_codigo",
            "buscar_producto_por_codigo",
            "buscar_producto_codigo_sistema",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(codigo)
            except Exception as error:
                return {
                    "ok": False,
                    "mensaje": f"Error al buscar producto: {error}",
                    "data": None,
                }

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            if isinstance(resultado, dict):
                return {
                    "ok": True,
                    "mensaje": "Producto encontrado.",
                    "data": resultado,
                }

            return {
                "ok": False,
                "mensaje": "Producto no encontrado.",
                "data": None,
            }

        return self.backend.buscar_producto_codigo(codigo)

    def agregar_o_sumar_item(self, item_nuevo):
        for item in self.items:
            mismo_producto = str(item.get("producto_id")) == str(item_nuevo.get("producto_id"))
            mismo_costo = Decimal(str(item.get("costo_unitario"))) == Decimal(str(item_nuevo.get("costo_unitario")))

            if mismo_producto and mismo_costo:
                item["cantidad"] = Decimal(str(item["cantidad"])) + Decimal(str(item_nuevo["cantidad"]))
                item["total_linea"] = item["cantidad"] * item["costo_unitario"]
                return

        self.items.append(item_nuevo)

    def actualizar_tabla_items(self):
        self.tabla_items.setRowCount(0)

        total = Decimal("0")

        if not self.items:
            self.tabla_items.setRowCount(1)
            item = QTableWidgetItem("No hay productos agregados a esta compra.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_items.setItem(0, 0, item)

            for columna in range(1, self.tabla_items.columnCount()):
                self.tabla_items.setItem(0, columna, QTableWidgetItem(""))

        else:
            for fila, item_compra in enumerate(self.items):
                self.tabla_items.insertRow(fila)

                total += Decimal(str(item_compra["total_linea"]))

                valores = [
                    item_compra["codigo_barra"],
                    item_compra["nombre"],
                    self.formato_numero(item_compra["cantidad"]),
                    self.formato_pesos(item_compra["costo_unitario"]),
                    self.formato_pesos(item_compra["total_linea"]),
                    item_compra["producto_id"],
                ]

                for columna, valor in enumerate(valores):
                    celda = QTableWidgetItem(str(valor or ""))

                    if columna == 1:
                        celda.setTextAlignment(
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                        )
                    else:
                        celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.tabla_items.setItem(fila, columna, celda)

        self.labels["items_actuales"].setText(str(len(self.items)))
        self.labels["total_actual"].setText(self.formato_pesos(total))

        if len(self.items) > 0:
            self.cambiar_tipo_card("items_actuales", "azul")
            self.cambiar_tipo_card("total_actual", "verde")
        else:
            self.cambiar_tipo_card("items_actuales", "neutro")
            self.cambiar_tipo_card("total_actual", "neutro")

        self.actualizar_botones_compra()

    def quitar_item(self):
        fila = self.tabla_items.currentRow()

        if fila < 0 or fila >= len(self.items):
            QMessageBox.warning(
                self,
                "Sin selección",
                "Selecciona un producto de la compra para quitarlo.",
            )
            return

        self.items.pop(fila)
        self.actualizar_tabla_items()
        self.actualizar_estado_operacion("Producto quitado de la compra.", "info")

    def limpiar_compra(self):
        if self.items:
            confirmar = QMessageBox.question(
                self,
                "Limpiar compra",
                "¿Seguro que deseas limpiar la compra actual?",
            )

            if confirmar != QMessageBox.StandardButton.Yes:
                return

        self.items = []
        self.input_documento.clear()
        self.input_observacion.clear()
        self.input_codigo.clear()
        self.input_cantidad.setValue(1)
        self.input_costo.setValue(0)
        self.actualizar_tabla_items()
        self.input_codigo.setFocus()
        self.actualizar_estado_operacion("Compra actual limpiada.", "info")

    def registrar_compra(self):
        if not self.items:
            QMessageBox.warning(
                self,
                "Compra vacía",
                "Agrega productos antes de registrar la compra.",
            )
            return

        total = self.calcular_total_actual()

        confirmar = QMessageBox.question(
            self,
            "Registrar compra",
            f"¿Deseas registrar esta compra por {self.formato_pesos(total)}?\n\n"
            "El stock de los productos aumentará automáticamente.",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        items_compra = []

        for item in self.items:
            items_compra.append({
                "producto_id": item["producto_id"],
                "codigo_barra": item["codigo_barra"],
                "cantidad": item["cantidad"],
                "costo_unitario": item["costo_unitario"],
            })

        resultado = self.registrar_compra_backend(
            proveedor_id=self.combo_proveedor.currentData(),
            numero_documento=self.input_documento.text().strip(),
            items=items_compra,
            observacion=self.input_observacion.toPlainText().strip(),
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo registrar la compra."),
            )
            return

        QMessageBox.information(
            self,
            "Compra registrada",
            resultado.get("mensaje", "Compra registrada correctamente."),
        )

        self.items = []
        self.input_documento.clear()
        self.input_observacion.clear()
        self.input_codigo.clear()
        self.input_cantidad.setValue(1)
        self.input_costo.setValue(0)
        self.actualizar_tabla_items()
        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion(
            "Compra registrada correctamente. Stock actualizado automáticamente.",
            "ok",
        )

    def registrar_compra_backend(self, proveedor_id, numero_documento, items, observacion):
        metodo = getattr(self.pos, "registrar_compra_sistema", None)

        if callable(metodo):
            return metodo(
                proveedor_id=proveedor_id,
                numero_documento=numero_documento,
                items=items,
                observacion=observacion,
            )

        return self.backend.registrar_compra_sistema(
            proveedor_id=proveedor_id,
            numero_documento=numero_documento,
            items=items,
            observacion=observacion,
        )

    # ============================================================
    # HISTORIAL
    # ============================================================

    def aplicar_filtro_historial(self):
        self.compras_visibles = self.filtrar_compras_local(
            self.compras_cache,
            self.input_busqueda_historial.text().strip(),
        )

        self.cargar_tabla_compras(self.compras_visibles)
        self.actualizar_resumen_historial()
        self.actualizar_estado_operacion(
            f"Mostrando {len(self.compras_visibles)} compra(s).",
            "info",
        )

    def limpiar_filtro_historial(self):
        self.input_busqueda_historial.clear()
        self.input_busqueda_historial.setFocus()
        self.aplicar_filtro_historial()

    def filtrar_compras_local(self, compras, texto):
        texto = str(texto or "").lower().strip()

        if not texto:
            return list(compras)

        filtradas = []

        for compra in compras:
            campos = [
                compra.get("id"),
                compra.get("proveedor"),
                compra.get("numero_documento"),
                compra.get("estado"),
                compra.get("usuario"),
                compra.get("observacion"),
            ]

            texto_compra = " ".join(str(campo or "").lower() for campo in campos)

            if texto in texto_compra:
                filtradas.append(compra)

        return filtradas

    def cargar_tabla_compras(self, compras):
        self.tabla_compras.setRowCount(0)

        if not compras:
            self.tabla_compras.setRowCount(1)

            item = QTableWidgetItem("No hay compras para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_compras.setItem(0, 0, item)

            for columna in range(1, self.tabla_compras.columnCount()):
                self.tabla_compras.setItem(0, columna, QTableWidgetItem(""))

            return

        for fila, compra in enumerate(compras):
            self.tabla_compras.insertRow(fila)

            valores = [
                compra.get("id"),
                self.formato_fecha(compra.get("fecha_compra")),
                compra.get("proveedor") or "Sin proveedor",
                compra.get("numero_documento") or "-",
                self.formato_pesos(compra.get("total")),
                compra.get("estado") or "-",
                compra.get("usuario") or "-",
            ]

            for columna, valor in enumerate(valores):
                celda = QTableWidgetItem(str(valor or ""))

                if columna in [2, 3, 6]:
                    celda.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                estado = str(compra.get("estado") or "").upper()

                if estado == "RECIBIDA":
                    celda.setForeground(QColor("#166534"))
                elif estado in ["ANULADA", "CANCELADA"]:
                    celda.setBackground(QColor("#FEF2F2"))
                    celda.setForeground(QColor("#991B1B"))

                self.tabla_compras.setItem(fila, columna, celda)

    def actualizar_resumen_historial(self):
        compras = self.compras_cache or []
        compras_visibles = self.compras_visibles or []

        hoy = QDateTime.currentDateTime().toString("yyyy-MM-dd")

        cantidad_hoy = 0
        total_hoy = Decimal("0")
        total_general = Decimal("0")
        ultima_compra = "-"

        for index, compra in enumerate(compras):
            total = self.decimal(compra.get("total"))
            total_general += total

            fecha = compra.get("fecha_compra")
            fecha_texto = str(fecha or "")

            if fecha_texto.startswith(hoy):
                cantidad_hoy += 1
                total_hoy += total

            if index == 0:
                ultima_compra = self.formato_pesos(total)

        self.labels["compras_hoy"].setText(str(cantidad_hoy))
        self.labels["total_hoy"].setText(self.formato_pesos(total_hoy))
        self.labels["total_historial"].setText(str(len(compras_visibles)))
        self.labels["total_general"].setText(self.formato_pesos(total_general))
        self.labels["ultima_compra"].setText(str(ultima_compra))

        self.cambiar_tipo_card("compras_hoy", "verde" if cantidad_hoy > 0 else "neutro")
        self.cambiar_tipo_card("total_hoy", "verde" if total_hoy > 0 else "neutro")
        self.cambiar_tipo_card("ultima_compra", "verde" if compras else "alerta")

    def actualizar_alertas(self):
        alertas = []

        if self.combo_proveedor.count() <= 1:
            alertas.append("No hay proveedores activos cargados.")

        if self.items:
            alertas.append(
                f"Hay una compra en edición con {len(self.items)} item(s) pendiente(s) de registrar."
            )

        if not self.compras_cache:
            alertas.append("Aún no hay compras registradas en el historial.")

        if not alertas:
            self.label_alertas.setText(
                "Compras en buen estado: historial cargado y módulo listo para registrar ingresos de stock."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de compras: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def obtener_id_compra_seleccionada_silencioso(self):
        fila = self.tabla_compras.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla_compras.item(fila, 0)

        if item_id is None:
            return None

        try:
            return int(item_id.text())
        except Exception:
            return None

    def restaurar_seleccion_compra(self, compra_id):
        if compra_id is None:
            return

        for fila in range(self.tabla_compras.rowCount()):
            item_id = self.tabla_compras.item(fila, 0)

            if item_id and item_id.text().isdigit() and int(item_id.text()) == compra_id:
                self.tabla_compras.selectRow(fila)
                return

    def obtener_compra_seleccionada(self, mostrar_mensaje=True):
        compra_id = self.obtener_id_compra_seleccionada_silencioso()

        if compra_id is None:
            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Sin selección",
                    "Selecciona una compra del historial.",
                )
            return None

        for compra in self.compras_cache:
            try:
                if int(compra.get("id")) == compra_id:
                    return compra
            except Exception:
                continue

        if mostrar_mensaje:
            QMessageBox.warning(
                self,
                "Compra no encontrada",
                "No se pudo encontrar la compra seleccionada.",
            )

        return None

    def obtener_detalle_compra_backend(self, compra_id):
        posibles_metodos = [
            "obtener_compra_sistema",
            "obtener_compra",
            "obtener_detalle_compra",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(compra_id)
            except Exception as error:
                return {
                    "ok": False,
                    "mensaje": f"Error al obtener detalle: {error}",
                    "data": None,
                }

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            return {
                "ok": True,
                "mensaje": "Detalle obtenido correctamente.",
                "data": resultado,
            }

        return self.backend.obtener_compra_sistema(compra_id)

    def ver_detalle_compra(self):
        compra = self.obtener_compra_seleccionada()

        if not compra:
            return

        resultado = self.obtener_detalle_compra_backend(compra.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Detalle no disponible",
                resultado.get("mensaje", "No se pudo obtener el detalle de compra."),
            )
            return

        data = resultado.get("data") or {}
        detalle = data.get("detalle") or []

        lineas = [
            f"Compra ID: {data.get('id')}",
            f"Fecha: {self.formato_fecha(data.get('fecha_compra'))}",
            f"Proveedor: {data.get('proveedor') or 'Sin proveedor'}",
            f"Documento: {data.get('numero_documento') or '-'}",
            f"Usuario: {data.get('usuario') or '-'}",
            f"Estado: {data.get('estado') or '-'}",
            f"Total: {self.formato_pesos(data.get('total'))}",
            "",
            "DETALLE:",
        ]

        if not detalle:
            lineas.append("Sin detalle registrado.")
        else:
            for item in detalle:
                lineas.append(
                    f"- {item.get('nombre_producto')} | "
                    f"Cant: {self.formato_numero(item.get('cantidad'))} | "
                    f"Costo: {self.formato_pesos(item.get('costo_unitario'))} | "
                    f"Total: {self.formato_pesos(item.get('total_linea'))}"
                )

        QMessageBox.information(
            self,
            "Detalle de compra",
            "\n".join(lineas),
        )

    def copiar_resumen_compra(self):
        compra = self.obtener_compra_seleccionada()

        if not compra:
            return

        texto = "\n".join([
            "COMPRA",
            "========================",
            f"ID: {compra.get('id')}",
            f"Fecha: {self.formato_fecha(compra.get('fecha_compra'))}",
            f"Proveedor: {compra.get('proveedor') or 'Sin proveedor'}",
            f"Documento: {compra.get('numero_documento') or '-'}",
            f"Total: {self.formato_pesos(compra.get('total'))}",
            f"Estado: {compra.get('estado') or '-'}",
            f"Usuario: {compra.get('usuario') or '-'}",
            "",
            f"Observación: {compra.get('observacion') or ''}",
        ])

        QApplication.clipboard().setText(texto)
        self.actualizar_estado_operacion(
            "Resumen de compra copiado al portapapeles.",
            "ok",
        )

    def actualizar_botones_historial(self):
        compra = self.obtener_compra_seleccionada(mostrar_mensaje=False)
        hay_seleccion = compra is not None

        if self.btn_ver_detalle is not None:
            self.btn_ver_detalle.setEnabled(hay_seleccion)

        if self.btn_copiar is not None:
            self.btn_copiar.setEnabled(hay_seleccion)

    def actualizar_botones_compra(self):
        hay_items = len(self.items) > 0

        if self.btn_quitar is not None:
            self.btn_quitar.setEnabled(hay_items)

        if self.btn_limpiar is not None:
            self.btn_limpiar.setEnabled(hay_items)

        if self.btn_registrar is not None:
            self.btn_registrar.setEnabled(hay_items)

    # ============================================================
    # UTILIDADES
    # ============================================================

    def calcular_total_actual(self):
        total = Decimal("0")

        for item in self.items:
            total += Decimal(str(item.get("total_linea") or 0))

        return total

    def decimal(self, valor):
        try:
            return Decimal(str(valor or 0))
        except Exception:
            return Decimal("0")

    def formato_pesos(self, valor):
        metodo = getattr(self.pos, "formato_pesos", None)

        if callable(metodo):
            try:
                return metodo(valor)
            except Exception:
                pass

        try:
            valor = int(Decimal(str(valor or 0)))
            return f"${valor:,.0f}".replace(",", ".")
        except Exception:
            return "$0"

    def formato_numero(self, valor):
        try:
            numero = Decimal(str(valor or 0))

            if numero == numero.to_integral():
                return str(int(numero))

            return f"{numero:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return "0"

    def formato_fecha(self, fecha):
        if not fecha:
            return "-"

        metodo = getattr(self.pos, "formato_fecha", None)

        if callable(metodo):
            try:
                return metodo(fecha)
            except Exception:
                pass

        try:
            return fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(fecha)

    def actualizar_estado_operacion(self, texto, tipo="info"):
        if self.label_estado_operacion is None:
            return

        self.label_estado_operacion.setText(texto)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta(tipo))

    def cambiar_tipo_card(self, key, tipo):
        card = self.cards.get(key)

        if card is None:
            return

        card.setProperty("tipo", tipo)
        card.style().unpolish(card)
        card.style().polish(card)

    def estilo_alerta(self, tipo):
        if tipo == "ok":
            return """
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 12px;
                    padding: 12px;
                    color: #166534;
                    font-size: 13px;
                    font-weight: 800;
                }
            """

        if tipo == "error":
            return """
                QLabel {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 12px;
                    padding: 12px;
                    color: #B91C1C;
                    font-size: 13px;
                    font-weight: 800;
                }
            """

        if tipo == "alerta":
            return """
                QLabel {
                    background-color: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 12px;
                    padding: 12px;
                    color: #92400E;
                    font-size: 13px;
                    font-weight: 800;
                }
            """

        return """
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px;
                color: #334155;
                font-size: 13px;
                font-weight: 700;
            }
        """

    # ============================================================
    # ESTILOS
    # ============================================================

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QFrame#panelCompra,
            QFrame#panelHistorialCompras {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#controlSpinCompra {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
            }

            QFrame#controlSpinCompra:hover {
                border: 1px solid #94A3B8;
            }

            QFrame#cardCompra {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardCompra[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardCompra[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardCompra[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardCompra[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardCompra[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardCompra[tipo="neutro"] {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
            }

            QLabel#cardTitulo {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
                background-color: transparent;
            }

            QLabel#cardValor {
                color: #0F172A;
                font-size: 26px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#cardDetalle {
                color: #64748B;
                font-size: 12px;
                font-weight: 600;
                background-color: transparent;
            }

            QLineEdit,
            QComboBox,
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 12px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QTextEdit:focus {
                border: 1px solid #2563EB;
            }

            QPushButton {
                background-color: #111827;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #1F2937;
            }

            QPushButton#botonPrincipal {
                background-color: #2563EB;
                color: white;
            }

            QPushButton#botonPrincipal:hover {
                background-color: #1D4ED8;
            }

            QPushButton#botonMiniSpin {
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-radius: 9px;
                font-size: 17px;
                font-weight: 900;
                padding: 0px;
            }

            QPushButton#botonMiniSpin:hover {
                background-color: #DBEAFE;
                border: 1px solid #BFDBFE;
                color: #1D4ED8;
            }

            QPushButton#botonMiniSpin:pressed {
                background-color: #2563EB;
                border: 1px solid #2563EB;
                color: white;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
                border: none;
                border-radius: 10px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                gridline-color: #E5E7EB;
                color: #0F172A;
                alternate-background-color: #F8FAFC;
            }

            QHeaderView::section {
                background-color: #F8FAFC;
                color: #0F172A;
                font-weight: 900;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 10px;
            }

            QTableWidget::item {
                padding: 8px;
            }
        """)