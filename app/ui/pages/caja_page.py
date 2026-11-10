from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QTextEdit,
    QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, QTimer, QDateTime


# ============================================================
# IMPORT FLEXIBLE DE LA LÓGICA DE CAJA
# ============================================================

from app.caja import (
    obtener_resumen_caja_actual,
    abrir_caja,
    registrar_ingreso_extra,
    registrar_retiro,
    cerrar_caja
)


class CajaServiceAdapter:
    def __init__(self, usuario_id=1):
        self.usuario_id = usuario_id

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

    def obtener_resumen_caja(self):
        if obtener_resumen_caja_actual is None:
            return {
                "ok": False,
                "mensaje": "No se pudo importar la lógica de caja.py. Revisa la ruta del import en caja_page.py."
            }

        return obtener_resumen_caja_actual()

    def abrir_caja_sistema(self, monto_inicial=0, observacion_apertura=None):
        if abrir_caja is None:
            return {
                "ok": False,
                "mensaje": "No se pudo importar abrir_caja desde caja.py."
            }

        return abrir_caja(
            usuario_id=self.usuario_id,
            monto_inicial=monto_inicial,
            observacion_apertura=observacion_apertura
        )

    def registrar_ingreso_extra_caja(self, monto, descripcion=None):
        if registrar_ingreso_extra is None:
            return {
                "ok": False,
                "mensaje": "No se pudo importar registrar_ingreso_extra desde caja.py."
            }

        return registrar_ingreso_extra(
            monto=monto,
            descripcion=descripcion
        )

    def registrar_retiro_caja(self, monto, descripcion=None):
        if registrar_retiro is None:
            return {
                "ok": False,
                "mensaje": "No se pudo importar registrar_retiro desde caja.py."
            }

        return registrar_retiro(
            monto=monto,
            descripcion=descripcion
        )

    def cerrar_caja_sistema(self, monto_real_cierre, observacion_cierre=None):
        if cerrar_caja is None:
            return {
                "ok": False,
                "mensaje": "No se pudo importar cerrar_caja desde caja.py."
            }

        return cerrar_caja(
            usuario_cierre_id=self.usuario_id,
            monto_real_cierre=monto_real_cierre,
            observacion_cierre=observacion_cierre
        )


class MontoDialog(QDialog):
    def __init__(
        self,
        titulo,
        texto_monto,
        texto_observacion,
        texto_boton,
        monto_default=0,
        parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle(titulo)
        self.setMinimumWidth(480)

        self.input_monto = QDoubleSpinBox()
        self.input_observacion = QTextEdit()

        self.texto_monto = texto_monto
        self.texto_observacion = texto_observacion
        self.texto_boton = texto_boton
        self.monto_default = monto_default

        self.construir_interfaz()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel(self.windowTitle())
        titulo.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 800;
                color: #0F172A;
            }
        """)

        self.input_monto.setMaximum(999999999)
        self.input_monto.setMinimum(0)
        self.input_monto.setDecimals(0)
        self.input_monto.setSingleStep(1000)
        self.input_monto.setPrefix("$ ")
        self.input_monto.setValue(float(self.monto_default or 0))
        self.input_monto.setMinimumHeight(40)

        self.input_observacion.setPlaceholderText(self.texto_observacion)
        self.input_observacion.setFixedHeight(90)

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow(self.texto_monto, self.input_monto)
        form.addRow("Observación:", self.input_observacion)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton(self.texto_boton)
        btn_confirmar.setObjectName("botonPrincipal")
        btn_confirmar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addLayout(form)
        layout.addLayout(botones)

    def obtener_datos(self):
        return {
            "monto": Decimal(str(self.input_monto.value())),
            "observacion": self.input_observacion.toPlainText().strip()
        }


class CerrarCajaDialog(QDialog):
    def __init__(self, pos_service, efectivo_esperado=0, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.efectivo_esperado = Decimal(str(efectivo_esperado or 0))

        self.setWindowTitle("Cerrar caja")
        self.setMinimumWidth(560)

        self.input_monto_real = QDoubleSpinBox()
        self.input_observacion = QTextEdit()

        self.label_esperado = QLabel()
        self.label_diferencia = QLabel()

        self.construir_interfaz()
        self.actualizar_diferencia()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("Arqueo y cierre de caja")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 800;
                color: #0F172A;
            }
        """)

        texto = QLabel(
            "Ingresa solo el efectivo contado físicamente en caja. "
            "No incluyas ventas con tarjeta ni transferencias. "
            "El sistema calculará automáticamente la diferencia."
        )
        texto.setWordWrap(True)
        texto.setStyleSheet("color: #64748B; font-size: 14px;")

        self.label_esperado.setText(
            f"Efectivo esperado en caja: {self.pos.formato_pesos(self.efectivo_esperado)}"
        )
        self.label_esperado.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 12px;
                color: #0F172A;
                font-size: 16px;
                font-weight: 700;
            }
        """)

        self.input_monto_real.setMaximum(999999999)
        self.input_monto_real.setMinimum(0)
        self.input_monto_real.setDecimals(0)
        self.input_monto_real.setSingleStep(1000)
        self.input_monto_real.setPrefix("$ ")
        self.input_monto_real.setValue(float(self.efectivo_esperado))
        self.input_monto_real.setMinimumHeight(40)
        self.input_monto_real.valueChanged.connect(self.actualizar_diferencia)

        self.input_observacion.setPlaceholderText(
            "Ej: Caja cuadrada, falta sencillo, diferencia por vuelto, etc."
        )
        self.input_observacion.setFixedHeight(90)

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Efectivo contado:", self.input_monto_real)
        form.addRow("Observación cierre:", self.input_observacion)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Cerrar caja")
        btn_confirmar.setObjectName("botonPeligro")
        btn_confirmar.clicked.connect(self.confirmar_cierre)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(texto)
        layout.addWidget(self.label_esperado)
        layout.addWidget(self.label_diferencia)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.setStyleSheet("""
            QPushButton#botonPeligro {
                background-color: #DC2626;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#botonPeligro:hover {
                background-color: #B91C1C;
            }
        """)

    def actualizar_diferencia(self):
        monto_real = Decimal(str(self.input_monto_real.value()))
        diferencia = monto_real - self.efectivo_esperado

        texto = f"Diferencia: {self.pos.formato_pesos(diferencia)}"

        if diferencia == 0:
            texto += "  | Caja cuadrada"
            color = "#166534"
            fondo = "#DCFCE7"
            borde = "#BBF7D0"
        elif diferencia > 0:
            texto += "  | Sobra efectivo"
            color = "#1D4ED8"
            fondo = "#DBEAFE"
            borde = "#BFDBFE"
        else:
            texto += "  | Falta efectivo"
            color = "#B91C1C"
            fondo = "#FEE2E2"
            borde = "#FECACA"

        self.label_diferencia.setText(texto)
        self.label_diferencia.setStyleSheet(f"""
            QLabel {{
                background-color: {fondo};
                border: 1px solid {borde};
                border-radius: 10px;
                padding: 12px;
                color: {color};
                font-size: 16px;
                font-weight: 800;
            }}
        """)

    def confirmar_cierre(self):
        confirmar = QMessageBox.question(
            self,
            "Confirmar cierre",
            "¿Seguro que deseas cerrar la caja?\n\n"
            "Recuerda: el monto contado debe ser solo efectivo físico, "
            "sin incluir tarjeta ni transferencia."
        )

        if confirmar != QMessageBox.Yes:
            return

        self.accept()

    def obtener_datos(self):
        return {
            "monto_real_cierre": Decimal(str(self.input_monto_real.value())),
            "observacion_cierre": self.input_observacion.toPlainText().strip()
        }


class CajaPage(QWidget):
    def __init__(self, pos_service=None, usuario_id=1):
        super().__init__()

        self.pos = pos_service or CajaServiceAdapter(usuario_id=usuario_id)
        self.caja_actual = {}

        self.actualizando_caja = False
        self.timer_caja = None

        self.label_estado_banner = None
        self.label_estado_detalle = None
        self.label_ultima_actualizacion = None

        self.labels = {}
        self.tabla_detalle = QTableWidget()

        self.btn_abrir = None
        self.btn_ingreso = None
        self.btn_retiro = None
        self.btn_cerrar = None
        self.btn_copiar = None

        self.construir_interfaz()
        self.cargar_caja()
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_caja = QTimer(self)
        self.timer_caja.timeout.connect(self.cargar_caja_automatica)
        self.timer_caja.start(5000)

    def cargar_caja_automatica(self):
        if self.actualizando_caja:
            return

        self.cargar_caja()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()

        titulo = QLabel("Caja")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Apertura, cierre, ingresos, retiros y arqueo profesional del turno actual."
        )
        subtitulo.setObjectName("subtituloPagina")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        estado_actualizacion = QVBoxLayout()
        estado_actualizacion.setSpacing(4)
        estado_actualizacion.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        label_auto = QLabel("Actualización automática")
        label_auto.setAlignment(Qt.AlignCenter)
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
        self.label_ultima_actualizacion.setAlignment(Qt.AlignCenter)
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

        encabezado.addLayout(textos)
        encabezado.addStretch()
        encabezado.addLayout(estado_actualizacion)

        layout.addLayout(encabezado)

        banner = QFrame()
        banner.setObjectName("bannerCaja")

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(18, 14, 18, 14)
        banner_layout.setSpacing(4)

        self.label_estado_banner = QLabel("Caja sin cargar")
        self.label_estado_banner.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 900;
                color: #0F172A;
                background: transparent;
            }
        """)

        self.label_estado_detalle = QLabel("El sistema revisa automáticamente el estado de caja.")
        self.label_estado_detalle.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #64748B;
                background: transparent;
            }
        """)

        banner_layout.addWidget(self.label_estado_banner)
        banner_layout.addWidget(self.label_estado_detalle)

        layout.addWidget(banner)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(12)

        self.labels["estado"] = self.crear_card(cards, 0, 0, "Estado", "-")
        self.labels["fecha_apertura"] = self.crear_card(cards, 0, 1, "Apertura", "-")
        self.labels["monto_inicial"] = self.crear_card(cards, 0, 2, "Monto inicial", "$0")
        self.labels["monto_esperado"] = self.crear_card(cards, 0, 3, "Efectivo esperado", "$0")

        self.labels["ventas_total"] = self.crear_card(cards, 1, 0, "Total vendido", "$0")
        self.labels["ventas_efectivo"] = self.crear_card(cards, 1, 1, "Ventas en efectivo", "$0")
        self.labels["ventas_tarjeta"] = self.crear_card(cards, 1, 2, "Ventas con tarjeta", "$0")
        self.labels["ventas_transferencia"] = self.crear_card(cards, 1, 3, "Ventas por transferencia", "$0")

        self.labels["ingresos_extra"] = self.crear_card(cards, 2, 0, "Ingresos extra", "$0")
        self.labels["retiros"] = self.crear_card(cards, 2, 1, "Retiros", "$0")
        self.labels["diferencia"] = self.crear_card(cards, 2, 2, "Diferencia", "$0")
        self.labels["caja_id"] = self.crear_card(cards, 2, 3, "Turno actual", "-")

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        self.btn_abrir = QPushButton("Abrir caja")
        self.btn_abrir.setObjectName("botonPrincipal")
        self.btn_abrir.setMinimumHeight(44)
        self.btn_abrir.clicked.connect(self.abrir_caja)

        self.btn_ingreso = QPushButton("Ingreso extra")
        self.btn_ingreso.setMinimumHeight(44)
        self.btn_ingreso.clicked.connect(self.registrar_ingreso)

        self.btn_retiro = QPushButton("Registrar retiro")
        self.btn_retiro.setMinimumHeight(44)
        self.btn_retiro.clicked.connect(self.registrar_retiro)

        self.btn_copiar = QPushButton("Copiar resumen")
        self.btn_copiar.setMinimumHeight(44)
        self.btn_copiar.clicked.connect(self.copiar_resumen)

        self.btn_cerrar = QPushButton("Cerrar caja")
        self.btn_cerrar.setObjectName("botonPeligro")
        self.btn_cerrar.setMinimumHeight(44)
        self.btn_cerrar.clicked.connect(self.cerrar_caja)

        acciones.addWidget(self.btn_abrir)
        acciones.addWidget(self.btn_ingreso)
        acciones.addWidget(self.btn_retiro)
        acciones.addStretch()
        acciones.addWidget(self.btn_copiar)
        acciones.addWidget(self.btn_cerrar)

        layout.addLayout(acciones)

        titulo_detalle = QLabel("Detalle del turno")
        titulo_detalle.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 800;
                background: transparent;
            }
        """)

        layout.addWidget(titulo_detalle)

        self.tabla_detalle.setColumnCount(3)
        self.tabla_detalle.setHorizontalHeaderLabels([
            "Concepto",
            "Valor",
            "Detalle"
        ])
        self.tabla_detalle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_detalle.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_detalle.setAlternatingRowColors(True)
        self.tabla_detalle.setMinimumHeight(300)

        layout.addWidget(self.tabla_detalle)

        self.setStyleSheet("""
            QFrame#bannerCaja {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QFrame#cardResumenCaja {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QLabel#cardResumenTitulo {
                color: #64748B;
                font-size: 13px;
                font-weight: 500;
                background-color: transparent;
            }

            QLabel#cardResumenValor {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background-color: transparent;
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

            QPushButton#botonPrincipal:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }

            QPushButton#botonPeligro:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                gridline-color: #E5E7EB;
                color: #0F172A;
            }

            QHeaderView::section {
                background-color: #F8FAFC;
                color: #0F172A;
                font-weight: 800;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 10px;
            }
        """)

    def crear_card(self, grid, fila, columna, titulo, valor):
        card = QFrame()
        card.setObjectName("cardResumenCaja")
        card.setMinimumHeight(95)
        card.setMaximumHeight(105)
        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("cardResumenTitulo")
        label_titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        label_valor = QLabel(valor)
        label_valor.setObjectName("cardResumenValor")
        label_valor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        label_valor.setWordWrap(False)
        label_valor.setMinimumHeight(28)

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)

        grid.addWidget(card, fila, columna)

        return label_valor

    def actualizar_label_ultima_actualizacion(self):
        if self.label_ultima_actualizacion is None:
            return

        hora_actual = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora_actual}")

    def cargar_caja(self):
        if self.actualizando_caja:
            return

        self.actualizando_caja = True

        try:
            resultado = self.pos.obtener_resumen_caja()

            if resultado.get("ok"):
                data = resultado.get("data") or {}
                self.caja_actual = self.normalizar_data_caja(data)
                self.actualizar_interfaz()
                return

            self.caja_actual = {}
            self.actualizar_interfaz(mensaje_error=resultado.get("mensaje"))

        except Exception as e:
            self.caja_actual = {}
            self.actualizar_interfaz(
                mensaje_error=f"No se pudo actualizar la caja: {e}"
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_caja = False

    def normalizar_data_caja(self, data):
        if not isinstance(data, dict):
            return {}

        caja = {}

        if isinstance(data.get("caja"), dict):
            caja.update(data.get("caja"))

        caja.update(data)

        return caja

    def actualizar_interfaz(self, mensaje_error=None):
        abierta = self.caja_esta_abierta()

        if abierta:
            self.actualizar_banner_abierta()
        else:
            self.actualizar_banner_cerrada(mensaje_error)

        self.actualizar_cards()
        self.actualizar_tabla_detalle()
        self.actualizar_botones()

    def caja_esta_abierta(self):
        estado = str(self.obtener_valor("estado", "") or "").upper()

        caja_id = (
            self.caja_actual.get("id")
            or self.caja_actual.get("caja_id")
            or self.caja_actual.get("turno_id")
            or self.caja_actual.get("id_caja")
            or self.caja_actual.get("id_turno")
        )

        return estado == "ABIERTA" and bool(caja_id)

    def actualizar_banner_abierta(self):
        fecha_apertura = self.obtener_valor("fecha_apertura", "-")
        usuario = self.obtener_valor("usuario_apertura", "Usuario actual")

        self.label_estado_banner.setText("Caja abierta")
        self.label_estado_detalle.setText(
            f"Turno activo desde {self.formatear_fecha(fecha_apertura)} | Apertura: {usuario}"
        )

        self.label_estado_banner.parent().setStyleSheet("""
            QFrame#bannerCaja {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
                border-radius: 14px;
            }
        """)

    def actualizar_banner_cerrada(self, mensaje_error=None):
        self.label_estado_banner.setText("Caja cerrada")
        self.label_estado_detalle.setText(
            mensaje_error or "Para comenzar a vender, abre una caja con el monto inicial disponible en efectivo."
        )

        self.label_estado_banner.parent().setStyleSheet("""
            QFrame#bannerCaja {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 14px;
            }
        """)

    def actualizar_cards(self):
        estado = "ABIERTA" if self.caja_esta_abierta() else "CERRADA"

        monto_inicial = self.obtener_numero("monto_inicial")
        ventas_efectivo = self.obtener_numero("monto_ventas_efectivo", "ventas_efectivo")
        ventas_tarjeta = self.obtener_numero("monto_ventas_tarjeta", "ventas_tarjeta")
        ventas_transferencia = self.obtener_numero("monto_ventas_transferencia", "ventas_transferencia")
        ventas_total = self.obtener_numero("monto_ventas_total", "ventas_total", "total_ventas")
        ingresos_extra = self.obtener_numero("monto_ingresos_extra", "ingresos_extra")
        retiros = self.obtener_numero("monto_retiros", "retiros")
        efectivo_esperado = self.obtener_efectivo_esperado()
        diferencia = self.obtener_numero("diferencia")

        caja_id = self.obtener_id_caja()

        self.labels["estado"].setText(estado)
        self.labels["fecha_apertura"].setText(
            self.formatear_fecha(self.obtener_valor("fecha_apertura", "-"))
        )
        self.labels["monto_inicial"].setText(self.pos.formato_pesos(monto_inicial))
        self.labels["monto_esperado"].setText(self.pos.formato_pesos(efectivo_esperado))

        self.labels["ventas_total"].setText(self.pos.formato_pesos(ventas_total))
        self.labels["ventas_efectivo"].setText(self.pos.formato_pesos(ventas_efectivo))
        self.labels["ventas_tarjeta"].setText(self.pos.formato_pesos(ventas_tarjeta))
        self.labels["ventas_transferencia"].setText(self.pos.formato_pesos(ventas_transferencia))

        self.labels["ingresos_extra"].setText(self.pos.formato_pesos(ingresos_extra))
        self.labels["retiros"].setText(self.pos.formato_pesos(retiros))
        self.labels["diferencia"].setText(self.pos.formato_pesos(diferencia))
        self.labels["caja_id"].setText(str(caja_id))

    def actualizar_tabla_detalle(self):
        self.tabla_detalle.setRowCount(0)

        filas = [
            ("ID caja", self.obtener_id_caja(), "Identificador del turno de caja"),
            ("Estado", "ABIERTA" if self.caja_esta_abierta() else "CERRADA", "Estado actual del turno"),
            ("Fecha apertura", self.formatear_fecha(self.obtener_valor("fecha_apertura", "-")), "Inicio del turno"),
            ("Fecha cierre", self.formatear_fecha(self.obtener_valor("fecha_cierre", "-")), "Cierre del turno"),
            ("Monto inicial", self.pos.formato_pesos(self.obtener_numero("monto_inicial")), "Dinero físico al abrir caja"),
            ("Ventas efectivo", self.pos.formato_pesos(self.obtener_numero("monto_ventas_efectivo", "ventas_efectivo")), "Ventas pagadas en efectivo físico"),
            ("Ventas tarjeta", self.pos.formato_pesos(self.obtener_numero("monto_ventas_tarjeta", "ventas_tarjeta")), "Ventas pagadas con tarjeta, no se cuentan en caja física"),
            ("Ventas transferencia", self.pos.formato_pesos(self.obtener_numero("monto_ventas_transferencia", "ventas_transferencia")), "Ventas por transferencia, no se cuentan en caja física"),
            ("Ventas total", self.pos.formato_pesos(self.obtener_numero("monto_ventas_total", "ventas_total", "total_ventas")), "Total vendido en el turno"),
            ("Ingresos extra", self.pos.formato_pesos(self.obtener_numero("monto_ingresos_extra", "ingresos_extra")), "Dinero efectivo agregado manualmente a caja"),
            ("Retiros", self.pos.formato_pesos(self.obtener_numero("monto_retiros", "retiros")), "Dinero efectivo retirado de caja"),
            ("Efectivo esperado caja", self.pos.formato_pesos(self.obtener_efectivo_esperado()), "Monto inicial + ventas efectivo + ingresos extra - retiros"),
            ("Monto real cierre", self.pos.formato_pesos(self.obtener_numero("monto_real_cierre")), "Efectivo contado al cierre"),
            ("Diferencia", self.pos.formato_pesos(self.obtener_numero("diferencia")), "Efectivo contado menos efectivo esperado"),
            ("Observación apertura", self.obtener_valor("observacion_apertura", ""), "Comentario registrado al abrir"),
            ("Observación cierre", self.obtener_valor("observacion_cierre", ""), "Comentario registrado al cerrar"),
        ]

        for fila, valores in enumerate(filas):
            self.tabla_detalle.insertRow(fila)

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor or ""))
                item.setTextAlignment(
                    Qt.AlignCenter if columna != 0 else Qt.AlignLeft | Qt.AlignVCenter
                )
                self.tabla_detalle.setItem(fila, columna, item)

    def actualizar_botones(self):
        abierta = self.caja_esta_abierta()

        self.btn_abrir.setEnabled(not abierta)
        self.btn_ingreso.setEnabled(abierta)
        self.btn_retiro.setEnabled(abierta)
        self.btn_cerrar.setEnabled(abierta)
        self.btn_copiar.setEnabled(bool(self.caja_actual))

        if abierta:
            self.btn_abrir.setText("Caja ya abierta")
        else:
            self.btn_abrir.setText("Abrir caja")

    def abrir_caja(self):
        dialogo = MontoDialog(
            titulo="Abrir caja",
            texto_monto="Monto inicial:",
            texto_observacion="Ej: Caja abierta por inicio de turno",
            texto_boton="Abrir caja",
            monto_default=0,
            parent=self
        )

        if dialogo.exec() != QDialog.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.pos.abrir_caja_sistema(
            monto_inicial=datos["monto"],
            observacion_apertura=datos["observacion"]
        )

        self.mostrar_resultado(resultado, "Caja abierta correctamente.")

    def registrar_ingreso(self):
        if not self.caja_esta_abierta():
            QMessageBox.warning(self, "Caja cerrada", "Debe abrir caja antes de registrar ingresos.")
            return

        dialogo = MontoDialog(
            titulo="Registrar ingreso extra",
            texto_monto="Monto ingreso:",
            texto_observacion="Ej: Ingreso de sencillo, fondo adicional, ajuste positivo",
            texto_boton="Registrar ingreso",
            monto_default=0,
            parent=self
        )

        if dialogo.exec() != QDialog.Accepted:
            return

        datos = dialogo.obtener_datos()

        if datos["monto"] <= 0:
            QMessageBox.warning(self, "Monto inválido", "El monto debe ser mayor a 0.")
            return

        resultado = self.pos.registrar_ingreso_extra_caja(
            monto=datos["monto"],
            descripcion=datos["observacion"]
        )

        self.mostrar_resultado(resultado, "Ingreso registrado correctamente.")

    def registrar_retiro(self):
        if not self.caja_esta_abierta():
            QMessageBox.warning(self, "Caja cerrada", "Debe abrir caja antes de registrar retiros.")
            return

        dialogo = MontoDialog(
            titulo="Registrar retiro",
            texto_monto="Monto retiro:",
            texto_observacion="Ej: Retiro de efectivo, pago menor, retiro por seguridad",
            texto_boton="Registrar retiro",
            monto_default=0,
            parent=self
        )

        if dialogo.exec() != QDialog.Accepted:
            return

        datos = dialogo.obtener_datos()

        if datos["monto"] <= 0:
            QMessageBox.warning(self, "Monto inválido", "El monto debe ser mayor a 0.")
            return

        resultado = self.pos.registrar_retiro_caja(
            monto=datos["monto"],
            descripcion=datos["observacion"]
        )

        self.mostrar_resultado(resultado, "Retiro registrado correctamente.")

    def cerrar_caja(self):
        if not self.caja_esta_abierta():
            QMessageBox.warning(self, "Caja cerrada", "No hay una caja abierta para cerrar.")
            return

        efectivo_esperado = self.obtener_efectivo_esperado()

        dialogo = CerrarCajaDialog(
            pos_service=self.pos,
            efectivo_esperado=efectivo_esperado,
            parent=self
        )

        if dialogo.exec() != QDialog.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.pos.cerrar_caja_sistema(
            monto_real_cierre=datos["monto_real_cierre"],
            observacion_cierre=datos["observacion_cierre"]
        )

        self.mostrar_resultado(resultado, "Caja cerrada correctamente.")

    def copiar_resumen(self):
        if not self.caja_actual:
            QMessageBox.warning(self, "Sin caja", "No hay información de caja para copiar.")
            return

        texto = self.generar_resumen_texto()
        QApplication.clipboard().setText(texto)

        QMessageBox.information(self, "Resumen copiado", "El resumen de caja fue copiado al portapapeles.")

    def generar_resumen_texto(self):
        lineas = [
            "RESUMEN DE CAJA",
            "==========================",
            f"ID caja: {self.obtener_id_caja()}",
            f"Estado: {'ABIERTA' if self.caja_esta_abierta() else 'CERRADA'}",
            f"Fecha apertura: {self.formatear_fecha(self.obtener_valor('fecha_apertura', '-'))}",
            f"Monto inicial: {self.pos.formato_pesos(self.obtener_numero('monto_inicial'))}",
            f"Ventas total: {self.pos.formato_pesos(self.obtener_numero('monto_ventas_total', 'ventas_total', 'total_ventas'))}",
            f"Ventas efectivo: {self.pos.formato_pesos(self.obtener_numero('monto_ventas_efectivo', 'ventas_efectivo'))}",
            f"Ventas tarjeta: {self.pos.formato_pesos(self.obtener_numero('monto_ventas_tarjeta', 'ventas_tarjeta'))}",
            f"Ventas transferencia: {self.pos.formato_pesos(self.obtener_numero('monto_ventas_transferencia', 'ventas_transferencia'))}",
            f"Ingresos extra: {self.pos.formato_pesos(self.obtener_numero('monto_ingresos_extra', 'ingresos_extra'))}",
            f"Retiros: {self.pos.formato_pesos(self.obtener_numero('monto_retiros', 'retiros'))}",
            f"Efectivo esperado: {self.pos.formato_pesos(self.obtener_efectivo_esperado())}",
            f"Monto real cierre: {self.pos.formato_pesos(self.obtener_numero('monto_real_cierre'))}",
            f"Diferencia: {self.pos.formato_pesos(self.obtener_numero('diferencia'))}",
            "",
            "Nota: El efectivo esperado no incluye ventas con tarjeta ni transferencia."
        ]

        return "\n".join(lineas)

    def mostrar_resultado(self, resultado, mensaje_ok):
        if not resultado.get("ok"):
            QMessageBox.warning(self, "Caja", resultado.get("mensaje", "Ocurrió un error."))
            self.cargar_caja()
            return

        QMessageBox.information(self, "Caja", resultado.get("mensaje") or mensaje_ok)
        self.cargar_caja()

    def obtener_valor(self, *claves):
        default = None

        if claves:
            default = claves[-1]

        for clave in claves:
            if clave in self.caja_actual and self.caja_actual.get(clave) is not None:
                return self.caja_actual.get(clave)

        return default

    def obtener_numero(self, *claves):
        for clave in claves:
            valor = self.caja_actual.get(clave)

            if valor is None:
                continue

            try:
                return Decimal(str(valor))
            except Exception:
                continue

        return Decimal("0")

    def obtener_id_caja(self):
        return (
            self.caja_actual.get("id")
            or self.caja_actual.get("caja_id")
            or self.caja_actual.get("turno_id")
            or self.caja_actual.get("id_caja")
            or self.caja_actual.get("id_turno")
            or "-"
        )

    def obtener_efectivo_esperado(self):
        monto_inicial = self.obtener_numero("monto_inicial")
        ventas_efectivo = self.obtener_numero("monto_ventas_efectivo", "ventas_efectivo")
        ingresos_extra = self.obtener_numero("monto_ingresos_extra", "ingresos_extra")
        retiros = self.obtener_numero("monto_retiros", "retiros")

        return monto_inicial + ventas_efectivo + ingresos_extra - retiros

    def formatear_fecha(self, fecha):
        if not fecha or str(fecha) == "-":
            return "-"

        try:
            return self.pos.formato_fecha(fecha)
        except Exception:
            return str(fecha)