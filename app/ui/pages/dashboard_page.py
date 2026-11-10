from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, QTimer, QDateTime

from app.dashboard import obtener_dashboard_principal


class DashboardPage(QWidget):
    def __init__(self, pos_service=None):
        super().__init__()

        self.pos = pos_service

        self.actualizando_dashboard = False
        self.timer_dashboard = None

        self.label_ultima_actualizacion = None
        self.label_estado_general = None
        self.label_alertas = None

        self.labels = {}
        self.cards = {}

        self.tabla_ultimas_ventas = QTableWidget()
        self.tabla_productos_top = QTableWidget()

        self.construir_interfaz()
        self.cargar_datos()
        self.iniciar_actualizacion_automatica()

    # ============================================================
    # ACTUALIZACIÓN AUTOMÁTICA
    # ============================================================

    def iniciar_actualizacion_automatica(self):
        self.timer_dashboard = QTimer(self)
        self.timer_dashboard.timeout.connect(self.cargar_datos_automatico)

        # Cada 5 segundos.
        # Para producción puedes cambiar a 10000.
        self.timer_dashboard.start(5000)

    def cargar_datos_automatico(self):
        if self.actualizando_dashboard:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_datos()

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

        # HEADER
        encabezado = QHBoxLayout()

        textos = QVBoxLayout()
        textos.setSpacing(6)

        titulo = QLabel("Dashboard principal")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Resumen automático del negocio: caja, ventas del día, métodos de pago, stock y productos más vendidos."
        )
        subtitulo.setObjectName("subtituloPagina")
        subtitulo.setWordWrap(True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        estado_actualizacion = QVBoxLayout()
        estado_actualizacion.setSpacing(4)
        estado_actualizacion.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

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

        # ESTADO GENERAL
        self.label_estado_general = QLabel("Cargando estado general...")
        self.label_estado_general.setWordWrap(True)
        self.label_estado_general.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 14px 16px;
                color: #334155;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.label_estado_general)

        # CARDS PRINCIPALES
        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["caja_estado"] = self.crear_card(
            cards, 0, 0,
            key="caja_estado",
            titulo="Caja actual",
            valor="Cargando...",
            detalle="Estado del turno de caja",
            tipo="neutro"
        )

        self.labels["total_vendido"] = self.crear_card(
            cards, 0, 1,
            key="total_vendido",
            titulo="Total vendido hoy",
            valor="$0",
            detalle="Suma de ventas pagadas",
            tipo="azul"
        )

        self.labels["cantidad_ventas"] = self.crear_card(
            cards, 0, 2,
            key="cantidad_ventas",
            titulo="Ventas de hoy",
            valor="0",
            detalle="Cantidad de ventas pagadas",
            tipo="neutro"
        )

        self.labels["bajo_stock"] = self.crear_card(
            cards, 0, 3,
            key="bajo_stock",
            titulo="Productos bajo stock",
            valor="0",
            detalle="Productos que requieren reposición",
            tipo="alerta"
        )

        self.labels["monto_esperado"] = self.crear_card(
            cards, 1, 0,
            key="monto_esperado",
            titulo="Efectivo esperado",
            valor="$0",
            detalle="Monto físico esperado en caja",
            tipo="verde"
        )

        self.labels["total_efectivo"] = self.crear_card(
            cards, 1, 1,
            key="total_efectivo",
            titulo="Ventas en efectivo",
            valor="$0",
            detalle="Afecta caja física",
            tipo="verde"
        )

        self.labels["total_tarjeta"] = self.crear_card(
            cards, 1, 2,
            key="total_tarjeta",
            titulo="Ventas con tarjeta",
            valor="$0",
            detalle="No afecta efectivo físico",
            tipo="morado"
        )

        self.labels["total_transferencia"] = self.crear_card(
            cards, 1, 3,
            key="total_transferencia",
            titulo="Ventas por transferencia",
            valor="$0",
            detalle="No afecta efectivo físico",
            tipo="morado"
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        # ALERTAS
        self.label_alertas = QLabel("Sin alertas importantes por ahora.")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 14px 16px;
                color: #334155;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.label_alertas)

        # TABLAS
        tablas_layout = QHBoxLayout()
        tablas_layout.setSpacing(18)

        panel_ventas = self.crear_panel_tabla(
            "Últimas ventas del día",
            self.tabla_ultimas_ventas
        )
        panel_productos = self.crear_panel_tabla(
            "Productos más vendidos hoy",
            self.tabla_productos_top
        )

        tablas_layout.addWidget(panel_ventas, 1)
        tablas_layout.addWidget(panel_productos, 1)

        layout.addLayout(tablas_layout)

        self.configurar_tablas()
        self.aplicar_estilos()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardDashboard")
        card.setProperty("tipo", tipo)
        card.setMinimumHeight(130)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("cardTitulo")
        label_titulo.setWordWrap(True)

        label_valor = QLabel(valor)
        label_valor.setObjectName("cardValor")
        label_valor.setWordWrap(False)

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

    def crear_panel_tabla(self, titulo, tabla):
        panel = QFrame()
        panel.setObjectName("panelTablaDashboard")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloPanelTabla")

        layout.addWidget(label_titulo)
        layout.addWidget(tabla)

        return panel

    def configurar_tablas(self):
        self.tabla_ultimas_ventas.setColumnCount(5)
        self.tabla_ultimas_ventas.setHorizontalHeaderLabels([
            "Número",
            "Fecha",
            "Método",
            "Total",
            "Estado"
        ])
        self.preparar_tabla(self.tabla_ultimas_ventas)

        self.tabla_productos_top.setColumnCount(3)
        self.tabla_productos_top.setHorizontalHeaderLabels([
            "Producto",
            "Cantidad",
            "Total vendido"
        ])
        self.preparar_tabla(self.tabla_productos_top)

    def preparar_tabla(self, tabla):
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setMinimumHeight(280)
        tabla.setShowGrid(True)

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def cargar_datos(self):
        if self.actualizando_dashboard:
            return

        self.actualizando_dashboard = True

        try:
            resultado = self.obtener_dashboard()

            if not resultado.get("ok"):
                self.mostrar_error(
                    resultado.get("mensaje", "No se pudo cargar el dashboard.")
                )
                return

            data = resultado.get("data") or {}

            self.actualizar_cards(data)
            self.actualizar_estado_general(data)
            self.actualizar_alertas(data)
            self.cargar_tabla_ultimas_ventas(data.get("ultimas_ventas") or [])
            self.cargar_tabla_productos_top(
                data.get("productos_mas_vendidos_hoy") or []
            )

        except Exception as error:
            self.mostrar_error(
                f"No se pudo actualizar el dashboard automáticamente: {error}"
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_dashboard = False

    def obtener_dashboard(self):
        if self.pos is not None:
            posibles_metodos = [
                "obtener_dashboard_principal_sistema",
                "obtener_dashboard_principal",
                "dashboard_principal",
                "cargar_dashboard"
            ]

            for nombre_metodo in posibles_metodos:
                metodo = getattr(self.pos, nombre_metodo, None)

                if callable(metodo):
                    return metodo()

        return obtener_dashboard_principal()

    def actualizar_cards(self, data):
        caja = data.get("caja_actual") or {}
        ventas = data.get("ventas_hoy") or {}
        bajo_stock = data.get("bajo_stock") or {}

        caja_abierta = bool(caja) and str(caja.get("estado", "")).upper() == "ABIERTA"

        if caja_abierta:
            self.labels["caja_estado"].setText("ABIERTA")
            self.cambiar_tipo_card("caja_estado", "verde")
        else:
            self.labels["caja_estado"].setText("CERRADA")
            self.cambiar_tipo_card("caja_estado", "rojo")

        total_vendido = self.obtener_numero(ventas, "total_vendido")
        cantidad_ventas = ventas.get("cantidad_ventas") or 0
        productos_bajo_stock = bajo_stock.get("productos_bajo_stock") or 0

        total_efectivo = self.obtener_numero(ventas, "total_efectivo")
        total_tarjeta = self.obtener_numero(ventas, "total_tarjeta")
        total_transferencia = self.obtener_numero(ventas, "total_transferencia")

        monto_esperado = (
            caja.get("monto_esperado_caja")
            or caja.get("monto_esperado")
            or caja.get("efectivo_esperado")
            or 0
        )

        self.labels["total_vendido"].setText(self.formato_pesos(total_vendido))
        self.labels["cantidad_ventas"].setText(str(cantidad_ventas))
        self.labels["bajo_stock"].setText(str(productos_bajo_stock))
        self.labels["monto_esperado"].setText(self.formato_pesos(monto_esperado))
        self.labels["total_efectivo"].setText(self.formato_pesos(total_efectivo))
        self.labels["total_tarjeta"].setText(self.formato_pesos(total_tarjeta))
        self.labels["total_transferencia"].setText(
            self.formato_pesos(total_transferencia)
        )

        if int(productos_bajo_stock or 0) > 0:
            self.cambiar_tipo_card("bajo_stock", "alerta")
        else:
            self.cambiar_tipo_card("bajo_stock", "verde")

    def actualizar_estado_general(self, data):
        caja = data.get("caja_actual") or {}
        ventas = data.get("ventas_hoy") or {}

        caja_abierta = bool(caja) and str(caja.get("estado", "")).upper() == "ABIERTA"

        cantidad_ventas = ventas.get("cantidad_ventas") or 0
        total_vendido = self.formato_pesos(ventas.get("total_vendido") or 0)

        if caja_abierta:
            caja_id = caja.get("id") or caja.get("caja_id") or "-"
            fecha_apertura = self.formato_fecha(caja.get("fecha_apertura"))

            self.label_estado_general.setText(
                f"Caja abierta | Turno ID: {caja_id} | Apertura: {fecha_apertura} | "
                f"Ventas hoy: {cantidad_ventas} | Total vendido: {total_vendido}"
            )
            self.label_estado_general.setStyleSheet("""
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 14px;
                    padding: 14px 16px;
                    color: #166534;
                    font-size: 14px;
                    font-weight: 800;
                }
            """)
        else:
            self.label_estado_general.setText(
                "Caja cerrada | Para vender, primero debes abrir una caja desde el módulo Caja."
            )
            self.label_estado_general.setStyleSheet("""
                QLabel {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 14px;
                    padding: 14px 16px;
                    color: #B91C1C;
                    font-size: 14px;
                    font-weight: 800;
                }
            """)

    def actualizar_alertas(self, data):
        caja = data.get("caja_actual") or {}
        ventas = data.get("ventas_hoy") or {}
        bajo_stock = data.get("bajo_stock") or {}

        alertas = []

        caja_abierta = bool(caja) and str(caja.get("estado", "")).upper() == "ABIERTA"
        productos_bajo_stock = int(bajo_stock.get("productos_bajo_stock") or 0)
        cantidad_ventas = int(ventas.get("cantidad_ventas") or 0)

        if not caja_abierta:
            alertas.append("Caja cerrada: abre caja antes de comenzar a vender.")

        if productos_bajo_stock > 0:
            alertas.append(
                f"Hay {productos_bajo_stock} producto(s) bajo stock. Revisa Inventario."
            )

        if caja_abierta and cantidad_ventas == 0:
            alertas.append("Caja abierta, pero aún no hay ventas registradas hoy.")

        if not alertas:
            self.label_alertas.setText(
                "Operación normal: sin alertas importantes por ahora."
            )
            self.label_alertas.setStyleSheet("""
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 14px;
                    padding: 14px 16px;
                    color: #166534;
                    font-size: 14px;
                    font-weight: 800;
                }
            """)
            return

        texto = "Alertas del sistema: " + " | ".join(alertas)
        self.label_alertas.setText(texto)
        self.label_alertas.setStyleSheet("""
            QLabel {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
                border-radius: 14px;
                padding: 14px 16px;
                color: #92400E;
                font-size: 14px;
                font-weight: 800;
            }
        """)

    def cargar_tabla_ultimas_ventas(self, ventas):
        self.tabla_ultimas_ventas.setRowCount(0)

        if not ventas:
            self.insertar_fila_vacia(
                self.tabla_ultimas_ventas,
                "No hay ventas registradas hoy."
            )
            return

        for fila, venta in enumerate(ventas):
            self.tabla_ultimas_ventas.insertRow(fila)

            valores = [
                venta.get("numero_venta") or "-",
                self.formato_fecha(venta.get("fecha_venta")),
                venta.get("metodo_pago") or "-",
                self.formato_pesos(venta.get("total")),
                venta.get("estado") or "-"
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_ultimas_ventas.setItem(fila, columna, item)

    def cargar_tabla_productos_top(self, productos):
        self.tabla_productos_top.setRowCount(0)

        if not productos:
            self.insertar_fila_vacia(
                self.tabla_productos_top,
                "Aún no hay productos vendidos hoy."
            )
            return

        for fila, producto in enumerate(productos):
            self.tabla_productos_top.insertRow(fila)

            valores = [
                producto.get("nombre_producto") or "-",
                producto.get("cantidad_vendida") or "0",
                self.formato_pesos(producto.get("total_vendido"))
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))

                if columna == 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tabla_productos_top.setItem(fila, columna, item)

    def insertar_fila_vacia(self, tabla, texto):
        tabla.setRowCount(1)

        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        tabla.setItem(0, 0, item)

        for columna in range(1, tabla.columnCount()):
            vacio = QTableWidgetItem("")
            vacio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tabla.setItem(0, columna, vacio)

    def mostrar_error(self, mensaje):
        self.label_estado_general.setText(mensaje)
        self.label_estado_general.setStyleSheet("""
            QLabel {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 14px;
                padding: 14px 16px;
                color: #B91C1C;
                font-size: 14px;
                font-weight: 800;
            }
        """)

        for key in self.labels:
            if key == "caja_estado":
                self.labels[key].setText("ERROR")
            elif key in ["cantidad_ventas", "bajo_stock"]:
                self.labels[key].setText("0")
            else:
                self.labels[key].setText("$0")

        self.cargar_tabla_ultimas_ventas([])
        self.cargar_tabla_productos_top([])

    # ============================================================
    # UTILIDADES
    # ============================================================

    def cambiar_tipo_card(self, key, tipo):
        card = self.cards.get(key)

        if card is None:
            return

        card.setProperty("tipo", tipo)
        card.style().unpolish(card)
        card.style().polish(card)

    def obtener_numero(self, data, clave):
        try:
            return Decimal(str(data.get(clave) or 0))
        except Exception:
            return Decimal("0")

    def formato_pesos(self, valor):
        if self.pos is not None:
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

    def formato_fecha(self, fecha):
        if not fecha:
            return "-"

        if self.pos is not None:
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

    # ============================================================
    # ESTILOS
    # ============================================================

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QFrame#cardDashboard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardDashboard[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardDashboard[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardDashboard[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardDashboard[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardDashboard[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
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

            QFrame#panelTablaDashboard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QLabel#tituloPanelTabla {
                color: #0F172A;
                font-size: 18px;
                font-weight: 900;
                background-color: transparent;
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