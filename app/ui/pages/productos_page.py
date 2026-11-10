from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QDoubleSpinBox,
    QAbstractSpinBox,
    QCheckBox,
    QFrame,
    QSizePolicy,
    QApplication,
    QStackedWidget,
    QScrollArea,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.productos import (
    listar_productos,
    crear_producto,
    actualizar_stock,
    desactivar_producto,
)
from app.database import ejecutar_consulta


class ItemTablaOrdenable(QTableWidgetItem):
    def __lt__(self, otro):
        valor_actual = self.data(Qt.ItemDataRole.UserRole)
        valor_otro = otro.data(Qt.ItemDataRole.UserRole)

        if valor_actual is not None and valor_otro is not None:
            try:
                return Decimal(str(valor_actual)) < Decimal(str(valor_otro))
            except Exception:
                return str(valor_actual).lower() < str(valor_otro).lower()

        return self.text().lower() < otro.text().lower()


class ProductosServiceAdapter:
    def formato_pesos(self, valor):
        try:
            valor = int(Decimal(str(valor or 0)))
            return f"${valor:,.0f}".replace(",", ".")
        except Exception:
            return "$0"

    def _normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return {
            "ok": True,
            "mensaje": mensaje_ok,
            "data": resultado,
        }

    def listar_productos_sistema(self):
        resultado = listar_productos()
        return self._normalizar_respuesta(
            resultado,
            "Productos cargados correctamente.",
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
        requiere_mayoria_edad,
    ):
        resultado = crear_producto(
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
            permite_venta_sin_stock=permite_venta_sin_stock,
            requiere_mayoria_edad=requiere_mayoria_edad,
        )

        return self._normalizar_respuesta(
            resultado,
            "Producto creado correctamente.",
        )

    def actualizar_stock_sistema(self, producto_id, nuevo_stock):
        resultado = actualizar_stock(producto_id, nuevo_stock)
        return self._normalizar_respuesta(
            resultado,
            "Stock actualizado correctamente.",
        )

    def desactivar_producto_sistema(self, producto_id):
        resultado = desactivar_producto(producto_id)
        return self._normalizar_respuesta(
            resultado,
            "Producto desactivado correctamente.",
        )

    def obtener_categorias(self):
        try:
            resultado = ejecutar_consulta(
                """
                SELECT id, nombre
                FROM categorias
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
                    FROM categorias
                    ORDER BY nombre ASC;
                    """,
                    obtener_todos=True,
                )
            except Exception:
                resultado = []

        return self._normalizar_respuesta(resultado, "Categorías obtenidas.")

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

        return self._normalizar_respuesta(resultado, "Proveedores obtenidos.")


class CrearProductoDialog(QDialog):
    def __init__(self, pos_service, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.backend = ProductosServiceAdapter()

        self.setWindowTitle("Crear producto")
        self.setMinimumSize(760, 680)
        self.resize(780, 720)

        self.combo_categoria = None
        self.combo_proveedor = None
        self.input_codigo = None
        self.input_sku = None
        self.input_nombre = None
        self.input_descripcion = None
        self.combo_unidad = None
        self.input_precio_compra = None
        self.input_precio_venta = None
        self.input_stock = None
        self.input_stock_minimo = None
        self.check_sin_stock = None
        self.check_mayoria_edad = None
        self.label_margen = None

        self.construir_interfaz()
        self.cargar_catalogos()
        self.actualizar_margen()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 20)
        layout.setSpacing(16)

        titulo = QLabel("Crear nuevo producto")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 25px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        ayuda = QLabel(
            "Registra el producto con categoría, código de barra, precios, stock y reglas de venta."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        layout.addWidget(titulo)
        layout.addWidget(ayuda)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        contenido_scroll = QWidget()
        contenido_layout = QVBoxLayout(contenido_scroll)
        contenido_layout.setContentsMargins(0, 0, 12, 0)
        contenido_layout.setSpacing(14)

        panel_formulario = QFrame()
        panel_formulario.setObjectName("panelFormularioProducto")

        panel_layout = QVBoxLayout(panel_formulario)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.combo_categoria = QComboBox()
        self.combo_proveedor = QComboBox()

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Ej: 7800000000011")

        self.input_sku = QLineEdit()
        self.input_sku.setPlaceholderText("Ej: PROD-001")

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Producto o servicio")

        self.input_descripcion = QTextEdit()
        self.input_descripcion.setPlaceholderText("Descripción opcional del producto")
        self.input_descripcion.setFixedHeight(76)

        self.combo_unidad = QComboBox()
        self.combo_unidad.addItems([
            "UNIDAD",
            "PACK",
            "CAJA",
            "KG",
            "LITRO",
            "GRAMO",
            "METRO",
            "SERVICIO",
        ])

        self.input_precio_compra = self.crear_input_monto()
        self.input_precio_venta = self.crear_input_monto()
        self.input_precio_compra.valueChanged.connect(self.actualizar_margen)
        self.input_precio_venta.valueChanged.connect(self.actualizar_margen)

        self.input_stock = self.crear_input_stock(valor=0, minimo=0, decimales=3)
        self.input_stock_minimo = self.crear_input_stock(valor=5, minimo=0, decimales=3)

        control_precio_compra = self.crear_control_spinbox(self.input_precio_compra)
        control_precio_venta = self.crear_control_spinbox(self.input_precio_venta)
        control_stock = self.crear_control_spinbox(self.input_stock)
        control_stock_minimo = self.crear_control_spinbox(self.input_stock_minimo)

        self.check_sin_stock = QCheckBox("Permitir vender sin stock")
        self.check_mayoria_edad = QCheckBox("Requiere mayoría de edad")

        self.label_margen = QLabel("Margen estimado: $0")
        self.label_margen.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 12px;
                color: #334155;
                font-size: 14px;
                font-weight: 800;
            }
        """)

        for widget in [
            self.combo_categoria,
            self.combo_proveedor,
            self.input_codigo,
            self.input_sku,
            self.input_nombre,
            self.combo_unidad,
            self.input_precio_compra,
            self.input_precio_venta,
            self.input_stock,
            self.input_stock_minimo,
        ]:
            widget.setMinimumHeight(42)

        form.addRow("Categoría:", self.combo_categoria)
        form.addRow("Proveedor:", self.combo_proveedor)
        form.addRow("Código de barra:", self.input_codigo)
        form.addRow("SKU:", self.input_sku)
        form.addRow("Nombre:", self.input_nombre)
        form.addRow("Descripción:", self.input_descripcion)
        form.addRow("Unidad medida:", self.combo_unidad)
        form.addRow("Precio compra:", control_precio_compra)
        form.addRow("Precio venta:", control_precio_venta)
        form.addRow("Margen:", self.label_margen)
        form.addRow("Stock inicial:", control_stock)
        form.addRow("Stock mínimo:", control_stock_minimo)
        form.addRow("", self.check_sin_stock)
        form.addRow("", self.check_mayoria_edad)

        panel_layout.addLayout(form)
        contenido_layout.addWidget(panel_formulario)
        contenido_layout.addStretch()

        scroll.setWidget(contenido_scroll)
        layout.addWidget(scroll, 1)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: #E5E7EB;")
        layout.addWidget(linea)

        botones = QHBoxLayout()
        botones.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar producto")
        btn_guardar.setObjectName("botonPrincipal")
        btn_guardar.clicked.connect(self.guardar_producto)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addLayout(botones)

        self.setStyleSheet("""
            QFrame#panelFormularioProducto {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#controlSpinProducto {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 14px;
            }

            QFrame#controlSpinProducto:hover {
                border: 1px solid #94A3B8;
            }

            QPushButton#botonMiniSpin {
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 900;
                padding: 0px;
                margin: 0px;
                min-width: 38px;
                max-width: 38px;
                min-height: 38px;
                max-height: 38px;
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

            QLineEdit,
            QComboBox,
            QDoubleSpinBox,
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDoubleSpinBox:focus,
            QTextEdit:focus {
                border: 1px solid #2563EB;
            }

            QCheckBox {
                color: #334155;
                font-size: 14px;
                font-weight: 700;
                padding: 6px;
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
            }

            QPushButton#botonPrincipal:hover {
                background-color: #1D4ED8;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background-color: #F1F5F9;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #94A3B8;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def configurar_spinbox_producto(
        self,
        spinbox,
        decimales=0,
        minimo=0,
        maximo=999999999,
        paso=1,
        prefijo="",
        ancho=170,
    ):
        spinbox.setMinimum(minimo)
        spinbox.setMaximum(maximo)
        spinbox.setDecimals(decimales)
        spinbox.setSingleStep(paso)
        spinbox.setPrefix(prefijo)
        spinbox.setFixedWidth(ancho)
        spinbox.setMinimumHeight(38)
        spinbox.setMaximumHeight(38)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setAccelerated(True)
        spinbox.setKeyboardTracking(False)
        spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        spinbox.setStyleSheet("""
            QDoubleSpinBox {
                background-color: transparent;
                border: none;
                padding: 0px 6px;
                color: #0F172A;
                font-size: 14px;
                font-weight: 800;
            }

            QDoubleSpinBox:focus {
                background-color: transparent;
                border: none;
            }
        """)

    def crear_control_spinbox(self, spinbox):
        contenedor = QFrame()
        contenedor.setObjectName("controlSpinProducto")
        contenedor.setFixedHeight(46)
        contenedor.setMinimumWidth(spinbox.width() + 88)
        contenedor.setMaximumWidth(spinbox.width() + 88)

        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        btn_menos = QPushButton("−")
        btn_menos.setObjectName("botonMiniSpin")
        btn_menos.setFixedSize(38, 38)
        btn_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menos.clicked.connect(lambda: spinbox.stepDown())

        btn_mas = QPushButton("+")
        btn_mas.setObjectName("botonMiniSpin")
        btn_mas.setFixedSize(38, 38)
        btn_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_mas.clicked.connect(lambda: spinbox.stepUp())

        layout.addWidget(btn_menos)
        layout.addWidget(spinbox, 1)
        layout.addWidget(btn_mas)

        return contenedor

    def crear_input_monto(self):
        input_monto = QDoubleSpinBox()

        self.configurar_spinbox_producto(
            input_monto,
            decimales=0,
            minimo=0,
            maximo=999999999,
            paso=100,
            prefijo="$ ",
            ancho=170,
        )

        return input_monto

    def crear_input_stock(self, valor=0, minimo=0, decimales=3):
        input_stock = QDoubleSpinBox()

        self.configurar_spinbox_producto(
            input_stock,
            decimales=decimales,
            minimo=minimo,
            maximo=999999999,
            paso=1,
            prefijo="",
            ancho=170,
        )

        input_stock.setValue(float(Decimal(str(valor or 0))))

        return input_stock

    def cargar_catalogos(self):
        self.combo_categoria.clear()
        self.combo_proveedor.clear()

        self.combo_categoria.addItem("Sin categoría", None)
        self.combo_proveedor.addItem("Sin proveedor", None)

        categorias = self.obtener_categorias_backend()

        if categorias.get("ok"):
            for categoria in categorias.get("data") or []:
                self.combo_categoria.addItem(
                    str(categoria.get("nombre") or "Sin nombre"),
                    categoria.get("id"),
                )

        proveedores = self.obtener_proveedores_backend()

        if proveedores.get("ok"):
            for proveedor in proveedores.get("data") or []:
                self.combo_proveedor.addItem(
                    str(proveedor.get("nombre") or "Sin nombre"),
                    proveedor.get("id"),
                )

    def obtener_categorias_backend(self):
        metodo = getattr(self.pos, "obtener_categorias", None)

        if callable(metodo):
            try:
                resultado = metodo()

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Categorías obtenidas.",
                    "data": resultado or [],
                }
            except Exception:
                pass

        return self.backend.obtener_categorias()

    def obtener_proveedores_backend(self):
        metodo = getattr(self.pos, "obtener_proveedores", None)

        if callable(metodo):
            try:
                resultado = metodo()

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Proveedores obtenidos.",
                    "data": resultado or [],
                }
            except Exception:
                pass

        return self.backend.obtener_proveedores()

    def crear_producto_backend(self, **kwargs):
        metodo = getattr(self.pos, "crear_producto_sistema", None)

        if callable(metodo):
            return metodo(**kwargs)

        return self.backend.crear_producto_sistema(**kwargs)

    def formato_pesos(self, valor):
        metodo = getattr(self.pos, "formato_pesos", None)

        if callable(metodo):
            try:
                return metodo(valor)
            except Exception:
                pass

        return self.backend.formato_pesos(valor)

    def actualizar_margen(self):
        if self.label_margen is None:
            return

        compra = Decimal(str(self.input_precio_compra.value()))
        venta = Decimal(str(self.input_precio_venta.value()))
        margen = venta - compra

        porcentaje = Decimal("0")

        if venta > 0:
            porcentaje = (margen / venta) * Decimal("100")

        texto = (
            f"Margen estimado: {self.formato_pesos(margen)} "
            f"({porcentaje:.1f}%)"
        )

        if margen < 0:
            color = "#B91C1C"
            fondo = "#FEF2F2"
            borde = "#FECACA"
        elif margen == 0:
            color = "#92400E"
            fondo = "#FFFBEB"
            borde = "#FDE68A"
        else:
            color = "#166534"
            fondo = "#ECFDF5"
            borde = "#BBF7D0"

        self.label_margen.setText(texto)
        self.label_margen.setStyleSheet(f"""
            QLabel {{
                background-color: {fondo};
                border: 1px solid {borde};
                border-radius: 10px;
                padding: 10px 12px;
                color: {color};
                font-size: 14px;
                font-weight: 800;
            }}
        """)

    def guardar_producto(self):
        codigo = self.input_codigo.text().strip()
        nombre = self.input_nombre.text().strip()

        if not codigo:
            QMessageBox.warning(
                self,
                "Dato obligatorio",
                "Debe ingresar el código de barra.",
            )
            self.input_codigo.setFocus()
            return

        if not nombre:
            QMessageBox.warning(
                self,
                "Dato obligatorio",
                "Debe ingresar el nombre del producto.",
            )
            self.input_nombre.setFocus()
            return

        resultado = self.crear_producto_backend(
            categoria_id=self.combo_categoria.currentData(),
            proveedor_id=self.combo_proveedor.currentData(),
            codigo_barra=codigo,
            sku=self.input_sku.text().strip(),
            nombre=nombre,
            descripcion=self.input_descripcion.toPlainText().strip(),
            tipo_producto="GENERAL",
            unidad_medida=self.combo_unidad.currentText(),
            precio_compra=Decimal(str(self.input_precio_compra.value())),
            precio_venta=Decimal(str(self.input_precio_venta.value())),
            stock_actual=Decimal(str(self.input_stock.value())),
            stock_minimo=Decimal(str(self.input_stock_minimo.value())),
            permite_venta_sin_stock=1 if self.check_sin_stock.isChecked() else 0,
            requiere_mayoria_edad=1 if self.check_mayoria_edad.isChecked() else 0,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo crear el producto."),
            )
            return

        QMessageBox.information(
            self,
            "Producto creado",
            resultado.get("mensaje", "Producto creado correctamente."),
        )
        self.accept()


class ProductosPage(QWidget):
    def __init__(self, pos_service=None):
        super().__init__()

        self.backend = ProductosServiceAdapter()
        self.pos = pos_service or self.backend

        self.actualizando_productos = False
        self.timer_productos = None

        self.productos_cache = []
        self.filtro_columna = None
        self.filtro_valor = None

        self.input_busqueda = None
        self.label_ultima_actualizacion = None
        self.label_estado_operacion = None
        self.label_alertas = None

        self.labels = {}
        self.cards = {}

        self.tabla_productos = QTableWidget()

        self.construir_interfaz()
        self.cargar_productos(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_productos = QTimer(self)
        self.timer_productos.timeout.connect(self.cargar_productos_automatico)
        self.timer_productos.start(5000)

    def cargar_productos_automatico(self):
        if self.actualizando_productos:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_productos(mostrar_mensaje=False)

    def actualizar_label_ultima_actualizacion(self):
        if self.label_ultima_actualizacion is None:
            return

        hora_actual = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora_actual}")

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()
        textos.setSpacing(6)

        titulo = QLabel("Productos")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Administra productos, códigos de barra, categorías, precios, stock mínimo y alertas de inventario."
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

        btn_exportar_pdf = QPushButton("Exportar PDF")
        btn_exportar_pdf.setMinimumHeight(46)
        btn_exportar_pdf.setFixedWidth(160)
        btn_exportar_pdf.clicked.connect(self.exportar_productos_pdf)

        btn_nuevo = QPushButton("Nuevo producto")
        btn_nuevo.setObjectName("botonPrincipal")
        btn_nuevo.setMinimumHeight(46)
        btn_nuevo.setFixedWidth(190)
        btn_nuevo.clicked.connect(self.abrir_dialogo_crear)

        encabezado.addLayout(textos, 1)
        encabezado.addStretch()
        encabezado.addLayout(estado_actualizacion)
        encabezado.addSpacing(12)
        encabezado.addWidget(btn_exportar_pdf)
        encabezado.addWidget(btn_nuevo)

        layout.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["total_productos"] = self.crear_card(
            cards, 0, 0,
            key="total_productos",
            titulo="Productos activos",
            valor="0",
            detalle="Productos disponibles para venta",
            tipo="azul",
        )

        self.labels["bajo_stock"] = self.crear_card(
            cards, 0, 1,
            key="bajo_stock",
            titulo="Bajo stock",
            valor="0",
            detalle="Requieren reposición",
            tipo="alerta",
        )

        self.labels["sin_stock"] = self.crear_card(
            cards, 0, 2,
            key="sin_stock",
            titulo="Sin stock",
            valor="0",
            detalle="Productos agotados",
            tipo="rojo",
        )

        self.labels["valor_costo"] = self.crear_card(
            cards, 0, 3,
            key="valor_costo",
            titulo="Inventario al costo",
            valor="$0",
            detalle="Stock valorizado a precio compra",
            tipo="neutro",
        )

        self.labels["valor_venta"] = self.crear_card(
            cards, 1, 0,
            key="valor_venta",
            titulo="Venta proyectada",
            valor="$0",
            detalle="Stock valorizado a precio venta",
            tipo="verde",
        )

        self.labels["margen_estimado"] = self.crear_card(
            cards, 1, 1,
            key="margen_estimado",
            titulo="Margen estimado",
            valor="$0",
            detalle="Venta proyectada menos costo",
            tipo="morado",
        )

        self.labels["precio_promedio"] = self.crear_card(
            cards, 1, 2,
            key="precio_promedio",
            titulo="Precio promedio",
            valor="$0",
            detalle="Promedio precio de venta",
            tipo="neutro",
        )

        self.labels["productos_filtrados"] = self.crear_card(
            cards, 1, 3,
            key="productos_filtrados",
            titulo="Resultados visibles",
            valor="0",
            detalle="Productos según búsqueda actual",
            tipo="neutro",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de productos...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_alertas)

        panel_busqueda = QFrame()
        panel_busqueda.setObjectName("panelBusquedaProductos")

        busqueda_layout = QHBoxLayout(panel_busqueda)
        busqueda_layout.setContentsMargins(16, 14, 16, 14)
        busqueda_layout.setSpacing(12)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText(
            "Buscar por ID, nombre, código de barra, SKU, categoría o proveedor..."
        )
        self.input_busqueda.setMinimumHeight(44)
        self.input_busqueda.textChanged.connect(self.aplicar_filtro)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setMinimumHeight(44)
        btn_limpiar.setFixedWidth(140)
        btn_limpiar.clicked.connect(self.limpiar_busqueda)

        busqueda_layout.addWidget(self.input_busqueda, 1)
        busqueda_layout.addWidget(btn_limpiar)

        layout.addWidget(panel_busqueda)

        titulo_tabla = QLabel("Listado de productos")
        titulo_tabla.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)
        layout.addWidget(titulo_tabla)

        ayuda_tabla = QLabel(
            "Click en un encabezado para ordenar. Doble click en una celda para filtrar por ese valor."
        )
        ayuda_tabla.setWordWrap(True)
        ayuda_tabla.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }
        """)
        layout.addWidget(ayuda_tabla)

        self.tabla_productos.setColumnCount(11)
        self.tabla_productos.setHorizontalHeaderLabels([
            "ID",
            "Código",
            "SKU",
            "Producto",
            "Categoría",
            "Precio compra",
            "Precio venta",
            "Margen",
            "Stock",
            "Stock mínimo",
            "Estado",
        ])
        self.preparar_tabla()
        layout.addWidget(self.tabla_productos)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        btn_ajustar_stock = QPushButton("Ajustar stock en Inventario")
        btn_ajustar_stock.setMinimumHeight(44)
        btn_ajustar_stock.clicked.connect(self.ir_a_inventario)

        btn_copiar = QPushButton("Copiar producto")
        btn_copiar.setMinimumHeight(44)
        btn_copiar.clicked.connect(self.copiar_producto)

        btn_desactivar = QPushButton("Desactivar producto")
        btn_desactivar.setObjectName("botonPeligro")
        btn_desactivar.setMinimumHeight(44)
        btn_desactivar.clicked.connect(self.desactivar_producto_seleccionado)

        acciones.addWidget(btn_ajustar_stock)
        acciones.addWidget(btn_copiar)
        acciones.addStretch()
        acciones.addWidget(btn_desactivar)

        layout.addLayout(acciones)

        self.label_estado_operacion = QLabel("Productos listos para administrar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_estado_operacion)

        self.aplicar_estilos()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardProducto")
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

    def preparar_tabla(self):
        self.tabla_productos.setAlternatingRowColors(True)
        self.tabla_productos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_productos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_productos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_productos.verticalHeader().setVisible(False)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_productos.setMinimumHeight(360)
        self.tabla_productos.setShowGrid(True)

        self.tabla_productos.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_productos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_productos.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.tabla_productos.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        self.tabla_productos.setSortingEnabled(True)
        self.tabla_productos.horizontalHeader().setSectionsClickable(True)
        self.tabla_productos.horizontalHeader().setSortIndicatorShown(True)

        self.tabla_productos.cellDoubleClicked.connect(self.filtrar_por_celda)
        self.tabla_productos.horizontalHeader().sectionClicked.connect(self.aviso_ordenamiento_tabla)

    def cargar_productos(self, mostrar_mensaje=False):
        if self.actualizando_productos:
            return

        self.actualizando_productos = True

        try:
            resultado = self.obtener_productos()

            if not resultado.get("ok"):
                self.productos_cache = []
                self.cargar_tabla([])
                self.actualizar_tarjetas([])
                self.actualizar_alertas([])
                self.actualizar_estado_operacion(
                    resultado.get("mensaje", "No se pudieron cargar los productos."),
                    "error",
                )
                return

            self.productos_cache = resultado.get("data") or []
            productos_filtrados = self.obtener_productos_filtrados()

            self.cargar_tabla(productos_filtrados)
            self.actualizar_tarjetas(productos_filtrados)
            self.actualizar_alertas(self.productos_cache)

            if mostrar_mensaje:
                self.actualizar_estado_operacion(
                    "Productos cargados correctamente.",
                    "ok",
                )

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar productos automáticamente: {error}",
                "error",
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_productos = False

    def obtener_productos(self):
        posibles_metodos = [
            "listar_productos_sistema",
            "obtener_productos_sistema",
            "listar_productos",
            "obtener_productos",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if callable(metodo):
                resultado = metodo()

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Productos cargados correctamente.",
                    "data": resultado or [],
                }

        return self.backend.listar_productos_sistema()

    def obtener_productos_filtrados(self):
        texto = ""

        if self.input_busqueda is not None:
            texto = self.input_busqueda.text().strip().lower()

        filtrados = []

        for producto in self.productos_cache:
            campos = [
                producto.get("id"),
                producto.get("nombre"),
                producto.get("codigo_barra"),
                producto.get("sku"),
                producto.get("categoria"),
                producto.get("proveedor"),
            ]

            texto_producto = " ".join(str(campo or "").lower() for campo in campos)

            if texto and texto not in texto_producto:
                continue

            if self.filtro_columna is not None and self.filtro_valor is not None:
                valor_visible, _ = self.obtener_valor_columna_producto(
                    producto,
                    self.filtro_columna,
                )

                if str(valor_visible).strip() != str(self.filtro_valor).strip():
                    continue

            filtrados.append(producto)

        return filtrados

    def aplicar_filtro(self):
        productos_filtrados = self.obtener_productos_filtrados()

        self.cargar_tabla(productos_filtrados)
        self.actualizar_tarjetas(productos_filtrados)

        self.actualizar_estado_operacion(
            f"Mostrando {len(productos_filtrados)} producto(s).",
            "info",
        )

    def limpiar_busqueda(self):
        self.input_busqueda.clear()
        self.filtro_columna = None
        self.filtro_valor = None
        self.input_busqueda.setFocus()
        self.aplicar_filtro()

        self.actualizar_estado_operacion(
            "Filtros limpiados. Mostrando todos los productos.",
            "info",
        )

    def cargar_tabla(self, productos):
        self.tabla_productos.setSortingEnabled(False)
        self.tabla_productos.setRowCount(0)

        if not productos:
            self.tabla_productos.setRowCount(1)
            item = QTableWidgetItem("No hay productos para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_productos.setItem(0, 0, item)

            for columna in range(1, self.tabla_productos.columnCount()):
                self.tabla_productos.setItem(0, columna, QTableWidgetItem(""))

            self.tabla_productos.setSortingEnabled(False)
            return

        for fila, producto in enumerate(productos):
            self.tabla_productos.insertRow(fila)

            stock = self.decimal(producto.get("stock_actual"))
            stock_minimo = self.decimal(producto.get("stock_minimo"))
            estado_stock = self.obtener_estado_stock(stock, stock_minimo)

            for columna in range(self.tabla_productos.columnCount()):
                valor_visible, valor_orden = self.obtener_valor_columna_producto(
                    producto,
                    columna,
                )

                item = ItemTablaOrdenable(str(valor_visible or ""))
                item.setData(Qt.ItemDataRole.UserRole, valor_orden)

                if columna in [0, 5, 6, 7, 8, 9, 10]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )

                item.setToolTip(str(valor_visible or ""))

                if estado_stock == "SIN STOCK":
                    item.setBackground(QColor("#FEF2F2"))
                    item.setForeground(QColor("#991B1B"))
                elif estado_stock == "BAJO STOCK":
                    item.setBackground(QColor("#FFFBEB"))
                    item.setForeground(QColor("#92400E"))
                else:
                    item.setBackground(QColor("#FFFFFF"))
                    item.setForeground(QColor("#0F172A"))

                self.tabla_productos.setItem(fila, columna, item)

        self.tabla_productos.setSortingEnabled(True)

    def obtener_valor_columna_producto(self, producto, columna):
        precio_compra = self.decimal(producto.get("precio_compra"))
        precio_venta = self.decimal(producto.get("precio_venta"))
        stock = self.decimal(producto.get("stock_actual"))
        stock_minimo = self.decimal(producto.get("stock_minimo"))
        margen = precio_venta - precio_compra
        estado_stock = self.obtener_estado_stock(stock, stock_minimo)

        if columna == 0:
            valor = producto.get("id") or 0
            try:
                return valor, int(valor)
            except Exception:
                return valor, 0

        if columna == 1:
            valor = producto.get("codigo_barra") or ""
            return valor, str(valor).lower()

        if columna == 2:
            valor = producto.get("sku") or ""
            return valor, str(valor).lower()

        if columna == 3:
            valor = producto.get("nombre") or ""
            return valor, str(valor).lower()

        if columna == 4:
            valor = producto.get("categoria") or "Sin categoría"
            return valor, str(valor).lower()

        if columna == 5:
            return self.formato_pesos(precio_compra), precio_compra

        if columna == 6:
            return self.formato_pesos(precio_venta), precio_venta

        if columna == 7:
            return self.formato_pesos(margen), margen

        if columna == 8:
            return self.formato_numero(stock), stock

        if columna == 9:
            return self.formato_numero(stock_minimo), stock_minimo

        if columna == 10:
            return estado_stock, estado_stock

        return "", ""

    def filtrar_por_celda(self, fila, columna):
        item = self.tabla_productos.item(fila, columna)

        if item is None:
            return

        valor = item.text().strip()

        if not valor or valor == "No hay productos para mostrar.":
            return

        encabezado = self.tabla_productos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.filtro_columna = columna
        self.filtro_valor = valor
        self.aplicar_filtro()

        self.actualizar_estado_operacion(
            f"Filtro aplicado: {encabezado.text()} = {valor}. Presiona Limpiar para volver a ver todo.",
            "info",
        )

    def aviso_ordenamiento_tabla(self, columna):
        encabezado = self.tabla_productos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.actualizar_estado_operacion(
            f"Tabla ordenada por: {encabezado.text()}.",
            "info",
        )

    def actualizar_tarjetas(self, productos_visibles):
        productos_totales = self.productos_cache

        total_productos = len(productos_totales)
        total_filtrados = len(productos_visibles)

        bajo_stock = 0
        sin_stock = 0
        valor_costo = Decimal("0")
        valor_venta = Decimal("0")
        suma_precios = Decimal("0")
        productos_con_precio = 0

        for producto in productos_totales:
            stock = self.decimal(producto.get("stock_actual"))
            stock_minimo = self.decimal(producto.get("stock_minimo"))
            precio_compra = self.decimal(producto.get("precio_compra"))
            precio_venta = self.decimal(producto.get("precio_venta"))

            if stock <= 0:
                sin_stock += 1

            if stock <= stock_minimo:
                bajo_stock += 1

            valor_costo += stock * precio_compra
            valor_venta += stock * precio_venta

            if precio_venta > 0:
                suma_precios += precio_venta
                productos_con_precio += 1

        margen_estimado = valor_venta - valor_costo
        precio_promedio = Decimal("0")

        if productos_con_precio > 0:
            precio_promedio = suma_precios / Decimal(str(productos_con_precio))

        self.labels["total_productos"].setText(str(total_productos))
        self.labels["bajo_stock"].setText(str(bajo_stock))
        self.labels["sin_stock"].setText(str(sin_stock))
        self.labels["valor_costo"].setText(self.formato_pesos(valor_costo))
        self.labels["valor_venta"].setText(self.formato_pesos(valor_venta))
        self.labels["margen_estimado"].setText(self.formato_pesos(margen_estimado))
        self.labels["precio_promedio"].setText(self.formato_pesos(precio_promedio))
        self.labels["productos_filtrados"].setText(str(total_filtrados))

        self.cambiar_tipo_card("bajo_stock", "alerta" if bajo_stock > 0 else "verde")
        self.cambiar_tipo_card("sin_stock", "rojo" if sin_stock > 0 else "verde")
        self.cambiar_tipo_card("margen_estimado", "verde" if margen_estimado >= 0 else "rojo")

    def actualizar_alertas(self, productos):
        bajo_stock = []
        sin_stock = []

        for producto in productos:
            stock = self.decimal(producto.get("stock_actual"))
            stock_minimo = self.decimal(producto.get("stock_minimo"))

            if stock <= 0:
                sin_stock.append(producto)
            elif stock <= stock_minimo:
                bajo_stock.append(producto)

        alertas = []

        if sin_stock:
            alertas.append(f"{len(sin_stock)} producto(s) sin stock.")

        if bajo_stock:
            alertas.append(f"{len(bajo_stock)} producto(s) bajo stock.")

        if not alertas:
            self.label_alertas.setText("Inventario normal: no hay alertas importantes de stock.")
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText(
            "Alertas de inventario: " + " | ".join(alertas)
        )
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def abrir_dialogo_crear(self):
        dialogo = CrearProductoDialog(self.pos, self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        self.cargar_productos(mostrar_mensaje=True)

    def obtener_producto_seleccionado(self):
        fila = self.tabla_productos.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla_productos.item(fila, 0)

        if item_id is None:
            return None

        producto_id = item_id.text().strip()

        if not producto_id or not producto_id.isdigit():
            return None

        for producto in self.productos_cache:
            if str(producto.get("id")) == producto_id:
                return producto

        return None

    def ir_a_inventario(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Selecciona un producto antes de ir a Inventario.",
            )
            return

        nombre_pagina = "Inventario"

        candidatos = []

        widget_actual = self
        while widget_actual is not None:
            candidatos.append(widget_actual)
            widget_actual = widget_actual.parent()

        ventana = self.window()
        if ventana not in candidatos:
            candidatos.append(ventana)

        for objeto in candidatos:
            for nombre_metodo in [
                "abrir_pagina",
                "cambiar_pagina",
                "mostrar_pagina",
                "navegar_a",
                "ir_a_pagina",
                "set_pagina_actual",
            ]:
                metodo = getattr(objeto, nombre_metodo, None)

                if callable(metodo):
                    try:
                        metodo(nombre_pagina)
                        QTimer.singleShot(80, lambda p=dict(producto): self.preparar_producto_en_inventario(p))
                        self.actualizar_estado_operacion(
                            "Redirigido al módulo Inventario para ajustar stock.",
                            "info",
                        )
                        return
                    except TypeError:
                        pass
                    except Exception:
                        pass

        for objeto in candidatos:
            stack = (
                getattr(objeto, "stack", None)
                or getattr(objeto, "stacked_widget", None)
                or getattr(objeto, "paginas_stack", None)
                or getattr(objeto, "contenido", None)
            )

            if isinstance(stack, QStackedWidget):
                indices = (
                    getattr(objeto, "indices_paginas", None)
                    or getattr(objeto, "paginas_indices", None)
                    or getattr(objeto, "mapa_paginas", None)
                    or {}
                )

                if isinstance(indices, dict) and nombre_pagina in indices:
                    stack.setCurrentIndex(indices[nombre_pagina])
                    self.marcar_boton_menu(objeto, nombre_pagina)
                    QTimer.singleShot(80, lambda p=dict(producto): self.preparar_producto_en_inventario(p))
                    return

        QMessageBox.information(
            self,
            "Inventario",
            "No pude cambiar automáticamente al módulo Inventario. "
            "Abre Inventario desde el menú lateral para ajustar el stock.",
        )

    def obtener_pagina_inventario(self):
        ventana = self.window()

        paginas = getattr(ventana, "paginas", None)
        if isinstance(paginas, dict):
            for nombre, pagina in paginas.items():
                if str(nombre).strip().lower() == "inventario":
                    if isinstance(pagina, QScrollArea):
                        return pagina.widget()
                    return pagina

        for widget in ventana.findChildren(QWidget):
            if widget.__class__.__name__ == "InventarioPage":
                return widget

        return None

    def preparar_producto_en_inventario(self, producto):
        inventario = self.obtener_pagina_inventario()

        if inventario is None:
            return

        selector = getattr(inventario, "seleccionar_producto_externo", None)
        if callable(selector):
            selector(producto)
            return

        input_busqueda = getattr(inventario, "input_busqueda", None)
        texto_busqueda = str(
            producto.get("codigo_barra")
            or producto.get("nombre")
            or producto.get("id")
            or ""
        ).strip()

        if input_busqueda is not None and texto_busqueda:
            input_busqueda.setText(texto_busqueda)

        restaurar = getattr(inventario, "restaurar_seleccion_producto", None)
        if callable(restaurar):
            try:
                restaurar(int(producto.get("id")))
            except Exception:
                pass

    def marcar_boton_menu(self, ventana, nombre_pagina):
        for nombre_attr in ["botones_menu", "botones_nav", "menu_botones"]:
            contenedor = getattr(ventana, nombre_attr, None)

            if not isinstance(contenedor, dict):
                continue

            for nombre, boton in contenedor.items():
                if hasattr(boton, "setChecked"):
                    boton.setChecked(str(nombre).lower() == nombre_pagina.lower())

    def copiar_producto(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Selecciona un producto para copiar sus datos.",
            )
            return

        texto = "\n".join([
            "PRODUCTO",
            "========================",
            f"ID: {producto.get('id')}",
            f"Código: {producto.get('codigo_barra')}",
            f"SKU: {producto.get('sku')}",
            f"Nombre: {producto.get('nombre')}",
            f"Categoría: {producto.get('categoria') or 'Sin categoría'}",
            f"Proveedor: {producto.get('proveedor') or 'Sin proveedor'}",
            f"Precio compra: {self.formato_pesos(producto.get('precio_compra'))}",
            f"Precio venta: {self.formato_pesos(producto.get('precio_venta'))}",
            f"Stock actual: {self.formato_numero(producto.get('stock_actual'))}",
            f"Stock mínimo: {self.formato_numero(producto.get('stock_minimo'))}",
        ])

        QApplication.clipboard().setText(texto)

        self.actualizar_estado_operacion(
            "Datos del producto copiados al portapapeles.",
            "ok",
        )

    def desactivar_producto_seleccionado(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Selecciona un producto para desactivarlo.",
            )
            return

        confirmar = QMessageBox.question(
            self,
            "Desactivar producto",
            f"¿Seguro que deseas desactivar este producto?\n\n{producto.get('nombre')}",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        resultado = self.desactivar_producto_backend(producto.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo desactivar el producto."),
            )
            return

        self.actualizar_estado_operacion(
            "Producto desactivado correctamente.",
            "ok",
        )
        self.cargar_productos(mostrar_mensaje=False)

    def desactivar_producto_backend(self, producto_id):
        posibles_metodos = [
            "desactivar_producto_sistema",
            "desactivar_producto",
            "eliminar_producto",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if callable(metodo):
                resultado = metodo(producto_id)

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Producto desactivado correctamente.",
                    "data": resultado,
                }

        return self.backend.desactivar_producto_sistema(producto_id)

    def exportar_productos_pdf(self):
        productos = self.obtener_productos_filtrados()

        if not productos:
            QMessageBox.warning(
                self,
                "Sin productos",
                "No hay productos para exportar a PDF.",
            )
            return

        fecha_actual = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        nombre_sugerido = f"productos_pos_{fecha_actual}.pdf"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar productos en PDF",
            nombre_sugerido,
            "PDF (*.pdf)",
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
            )
        except ModuleNotFoundError:
            QMessageBox.warning(
                self,
                "Falta ReportLab",
                "Debes instalar ReportLab para exportar PDF.\n\n"
                "Ejecuta en la terminal:\n"
                "pip install reportlab",
            )
            return

        try:
            doc = SimpleDocTemplate(
                ruta,
                pagesize=landscape(A4),
                rightMargin=1.2 * cm,
                leftMargin=1.2 * cm,
                topMargin=1.2 * cm,
                bottomMargin=1.2 * cm,
            )

            estilos = getSampleStyleSheet()

            estilo_titulo = ParagraphStyle(
                "TituloPOS",
                parent=estilos["Title"],
                fontName="Helvetica-Bold",
                fontSize=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#0F172A"),
                spaceAfter=10,
            )

            estilo_subtitulo = ParagraphStyle(
                "SubtituloPOS",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#475569"),
                spaceAfter=14,
            )

            estilo_texto = ParagraphStyle(
                "TextoTabla",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=7,
                alignment=TA_LEFT,
                leading=9,
            )

            elementos = []

            elementos.append(Paragraph("Reporte de Productos", estilo_titulo))

            fecha_reporte = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
            filtro = self.input_busqueda.text().strip() if self.input_busqueda else ""

            subtitulo = (
                f"Generado: {fecha_reporte} | "
                f"Productos exportados: {len(productos)}"
            )

            if filtro:
                subtitulo += f" | Filtro aplicado: {filtro}"

            elementos.append(Paragraph(subtitulo, estilo_subtitulo))
            elementos.append(Spacer(1, 8))

            resumen = [
                ["Indicador", "Valor"],
                ["Productos activos", self.labels["total_productos"].text()],
                ["Bajo stock", self.labels["bajo_stock"].text()],
                ["Sin stock", self.labels["sin_stock"].text()],
                ["Inventario al costo", self.labels["valor_costo"].text()],
                ["Venta proyectada", self.labels["valor_venta"].text()],
                ["Margen estimado", self.labels["margen_estimado"].text()],
                ["Precio promedio", self.labels["precio_promedio"].text()],
                ["Resultados visibles", self.labels["productos_filtrados"].text()],
            ]

            tabla_resumen = Table(
                resumen,
                colWidths=[6 * cm, 5 * cm],
                hAlign="LEFT",
            )

            tabla_resumen.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
            ]))

            elementos.append(tabla_resumen)
            elementos.append(Spacer(1, 14))

            data = [[
                "ID",
                "Código",
                "SKU",
                "Producto",
                "Categoría",
                "P. compra",
                "P. venta",
                "Margen",
                "Stock",
                "Mínimo",
                "Estado",
            ]]

            for producto in productos:
                precio_compra = self.decimal(producto.get("precio_compra"))
                precio_venta = self.decimal(producto.get("precio_venta"))
                stock = self.decimal(producto.get("stock_actual"))
                stock_minimo = self.decimal(producto.get("stock_minimo"))
                margen = precio_venta - precio_compra
                estado_stock = self.obtener_estado_stock(stock, stock_minimo)

                data.append([
                    str(producto.get("id") or ""),
                    str(producto.get("codigo_barra") or ""),
                    str(producto.get("sku") or ""),
                    Paragraph(str(producto.get("nombre") or ""), estilo_texto),
                    Paragraph(str(producto.get("categoria") or "Sin categoría"), estilo_texto),
                    self.formato_pesos(precio_compra),
                    self.formato_pesos(precio_venta),
                    self.formato_pesos(margen),
                    self.formato_numero(stock),
                    self.formato_numero(stock_minimo),
                    estado_stock,
                ])

            tabla = Table(
                data,
                repeatRows=1,
                colWidths=[
                    1.1 * cm,
                    2.7 * cm,
                    2.2 * cm,
                    5.0 * cm,
                    3.6 * cm,
                    2.3 * cm,
                    2.3 * cm,
                    2.1 * cm,
                    1.6 * cm,
                    1.6 * cm,
                    2.2 * cm,
                ],
            )

            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (2, -1), "CENTER"),
                ("ALIGN", (5, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
            ]))

            for fila in range(1, len(data)):
                estado = str(data[fila][-1])

                if estado == "SIN STOCK":
                    tabla.setStyle(TableStyle([
                        ("BACKGROUND", (0, fila), (-1, fila), colors.HexColor("#FEF2F2")),
                        ("TEXTCOLOR", (0, fila), (-1, fila), colors.HexColor("#991B1B")),
                    ]))
                elif estado == "BAJO STOCK":
                    tabla.setStyle(TableStyle([
                        ("BACKGROUND", (0, fila), (-1, fila), colors.HexColor("#FFFBEB")),
                        ("TEXTCOLOR", (0, fila), (-1, fila), colors.HexColor("#92400E")),
                    ]))

            elementos.append(tabla)

            doc.build(elementos)

            QMessageBox.information(
                self,
                "PDF exportado",
                f"Archivo PDF exportado correctamente en:\n{ruta}",
            )

            self.actualizar_estado_operacion(
                f"Productos exportados a PDF correctamente: {ruta}",
                "ok",
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Error al exportar PDF",
                f"No se pudo generar el PDF:\n{error}",
            )

            self.actualizar_estado_operacion(
                f"No se pudo exportar el PDF: {error}",
                "error",
            )

    def actualizar_estado_operacion(self, texto, tipo="info"):
        if self.label_estado_operacion is None:
            return

        self.label_estado_operacion.setText(texto)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta(tipo))

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

        return self.backend.formato_pesos(valor)

    def formato_numero(self, valor):
        try:
            numero = Decimal(str(valor or 0))

            if numero == numero.to_integral():
                return str(int(numero))

            return f"{numero:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return "0"

    def obtener_estado_stock(self, stock, stock_minimo):
        if stock <= 0:
            return "SIN STOCK"

        if stock <= stock_minimo:
            return "BAJO STOCK"

        return "OK"

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

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QFrame#panelBusquedaProductos {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardProducto {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardProducto[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardProducto[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardProducto[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardProducto[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardProducto[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardProducto[tipo="neutro"] {
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

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 12px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus {
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

            QPushButton#botonPeligro {
                background-color: #DC2626;
                color: white;
            }

            QPushButton#botonPeligro:hover {
                background-color: #B91C1C;
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

            QHeaderView::section:hover {
                background-color: #E2E8F0;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QScrollBar:vertical {
                background-color: #F1F5F9;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 6px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #94A3B8;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #F1F5F9;
                height: 12px;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:horizontal {
                background-color: #CBD5E1;
                border-radius: 6px;
                min-width: 35px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #94A3B8;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)