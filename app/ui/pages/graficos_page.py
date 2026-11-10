from collections import defaultdict
from decimal import Decimal
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDate, QDateTime
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
    QPieSeries,
    QHorizontalBarSeries,
    QBarSet,
    QBarCategoryAxis,
)


try:
    from app.reportes import (
        ventas_por_rango,
        productos_mas_vendidos,
        productos_bajo_stock,
    )
except Exception:
    ventas_por_rango = None
    productos_mas_vendidos = None
    productos_bajo_stock = None


try:
    from app.productos import listar_productos
except Exception:
    listar_productos = None


class GraficosServiceAdapter:
    def __init__(self, pos_service):
        self.pos = pos_service

    def respuesta(self, ok, mensaje, data=None):
        return {
            "ok": ok,
            "mensaje": mensaje,
            "data": data,
        }

    def normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return {
            "ok": True,
            "mensaje": mensaje_ok,
            "data": resultado,
        }

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

    def obtener_ventas_hoy(self):
        fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")

        metodos = [
            "reporte_ventas_por_rango",
            "ventas_por_rango",
            "obtener_ventas_por_rango",
        ]

        for nombre_metodo in metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(fecha_hoy, fecha_hoy)
            except TypeError:
                try:
                    resultado = metodo(fecha_inicio=fecha_hoy, fecha_fin=fecha_hoy)
                except Exception:
                    continue
            except Exception:
                continue

            return self.normalizar_respuesta(
                resultado,
                "Ventas obtenidas correctamente.",
            )

        if ventas_por_rango is not None:
            try:
                return ventas_por_rango(fecha_hoy, fecha_hoy)
            except Exception as error:
                return self.respuesta(False, f"Error al obtener ventas: {error}", [])

        return self.respuesta(
            False,
            "No existe método para obtener ventas por rango.",
            [],
        )

    def obtener_productos_top_hoy(self, limite=8):
        fecha_hoy = QDate.currentDate().toString("yyyy-MM-dd")

        metodos = [
            "reporte_productos_mas_vendidos",
            "productos_mas_vendidos",
            "obtener_productos_mas_vendidos",
        ]

        for nombre_metodo in metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(fecha_inicio=fecha_hoy, fecha_fin=fecha_hoy, limite=limite)
            except TypeError:
                try:
                    resultado = metodo(fecha_hoy, fecha_hoy, limite)
                except Exception:
                    continue
            except Exception:
                continue

            return self.normalizar_respuesta(
                resultado,
                "Productos más vendidos obtenidos correctamente.",
            )

        if productos_mas_vendidos is not None:
            try:
                return productos_mas_vendidos(fecha_hoy, fecha_hoy, limite)
            except Exception as error:
                return self.respuesta(False, f"Error al obtener productos vendidos: {error}", [])

        return self.respuesta(
            False,
            "No existe método para obtener productos más vendidos.",
            [],
        )

    def obtener_bajo_stock(self):
        metodos = [
            "productos_con_bajo_stock",
            "reporte_productos_bajo_stock",
            "productos_bajo_stock",
        ]

        for nombre_metodo in metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo()
            except Exception:
                continue

            return self.normalizar_respuesta(
                resultado,
                "Productos bajo stock obtenidos correctamente.",
            )

        if productos_bajo_stock is not None:
            try:
                return productos_bajo_stock()
            except Exception as error:
                return self.respuesta(False, f"Error al obtener bajo stock: {error}", [])

        return self.respuesta(
            False,
            "No existe método para obtener productos bajo stock.",
            [],
        )

    def obtener_productos(self):
        metodos = [
            "obtener_productos",
            "listar_productos_sistema",
            "obtener_productos_sistema",
            "listar_productos",
        ]

        for nombre_metodo in metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo()
            except Exception:
                continue

            return self.normalizar_respuesta(
                resultado,
                "Productos obtenidos correctamente.",
            )

        if listar_productos is not None:
            try:
                resultado = listar_productos()
                return self.normalizar_respuesta(
                    resultado,
                    "Productos obtenidos correctamente.",
                )
            except Exception as error:
                return self.respuesta(False, f"Error al obtener productos: {error}", [])

        return self.respuesta(
            False,
            "No existe método para listar productos.",
            [],
        )


class GraficosPage(QWidget):
    def __init__(self, pos_service):
        super().__init__()

        self.pos = pos_service
        self.service = GraficosServiceAdapter(pos_service)

        self.actualizando_graficos = False
        self.timer_graficos = None

        self.ventas_hoy = []
        self.productos_top = []
        self.bajo_stock = []
        self.productos = []

        self.labels = {}
        self.cards = {}

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.chart_ventas_hora = None
        self.chart_metodos_pago = None
        self.chart_productos_top = None
        self.chart_stock = None

        self.construir_interfaz()
        self.cargar_datos(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_graficos = QTimer(self)
        self.timer_graficos.timeout.connect(self.cargar_datos_automatico)
        self.timer_graficos.start(10000)

    def cargar_datos_automatico(self):
        if self.actualizando_graficos:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_datos(mostrar_mensaje=False)

    def construir_interfaz(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(32, 32, 32, 32)
        layout_principal.setSpacing(20)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()
        textos.setSpacing(6)

        titulo = QLabel("Gráficos en tiempo real")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Panel visual automático de ventas, métodos de pago, productos más vendidos y estado de stock."
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

        layout_principal.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["total_vendido"] = self.crear_card(
            cards, 0, 0,
            key="total_vendido",
            titulo="Total vendido hoy",
            valor="$0",
            detalle="Ventas pagadas del día",
            tipo="verde",
        )

        self.labels["ventas_hoy"] = self.crear_card(
            cards, 0, 1,
            key="ventas_hoy",
            titulo="Ventas hoy",
            valor="0",
            detalle="Cantidad de ventas pagadas",
            tipo="azul",
        )

        self.labels["ticket_promedio"] = self.crear_card(
            cards, 0, 2,
            key="ticket_promedio",
            titulo="Ticket promedio",
            valor="$0",
            detalle="Promedio por venta",
            tipo="morado",
        )

        self.labels["bajo_stock"] = self.crear_card(
            cards, 0, 3,
            key="bajo_stock",
            titulo="Bajo stock",
            valor="0",
            detalle="Productos que requieren reposición",
            tipo="alerta",
        )

        self.labels["efectivo"] = self.crear_card(
            cards, 1, 0,
            key="efectivo",
            titulo="Efectivo",
            valor="$0",
            detalle="Afecta caja física",
            tipo="verde",
        )

        self.labels["tarjeta"] = self.crear_card(
            cards, 1, 1,
            key="tarjeta",
            titulo="Tarjeta",
            valor="$0",
            detalle="Ventas con tarjeta",
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

        self.labels["producto_top"] = self.crear_card(
            cards, 1, 3,
            key="producto_top",
            titulo="Producto top",
            valor="-",
            detalle="Más vendido del día",
            tipo="neutro",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout_principal.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas gráficas...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout_principal.addWidget(self.label_alertas)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        contenedor = QWidget()
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(20)

        grid_graficos = QGridLayout()
        grid_graficos.setContentsMargins(0, 0, 0, 0)
        grid_graficos.setHorizontalSpacing(18)
        grid_graficos.setVerticalSpacing(18)

        self.chart_ventas_hora = self.crear_chart_view()
        self.chart_metodos_pago = self.crear_chart_view()
        self.chart_productos_top = self.crear_chart_view()
        self.chart_stock = self.crear_chart_view()

        grid_graficos.addWidget(
            self.crear_panel_grafico(
                "Ventas por hora",
                "Distribución de ventas pagadas durante el día.",
                self.chart_ventas_hora,
            ),
            0,
            0,
        )

        grid_graficos.addWidget(
            self.crear_panel_grafico(
                "Métodos de pago",
                "Participación de efectivo, tarjeta y transferencia.",
                self.chart_metodos_pago,
            ),
            0,
            1,
        )

        grid_graficos.addWidget(
            self.crear_panel_grafico(
                "Productos más vendidos",
                "Ranking por total vendido durante el día.",
                self.chart_productos_top,
            ),
            1,
            0,
        )

        grid_graficos.addWidget(
            self.crear_panel_grafico(
                "Estado de stock",
                "Resumen visual de productos OK, bajo stock y sin stock.",
                self.chart_stock,
            ),
            1,
            1,
        )

        grid_graficos.setColumnStretch(0, 1)
        grid_graficos.setColumnStretch(1, 1)

        layout_scroll.addLayout(grid_graficos)

        self.label_estado_operacion = QLabel("Gráficos listos para monitorear.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout_scroll.addWidget(self.label_estado_operacion)

        scroll.setWidget(contenedor)
        layout_principal.addWidget(scroll)

        self.aplicar_estilos()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardGrafico")
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

    def crear_panel_grafico(self, titulo, descripcion, chart_view):
        panel = QFrame()
        panel.setObjectName("panelGrafico")
        panel.setMinimumHeight(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(10)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("seccionTitulo")

        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("textoAyuda")
        label_descripcion.setWordWrap(True)

        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        layout.addWidget(chart_view)

        return panel

    def crear_chart_view(self):
        chart = QChart()
        chart.setTitle("Cargando...")
        chart.legend().setVisible(True)
        chart.setDropShadowEnabled(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(330)
        chart_view.setStyleSheet("background: transparent; border: none;")

        return chart_view

    # ============================================================
    # CARGA DE DATOS
    # ============================================================

    def cargar_datos(self, mostrar_mensaje=False):
        if self.actualizando_graficos:
            return

        self.actualizando_graficos = True

        try:
            ventas_resultado = self.service.obtener_ventas_hoy()

            if not ventas_resultado.get("ok"):
                self.mostrar_error(ventas_resultado.get("mensaje", "No se pudieron cargar ventas."))
                return

            productos_resultado = self.service.obtener_productos_top_hoy(limite=8)
            bajo_stock_resultado = self.service.obtener_bajo_stock()
            productos_resultado_todos = self.service.obtener_productos()

            self.ventas_hoy = ventas_resultado.get("data") or []
            self.productos_top = productos_resultado.get("data") if productos_resultado.get("ok") else []
            self.bajo_stock = bajo_stock_resultado.get("data") if bajo_stock_resultado.get("ok") else []
            self.productos = productos_resultado_todos.get("data") if productos_resultado_todos.get("ok") else []

            self.actualizar_cards()
            self.cargar_grafico_ventas_por_hora()
            self.cargar_grafico_metodos_pago()
            self.cargar_grafico_productos_top()
            self.cargar_grafico_stock()
            self.actualizar_alertas()

            if mostrar_mensaje:
                self.actualizar_estado_operacion("Gráficos cargados correctamente.", "ok")

        except Exception as error:
            self.mostrar_error(f"Error al cargar gráficos: {error}")

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_graficos = False

    def actualizar_label_ultima_actualizacion(self):
        hora = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora}")

    # ============================================================
    # CARDS
    # ============================================================

    def actualizar_cards(self):
        ventas_pagadas = self.obtener_ventas_pagadas()

        total_vendido = sum(
            self.decimal(venta.get("total"))
            for venta in ventas_pagadas
        )

        cantidad_ventas = len(ventas_pagadas)

        if cantidad_ventas > 0:
            ticket_promedio = total_vendido / Decimal(str(cantidad_ventas))
        else:
            ticket_promedio = Decimal("0")

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

        producto_top = "-"

        if self.productos_top:
            primero = self.productos_top[0]
            producto_top = str(
                primero.get("nombre_producto")
                or primero.get("producto")
                or primero.get("nombre")
                or "-"
            )

        bajo_stock = self.calcular_bajo_stock()
        sin_stock = self.calcular_sin_stock()

        self.labels["total_vendido"].setText(self.formato_pesos(total_vendido))
        self.labels["ventas_hoy"].setText(str(cantidad_ventas))
        self.labels["ticket_promedio"].setText(self.formato_pesos(ticket_promedio))
        self.labels["bajo_stock"].setText(str(bajo_stock))
        self.labels["efectivo"].setText(self.formato_pesos(efectivo))
        self.labels["tarjeta"].setText(self.formato_pesos(tarjeta))
        self.labels["transferencia"].setText(self.formato_pesos(transferencia))
        self.labels["producto_top"].setText(self.recortar(producto_top, 24))

        self.cambiar_tipo_card("total_vendido", "verde" if total_vendido > 0 else "neutro")
        self.cambiar_tipo_card("ventas_hoy", "verde" if cantidad_ventas > 0 else "neutro")
        self.cambiar_tipo_card("ticket_promedio", "morado" if ticket_promedio > 0 else "neutro")
        self.cambiar_tipo_card("bajo_stock", "rojo" if sin_stock > 0 else "alerta" if bajo_stock > 0 else "verde")
        self.cambiar_tipo_card("producto_top", "verde" if producto_top != "-" else "neutro")

    # ============================================================
    # GRÁFICOS
    # ============================================================

    def cargar_grafico_ventas_por_hora(self):
        ventas_por_hora = defaultdict(Decimal)

        for venta in self.obtener_ventas_pagadas():
            hora = self.extraer_hora(venta.get("fecha_venta"))
            total = self.decimal(venta.get("total"))
            ventas_por_hora[hora] += total

        series = QLineSeries()
        series.setName("Ventas")
        series.setPointsVisible(True)
        series.setPen(QPen(QColor("#2563EB"), 3))

        max_valor = Decimal("0")

        for hora in range(24):
            valor = ventas_por_hora[hora]
            max_valor = max(max_valor, valor)
            series.append(hora, float(valor))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Ventas por hora del día")
        chart.legend().setVisible(False)
        chart.setDropShadowEnabled(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        axis_x = QValueAxis()
        axis_x.setTitleText("Hora")
        axis_x.setRange(0, 23)
        axis_x.setTickCount(12)
        axis_x.setLabelFormat("%d")

        axis_y = QValueAxis()
        axis_y.setTitleText("Monto vendido")
        axis_y.setRange(0, self.obtener_max_eje(max_valor))
        axis_y.setLabelFormat("%.0f")

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self.chart_ventas_hora.setChart(chart)

    def cargar_grafico_metodos_pago(self):
        totales = defaultdict(Decimal)

        for venta in self.obtener_ventas_pagadas():
            metodo = str(venta.get("metodo_pago") or "SIN MÉTODO").upper()
            total = self.decimal(venta.get("total"))
            vuelto = self.decimal(venta.get("vuelto"))

            if venta.get("monto_efectivo") is not None:
                efectivo_neto = max(self.decimal(venta.get("monto_efectivo")) - vuelto, Decimal("0"))
                if efectivo_neto > 0:
                    totales["EFECTIVO"] += efectivo_neto
                if self.decimal(venta.get("monto_tarjeta")) > 0:
                    totales["TARJETA"] += self.decimal(venta.get("monto_tarjeta"))
                if self.decimal(venta.get("monto_transferencia")) > 0:
                    totales["TRANSFERENCIA"] += self.decimal(venta.get("monto_transferencia"))
            else:
                totales[metodo] += total

        series = QPieSeries()
        series.setHoleSize(0.38)

        if not totales:
            series.append("Sin ventas", 1)
        else:
            for metodo, total in sorted(totales.items(), key=lambda item: item[1], reverse=True):
                etiqueta = f"{metodo}: {self.formato_pesos(total)}"
                series.append(etiqueta, float(total))

        colores = [
            "#2563EB",
            "#0F172A",
            "#16A34A",
            "#9333EA",
            "#F59E0B",
            "#DC2626",
        ]

        for index, slice_item in enumerate(series.slices()):
            slice_item.setLabelVisible(True)
            slice_item.setLabelColor(QColor("#0F172A"))
            slice_item.setColor(QColor(colores[index % len(colores)]))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Ventas por método de pago")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setDropShadowEnabled(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chart_metodos_pago.setChart(chart)

    def cargar_grafico_productos_top(self):
        bar_set = QBarSet("Total vendido")
        bar_set.setColor(QColor("#2563EB"))

        categorias = []
        max_valor = Decimal("0")

        productos = list(self.productos_top or [])[:8]

        if not productos:
            categorias.append("Sin ventas")
            bar_set.append(0)
        else:
            productos_ordenados = sorted(
                productos,
                key=lambda producto: self.decimal(producto.get("total_vendido")),
                reverse=True,
            )

            for producto in productos_ordenados:
                nombre = str(
                    producto.get("nombre_producto")
                    or producto.get("producto")
                    or producto.get("nombre")
                    or "Producto"
                )

                total = self.decimal(producto.get("total_vendido"))

                categorias.append(self.recortar(nombre, 22))
                bar_set.append(float(total))
                max_valor = max(max_valor, total)

        series = QHorizontalBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Top productos por venta")
        chart.legend().setVisible(False)
        chart.setDropShadowEnabled(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        axis_y = QBarCategoryAxis()
        axis_y.append(categorias)

        axis_x = QValueAxis()
        axis_x.setTitleText("Total vendido")
        axis_x.setRange(0, self.obtener_max_eje(max_valor))
        axis_x.setLabelFormat("%.0f")

        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

        series.attachAxis(axis_y)
        series.attachAxis(axis_x)

        self.chart_productos_top.setChart(chart)

    def cargar_grafico_stock(self):
        ok_stock = 0
        bajo_stock = 0
        sin_stock = 0

        if self.productos:
            for producto in self.productos:
                stock = self.decimal(producto.get("stock_actual"))
                minimo = self.decimal(producto.get("stock_minimo"))

                if stock <= 0:
                    sin_stock += 1
                elif stock <= minimo:
                    bajo_stock += 1
                else:
                    ok_stock += 1
        else:
            bajo_stock = len(self.bajo_stock or [])

            if bajo_stock <= 0:
                ok_stock = 1

        series = QPieSeries()
        series.setHoleSize(0.38)

        if ok_stock > 0:
            series.append(f"Stock OK: {ok_stock}", ok_stock)

        if bajo_stock > 0:
            series.append(f"Bajo stock: {bajo_stock}", bajo_stock)

        if sin_stock > 0:
            series.append(f"Sin stock: {sin_stock}", sin_stock)

        if series.count() == 0:
            series.append("Sin información", 1)

        colores = [
            "#16A34A",
            "#F59E0B",
            "#DC2626",
            "#64748B",
        ]

        for index, slice_item in enumerate(series.slices()):
            slice_item.setLabelVisible(True)
            slice_item.setLabelColor(QColor("#0F172A"))
            slice_item.setColor(QColor(colores[index % len(colores)]))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Estado general de stock")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setDropShadowEnabled(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chart_stock.setChart(chart)

    # ============================================================
    # ALERTAS
    # ============================================================

    def actualizar_alertas(self):
        alertas = []

        ventas_pagadas = self.obtener_ventas_pagadas()
        bajo_stock = self.calcular_bajo_stock()
        sin_stock = self.calcular_sin_stock()

        if not ventas_pagadas:
            alertas.append("No hay ventas pagadas hoy.")

        if bajo_stock > 0:
            alertas.append(f"{bajo_stock} producto(s) bajo stock.")

        if sin_stock > 0:
            alertas.append(f"{sin_stock} producto(s) sin stock.")

        if not self.productos_top:
            alertas.append("Aún no hay ranking de productos vendidos hoy.")

        if not alertas:
            self.label_alertas.setText(
                "Gráficos en buen estado: ventas, métodos de pago y stock cargados correctamente."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas visuales: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def mostrar_error(self, mensaje):
        self.actualizar_estado_operacion(mensaje, "error")
        self.label_alertas.setText(f"Error en gráficos: {mensaje}")
        self.label_alertas.setStyleSheet(self.estilo_alerta("error"))

    def actualizar_estado_operacion(self, texto, tipo="info"):
        if self.label_estado_operacion is None:
            return

        self.label_estado_operacion.setText(texto)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta(tipo))

    # ============================================================
    # UTILIDADES
    # ============================================================

    def obtener_ventas_pagadas(self):
        return [
            venta for venta in self.ventas_hoy
            if str(venta.get("estado") or "").upper() == "PAGADA"
        ]

    def decimal(self, valor):
        try:
            return Decimal(str(valor or 0))
        except Exception:
            return Decimal("0")

    def formato_pesos(self, valor):
        return self.service.formato_pesos(valor)

    def extraer_hora(self, fecha):
        if fecha is None:
            return 0

        try:
            return int(fecha.hour)
        except Exception:
            pass

        try:
            texto = str(fecha)

            if "T" in texto:
                texto = texto.replace("T", " ")

            fecha_parseada = datetime.fromisoformat(texto.split(".")[0])
            return int(fecha_parseada.hour)
        except Exception:
            return 0

    def obtener_max_eje(self, max_valor):
        max_valor = self.decimal(max_valor)

        if max_valor <= 0:
            return 1000

        valor = float(max_valor)

        return max(1000, valor * 1.25)

    def calcular_bajo_stock(self):
        if self.productos:
            contador = 0

            for producto in self.productos:
                stock = self.decimal(producto.get("stock_actual"))
                minimo = self.decimal(producto.get("stock_minimo"))

                if stock <= minimo:
                    contador += 1

            return contador

        return len(self.bajo_stock or [])

    def calcular_sin_stock(self):
        if not self.productos:
            return 0

        contador = 0

        for producto in self.productos:
            stock = self.decimal(producto.get("stock_actual"))

            if stock <= 0:
                contador += 1

        return contador

    def recortar(self, texto, largo):
        texto = str(texto or "")

        if len(texto) <= largo:
            return texto

        return texto[:largo - 3] + "..."

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
            QFrame#panelGrafico {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardGrafico {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardGrafico[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardGrafico[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardGrafico[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardGrafico[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardGrafico[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardGrafico[tipo="neutro"] {
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

            QLabel#seccionTitulo {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#textoAyuda {
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
                background-color: transparent;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)