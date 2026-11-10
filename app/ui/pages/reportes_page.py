from decimal import Decimal
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDateEdit,
    QTabWidget,
    QFrame,
    QFileDialog,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QDate, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.database import ejecutar_consulta

from app.reportes import (
    ventas_por_rango,
    ganancia_por_rango,
    productos_mas_vendidos,
    productos_bajo_stock,
    resumen_caja_actual,
)


class ReportesServiceAdapter:
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

    def reporte_ventas_por_rango(self, fecha_inicio, fecha_fin):
        return ventas_por_rango(fecha_inicio, fecha_fin)

    def reporte_ganancia_por_rango(self, fecha_inicio, fecha_fin):
        return ganancia_por_rango(fecha_inicio, fecha_fin)

    def reporte_productos_mas_vendidos(self, fecha_inicio, fecha_fin, limite=50):
        return productos_mas_vendidos(fecha_inicio, fecha_fin, limite)

    def productos_con_bajo_stock(self):
        return productos_bajo_stock()

    def reporte_resumen_caja_actual(self):
        return resumen_caja_actual()


class ReportesPage(QWidget):
    def __init__(self, pos_service=None):
        super().__init__()

        self.pos = pos_service or ReportesServiceAdapter()
        self.backend = ReportesServiceAdapter()

        self.actualizando_reportes = False
        self.bloqueando_fechas = False
        self.timer_reportes = None

        self.fecha_inicio = None
        self.fecha_fin = None

        self.tabs = None

        self.tabla_resumen = QTableWidget()
        self.tabla_ventas = QTableWidget()
        self.tabla_productos = QTableWidget()
        self.tabla_ganancia = QTableWidget()
        self.tabla_caja = QTableWidget()
        self.tabla_bajo_stock = QTableWidget()

        self.datos_ventas = []
        self.datos_productos = []
        self.datos_ganancia = {}
        self.datos_caja = None
        self.datos_bajo_stock = []
        self.datos_resumen = {}

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.labels = {}
        self.cards = {}

        self.construir_interfaz()
        self.cargar_reportes_por_rango(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    # ============================================================
    # ACTUALIZACIÓN AUTOMÁTICA
    # ============================================================

    def iniciar_actualizacion_automatica(self):
        self.timer_reportes = QTimer(self)
        self.timer_reportes.timeout.connect(self.cargar_reportes_automatico)
        self.timer_reportes.start(15000)

    def cargar_reportes_automatico(self):
        if self.actualizando_reportes:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_reportes_por_rango(mostrar_mensaje=False)

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

        titulo = QLabel("Reportes")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Consulta ventas, ganancias, caja, productos más vendidos, bajo stock y exporta a Excel o PDF."
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

        btn_exportar_actual = QPushButton("Exportar pestaña")
        btn_exportar_actual.setMinimumHeight(46)
        btn_exportar_actual.setFixedWidth(170)
        btn_exportar_actual.clicked.connect(self.exportar_pestana_actual)

        btn_exportar_pdf = QPushButton("Exportar PDF")
        btn_exportar_pdf.setMinimumHeight(46)
        btn_exportar_pdf.setFixedWidth(155)
        btn_exportar_pdf.clicked.connect(self.exportar_reporte_pdf)

        btn_exportar_completo = QPushButton("Exportar Excel completo")
        btn_exportar_completo.setObjectName("botonPrincipal")
        btn_exportar_completo.setMinimumHeight(46)
        btn_exportar_completo.setFixedWidth(220)
        btn_exportar_completo.clicked.connect(self.exportar_reporte_completo)

        encabezado.addLayout(textos, 1)
        encabezado.addStretch()
        encabezado.addLayout(estado_actualizacion)
        encabezado.addSpacing(12)
        encabezado.addWidget(btn_exportar_actual)
        encabezado.addWidget(btn_exportar_pdf)
        encabezado.addWidget(btn_exportar_completo)

        layout.addLayout(encabezado)

        # FILTROS
        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelFiltrosReportes")

        filtros = QHBoxLayout(panel_filtros)
        filtros.setContentsMargins(16, 14, 16, 14)
        filtros.setSpacing(12)

        label_inicio = QLabel("Desde:")
        label_fin = QLabel("Hasta:")

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio.setMinimumHeight(42)
        self.fecha_inicio.setFixedWidth(165)
        self.fecha_inicio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fecha_inicio.dateChanged.connect(self.cambio_fechas)

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin.setMinimumHeight(42)
        self.fecha_fin.setFixedWidth(165)
        self.fecha_fin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fecha_fin.dateChanged.connect(self.cambio_fechas)

        btn_hoy = QPushButton("Hoy")
        btn_hoy.setMinimumHeight(42)
        btn_hoy.setFixedWidth(100)
        btn_hoy.clicked.connect(self.setear_hoy)

        filtros.addWidget(label_inicio)
        filtros.addWidget(self.fecha_inicio)
        filtros.addWidget(label_fin)
        filtros.addWidget(self.fecha_fin)
        filtros.addWidget(btn_hoy)
        filtros.addStretch()

        layout.addWidget(panel_filtros)

        # CARDS
        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["ventas"] = self.crear_card(
            cards, 0, 0,
            key="ventas",
            titulo="Ventas pagadas",
            valor="0",
            detalle="Cantidad de ventas del rango",
            tipo="azul",
        )

        self.labels["total_vendido"] = self.crear_card(
            cards, 0, 1,
            key="total_vendido",
            titulo="Total vendido",
            valor="$0",
            detalle="Suma de ventas pagadas",
            tipo="verde",
        )

        self.labels["ganancia"] = self.crear_card(
            cards, 0, 2,
            key="ganancia",
            titulo="Ganancia estimada",
            valor="$0",
            detalle="Venta menos costo estimado",
            tipo="morado",
        )

        self.labels["ticket_promedio"] = self.crear_card(
            cards, 0, 3,
            key="ticket_promedio",
            titulo="Ticket promedio",
            valor="$0",
            detalle="Promedio por venta pagada",
            tipo="neutro",
        )

        self.labels["efectivo"] = self.crear_card(
            cards, 1, 0,
            key="efectivo",
            titulo="Efectivo",
            valor="$0",
            detalle="Ventas pagadas en efectivo",
            tipo="verde",
        )

        self.labels["tarjeta"] = self.crear_card(
            cards, 1, 1,
            key="tarjeta",
            titulo="Tarjeta",
            valor="$0",
            detalle="Ventas pagadas con tarjeta",
            tipo="azul",
        )

        self.labels["transferencia"] = self.crear_card(
            cards, 1, 2,
            key="transferencia",
            titulo="Transferencia",
            valor="$0",
            detalle="Ventas por transferencia",
            tipo="azul",
        )

        self.labels["bajo_stock"] = self.crear_card(
            cards, 1, 3,
            key="bajo_stock",
            titulo="Bajo stock",
            valor="0",
            detalle="Productos que requieren reposición",
            tipo="alerta",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de reportes...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_alertas)

        # TABS
        panel_tabs = QFrame()
        panel_tabs.setObjectName("panelTabsReportes")

        panel_tabs_layout = QVBoxLayout(panel_tabs)
        panel_tabs_layout.setContentsMargins(18, 16, 18, 18)
        panel_tabs_layout.setSpacing(12)

        self.tabs = QTabWidget()

        self.configurar_tablas()

        self.tabs.addTab(self.tabla_resumen, "Resumen")
        self.tabs.addTab(self.tabla_ventas, "Ventas")
        self.tabs.addTab(self.tabla_productos, "Productos más vendidos")
        self.tabs.addTab(self.tabla_ganancia, "Ganancia")
        self.tabs.addTab(self.tabla_caja, "Caja actual")
        self.tabs.addTab(self.tabla_bajo_stock, "Bajo stock")

        panel_tabs_layout.addWidget(self.tabs)

        layout.addWidget(panel_tabs)

        self.label_estado_operacion = QLabel("Reportes listos para consultar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_estado_operacion)

        self.aplicar_estilos()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardReporte")
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
        label_valor.setWordWrap(True)

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

    def configurar_tablas(self):
        self.configurar_tabla(
            self.tabla_resumen,
            ["Concepto", "Valor", "Detalle"],
            altura=430,
        )

        self.configurar_tabla(
            self.tabla_ventas,
            ["Número", "Fecha", "Cajero", "Método pago", "Subtotal", "Descuento", "IVA", "Total", "Estado"],
            altura=430,
        )

        self.configurar_tabla(
            self.tabla_productos,
            ["Código", "Producto", "Cantidad vendida", "Total vendido", "Ganancia", "Margen"],
            altura=430,
        )

        self.configurar_tabla(
            self.tabla_ganancia,
            ["Concepto", "Valor"],
            altura=430,
        )

        self.configurar_tabla(
            self.tabla_caja,
            ["Concepto", "Valor"],
            altura=430,
        )

        self.configurar_tabla(
            self.tabla_bajo_stock,
            ["ID", "Código", "Producto", "Categoría", "Stock actual", "Stock mínimo", "Precio venta"],
            altura=430,
        )

    def configurar_tabla(self, tabla, headers, altura=360):
        tabla.setColumnCount(len(headers))
        tabla.setHorizontalHeaderLabels(headers)
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setMinimumHeight(altura)
        tabla.setShowGrid(True)

        tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tabla.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

    # ============================================================
    # FECHAS
    # ============================================================

    def obtener_fecha_inicio(self):
        return self.fecha_inicio.date().toString("yyyy-MM-dd")

    def obtener_fecha_fin(self):
        return self.fecha_fin.date().toString("yyyy-MM-dd")

    def cambio_fechas(self):
        if self.bloqueando_fechas:
            return

        self.cargar_reportes_por_rango(mostrar_mensaje=False)

    def setear_hoy(self):
        self.bloqueando_fechas = True

        hoy = QDate.currentDate()
        self.fecha_inicio.setDate(hoy)
        self.fecha_fin.setDate(hoy)

        self.bloqueando_fechas = False
        self.cargar_reportes_por_rango(mostrar_mensaje=True)

    def validar_fechas(self):
        inicio = self.fecha_inicio.date()
        fin = self.fecha_fin.date()

        return inicio <= fin

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def cargar_reportes_por_rango(self, mostrar_mensaje=False):
        if self.actualizando_reportes:
            return

        if not self.validar_fechas():
            QMessageBox.warning(
                self,
                "Rango inválido",
                "La fecha Desde no puede ser mayor que la fecha Hasta.",
            )
            return

        self.actualizando_reportes = True

        try:
            inicio = self.obtener_fecha_inicio()
            fin = self.obtener_fecha_fin()

            resultado_ventas = self.obtener_ventas_backend(inicio, fin)

            if not resultado_ventas.get("ok"):
                self.mostrar_error(resultado_ventas.get("mensaje", "No se pudieron cargar las ventas."))
                return

            self.datos_ventas = resultado_ventas.get("data") or []

            resultado_productos = self.obtener_productos_backend(inicio, fin)

            if not resultado_productos.get("ok"):
                self.mostrar_error(resultado_productos.get("mensaje", "No se pudieron cargar productos vendidos."))
                return

            self.datos_productos = resultado_productos.get("data") or []

            resultado_ganancia = self.obtener_ganancia_backend(inicio, fin)

            if not resultado_ganancia.get("ok"):
                self.mostrar_error(resultado_ganancia.get("mensaje", "No se pudo cargar la ganancia."))
                return

            self.datos_ganancia = resultado_ganancia.get("data") or {}

            resultado_caja = self.obtener_caja_backend()

            if not resultado_caja.get("ok"):
                self.mostrar_error(resultado_caja.get("mensaje", "No se pudo cargar caja actual."))
                return

            self.datos_caja = resultado_caja.get("data")

            resultado_bajo_stock = self.obtener_bajo_stock_backend()

            if not resultado_bajo_stock.get("ok"):
                self.mostrar_error(resultado_bajo_stock.get("mensaje", "No se pudo cargar bajo stock."))
                return

            self.datos_bajo_stock = resultado_bajo_stock.get("data") or []

            self.actualizar_cards()
            self.cargar_tabla_resumen()
            self.cargar_tabla_ventas()
            self.cargar_tabla_productos()
            self.cargar_tabla_ganancia()
            self.cargar_tabla_caja()
            self.cargar_tabla_bajo_stock()
            self.actualizar_alertas()

            if mostrar_mensaje:
                self.actualizar_estado_operacion("Reportes cargados correctamente.", "ok")

        except Exception as error:
            self.mostrar_error(f"No se pudo actualizar reportes automáticamente: {error}")

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_reportes = False

    def obtener_ventas_backend(self, inicio, fin):
        posibles_metodos = [
            "reporte_ventas_por_rango",
            "ventas_por_rango",
            "obtener_ventas_por_rango",
        ]

        for nombre in posibles_metodos:
            metodo = getattr(self.pos, nombre, None)

            if callable(metodo):
                try:
                    resultado = metodo(inicio, fin)
                except TypeError:
                    try:
                        resultado = metodo(fecha_inicio=inicio, fecha_fin=fin)
                    except Exception:
                        continue
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Ventas obtenidas correctamente.",
                    "data": resultado or [],
                }

        return self.backend.reporte_ventas_por_rango(inicio, fin)

    def obtener_productos_backend(self, inicio, fin):
        posibles_metodos = [
            "reporte_productos_mas_vendidos",
            "productos_mas_vendidos",
            "obtener_productos_mas_vendidos",
        ]

        for nombre in posibles_metodos:
            metodo = getattr(self.pos, nombre, None)

            if callable(metodo):
                try:
                    resultado = metodo(fecha_inicio=inicio, fecha_fin=fin, limite=50)
                except TypeError:
                    try:
                        resultado = metodo(inicio, fin, 50)
                    except Exception:
                        continue
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Productos vendidos obtenidos correctamente.",
                    "data": resultado or [],
                }

        return self.backend.reporte_productos_mas_vendidos(inicio, fin, 50)

    def obtener_ganancia_backend(self, inicio, fin):
        posibles_metodos = [
            "reporte_ganancia_por_rango",
            "ganancia_por_rango",
            "obtener_ganancia_por_rango",
        ]

        for nombre in posibles_metodos:
            metodo = getattr(self.pos, nombre, None)

            if callable(metodo):
                try:
                    resultado = metodo(inicio, fin)
                except TypeError:
                    try:
                        resultado = metodo(fecha_inicio=inicio, fecha_fin=fin)
                    except Exception:
                        continue
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Ganancia obtenida correctamente.",
                    "data": resultado or {},
                }

        return self.backend.reporte_ganancia_por_rango(inicio, fin)

    def obtener_caja_backend(self):
        posibles_metodos = [
            "reporte_resumen_caja_actual",
            "resumen_caja_actual",
            "obtener_resumen_caja",
        ]

        for nombre in posibles_metodos:
            metodo = getattr(self.pos, nombre, None)

            if callable(metodo):
                try:
                    resultado = metodo()
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Caja obtenida correctamente.",
                    "data": resultado,
                }

        return self.backend.reporte_resumen_caja_actual()

    def obtener_bajo_stock_backend(self):
        posibles_metodos = [
            "productos_con_bajo_stock",
            "reporte_productos_bajo_stock",
            "productos_bajo_stock",
        ]

        for nombre in posibles_metodos:
            metodo = getattr(self.pos, nombre, None)

            if callable(metodo):
                try:
                    resultado = metodo()
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Bajo stock obtenido correctamente.",
                    "data": resultado or [],
                }

        return self.backend.productos_con_bajo_stock()

    # ============================================================
    # TABLAS Y CARDS
    # ============================================================

    def actualizar_cards(self):
        ventas_pagadas = [
            venta for venta in self.datos_ventas
            if str(venta.get("estado") or "").upper() == "PAGADA"
        ]

        cantidad_ventas = len(ventas_pagadas)
        total_vendido = sum(self.decimal(venta.get("total")) for venta in ventas_pagadas)
        total_impuesto = sum(self.decimal(venta.get("impuesto_total")) for venta in ventas_pagadas)
        total_neto = sum(
            self.decimal(venta.get("subtotal")) - self.decimal(venta.get("descuento_total"))
            for venta in ventas_pagadas
        )

        efectivo = Decimal("0")
        tarjeta = Decimal("0")
        transferencia = Decimal("0")

        for venta in ventas_pagadas:
            total = self.decimal(venta.get("total"))
            metodo = str(venta.get("metodo_pago") or "").upper()

            monto_efectivo = venta.get("monto_efectivo")
            monto_tarjeta = venta.get("monto_tarjeta")
            monto_transferencia = venta.get("monto_transferencia")
            vuelto = self.decimal(venta.get("vuelto"))

            if monto_efectivo is not None:
                efectivo += max(self.decimal(monto_efectivo) - vuelto, Decimal("0"))
            elif metodo == "EFECTIVO":
                efectivo += total

            if monto_tarjeta is not None:
                tarjeta += self.decimal(monto_tarjeta)
            elif metodo == "TARJETA":
                tarjeta += total

            if monto_transferencia is not None:
                transferencia += self.decimal(monto_transferencia)
            elif metodo == "TRANSFERENCIA":
                transferencia += total

        ganancia = self.decimal(self.datos_ganancia.get("ganancia_estimada"))
        ticket_promedio = Decimal("0")

        if cantidad_ventas > 0:
            ticket_promedio = total_vendido / Decimal(str(cantidad_ventas))

        self.datos_resumen = {
            "cantidad_ventas": cantidad_ventas,
            "total_vendido": total_vendido,
            "total_neto": total_neto,
            "impuesto": total_impuesto,
            "efectivo": efectivo,
            "tarjeta": tarjeta,
            "transferencia": transferencia,
            "ganancia": ganancia,
            "ticket_promedio": ticket_promedio,
            "bajo_stock": len(self.datos_bajo_stock),
        }

        self.labels["ventas"].setText(str(cantidad_ventas))
        self.labels["total_vendido"].setText(self.formato_pesos(total_vendido))
        self.labels["ganancia"].setText(self.formato_pesos(ganancia))
        self.labels["ticket_promedio"].setText(self.formato_pesos(ticket_promedio))
        self.labels["efectivo"].setText(self.formato_pesos(efectivo))
        self.labels["tarjeta"].setText(self.formato_pesos(tarjeta))
        self.labels["transferencia"].setText(self.formato_pesos(transferencia))
        self.labels["bajo_stock"].setText(str(len(self.datos_bajo_stock)))

        self.cambiar_tipo_card("ventas", "verde" if cantidad_ventas > 0 else "neutro")
        self.cambiar_tipo_card("total_vendido", "verde" if total_vendido > 0 else "neutro")
        self.cambiar_tipo_card("ganancia", "verde" if ganancia >= 0 else "rojo")
        self.cambiar_tipo_card("bajo_stock", "alerta" if self.datos_bajo_stock else "verde")

    def cargar_tabla_resumen(self):
        inicio = self.obtener_fecha_inicio()
        fin = self.obtener_fecha_fin()

        filas = [
            ("Rango consultado", f"{inicio} al {fin}", "Fechas usadas para ventas, ganancia y productos vendidos"),
            ("Ventas pagadas", self.datos_resumen.get("cantidad_ventas", 0), "Solo ventas con estado PAGADA"),
            ("Total neto", self.formato_pesos(self.datos_resumen.get("total_neto")), "Subtotal menos descuentos antes de IVA"),
            ("IVA", self.formato_pesos(self.datos_resumen.get("impuesto")), "Impuesto aplicado sobre el neto gravado"),
            ("Total vendido", self.formato_pesos(self.datos_resumen.get("total_vendido")), "Suma total de ventas pagadas con IVA"),
            ("Ganancia estimada", self.formato_pesos(self.datos_resumen.get("ganancia")), "Venta neta menos costo registrado en detalle"),
            ("Ticket promedio", self.formato_pesos(self.datos_resumen.get("ticket_promedio")), "Total vendido dividido por cantidad de ventas"),
            ("Efectivo", self.formato_pesos(self.datos_resumen.get("efectivo")), "Estimado por método de pago o montos si existen"),
            ("Tarjeta", self.formato_pesos(self.datos_resumen.get("tarjeta")), "Estimado por método de pago o montos si existen"),
            ("Transferencia", self.formato_pesos(self.datos_resumen.get("transferencia")), "Estimado por método de pago o montos si existen"),
            ("Productos bajo stock", self.datos_resumen.get("bajo_stock", 0), "Productos activos con stock actual menor o igual al mínimo"),
        ]

        self.cargar_tabla_generica(self.tabla_resumen, filas)

    def cargar_tabla_ventas(self):
        self.tabla_ventas.setRowCount(0)

        if not self.datos_ventas:
            self.insertar_fila_vacia(self.tabla_ventas, "No hay ventas en el rango seleccionado.")
            return

        for fila, venta in enumerate(self.datos_ventas):
            self.tabla_ventas.insertRow(fila)

            valores = [
                venta.get("numero_venta"),
                self.formato_fecha(venta.get("fecha_venta")),
                venta.get("cajero"),
                venta.get("metodo_pago"),
                self.formato_pesos(venta.get("subtotal")),
                self.formato_pesos(venta.get("descuento_total")),
                self.formato_pesos(venta.get("impuesto_total")),
                self.formato_pesos(venta.get("total")),
                venta.get("estado"),
            ]

            self.insertar_fila(self.tabla_ventas, fila, valores)

            estado = str(venta.get("estado") or "").upper()

            if estado == "PAGADA":
                self.colorear_fila(self.tabla_ventas, fila, "#ECFDF5", "#166534")
            elif estado in ["ANULADA", "CANCELADA"]:
                self.colorear_fila(self.tabla_ventas, fila, "#FEF2F2", "#991B1B")

    def cargar_tabla_productos(self):
        self.tabla_productos.setRowCount(0)

        if not self.datos_productos:
            self.insertar_fila_vacia(self.tabla_productos, "No hay productos vendidos en el rango seleccionado.")
            return

        for fila, producto in enumerate(self.datos_productos):
            self.tabla_productos.insertRow(fila)

            total_vendido = self.decimal(producto.get("total_vendido"))
            ganancia = self.decimal(producto.get("ganancia_estimada"))
            margen = Decimal("0")

            if total_vendido > 0:
                margen = (ganancia / total_vendido) * Decimal("100")

            valores = [
                producto.get("codigo_barra"),
                producto.get("nombre_producto"),
                self.formato_numero(producto.get("cantidad_vendida")),
                self.formato_pesos(total_vendido),
                self.formato_pesos(ganancia),
                f"{margen:.1f}%",
            ]

            self.insertar_fila(self.tabla_productos, fila, valores)

    def cargar_tabla_ganancia(self):
        inicio = self.obtener_fecha_inicio()
        fin = self.obtener_fecha_fin()

        filas = [
            ("Rango consultado", f"{inicio} al {fin}"),
            ("Cantidad ventas", self.datos_ganancia.get("cantidad_ventas")),
            ("Total vendido", self.formato_pesos(self.datos_ganancia.get("total_vendido"))),
            ("Total neto", self.formato_pesos(self.datos_ganancia.get("total_neto"))),
            ("IVA", self.formato_pesos(self.datos_ganancia.get("impuesto_total"))),
            ("Costo total", self.formato_pesos(self.datos_ganancia.get("costo_total"))),
            ("Ganancia estimada", self.formato_pesos(self.datos_ganancia.get("ganancia_estimada"))),
        ]

        self.cargar_tabla_generica(self.tabla_ganancia, filas)

    def cargar_tabla_caja(self):
        if not self.datos_caja:
            self.cargar_tabla_generica(
                self.tabla_caja,
                [
                    ("Estado", "No hay caja abierta"),
                    ("Acción sugerida", "Abrir caja desde el módulo Caja"),
                ],
            )
            return

        caja = self.datos_caja

        filas = [
            ("ID caja", caja.get("id")),
            ("Estado", caja.get("estado")),
            ("Usuario apertura", caja.get("usuario_apertura")),
            ("Usuario cierre", caja.get("usuario_cierre")),
            ("Fecha apertura", self.formato_fecha(caja.get("fecha_apertura"))),
            ("Fecha cierre", self.formato_fecha(caja.get("fecha_cierre"))),
            ("Monto inicial", self.formato_pesos(caja.get("monto_inicial"))),
            ("Ventas efectivo", self.formato_pesos(caja.get("monto_ventas_efectivo"))),
            ("Ventas tarjeta", self.formato_pesos(caja.get("monto_ventas_tarjeta"))),
            ("Ventas transferencia", self.formato_pesos(caja.get("monto_ventas_transferencia"))),
            ("Ventas total", self.formato_pesos(caja.get("monto_ventas_total"))),
            ("Ingresos extra", self.formato_pesos(caja.get("monto_ingresos_extra"))),
            ("Retiros", self.formato_pesos(caja.get("monto_retiros"))),
            ("Monto esperado", self.formato_pesos(caja.get("monto_esperado_caja"))),
            ("Monto real cierre", self.formato_pesos(caja.get("monto_real_cierre"))),
            ("Diferencia", self.formato_pesos(caja.get("diferencia"))),
        ]

        self.cargar_tabla_generica(self.tabla_caja, filas)

    def cargar_tabla_bajo_stock(self):
        self.tabla_bajo_stock.setRowCount(0)

        if not self.datos_bajo_stock:
            self.insertar_fila_vacia(self.tabla_bajo_stock, "No hay productos bajo stock.")
            return

        for fila, producto in enumerate(self.datos_bajo_stock):
            self.tabla_bajo_stock.insertRow(fila)

            valores = [
                producto.get("id"),
                producto.get("codigo_barra"),
                producto.get("nombre"),
                producto.get("categoria") or "Sin categoría",
                self.formato_numero(producto.get("stock_actual")),
                self.formato_numero(producto.get("stock_minimo")),
                self.formato_pesos(producto.get("precio_venta")),
            ]

            self.insertar_fila(self.tabla_bajo_stock, fila, valores)
            self.colorear_fila(self.tabla_bajo_stock, fila, "#FFFBEB", "#92400E")

    def cargar_tabla_generica(self, tabla, filas):
        tabla.setRowCount(0)

        if not filas:
            self.insertar_fila_vacia(tabla, "Sin información para mostrar.")
            return

        for fila, datos in enumerate(filas):
            tabla.insertRow(fila)

            for columna, valor in enumerate(datos):
                item = QTableWidgetItem(str(valor if valor is not None else ""))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if columna == 0
                    else Qt.AlignmentFlag.AlignCenter
                )
                tabla.setItem(fila, columna, item)

    def insertar_fila(self, tabla, fila, valores):
        for columna, valor in enumerate(valores):
            item = QTableWidgetItem(str(valor if valor is not None else ""))

            if columna in [1, 2] and (tabla is self.tabla_productos or tabla is self.tabla_bajo_stock):
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item.setToolTip(str(valor if valor is not None else ""))
            tabla.setItem(fila, columna, item)

    def insertar_fila_vacia(self, tabla, texto):
        tabla.setRowCount(1)

        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        tabla.setItem(0, 0, item)

        for columna in range(1, tabla.columnCount()):
            tabla.setItem(0, columna, QTableWidgetItem(""))

    def colorear_fila(self, tabla, fila, fondo, texto):
        for columna in range(tabla.columnCount()):
            item = tabla.item(fila, columna)

            if item:
                item.setBackground(QColor(fondo))
                item.setForeground(QColor(texto))

    def actualizar_alertas(self):
        alertas = []

        if not self.datos_ventas:
            alertas.append("No hay ventas en el rango seleccionado.")

        if self.datos_bajo_stock:
            alertas.append(f"{len(self.datos_bajo_stock)} producto(s) bajo stock.")

        if not self.datos_caja:
            alertas.append("No hay caja abierta actualmente.")

        ganancia = self.decimal(self.datos_ganancia.get("ganancia_estimada"))

        if ganancia < 0:
            alertas.append("La ganancia estimada del rango es negativa.")

        if not alertas:
            self.label_alertas.setText("Reportes en buen estado: datos cargados correctamente.")
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de reportes: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    # ============================================================
    # EXPORTACIÓN EXCEL
    # ============================================================

    def exportar_reporte_completo(self):
        inicio = self.obtener_fecha_inicio()
        fin = self.obtener_fecha_fin()

        nombre_sugerido = f"reporte_pos_{inicio}_a_{fin}.xlsx"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte completo",
            nombre_sugerido,
            "Excel (*.xlsx)",
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"

        resultado = self.exportar_reporte_completo_backend(
            ruta_archivo=ruta,
            fecha_inicio=inicio,
            fecha_fin=fin,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error al exportar",
                resultado.get("mensaje", "No se pudo exportar el reporte."),
            )
            return

        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Reporte exportado correctamente en:\n{resultado.get('data', {}).get('ruta_archivo', ruta)}",
        )

        self.actualizar_estado_operacion("Reporte Excel completo exportado correctamente.", "ok")

    def exportar_pestana_actual(self):
        indice = self.tabs.currentIndex()
        nombre_tab = self.tabs.tabText(indice)

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            f"Guardar {nombre_tab}",
            f"{nombre_tab.lower().replace(' ', '_')}.xlsx",
            "Excel (*.xlsx)",
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"

        headers, filas = self.obtener_datos_pestana_actual()

        if not headers:
            QMessageBox.warning(
                self,
                "Sin datos",
                "No se pudo obtener la información de la pestaña actual.",
            )
            return

        resultado = self.exportar_tabla_excel_backend(
            ruta_archivo=ruta,
            nombre_hoja=nombre_tab,
            headers=headers,
            filas=filas,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error al exportar",
                resultado.get("mensaje", "No se pudo exportar la pestaña."),
            )
            return

        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Archivo exportado correctamente en:\n{resultado.get('data', {}).get('ruta_archivo', ruta)}",
        )

        self.actualizar_estado_operacion("Pestaña exportada correctamente.", "ok")

    def exportar_reporte_completo_backend(self, ruta_archivo, fecha_inicio, fecha_fin):
        metodo = getattr(self.pos, "exportar_reporte_completo", None)

        if callable(metodo):
            try:
                return metodo(
                    ruta_archivo=ruta_archivo,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )
            except TypeError:
                pass
            except Exception as error:
                return {
                    "ok": False,
                    "mensaje": f"Error al exportar con servicio: {error}",
                    "data": None,
                }

        hojas = self.obtener_hojas_exportacion()
        return self.exportar_excel_local(ruta_archivo, hojas)

    def exportar_tabla_excel_backend(self, ruta_archivo, nombre_hoja, headers, filas):
        metodo = getattr(self.pos, "exportar_tabla_excel", None)

        if callable(metodo):
            try:
                return metodo(
                    ruta_archivo=ruta_archivo,
                    nombre_hoja=nombre_hoja,
                    headers=headers,
                    filas=filas,
                )
            except TypeError:
                pass
            except Exception as error:
                return {
                    "ok": False,
                    "mensaje": f"Error al exportar con servicio: {error}",
                    "data": None,
                }

        return self.exportar_excel_local(
            ruta_archivo,
            [(nombre_hoja, headers, filas)],
        )

    def exportar_excel_local(self, ruta_archivo, hojas):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ModuleNotFoundError:
            return {
                "ok": False,
                "mensaje": "Falta instalar openpyxl. Ejecuta: pip install openpyxl",
                "data": None,
            }

        try:
            wb = Workbook()
            hoja_inicial = wb.active
            wb.remove(hoja_inicial)

            fill_header = PatternFill("solid", fgColor="0F172A")
            font_header = Font(color="FFFFFF", bold=True)
            border = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="CBD5E1"),
                bottom=Side(style="thin", color="CBD5E1"),
            )

            for nombre_hoja, headers, filas in hojas:
                nombre_limpio = self.limpiar_nombre_hoja(nombre_hoja)
                ws = wb.create_sheet(nombre_limpio)

                ws.append(headers)

                for celda in ws[1]:
                    celda.fill = fill_header
                    celda.font = font_header
                    celda.alignment = Alignment(horizontal="center", vertical="center")
                    celda.border = border

                for fila in filas:
                    ws.append(list(fila))

                for row in ws.iter_rows():
                    for cell in row:
                        cell.border = border
                        cell.alignment = Alignment(
                            horizontal="center" if cell.column != 2 else "left",
                            vertical="center",
                            wrap_text=True,
                        )

                for columna in range(1, len(headers) + 1):
                    letra = get_column_letter(columna)
                    ancho = 16

                    if columna == 2:
                        ancho = 32
                    elif columna == 3:
                        ancho = 28

                    ws.column_dimensions[letra].width = ancho

                ws.freeze_panes = "A2"

            wb.save(ruta_archivo)

            return {
                "ok": True,
                "mensaje": "Archivo Excel exportado correctamente.",
                "data": {
                    "ruta_archivo": ruta_archivo,
                },
            }

        except Exception as error:
            return {
                "ok": False,
                "mensaje": f"No se pudo exportar Excel: {error}",
                "data": None,
            }

    def limpiar_nombre_hoja(self, nombre):
        nombre = str(nombre or "Hoja")
        caracteres_invalidos = ["\\", "/", "*", "[", "]", ":", "?"]

        for caracter in caracteres_invalidos:
            nombre = nombre.replace(caracter, "")

        return nombre[:31] or "Hoja"

    # ============================================================
    # CONFIGURACIÓN NEGOCIO PARA PDF
    # ============================================================

    def obtener_configuracion_negocio_segura(self):
        try:
            consulta = """
                SELECT
                    nombre_negocio,
                    rut,
                    direccion,
                    telefono,
                    email,
                    logo_url
                FROM negocio_config
                ORDER BY id ASC
                LIMIT 1;
            """

            config = ejecutar_consulta(
                consulta,
                obtener_uno=True
            )

            if config:
                return config

        except Exception:
            pass

        return {}

    def obtener_nombre_negocio_pdf(self, config):
        nombre = str((config or {}).get("nombre_negocio") or "").strip()

        if nombre:
            return nombre

        return "POS PYMES"

    def obtener_logo_negocio_pdf(self, config):
        logo = str((config or {}).get("logo_url") or "").strip()

        if not logo:
            return ""

        if logo.lower().startswith(("http://", "https://")):
            return ""

        ruta = Path(logo)

        if not ruta.exists():
            return ""

        return str(ruta)

    def crear_imagen_logo_pdf(self, ruta_logo, RLImage, cm, ancho_max=4.2, alto_max=1.9):
        try:
            if not ruta_logo:
                return None

            imagen = RLImage(ruta_logo)

            max_width = ancho_max * cm
            max_height = alto_max * cm

            if imagen.imageWidth <= 0 or imagen.imageHeight <= 0:
                return None

            escala = min(
                max_width / float(imagen.imageWidth),
                max_height / float(imagen.imageHeight),
            )

            imagen.drawWidth = imagen.imageWidth * escala
            imagen.drawHeight = imagen.imageHeight * escala

            return imagen

        except Exception:
            return None

    def crear_encabezado_pdf(
        self,
        config,
        fecha_reporte,
        inicio,
        fin,
        Table,
        TableStyle,
        Paragraph,
        ParagraphStyle,
        Spacer,
        RLImage,
        colors,
        cm,
        estilos
    ):
        nombre_negocio = self.obtener_nombre_negocio_pdf(config)
        rut = str((config or {}).get("rut") or "").strip()
        direccion = str((config or {}).get("direccion") or "").strip()
        telefono = str((config or {}).get("telefono") or "").strip()
        email = str((config or {}).get("email") or "").strip()
        ruta_logo = self.obtener_logo_negocio_pdf(config)

        estilo_negocio = ParagraphStyle(
            "NegocioPDF",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=2,
        )

        estilo_info = ParagraphStyle(
            "InfoNegocioPDF",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569"),
        )

        estilo_logo_fallback = ParagraphStyle(
            "LogoFallbackPDF",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor("#94A3B8"),
        )

        info_lineas = [
            f"<b>{nombre_negocio}</b>",
        ]

        if rut:
            info_lineas.append(f"RUT: {rut}")

        if direccion:
            info_lineas.append(direccion)

        contacto = " | ".join([dato for dato in [telefono, email] if dato])

        if contacto:
            info_lineas.append(contacto)

        texto_negocio = Paragraph("<br/>".join(info_lineas), estilo_negocio)

        texto_reporte = Paragraph(
            f"<b>Reporte POS</b><br/>"
            f"Rango: {inicio} al {fin}<br/>"
            f"Generado: {fecha_reporte}",
            estilo_info,
        )

        logo = self.crear_imagen_logo_pdf(ruta_logo, RLImage, cm)

        if logo is None:
            logo = Paragraph("SIN LOGO", estilo_logo_fallback)

        tabla_header = Table(
            [
                [
                    logo,
                    texto_negocio,
                    texto_reporte,
                ]
            ],
            colWidths=[4.6 * cm, 13.4 * cm, 8.0 * cm],
        )

        tabla_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        return [
            tabla_header,
            Spacer(1, 12),
        ]

    # ============================================================
    # EXPORTACIÓN PDF
    # ============================================================

    def exportar_reporte_pdf(self):
        inicio = self.obtener_fecha_inicio()
        fin = self.obtener_fecha_fin()

        nombre_sugerido = f"reporte_pos_{inicio}_a_{fin}.pdf"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte PDF",
            nombre_sugerido,
            "PDF (*.pdf)",
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        resultado = self.exportar_pdf_local(ruta)

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error al exportar PDF",
                resultado.get("mensaje", "No se pudo exportar el PDF."),
            )
            return

        QMessageBox.information(
            self,
            "PDF exportado",
            f"Reporte PDF exportado correctamente en:\n{ruta}",
        )

        self.actualizar_estado_operacion("Reporte PDF exportado correctamente.", "ok")

    def exportar_pdf_local(self, ruta_archivo):
        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
                PageBreak,
                Image as RLImage,
            )
        except ModuleNotFoundError:
            return {
                "ok": False,
                "mensaje": "Falta instalar reportlab. Ejecuta: pip install reportlab",
                "data": None,
            }

        try:
            doc = SimpleDocTemplate(
                ruta_archivo,
                pagesize=landscape(A4),
                rightMargin=1.1 * cm,
                leftMargin=1.1 * cm,
                topMargin=1.1 * cm,
                bottomMargin=1.1 * cm,
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
                spaceAfter=12,
            )

            estilo_celda = ParagraphStyle(
                "CeldaPOS",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=6.5,
                leading=8,
            )

            elementos = []

            fecha_reporte = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
            inicio = self.obtener_fecha_inicio()
            fin = self.obtener_fecha_fin()
            config_negocio = self.obtener_configuracion_negocio_segura()

            hojas = self.obtener_hojas_exportacion()

            for indice, (nombre_hoja, headers, filas) in enumerate(hojas):
                if indice > 0:
                    elementos.append(PageBreak())

                elementos.extend(
                    self.crear_encabezado_pdf(
                        config=config_negocio,
                        fecha_reporte=fecha_reporte,
                        inicio=inicio,
                        fin=fin,
                        Table=Table,
                        TableStyle=TableStyle,
                        Paragraph=Paragraph,
                        ParagraphStyle=ParagraphStyle,
                        Spacer=Spacer,
                        RLImage=RLImage,
                        colors=colors,
                        cm=cm,
                        estilos=estilos,
                    )
                )

                elementos.append(Paragraph(nombre_hoja, estilo_titulo))
                elementos.append(Paragraph(
                    f"Rango: {inicio} al {fin} | Generado: {fecha_reporte}",
                    estilo_subtitulo,
                ))
                elementos.append(Spacer(1, 8))

                data = [headers]

                for fila in filas:
                    fila_pdf = []
                    for valor in fila:
                        texto = str(valor if valor is not None else "")
                        fila_pdf.append(Paragraph(texto, estilo_celda))
                    data.append(fila_pdf)

                if len(data) == 1:
                    data.append(["Sin información"])

                tabla = Table(
                    data,
                    repeatRows=1,
                )

                tabla.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7),
                    ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                        colors.white,
                        colors.HexColor("#F8FAFC"),
                    ]),
                ]))

                elementos.append(tabla)

            doc.build(elementos)

            return {
                "ok": True,
                "mensaje": "PDF exportado correctamente.",
                "data": {
                    "ruta_archivo": ruta_archivo,
                },
            }

        except Exception as error:
            return {
                "ok": False,
                "mensaje": f"No se pudo exportar PDF: {error}",
                "data": None,
            }

    # ============================================================
    # DATOS PARA EXPORTAR
    # ============================================================

    def obtener_hojas_exportacion(self):
        return [
            (
                "Resumen",
                ["Concepto", "Valor", "Detalle"],
                self.obtener_filas_resumen_export(),
            ),
            (
                "Ventas",
                ["Número", "Fecha", "Cajero", "Método pago", "Subtotal", "Descuento", "IVA", "Total", "Estado"],
                self.obtener_filas_ventas_export(),
            ),
            (
                "Productos vendidos",
                ["Código", "Producto", "Cantidad vendida", "Total vendido", "Ganancia", "Margen"],
                self.obtener_filas_productos_export(),
            ),
            (
                "Ganancia",
                ["Concepto", "Valor"],
                self.obtener_filas_ganancia_export(),
            ),
            (
                "Caja actual",
                ["Concepto", "Valor"],
                self.obtener_filas_caja_export(),
            ),
            (
                "Bajo stock",
                ["ID", "Código", "Producto", "Categoría", "Stock actual", "Stock mínimo", "Precio venta"],
                self.obtener_filas_bajo_stock_export(),
            ),
        ]

    def obtener_datos_pestana_actual(self):
        indice = self.tabs.currentIndex()

        if indice == 0:
            return ["Concepto", "Valor", "Detalle"], self.obtener_filas_resumen_export()

        if indice == 1:
            return ["Número", "Fecha", "Cajero", "Método pago", "Subtotal", "Descuento", "IVA", "Total", "Estado"], self.obtener_filas_ventas_export()

        if indice == 2:
            return ["Código", "Producto", "Cantidad vendida", "Total vendido", "Ganancia", "Margen"], self.obtener_filas_productos_export()

        if indice == 3:
            return ["Concepto", "Valor"], self.obtener_filas_ganancia_export()

        if indice == 4:
            return ["Concepto", "Valor"], self.obtener_filas_caja_export()

        if indice == 5:
            return ["ID", "Código", "Producto", "Categoría", "Stock actual", "Stock mínimo", "Precio venta"], self.obtener_filas_bajo_stock_export()

        return [], []

    def obtener_filas_resumen_export(self):
        inicio = self.obtener_fecha_inicio()
        fin = self.obtener_fecha_fin()

        return [
            ("Rango consultado", f"{inicio} al {fin}", "Fechas usadas para ventas, ganancia y productos vendidos"),
            ("Ventas pagadas", self.datos_resumen.get("cantidad_ventas", 0), "Solo ventas con estado PAGADA"),
            ("Total neto", self.formato_pesos(self.datos_resumen.get("total_neto")), "Subtotal menos descuentos antes de IVA"),
            ("IVA", self.formato_pesos(self.datos_resumen.get("impuesto")), "Impuesto aplicado sobre el neto gravado"),
            ("Total vendido", self.formato_pesos(self.datos_resumen.get("total_vendido")), "Suma total de ventas pagadas con IVA"),
            ("Ganancia estimada", self.formato_pesos(self.datos_resumen.get("ganancia")), "Venta neta menos costo registrado en detalle"),
            ("Ticket promedio", self.formato_pesos(self.datos_resumen.get("ticket_promedio")), "Total vendido dividido por cantidad de ventas"),
            ("Efectivo", self.formato_pesos(self.datos_resumen.get("efectivo")), "Estimado por método de pago o montos si existen"),
            ("Tarjeta", self.formato_pesos(self.datos_resumen.get("tarjeta")), "Estimado por método de pago o montos si existen"),
            ("Transferencia", self.formato_pesos(self.datos_resumen.get("transferencia")), "Estimado por método de pago o montos si existen"),
            ("Productos bajo stock", self.datos_resumen.get("bajo_stock", 0), "Productos activos con stock actual menor o igual al mínimo"),
        ]

    def obtener_filas_ventas_export(self):
        filas = []

        for venta in self.datos_ventas:
            filas.append([
                venta.get("numero_venta"),
                self.formato_fecha(venta.get("fecha_venta")),
                venta.get("cajero"),
                venta.get("metodo_pago"),
                self.formato_pesos(venta.get("subtotal")),
                self.formato_pesos(venta.get("descuento_total")),
                self.formato_pesos(venta.get("impuesto_total")),
                self.formato_pesos(venta.get("total")),
                venta.get("estado"),
            ])

        return filas

    def obtener_filas_productos_export(self):
        filas = []

        for producto in self.datos_productos:
            total_vendido = self.decimal(producto.get("total_vendido"))
            ganancia = self.decimal(producto.get("ganancia_estimada"))
            margen = Decimal("0")

            if total_vendido > 0:
                margen = (ganancia / total_vendido) * Decimal("100")

            filas.append([
                producto.get("codigo_barra"),
                producto.get("nombre_producto"),
                self.formato_numero(producto.get("cantidad_vendida")),
                self.formato_pesos(total_vendido),
                self.formato_pesos(ganancia),
                f"{margen:.1f}%",
            ])

        return filas

    def obtener_filas_ganancia_export(self):
        return [
            ("Cantidad ventas", self.datos_ganancia.get("cantidad_ventas")),
            ("Total vendido", self.formato_pesos(self.datos_ganancia.get("total_vendido"))),
            ("Total neto", self.formato_pesos(self.datos_ganancia.get("total_neto"))),
            ("IVA", self.formato_pesos(self.datos_ganancia.get("impuesto_total"))),
            ("Costo total", self.formato_pesos(self.datos_ganancia.get("costo_total"))),
            ("Ganancia estimada", self.formato_pesos(self.datos_ganancia.get("ganancia_estimada"))),
        ]

    def obtener_filas_caja_export(self):
        if not self.datos_caja:
            return [
                ("Estado", "No hay caja abierta"),
                ("Acción sugerida", "Abrir caja desde el módulo Caja"),
            ]

        caja = self.datos_caja

        return [
            ("ID caja", caja.get("id")),
            ("Estado", caja.get("estado")),
            ("Usuario apertura", caja.get("usuario_apertura")),
            ("Usuario cierre", caja.get("usuario_cierre")),
            ("Fecha apertura", self.formato_fecha(caja.get("fecha_apertura"))),
            ("Fecha cierre", self.formato_fecha(caja.get("fecha_cierre"))),
            ("Monto inicial", self.formato_pesos(caja.get("monto_inicial"))),
            ("Ventas efectivo", self.formato_pesos(caja.get("monto_ventas_efectivo"))),
            ("Ventas tarjeta", self.formato_pesos(caja.get("monto_ventas_tarjeta"))),
            ("Ventas transferencia", self.formato_pesos(caja.get("monto_ventas_transferencia"))),
            ("Ventas total", self.formato_pesos(caja.get("monto_ventas_total"))),
            ("Ingresos extra", self.formato_pesos(caja.get("monto_ingresos_extra"))),
            ("Retiros", self.formato_pesos(caja.get("monto_retiros"))),
            ("Monto esperado", self.formato_pesos(caja.get("monto_esperado_caja"))),
            ("Monto real cierre", self.formato_pesos(caja.get("monto_real_cierre"))),
            ("Diferencia", self.formato_pesos(caja.get("diferencia"))),
        ]

    def obtener_filas_bajo_stock_export(self):
        filas = []

        for producto in self.datos_bajo_stock:
            filas.append([
                producto.get("id"),
                producto.get("codigo_barra"),
                producto.get("nombre"),
                producto.get("categoria") or "Sin categoría",
                self.formato_numero(producto.get("stock_actual")),
                self.formato_numero(producto.get("stock_minimo")),
                self.formato_pesos(producto.get("precio_venta")),
            ])

        return filas

    # ============================================================
    # UTILIDADES
    # ============================================================

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

    def formato_fecha(self, fecha):
        metodo = getattr(self.pos, "formato_fecha", None)

        if callable(metodo):
            try:
                return metodo(fecha)
            except Exception:
                pass

        return self.backend.formato_fecha(fecha)

    def formato_numero(self, valor):
        try:
            numero = Decimal(str(valor or 0))

            if numero == numero.to_integral():
                return str(int(numero))

            return f"{numero:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return "0"

    def actualizar_estado_operacion(self, texto, tipo="info"):
        if self.label_estado_operacion is None:
            return

        self.label_estado_operacion.setText(texto)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta(tipo))

    def mostrar_error(self, mensaje):
        self.actualizar_estado_operacion(mensaje, "error")

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
            QFrame#panelFiltrosReportes,
            QFrame#panelTabsReportes {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardReporte {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardReporte[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardReporte[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardReporte[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardReporte[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardReporte[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardReporte[tipo="neutro"] {
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

            QDateEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 6px 6px;
                color: #0F172A;
                font-size: 14px;
                font-weight: 700;
            }

            QDateEdit:focus {
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

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
                border: none;
                border-radius: 10px;
            }

            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                background-color: #FFFFFF;
            }

            QTabBar::tab {
                background-color: #F8FAFC;
                color: #475569;
                border: 1px solid #E5E7EB;
                border-bottom: none;
                padding: 10px 16px;
                font-weight: 700;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }

            QTabBar::tab:selected {
                background-color: #2563EB;
                color: white;
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