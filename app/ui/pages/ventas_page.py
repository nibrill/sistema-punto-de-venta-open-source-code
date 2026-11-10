import os
from decimal import Decimal
from pathlib import Path
import json
import urllib.request
from urllib.error import URLError

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QApplication,
    QInputDialog,
    QFrame,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QEvent
from PySide6.QtGui import QPixmap

from app.database import ejecutar_consulta


class CobroDialog(QDialog):
    def __init__(self, pos_service, total, requiere_mayoria_edad=False, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.total = Decimal(str(total or 0))
        self.requiere_mayoria_edad = requiere_mayoria_edad

        self.setWindowTitle("Cobrar venta")
        self.setMinimumWidth(500)

        self.combo_metodo = None
        self.input_efectivo = None
        self.input_tarjeta = None
        self.input_transferencia = None
        self.check_mayoria_edad = None
        self.label_vuelto = None

        self.construir_interfaz()
        self.actualizar_campos_pago()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("Cobrar venta")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        ayuda = QLabel(
            "Selecciona cómo pagará el cliente. "
            "Si es efectivo, escribe lo recibido para calcular el vuelto."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        label_total = QLabel(f"Total a pagar: {self.pos.formato_pesos(self.total)}")
        label_total.setStyleSheet("""
            QLabel {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                padding: 14px;
                font-size: 22px;
                font-weight: 900;
                color: #1D4ED8;
            }
        """)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addWidget(label_total)

        form = QFormLayout()
        form.setSpacing(12)

        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["EFECTIVO", "TARJETA", "TRANSFERENCIA", "MIXTO"])
        self.combo_metodo.setMinimumHeight(40)
        self.combo_metodo.currentTextChanged.connect(self.actualizar_campos_pago)

        self.input_efectivo = self.crear_input_monto()
        self.input_tarjeta = self.crear_input_monto()
        self.input_transferencia = self.crear_input_monto()

        self.input_efectivo.valueChanged.connect(self.actualizar_vuelto)
        self.input_tarjeta.valueChanged.connect(self.actualizar_vuelto)
        self.input_transferencia.valueChanged.connect(self.actualizar_vuelto)

        form.addRow("Método de pago:", self.combo_metodo)
        form.addRow("Monto efectivo:", self.input_efectivo)
        form.addRow("Monto tarjeta:", self.input_tarjeta)
        form.addRow("Monto transferencia:", self.input_transferencia)

        layout.addLayout(form)

        self.label_vuelto = QLabel("Vuelto: $0")
        self.label_vuelto.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 12px;
                color: #0F172A;
                font-size: 16px;
                font-weight: 800;
            }
        """)
        layout.addWidget(self.label_vuelto)

        self.check_mayoria_edad = QCheckBox("Confirmo que el cliente es mayor de edad")
        self.check_mayoria_edad.setChecked(not self.requiere_mayoria_edad)
        self.check_mayoria_edad.setVisible(self.requiere_mayoria_edad)
        layout.addWidget(self.check_mayoria_edad)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Confirmar venta")
        btn_confirmar.setObjectName("botonPrincipal")
        btn_confirmar.setMinimumHeight(42)
        btn_confirmar.clicked.connect(self.validar_y_aceptar)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addLayout(botones)

    def crear_input_monto(self):
        input_monto = QDoubleSpinBox()
        input_monto.setMaximum(999999999)
        input_monto.setDecimals(0)
        input_monto.setSingleStep(500)
        input_monto.setPrefix("$ ")
        input_monto.setMinimumHeight(38)
        return input_monto

    def actualizar_campos_pago(self):
        metodo = self.combo_metodo.currentText()

        self.input_efectivo.setEnabled(False)
        self.input_tarjeta.setEnabled(False)
        self.input_transferencia.setEnabled(False)

        self.input_efectivo.setValue(0)
        self.input_tarjeta.setValue(0)
        self.input_transferencia.setValue(0)

        total_float = float(self.total)

        if metodo == "EFECTIVO":
            self.input_efectivo.setEnabled(True)
            self.input_efectivo.setValue(total_float)

        elif metodo == "TARJETA":
            self.input_tarjeta.setValue(total_float)

        elif metodo == "TRANSFERENCIA":
            self.input_transferencia.setValue(total_float)

        elif metodo == "MIXTO":
            self.input_efectivo.setEnabled(True)
            self.input_tarjeta.setEnabled(True)
            self.input_transferencia.setEnabled(True)

        self.actualizar_vuelto()

    def actualizar_vuelto(self):
        if not self.label_vuelto:
            return

        efectivo = Decimal(str(self.input_efectivo.value()))
        tarjeta = Decimal(str(self.input_tarjeta.value()))
        transferencia = Decimal(str(self.input_transferencia.value()))

        pagado = efectivo + tarjeta + transferencia
        vuelto = pagado - self.total

        if vuelto < 0:
            self.label_vuelto.setText(f"Faltante: {self.pos.formato_pesos(abs(vuelto))}")
            self.label_vuelto.setStyleSheet("""
                QLabel {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 10px;
                    padding: 12px;
                    color: #B91C1C;
                    font-size: 16px;
                    font-weight: 800;
                }
            """)
        else:
            self.label_vuelto.setText(f"Vuelto: {self.pos.formato_pesos(vuelto)}")
            self.label_vuelto.setStyleSheet("""
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 10px;
                    padding: 12px;
                    color: #166534;
                    font-size: 16px;
                    font-weight: 800;
                }
            """)

    def validar_y_aceptar(self):
        datos = self.obtener_datos()

        pagado = (
            datos["monto_efectivo"]
            + datos["monto_tarjeta"]
            + datos["monto_transferencia"]
        )

        if pagado < self.total:
            QMessageBox.warning(
                self,
                "Pago insuficiente",
                "El monto pagado es menor al total de la venta."
            )
            return

        if self.requiere_mayoria_edad and not datos["confirmar_mayoria_edad"]:
            QMessageBox.warning(
                self,
                "Mayoría de edad",
                "Debes confirmar que el cliente es mayor de edad."
            )
            return

        self.accept()

    def obtener_datos(self):
        return {
            "metodo_pago": self.combo_metodo.currentText(),
            "monto_efectivo": Decimal(str(self.input_efectivo.value())),
            "monto_tarjeta": Decimal(str(self.input_tarjeta.value())),
            "monto_transferencia": Decimal(str(self.input_transferencia.value())),
            "confirmar_mayoria_edad": self.check_mayoria_edad.isChecked()
        }


class TicketDialog(QDialog):
    def __init__(self, ticket_texto, parent=None):
        super().__init__(parent)

        self.ticket_texto = ticket_texto
        self.config_negocio = self.obtener_configuracion_negocio_segura()

        self.logo_ticket = None
        self.nombre_negocio_label = None
        self.texto_ticket = None

        self.setWindowTitle("Ticket de venta")
        self.resize(500, 700)

        self.construir_interfaz()

    def obtener_configuracion_negocio_segura(self):
        try:
            consulta = """
                SELECT
                    nombre_negocio,
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

    def obtener_nombre_negocio(self):
        nombre = str(self.config_negocio.get("nombre_negocio") or "").strip()

        if nombre:
            return nombre

        return "POS PYMES"

    def obtener_logo_negocio(self):
        logo = str(self.config_negocio.get("logo_url") or "").strip()

        if logo:
            return logo

        return ""

    def cargar_pixmap_logo(self, ruta_logo, ancho=180, alto=80):
        ruta_logo = str(ruta_logo or "").strip()

        if not ruta_logo:
            return None

        if ruta_logo.lower().startswith(("http://", "https://")):
            return None

        ruta = Path(ruta_logo)

        if not ruta.exists():
            return None

        pixmap = QPixmap(str(ruta))

        if pixmap.isNull():
            return None

        return pixmap.scaled(
            ancho,
            alto,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel("Ticket generado")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #111827;")

        encabezado = QFrame()
        encabezado.setObjectName("encabezadoTicket")

        encabezado_layout = QVBoxLayout(encabezado)
        encabezado_layout.setContentsMargins(14, 12, 14, 12)
        encabezado_layout.setSpacing(6)

        self.logo_ticket = QLabel()
        self.logo_ticket.setObjectName("logoTicketVenta")
        self.logo_ticket.setFixedSize(210, 82)
        self.logo_ticket.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap_logo = self.cargar_pixmap_logo(self.obtener_logo_negocio())

        if pixmap_logo:
            self.logo_ticket.setPixmap(pixmap_logo)
            self.logo_ticket.setText("")
            self.logo_ticket.show()
        else:
            self.logo_ticket.setText("SIN LOGO")

        self.nombre_negocio_label = QLabel(self.obtener_nombre_negocio())
        self.nombre_negocio_label.setObjectName("nombreNegocioTicket")
        self.nombre_negocio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre_negocio_label.setWordWrap(True)

        encabezado_layout.addWidget(self.logo_ticket, 0, Qt.AlignmentFlag.AlignCenter)
        encabezado_layout.addWidget(self.nombre_negocio_label)

        self.texto_ticket = QTextEdit()
        self.texto_ticket.setReadOnly(True)
        self.texto_ticket.setPlainText(self.ticket_texto)
        self.texto_ticket.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-family: Consolas;
                font-size: 13px;
                padding: 10px;
            }
        """)

        botones = QHBoxLayout()

        btn_copiar = QPushButton("Copiar ticket")
        btn_copiar.clicked.connect(self.copiar_ticket)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_copiar)
        botones.addWidget(btn_cerrar)

        layout.addWidget(titulo)
        layout.addWidget(encabezado)
        layout.addWidget(self.texto_ticket)
        layout.addLayout(botones)

        self.setStyleSheet("""
            QFrame#encabezadoTicket {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }

            QLabel#logoTicketVenta {
                background-color: #F8FAFC;
                border: 1px dashed #CBD5E1;
                border-radius: 10px;
                color: #94A3B8;
                font-size: 12px;
                font-weight: 900;
            }

            QLabel#nombreNegocioTicket {
                color: #0F172A;
                font-size: 16px;
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
        """)

    def copiar_ticket(self):
        QApplication.clipboard().setText(self.ticket_texto)
        QMessageBox.information(self, "Copiado", "Ticket copiado al portapapeles.")


class VentasPage(QWidget):
    def __init__(self, pos_service):
        super().__init__()

        self.pos = pos_service

        self.input_codigo = None
        self.input_cantidad = None
        self.tabla_carrito = None

        self.label_total = None
        self.label_subtotal = None
        self.label_items = None
        self.label_unidades = None
        self.label_mayoria_edad = None
        self.label_descuento = None
        self.label_impuesto = None
        self.label_estado_caja = None
        self.label_estado_operacion = None
        self.label_ultima_actualizacion = None

        self.actualizando_ventas = False
        self.timer_ventas = None

        self.timer_scanner_movil = None

        self._buffer_lector_codigo = ""
        self._timer_buffer_lector = None
        self._event_filter_lector_instalado = False
        self._procesando_codigo_lector = False
        self._capturando_lector_codigo = False

        self.construir_interfaz()
        self.configurar_lector_codigo_barras()
        self.recargar_todo(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()
        self.iniciar_scanner_movil()

    def configurar_lector_codigo_barras(self):
        self._buffer_lector_codigo = ""
        self._capturando_lector_codigo = False
        self._procesando_codigo_lector = False

        self._timer_buffer_lector = QTimer(self)
        self._timer_buffer_lector.setSingleShot(True)
        self._timer_buffer_lector.timeout.connect(self.procesar_buffer_lector_por_timeout)

        app = QApplication.instance()

        if app is not None and not self._event_filter_lector_instalado:
            app.installEventFilter(self)
            self._event_filter_lector_instalado = True

        QTimer.singleShot(80, self.enfocar_input_codigo)

    def enfocar_input_codigo(self):
        if self.input_codigo is None:
            return

        if QApplication.activeModalWidget():
            return

        if not self.isVisible():
            return

        self.input_codigo.setFocus(Qt.FocusReason.OtherFocusReason)

    def limpiar_lector_codigo(self):
        self._buffer_lector_codigo = ""
        self._capturando_lector_codigo = False

        if self._timer_buffer_lector is not None:
            self._timer_buffer_lector.stop()

        if self.input_codigo is not None:
            self.input_codigo.clear()

    def procesar_buffer_lector_por_timeout(self):
        codigo = self._buffer_lector_codigo.strip()

        if not codigo:
            self._capturando_lector_codigo = False
            return

        if len(codigo) < 6:
            self.limpiar_lector_codigo()
            self.enfocar_input_codigo()
            return

        self.procesar_codigo_desde_lector(codigo)

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(obj, event)

        if QApplication.activeModalWidget():
            return super().eventFilter(obj, event)

        if not self.isVisible():
            return super().eventFilter(obj, event)

        if self.input_codigo is None:
            return super().eventFilter(obj, event)

        key = event.key()
        texto = event.text()
        widget_foco = QApplication.focusWidget()

        if isinstance(widget_foco, QTextEdit):
            return super().eventFilter(obj, event)

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            codigo_buffer = self._buffer_lector_codigo.strip()

            if codigo_buffer:
                self.procesar_codigo_desde_lector(codigo_buffer)
                return True

            if widget_foco is self.input_codigo:
                codigo_input = self.input_codigo.text().strip()

                if codigo_input:
                    self.procesar_codigo_desde_lector(codigo_input)
                    return True

            return super().eventFilter(obj, event)

        if texto and texto.isprintable() and texto.isdigit():
            if self._capturando_lector_codigo:
                self._buffer_lector_codigo += texto
                self.input_codigo.setText(self._buffer_lector_codigo)

                if self._timer_buffer_lector is not None:
                    self._timer_buffer_lector.start(180)

                return True

            if widget_foco is self.input_codigo:
                return super().eventFilter(obj, event)

            self._capturando_lector_codigo = True
            self._buffer_lector_codigo = texto

            self.input_codigo.clear()
            self.input_codigo.setFocus(Qt.FocusReason.OtherFocusReason)
            self.input_codigo.setText(self._buffer_lector_codigo)

            if self._timer_buffer_lector is not None:
                self._timer_buffer_lector.start(180)

            return True

        return super().eventFilter(obj, event)

    def procesar_codigo_desde_lector(self, codigo):
        codigo = str(codigo or "").strip()

        if not codigo:
            return

        if self._procesando_codigo_lector:
            return

        self._procesando_codigo_lector = True

        try:
            self._buffer_lector_codigo = ""
            self._capturando_lector_codigo = False

            if self._timer_buffer_lector is not None:
                self._timer_buffer_lector.stop()

            self.input_codigo.setText(codigo)
            self.input_cantidad.setValue(1)
            self.agregar_producto()

        finally:
            self._buffer_lector_codigo = ""
            self._capturando_lector_codigo = False
            self._procesando_codigo_lector = False

            if self.input_codigo is not None:
                self.input_codigo.clear()

            QTimer.singleShot(30, self.enfocar_input_codigo)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(80, self.enfocar_input_codigo)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        QTimer.singleShot(50, self.enfocar_input_codigo)

    def iniciar_actualizacion_automatica(self):
        self.timer_ventas = QTimer(self)
        self.timer_ventas.timeout.connect(self.recargar_todo_automatico)
        self.timer_ventas.start(5000)

    def iniciar_scanner_movil(self):
        self.timer_scanner_movil = QTimer(self)
        self.timer_scanner_movil.timeout.connect(self.revisar_scanner_movil)
        self.timer_scanner_movil.start(500)

    def revisar_scanner_movil(self):
        if self.actualizando_ventas:
            return

        if QApplication.activeModalWidget():
            return

        try:
            solicitud = urllib.request.Request("http://127.0.0.1:8000/obtener-scan")
            token_api = os.getenv("POS_API_TOKEN", "").strip()
            if token_api:
                solicitud.add_header("X-POS-Token", token_api)

            with urllib.request.urlopen(solicitud, timeout=0.25) as respuesta:
                data = json.loads(respuesta.read().decode("utf-8"))

            if not data.get("ok"):
                return

            scan = data.get("scan") or {}
            codigo = str(scan.get("codigo") or "").strip()

            if not codigo:
                return

            self.procesar_codigo_scanner_movil(codigo)

        except URLError:
            return

        except Exception:
            return

    def procesar_codigo_scanner_movil(self, codigo):
        codigo = str(codigo or "").strip()

        if not codigo:
            return

        self.input_codigo.setText(codigo)
        self.input_cantidad.setValue(1)

        self.actualizar_estado_operacion(
            f"Código recibido desde celular: {codigo}",
            "info"
        )

        self.agregar_producto()

    def recargar_todo_automatico(self):
        if self.actualizando_ventas:
            return

        if QApplication.activeModalWidget():
            return

        self.recargar_todo(mostrar_mensaje=False)

    def actualizar_label_ultima_actualizacion(self):
        if self.label_ultima_actualizacion is None:
            return

        hora_actual = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora_actual}")

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()

        titulo = QLabel("Ventas")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel("Escanea productos, arma el carrito y cobra la venta.")
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

        self.label_estado_caja = QLabel("Revisando estado de caja...")
        self.label_estado_caja.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px;
                color: #334155;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.label_estado_caja)

        panel_venta = QFrame()
        panel_venta.setObjectName("panelVentaRapida")

        panel_layout = QVBoxLayout(panel_venta)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        panel_layout.setSpacing(14)

        titulo_panel = QLabel("Venta rápida")
        titulo_panel.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 18px;
                font-weight: 900;
                background: transparent;
            }
        """)

        ayuda_panel = QLabel(
            "Escanea el código de barra o escríbelo manualmente. "
            "La cantidad sirve para vender más de una unidad o productos por peso."
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

        fila_campos = QHBoxLayout()
        fila_campos.setSpacing(14)

        bloque_codigo = QVBoxLayout()
        bloque_codigo.setSpacing(6)

        label_codigo = QLabel("Código de barra")
        label_codigo.setStyleSheet("color: #334155; font-weight: 800; background: transparent;")

        ayuda_codigo = QLabel("Aquí escaneas con la pistola, escribes manualmente o recibes códigos del celular.")
        ayuda_codigo.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 12px;
                background: transparent;
            }
        """)

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Escanea, ingresa código de barra o usa el celular")
        self.input_codigo.setMinimumHeight(46)
        self.input_codigo.returnPressed.connect(self.agregar_producto)

        bloque_codigo.addWidget(label_codigo)
        bloque_codigo.addWidget(ayuda_codigo)
        bloque_codigo.addWidget(self.input_codigo)

        bloque_cantidad = QVBoxLayout()
        bloque_cantidad.setSpacing(6)

        label_cantidad = QLabel("Cantidad / peso")
        label_cantidad.setStyleSheet("color: #334155; font-weight: 800; background: transparent;")

        ayuda_cantidad = QLabel(
            "Usa 1 para una unidad. Usa decimales para productos por kilo o litro."
        )
        ayuda_cantidad.setWordWrap(True)
        ayuda_cantidad.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 12px;
                background: transparent;
            }
        """)

        self.input_cantidad = QDoubleSpinBox()
        self.input_cantidad.setMinimum(0.001)
        self.input_cantidad.setMaximum(999999)
        self.input_cantidad.setDecimals(3)
        self.input_cantidad.setValue(1)
        self.input_cantidad.setSingleStep(1)
        self.input_cantidad.setMinimumHeight(46)
        self.input_cantidad.setFixedWidth(170)
        self.input_cantidad.setToolTip(
            "1 = una unidad | 0.500 = medio kilo | 1.500 = kilo y medio"
        )

        ayuda_decimal = QLabel("Ejemplos: 1 = unidad | 0.500 = medio kilo | 1.250 = kilo y cuarto")
        ayuda_decimal.setWordWrap(True)
        ayuda_decimal.setStyleSheet("""
            QLabel {
                color: #1E40AF;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """)

        bloque_cantidad.addWidget(label_cantidad)
        bloque_cantidad.addWidget(ayuda_cantidad)
        bloque_cantidad.addWidget(self.input_cantidad)
        bloque_cantidad.addWidget(ayuda_decimal)

        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("botonPrincipal")
        btn_agregar.setMinimumHeight(46)
        btn_agregar.setFixedWidth(170)
        btn_agregar.clicked.connect(self.agregar_producto)

        ayuda_boton = QLabel("Presiona Enter o haz clic para agregar")
        ayuda_boton.setWordWrap(True)
        ayuda_boton.setAlignment(Qt.AlignCenter)
        ayuda_boton.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 12px;
                background: transparent;
            }
        """)

        bloque_boton = QVBoxLayout()
        bloque_boton.setSpacing(6)
        bloque_boton.addWidget(QLabel(""))
        bloque_boton.addWidget(QLabel(""))
        bloque_boton.addWidget(btn_agregar)
        bloque_boton.addWidget(ayuda_boton)

        fila_campos.addLayout(bloque_codigo, 1)
        fila_campos.addLayout(bloque_cantidad)
        fila_campos.addLayout(bloque_boton)

        panel_layout.addLayout(fila_campos)

        barra_ayuda = QFrame()
        barra_ayuda.setObjectName("barraAyudaVenta")

        barra_ayuda_layout = QHBoxLayout(barra_ayuda)
        barra_ayuda_layout.setContentsMargins(12, 10, 12, 10)
        barra_ayuda_layout.setSpacing(16)

        chip_1 = QLabel("1 = una unidad")
        chip_2 = QLabel("0.500 = medio kilo")
        chip_3 = QLabel("1.000 = un kilo")
        chip_4 = QLabel("Celular → POS automático")

        for chip in [chip_1, chip_2, chip_3, chip_4]:
            chip.setStyleSheet("""
                QLabel {
                    color: #334155;
                    font-size: 12px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            barra_ayuda_layout.addWidget(chip)

        barra_ayuda_layout.addStretch()

        panel_layout.addWidget(barra_ayuda)

        layout.addWidget(panel_venta)

        resumen_layout = QGridLayout()
        resumen_layout.setContentsMargins(0, 0, 0, 0)
        resumen_layout.setHorizontalSpacing(16)
        resumen_layout.setVerticalSpacing(12)

        self.label_items = self.crear_card_resumen(resumen_layout, 0, 0, "Items", "0")
        self.label_unidades = self.crear_card_resumen(resumen_layout, 0, 1, "Unidades", "0")
        self.label_subtotal = self.crear_card_resumen(resumen_layout, 0, 2, "Subtotal neto", "$0")
        self.label_descuento = self.crear_card_resumen(resumen_layout, 0, 3, "Descuento", "$0")
        self.label_impuesto = self.crear_card_resumen(resumen_layout, 0, 4, "IVA 19%", "$0")
        self.label_mayoria_edad = self.crear_card_resumen(resumen_layout, 0, 5, "Mayoría edad", "No")
        self.label_total = self.crear_card_resumen(resumen_layout, 0, 6, "Total", "$0")

        for columna in range(7):
            resumen_layout.setColumnStretch(columna, 1)

        layout.addLayout(resumen_layout)

        titulo_carrito = QLabel("Detalle del carrito")
        titulo_carrito.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)
        layout.addWidget(titulo_carrito)

        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(7)
        self.tabla_carrito.setHorizontalHeaderLabels([
            "Código",
            "Producto",
            "Cantidad",
            "Precio",
            "Descuento",
            "Subtotal",
            "Stock"
        ])
        self.preparar_tabla(self.tabla_carrito)
        layout.addWidget(self.tabla_carrito)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        btn_cambiar_cantidad = QPushButton("Cambiar cantidad")
        btn_cambiar_cantidad.setMinimumHeight(42)
        btn_cambiar_cantidad.clicked.connect(self.cambiar_cantidad_item)

        btn_eliminar = QPushButton("Eliminar item")
        btn_eliminar.setMinimumHeight(42)
        btn_eliminar.clicked.connect(self.eliminar_item)

        btn_limpiar = QPushButton("Vaciar carrito")
        btn_limpiar.setMinimumHeight(42)
        btn_limpiar.clicked.connect(self.vaciar_carrito)

        btn_copiar = QPushButton("Copiar resumen")
        btn_copiar.setMinimumHeight(42)
        btn_copiar.clicked.connect(self.copiar_resumen_venta)

        btn_cobrar = QPushButton("Cobrar venta")
        btn_cobrar.setObjectName("botonPrincipal")
        btn_cobrar.setMinimumHeight(46)
        btn_cobrar.setFixedWidth(180)
        btn_cobrar.clicked.connect(self.cobrar_venta)

        acciones.addWidget(btn_cambiar_cantidad)
        acciones.addWidget(btn_eliminar)
        acciones.addWidget(btn_limpiar)
        acciones.addWidget(btn_copiar)
        acciones.addStretch()
        acciones.addWidget(btn_cobrar)

        layout.addLayout(acciones)

        self.label_estado_operacion = QLabel("Sistema listo para escanear productos.")
        self.label_estado_operacion.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px;
                color: #334155;
                font-size: 13px;
                font-weight: 700;
            }
        """)
        layout.addWidget(self.label_estado_operacion)

        self.setStyleSheet("""
            QFrame#panelVentaRapida {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#barraAyudaVenta {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }

            QFrame#cardResumenVenta {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QLabel#cardResumenTitulo {
                color: #64748B;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }

            QLabel#cardResumenValor {
                color: #0F172A;
                font-size: 22px;
                font-weight: 900;
                background-color: transparent;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
                border: none;
                border-radius: 10px;
            }
        """)

        QTimer.singleShot(80, self.enfocar_input_codigo)

    def crear_card_resumen(self, grid, fila, columna, titulo, valor):
        card = QFrame()
        card.setObjectName("cardResumenVenta")
        card.setMinimumHeight(105)
        card.setMaximumHeight(115)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("cardResumenTitulo")
        label_titulo.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        label_valor = QLabel(valor)
        label_valor.setObjectName("cardResumenValor")
        label_valor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        label_valor.setWordWrap(False)
        label_valor.setMinimumHeight(30)

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)

        grid.addWidget(card, fila, columna)
        return label_valor

    def preparar_tabla(self, tabla):
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectRows)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setMinimumHeight(340)

    def actualizar_estado_operacion(self, texto, tipo="info"):
        estilos = {
            "ok": """
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 12px;
                    padding: 12px;
                    color: #166534;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
            "error": """
                QLabel {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 12px;
                    padding: 12px;
                    color: #B91C1C;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
            "info": """
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
        }

        self.label_estado_operacion.setText(texto)
        self.label_estado_operacion.setStyleSheet(estilos.get(tipo, estilos["info"]))

    def recargar_todo(self, mostrar_mensaje=False):
        if self.actualizando_ventas:
            return

        self.actualizando_ventas = True

        try:
            self.cargar_estado_caja()
            self.actualizar_carrito()

            if mostrar_mensaje:
                self.actualizar_estado_operacion("Pantalla actualizada correctamente.", "info")
                self.enfocar_input_codigo()

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar ventas automáticamente: {error}",
                "error"
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_ventas = False

    def cargar_estado_caja(self):
        try:
            resultado = self.pos.obtener_caja_abierta_sistema()

            if resultado["ok"]:
                data = resultado.get("data") or {}
                caja_id = data.get("id") or data.get("caja_id") or data.get("turno_id") or "-"
                fecha = data.get("fecha_apertura") or "-"

                try:
                    fecha_formateada = self.pos.formato_fecha(fecha)
                except Exception:
                    fecha_formateada = str(fecha)

                self.label_estado_caja.setText(
                    f"Caja abierta | Turno ID: {caja_id} | Apertura: {fecha_formateada}"
                )
                self.label_estado_caja.setStyleSheet("""
                    QLabel {
                        background-color: #ECFDF5;
                        border: 1px solid #BBF7D0;
                        border-radius: 12px;
                        padding: 12px;
                        color: #166534;
                        font-size: 14px;
                        font-weight: 800;
                    }
                """)
            else:
                self.label_estado_caja.setText(
                    "Caja cerrada | Debes abrir caja antes de vender."
                )
                self.label_estado_caja.setStyleSheet("""
                    QLabel {
                        background-color: #FEF2F2;
                        border: 1px solid #FECACA;
                        border-radius: 12px;
                        padding: 12px;
                        color: #B91C1C;
                        font-size: 14px;
                        font-weight: 800;
                    }
                """)

        except Exception:
            self.label_estado_caja.setText("No se pudo revisar el estado de caja.")
            self.label_estado_caja.setStyleSheet("""
                QLabel {
                    background-color: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 12px;
                    padding: 12px;
                    color: #92400E;
                    font-size: 14px;
                    font-weight: 800;
                }
            """)

    def agregar_producto(self):
        codigo = self.input_codigo.text().strip()
        cantidad = Decimal(str(self.input_cantidad.value()))

        if not codigo:
            self.limpiar_lector_codigo()
            self.enfocar_input_codigo()
            self.actualizar_estado_operacion("No se agregó nada: falta el código de barra.", "error")
            return

        resultado = self.pos.carrito_agregar_producto(
            codigo_barra=codigo,
            cantidad=cantidad
        )

        self._buffer_lector_codigo = ""
        self._capturando_lector_codigo = False

        if self._timer_buffer_lector is not None:
            self._timer_buffer_lector.stop()

        if not resultado["ok"]:
            QMessageBox.warning(self, "Producto no agregado", resultado["mensaje"])
            self.input_codigo.clear()
            self.enfocar_input_codigo()
            self.actualizar_estado_operacion(
                f"No se pudo agregar el producto: {resultado['mensaje']}",
                "error"
            )
            return

        self.input_codigo.clear()
        self.input_cantidad.setValue(1)

        self.actualizar_carrito()
        self.actualizar_estado_operacion("Producto agregado correctamente al carrito.", "ok")
        QTimer.singleShot(30, self.enfocar_input_codigo)

    def actualizar_carrito(self):
        detalle = self.pos.carrito_obtener_detalle()
        resumen = self.pos.carrito_obtener_resumen()

        self.tabla_carrito.setRowCount(0)

        if not detalle["ok"]:
            self.label_items.setText("0")
            self.label_unidades.setText("0")
            self.label_subtotal.setText("$0")
            self.label_descuento.setText("$0")
            self.label_impuesto.setText("$0")
            self.label_total.setText("$0")
            self.label_mayoria_edad.setText("No")
            return

        items = detalle["data"] or []
        descuento_total = Decimal("0")

        for fila, item in enumerate(items):
            self.tabla_carrito.insertRow(fila)

            try:
                descuento_total += Decimal(str(item.get("descuento_linea") or 0))
            except Exception:
                pass

            valores = [
                item.get("codigo_barra"),
                item.get("nombre"),
                item.get("cantidad"),
                self.pos.formato_pesos(item.get("precio_unitario")),
                self.pos.formato_pesos(item.get("descuento_linea")),
                self.pos.formato_pesos(item.get("subtotal_linea")),
                item.get("stock_actual")
            ]

            for columna, valor in enumerate(valores):
                celda = QTableWidgetItem(str(valor or ""))
                celda.setTextAlignment(Qt.AlignCenter)
                self.tabla_carrito.setItem(fila, columna, celda)

        if resumen["ok"]:
            data = resumen["data"] or {}

            self.label_items.setText(str(data.get("cantidad_items") or 0))
            self.label_unidades.setText(str(data.get("total_unidades") or 0))
            porcentaje_iva = data.get("impuesto_porcentaje") or 19
            try:
                porcentaje_iva = int(Decimal(str(porcentaje_iva)))
            except Exception:
                porcentaje_iva = 19

            self.label_subtotal.setText(self.pos.formato_pesos(data.get("subtotal")))
            self.label_descuento.setText(self.pos.formato_pesos(data.get("descuento_total", descuento_total)))
            self.label_impuesto.setText(self.pos.formato_pesos(data.get("impuesto_total")))
            titulo_iva = None
            if self.label_impuesto and self.label_impuesto.parentWidget():
                titulo_iva = self.label_impuesto.parentWidget().findChild(QLabel, "cardResumenTitulo")
            if titulo_iva:
                titulo_iva.setText(f"IVA {porcentaje_iva}%")
            self.label_total.setText(self.pos.formato_pesos(data.get("total")))

            if data.get("requiere_mayoria_edad"):
                self.label_mayoria_edad.setText("Sí")
            else:
                self.label_mayoria_edad.setText("No")

    def cambiar_cantidad_item(self):
        fila = self.tabla_carrito.currentRow()

        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Selecciona un producto del carrito.")
            self.actualizar_estado_operacion("Debes seleccionar un producto para cambiar la cantidad.", "error")
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        cantidad, ok = QInputDialog.getDouble(
            self,
            "Cambiar cantidad",
            "Nueva cantidad:",
            1,
            0.001,
            999999,
            3
        )

        if not ok:
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        resultado = self.pos.carrito_actualizar_cantidad(
            indice=fila,
            cantidad=Decimal(str(cantidad))
        )

        if not resultado["ok"]:
            QMessageBox.warning(self, "Error", resultado["mensaje"])
            self.actualizar_estado_operacion(
                f"No se pudo cambiar la cantidad: {resultado['mensaje']}",
                "error"
            )
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        self.actualizar_carrito()
        self.actualizar_estado_operacion("Cantidad actualizada correctamente.", "ok")
        QTimer.singleShot(50, self.enfocar_input_codigo)

    def eliminar_item(self):
        fila = self.tabla_carrito.currentRow()

        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Selecciona un producto del carrito.")
            self.actualizar_estado_operacion("Debes seleccionar un producto para eliminarlo.", "error")
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        confirmar = QMessageBox.question(
            self,
            "Eliminar producto",
            "¿Deseas eliminar este producto del carrito?"
        )

        if confirmar != QMessageBox.Yes:
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        resultado = self.pos.carrito_eliminar_item(fila)

        if not resultado["ok"]:
            QMessageBox.warning(self, "Error", resultado["mensaje"])
            self.actualizar_estado_operacion(
                f"No se pudo eliminar el item: {resultado['mensaje']}",
                "error"
            )
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        self.actualizar_carrito()
        self.actualizar_estado_operacion("Producto eliminado del carrito.", "ok")
        QTimer.singleShot(50, self.enfocar_input_codigo)

    def vaciar_carrito(self):
        confirmar = QMessageBox.question(
            self,
            "Vaciar carrito",
            "¿Deseas vaciar todo el carrito?"
        )

        if confirmar != QMessageBox.Yes:
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        resultado = self.pos.carrito_vaciar()

        if not resultado["ok"]:
            QMessageBox.warning(self, "Error", resultado["mensaje"])
            self.actualizar_estado_operacion(
                f"No se pudo vaciar el carrito: {resultado['mensaje']}",
                "error"
            )
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        self.actualizar_carrito()
        self.enfocar_input_codigo()
        self.actualizar_estado_operacion("Carrito vaciado correctamente.", "ok")

    def generar_resumen_texto(self):
        detalle = self.pos.carrito_obtener_detalle()
        resumen = self.pos.carrito_obtener_resumen()

        if not detalle["ok"] or not resumen["ok"]:
            return "No hay resumen disponible."

        items = detalle["data"] or []
        data = resumen["data"] or {}

        lineas = [
            "RESUMEN DE VENTA",
            "==========================",
            f"Items: {data.get('cantidad_items', 0)}",
            f"Unidades: {data.get('total_unidades', 0)}",
            f"Subtotal neto: {self.pos.formato_pesos(data.get('subtotal'))}",
            f"Descuento: {self.pos.formato_pesos(data.get('descuento_total'))}",
            f"IVA {data.get('impuesto_porcentaje', 19)}%: {self.pos.formato_pesos(data.get('impuesto_total'))}",
            f"Total: {self.pos.formato_pesos(data.get('total'))}",
            f"Mayoría de edad: {'Sí' if data.get('requiere_mayoria_edad') else 'No'}",
            "",
            "DETALLE"
        ]

        for item in items:
            lineas.append(
                f"- {item.get('nombre')} | Cant: {item.get('cantidad')} | "
                f"Subtotal: {self.pos.formato_pesos(item.get('subtotal_linea'))}"
            )

        return "\n".join(lineas)

    def copiar_resumen_venta(self):
        texto = self.generar_resumen_texto()
        QApplication.clipboard().setText(texto)
        QMessageBox.information(
            self,
            "Resumen copiado",
            "El resumen de la venta fue copiado al portapapeles."
        )
        self.actualizar_estado_operacion("Resumen de venta copiado al portapapeles.", "ok")
        QTimer.singleShot(50, self.enfocar_input_codigo)

    def cobrar_venta(self):
        self.cargar_estado_caja()

        resumen = self.pos.carrito_obtener_resumen()

        if not resumen["ok"]:
            QMessageBox.warning(self, "Error", resumen["mensaje"])
            self.actualizar_estado_operacion(
                f"No se pudo obtener el resumen: {resumen['mensaje']}",
                "error"
            )
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        data = resumen["data"] or {}

        if data.get("cantidad_items", 0) == 0:
            QMessageBox.warning(self, "Carrito vacío", "No hay productos para cobrar.")
            self.actualizar_estado_operacion("No se puede cobrar una venta sin productos.", "error")
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        total = data.get("total")
        requiere_mayoria_edad = data.get("requiere_mayoria_edad", False)

        dialogo = CobroDialog(
            pos_service=self.pos,
            total=total,
            requiere_mayoria_edad=requiere_mayoria_edad,
            parent=self
        )

        if dialogo.exec() != QDialog.Accepted:
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        datos_pago = dialogo.obtener_datos()

        resultado = self.pos.vender_carrito(
            metodo_pago=datos_pago["metodo_pago"],
            monto_efectivo=datos_pago["monto_efectivo"],
            monto_tarjeta=datos_pago["monto_tarjeta"],
            monto_transferencia=datos_pago["monto_transferencia"],
            confirmar_mayoria_edad=datos_pago["confirmar_mayoria_edad"]
        )

        if not resultado["ok"]:
            QMessageBox.warning(self, "Venta no realizada", resultado["mensaje"])
            self.actualizar_estado_operacion(
                f"No se pudo realizar la venta: {resultado['mensaje']}",
                "error"
            )
            QTimer.singleShot(50, self.enfocar_input_codigo)
            return

        venta = resultado["data"] or {}

        QMessageBox.information(
            self,
            "Venta realizada",
            f"Venta realizada correctamente.\n\n"
            f"Número: {venta.get('numero_venta')}\n"
            f"Total: {self.pos.formato_pesos(venta.get('total'))}\n"
            f"Vuelto: {self.pos.formato_pesos(venta.get('vuelto'))}"
        )

        ticket = self.pos.generar_ticket_venta(venta.get("venta_id"))

        if ticket["ok"]:
            ticket_dialog = TicketDialog(ticket["data"], self)
            ticket_dialog.exec()
        else:
            QMessageBox.warning(self, "Ticket", ticket["mensaje"])

        self.cargar_estado_caja()
        self.actualizar_carrito()
        self.enfocar_input_codigo()
        self.actualizar_estado_operacion("Venta cobrada correctamente.", "ok")
        self.actualizar_label_ultima_actualizacion()