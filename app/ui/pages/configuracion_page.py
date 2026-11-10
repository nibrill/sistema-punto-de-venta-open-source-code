from decimal import Decimal
from pathlib import Path
import os
import shutil
import time

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QAbstractSpinBox,
    QMessageBox,
    QFrame,
    QFormLayout,
    QScrollArea,
    QSizePolicy,
    QApplication,
    QFileDialog,
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QPixmap



class ConfiguracionPage(QWidget):
    def __init__(self, pos_service):
        super().__init__()

        self.pos = pos_service

        self.hay_cambios = False
        self.bloqueando_cambios = False
        self.config_original = {}

        self.input_nombre = None
        self.input_rut = None
        self.input_giro = None
        self.input_direccion = None
        self.input_comuna = None
        self.input_ciudad = None
        self.input_telefono = None
        self.input_email = None
        self.input_logo = None
        self.logo_preview = None
        self.btn_seleccionar_logo = None
        self.btn_quitar_logo = None

        self.input_moneda = None
        self.input_impuesto = None
        self.input_mensaje_ticket = None

        self.label_ultima_carga = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.btn_guardar = None
        self.btn_descartar = None

        self.labels = {}
        self.cards = {}

        self.ticket_logo = None
        self.ticket_nombre = None
        self.ticket_giro = None
        self.ticket_rut = None
        self.ticket_direccion = None
        self.ticket_contacto = None
        self.ticket_mensaje = None
        self.ticket_impuesto = None

        self.construir_interfaz()
        self.cargar_configuracion()

    # ============================================================
    # INTERFAZ
    # ============================================================

    def construir_interfaz(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(32, 32, 32, 32)
        layout_principal.setSpacing(20)

        encabezado = QHBoxLayout()

        textos = QVBoxLayout()
        textos.setSpacing(6)

        titulo = QLabel("Configuración")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Administra los datos del negocio, ticket, impuestos, logo y parámetros generales del POS."
        )
        subtitulo.setObjectName("subtituloPagina")
        subtitulo.setWordWrap(True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        estado_layout = QVBoxLayout()
        estado_layout.setSpacing(4)
        estado_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        label_modo = QLabel("Vista previa en vivo")
        label_modo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_modo.setStyleSheet("""
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

        self.label_ultima_carga = QLabel("Última carga: --:--:--")
        self.label_ultima_carga.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_ultima_carga.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 12px;
                font-weight: 600;
                background-color: transparent;
            }
        """)

        estado_layout.addWidget(label_modo)
        estado_layout.addWidget(self.label_ultima_carga)

        self.btn_descartar = QPushButton("Descartar cambios")
        self.btn_descartar.setMinimumHeight(46)
        self.btn_descartar.setFixedWidth(180)
        self.btn_descartar.clicked.connect(self.descartar_cambios)

        self.btn_guardar = QPushButton("Guardar cambios")
        self.btn_guardar.setObjectName("botonPrincipal")
        self.btn_guardar.setMinimumHeight(46)
        self.btn_guardar.setFixedWidth(180)
        self.btn_guardar.clicked.connect(self.guardar_configuracion)

        encabezado.addLayout(textos, 1)
        encabezado.addStretch()
        encabezado.addLayout(estado_layout)
        encabezado.addSpacing(12)
        encabezado.addWidget(self.btn_descartar)
        encabezado.addWidget(self.btn_guardar)

        layout_principal.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["negocio"] = self.crear_card(
            cards, 0, 0,
            key="negocio",
            titulo="Negocio",
            valor="-",
            detalle="Nombre comercial del POS",
            tipo="azul",
        )

        self.labels["rut"] = self.crear_card(
            cards, 0, 1,
            key="rut",
            titulo="RUT",
            valor="-",
            detalle="Identificación tributaria",
            tipo="neutro",
        )

        self.labels["ciudad"] = self.crear_card(
            cards, 0, 2,
            key="ciudad",
            titulo="Ciudad",
            valor="-",
            detalle="Ubicación del negocio",
            tipo="neutro",
        )

        self.labels["moneda"] = self.crear_card(
            cards, 0, 3,
            key="moneda",
            titulo="Moneda",
            valor="CLP",
            detalle="Moneda usada en ventas",
            tipo="verde",
        )

        self.labels["impuesto"] = self.crear_card(
            cards, 1, 0,
            key="impuesto",
            titulo="Impuesto",
            valor="19%",
            detalle="Porcentaje aplicado",
            tipo="morado",
        )

        self.labels["contacto"] = self.crear_card(
            cards, 1, 1,
            key="contacto",
            titulo="Contacto",
            valor="-",
            detalle="Teléfono o email disponible",
            tipo="neutro",
        )

        self.labels["ticket"] = self.crear_card(
            cards, 1, 2,
            key="ticket",
            titulo="Ticket",
            valor="OK",
            detalle="Mensaje de comprobante",
            tipo="verde",
        )

        self.labels["estado"] = self.crear_card(
            cards, 1, 3,
            key="estado",
            titulo="Estado",
            valor="Sin cambios",
            detalle="Estado de configuración",
            tipo="neutro",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout_principal.addLayout(cards)

        self.label_alertas = QLabel("Cargando configuración...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout_principal.addWidget(self.label_alertas)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        contenedor_scroll = QWidget()
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(20)

        panel_principal = QFrame()
        panel_principal.setObjectName("panelConfiguracion")

        layout_panel = QVBoxLayout(panel_principal)
        layout_panel.setContentsMargins(22, 20, 22, 22)
        layout_panel.setSpacing(20)

        secciones = QHBoxLayout()
        secciones.setSpacing(20)

        secciones.addWidget(self.crear_seccion_negocio(), 1)
        secciones.addWidget(self.crear_seccion_sistema(), 1)

        layout_panel.addLayout(secciones)

        layout_scroll.addWidget(panel_principal)

        panel_ticket = self.crear_vista_ticket()
        layout_scroll.addWidget(panel_ticket)

        self.label_estado_operacion = QLabel("Configuración lista para administrar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout_scroll.addWidget(self.label_estado_operacion)

        layout_scroll.addStretch()

        scroll.setWidget(contenedor_scroll)
        layout_principal.addWidget(scroll)

        self.aplicar_estilos()
        self.conectar_senales()
        self.actualizar_estado_botones()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardConfig")
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

        if key == "negocio":
            label_valor.setObjectName("cardValorNegocio")
            label_valor.setMaximumHeight(56)
        else:
            label_valor.setObjectName("cardValor")

        label_valor.setWordWrap(True)
        label_valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

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

    def crear_seccion_negocio(self):
        card = QFrame()
        card.setObjectName("subPanelConfig")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Datos del negocio")
        titulo.setObjectName("seccionTitulo")

        ayuda = QLabel(
            "Estos datos aparecerán en tickets, reportes y documentos comerciales."
        )
        ayuda.setObjectName("textoAyuda")
        ayuda.setWordWrap(True)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.input_nombre = self.crear_input("Ej: Botillería Demo")
        self.input_rut = self.crear_input("Ej: 11111111-1")
        self.input_giro = self.crear_input("Ej: Venta de bebidas y alcoholes")
        self.input_direccion = self.crear_input("Ej: Av. Principal 123")
        self.input_comuna = self.crear_input("Ej: Santiago")
        self.input_ciudad = self.crear_input("Ej: Santiago")
        self.input_telefono = self.crear_input("Ej: +56912345678")
        self.input_email = self.crear_input("Ej: contacto@negocio.cl")

        self.input_logo = self.crear_input("Sin logo seleccionado")
        self.input_logo.setReadOnly(True)
        self.input_logo.setPlaceholderText("Selecciona una imagen desde tu computador")

        panel_logo = QFrame()
        panel_logo.setObjectName("panelLogoNegocio")

        logo_layout = QHBoxLayout(panel_logo)
        logo_layout.setContentsMargins(14, 14, 14, 14)
        logo_layout.setSpacing(14)

        self.logo_preview = QLabel("Sin logo")
        self.logo_preview.setObjectName("logoPreview")
        self.logo_preview.setFixedSize(126, 86)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setWordWrap(True)

        logo_derecha = QVBoxLayout()
        logo_derecha.setSpacing(8)

        texto_logo = QLabel(
            "Carga el logo del negocio. Se guardará la ruta en la configuración y se mostrará en la vista previa del ticket."
        )
        texto_logo.setObjectName("textoAyuda")
        texto_logo.setWordWrap(True)

        botones_logo = QHBoxLayout()
        botones_logo.setSpacing(8)

        self.btn_seleccionar_logo = QPushButton("Seleccionar logo")
        self.btn_seleccionar_logo.setMinimumHeight(38)
        self.btn_seleccionar_logo.clicked.connect(self.seleccionar_logo_negocio)

        self.btn_quitar_logo = QPushButton("Quitar logo")
        self.btn_quitar_logo.setMinimumHeight(38)
        self.btn_quitar_logo.clicked.connect(self.quitar_logo_negocio)

        botones_logo.addWidget(self.btn_seleccionar_logo)
        botones_logo.addWidget(self.btn_quitar_logo)
        botones_logo.addStretch()

        logo_derecha.addWidget(texto_logo)
        logo_derecha.addWidget(self.input_logo)
        logo_derecha.addLayout(botones_logo)

        logo_layout.addWidget(self.logo_preview)
        logo_layout.addLayout(logo_derecha, 1)

        form.addRow("Nombre negocio *:", self.input_nombre)
        form.addRow("RUT:", self.input_rut)
        form.addRow("Giro:", self.input_giro)
        form.addRow("Dirección:", self.input_direccion)
        form.addRow("Comuna:", self.input_comuna)
        form.addRow("Ciudad:", self.input_ciudad)
        form.addRow("Teléfono:", self.input_telefono)
        form.addRow("Email:", self.input_email)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addLayout(form)
        layout.addWidget(panel_logo)

        return card

    def crear_seccion_sistema(self):
        card = QFrame()
        card.setObjectName("subPanelConfig")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Parámetros del sistema")
        titulo.setObjectName("seccionTitulo")

        ayuda = QLabel(
            "Define la moneda, impuesto y mensaje que se usará en los comprobantes."
        )
        ayuda.setObjectName("textoAyuda")
        ayuda.setWordWrap(True)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.input_moneda = self.crear_input("CLP")
        self.input_moneda.setText("CLP")
        self.input_moneda.setMaxLength(6)

        self.input_impuesto = QDoubleSpinBox()
        self.configurar_spinbox_configuracion(
            self.input_impuesto,
            decimales=2,
            minimo=0,
            maximo=100,
            paso=1,
            sufijo=" %",
            ancho=260,
        )
        self.input_impuesto.setValue(19)

        control_impuesto = self.crear_control_spinbox(self.input_impuesto)

        self.input_mensaje_ticket = QTextEdit()
        self.input_mensaje_ticket.setFixedHeight(120)
        self.input_mensaje_ticket.setPlaceholderText("Ej: Gracias por su compra")

        form.addRow("Moneda:", self.input_moneda)
        form.addRow("Impuesto:", control_impuesto)
        form.addRow("Mensaje ticket:", self.input_mensaje_ticket)

        nota = QLabel(
            "Recomendación: para Chile usa moneda CLP e impuesto 19%. "
            "El mensaje del ticket debe ser breve y fácil de leer."
        )
        nota.setWordWrap(True)
        nota.setStyleSheet("""
            QLabel {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                padding: 12px;
                color: #1D4ED8;
                font-size: 13px;
                font-weight: 700;
            }
        """)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addLayout(form)
        layout.addWidget(nota)
        layout.addStretch()

        return card

    def crear_input(self, placeholder):
        input_texto = QLineEdit()
        input_texto.setPlaceholderText(placeholder)
        input_texto.setMinimumHeight(42)
        return input_texto

    def configurar_spinbox_configuracion(
        self,
        spinbox,
        decimales=0,
        minimo=0,
        maximo=999999999,
        paso=1,
        prefijo="",
        sufijo="",
        ancho=220,
    ):
        spinbox.setMinimum(minimo)
        spinbox.setMaximum(maximo)
        spinbox.setDecimals(decimales)
        spinbox.setSingleStep(paso)
        spinbox.setPrefix(prefijo)
        spinbox.setSuffix(sufijo)
        spinbox.setFixedWidth(ancho)
        spinbox.setMinimumHeight(38)
        spinbox.setMaximumHeight(38)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setAccelerated(True)
        spinbox.setKeyboardTracking(False)
        spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

    def crear_control_spinbox(self, spinbox):
        contenedor = QFrame()
        contenedor.setObjectName("controlSpinConfiguracion")
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

    def crear_vista_ticket(self):
        card = QFrame()
        card.setObjectName("panelTicket")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(24)

        textos = QVBoxLayout()
        textos.setSpacing(10)

        titulo = QLabel("Vista referencial del ticket")
        titulo.setObjectName("seccionTitulo")

        ayuda = QLabel(
            "Previsualización en vivo de cómo se verán los datos principales en el comprobante."
        )
        ayuda.setObjectName("textoAyuda")
        ayuda.setWordWrap(True)

        btn_copiar = QPushButton("Copiar datos del ticket")
        btn_copiar.setMinimumHeight(42)
        btn_copiar.setFixedWidth(190)
        btn_copiar.clicked.connect(self.copiar_datos_ticket)

        textos.addWidget(titulo)
        textos.addWidget(ayuda)
        textos.addStretch()
        textos.addWidget(btn_copiar)

        ticket = QFrame()
        ticket.setObjectName("ticketPreview")
        ticket.setFixedWidth(360)

        ticket_layout = QVBoxLayout(ticket)
        ticket_layout.setContentsMargins(22, 22, 22, 22)
        ticket_layout.setSpacing(8)

        self.ticket_logo = QLabel("LOGO")
        self.ticket_logo.setObjectName("ticketLogo")
        self.ticket_logo.setFixedSize(120, 70)
        self.ticket_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ticket_nombre = QLabel("NOMBRE NEGOCIO")
        self.ticket_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_nombre.setWordWrap(True)
        self.ticket_nombre.setObjectName("ticketNombre")

        self.ticket_giro = QLabel("Giro comercial")
        self.ticket_giro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_giro.setWordWrap(True)
        self.ticket_giro.setObjectName("ticketTexto")

        self.ticket_rut = QLabel("RUT: -")
        self.ticket_rut.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_rut.setObjectName("ticketTexto")

        self.ticket_direccion = QLabel("Dirección, comuna, ciudad")
        self.ticket_direccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_direccion.setWordWrap(True)
        self.ticket_direccion.setObjectName("ticketTexto")

        self.ticket_contacto = QLabel("Teléfono / Email")
        self.ticket_contacto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_contacto.setWordWrap(True)
        self.ticket_contacto.setObjectName("ticketTexto")

        linea_1 = QLabel("--------------------------------")
        linea_1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ejemplo = QLabel("Producto demo x1     $1.990\nTOTAL                $1.990")
        ejemplo.setObjectName("ticketTexto")
        ejemplo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ticket_impuesto = QLabel("Impuesto configurado: 19%")
        self.ticket_impuesto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_impuesto.setObjectName("ticketTexto")

        linea_2 = QLabel("--------------------------------")
        linea_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ticket_mensaje = QLabel("Gracias por su compra")
        self.ticket_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ticket_mensaje.setWordWrap(True)
        self.ticket_mensaje.setObjectName("ticketMensaje")

        ticket_layout.addWidget(self.ticket_logo, 0, Qt.AlignmentFlag.AlignCenter)
        ticket_layout.addWidget(self.ticket_nombre)
        ticket_layout.addWidget(self.ticket_giro)
        ticket_layout.addWidget(self.ticket_rut)
        ticket_layout.addWidget(self.ticket_direccion)
        ticket_layout.addWidget(self.ticket_contacto)
        ticket_layout.addWidget(linea_1)
        ticket_layout.addWidget(ejemplo)
        ticket_layout.addWidget(self.ticket_impuesto)
        ticket_layout.addWidget(linea_2)
        ticket_layout.addWidget(self.ticket_mensaje)

        layout.addLayout(textos, 1)
        layout.addWidget(ticket)

        return card

    # ============================================================
    # LOGO
    # ============================================================

    def obtener_directorio_logos(self):
        base = os.getenv("LOCALAPPDATA")

        if base:
            carpeta = Path(base) / "CorePOS" / "logos"
        else:
            carpeta = Path.home() / ".corepos" / "logos"

        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta

    def seleccionar_logo_negocio(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar logo del negocio",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )

        if not ruta:
            return

        origen = Path(ruta)

        if not origen.exists():
            QMessageBox.warning(self, "Logo", "No se encontró el archivo seleccionado.")
            return

        try:
            carpeta_logos = self.obtener_directorio_logos()
            extension = origen.suffix.lower() or ".png"
            destino = carpeta_logos / f"logo_negocio_{int(time.time())}{extension}"

            shutil.copy2(str(origen), str(destino))

            self.input_logo.setText(str(destino))
            self.actualizar_preview_logo_negocio()
            self.actualizar_logo_ticket(str(destino))
            self.marcar_cambios()

        except Exception as error:
            QMessageBox.warning(
                self,
                "Error al cargar logo",
                f"No se pudo copiar el logo al sistema:\n{error}",
            )

    def quitar_logo_negocio(self):
        if not self.input_logo.text().strip():
            return

        confirmar = QMessageBox.question(
            self,
            "Quitar logo",
            "¿Deseas quitar el logo configurado para este negocio?",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        self.input_logo.clear()
        self.actualizar_preview_logo_negocio()
        self.actualizar_logo_ticket("")
        self.marcar_cambios()

    def cargar_pixmap_logo(self, ruta_logo, ancho, alto):
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

    def actualizar_preview_logo_negocio(self):
        if self.logo_preview is None:
            return

        ruta_logo = self.input_logo.text().strip() if self.input_logo else ""
        pixmap = self.cargar_pixmap_logo(ruta_logo, 116, 76)

        if pixmap:
            self.logo_preview.setPixmap(pixmap)
            self.logo_preview.setText("")
            self.logo_preview.setToolTip(ruta_logo)
            return

        self.logo_preview.setPixmap(QPixmap())

        if ruta_logo.lower().startswith(("http://", "https://")):
            self.logo_preview.setText("Logo por URL")
            self.logo_preview.setToolTip(ruta_logo)
        else:
            self.logo_preview.setText("Sin logo")
            self.logo_preview.setToolTip("")

    def actualizar_logo_ticket(self, ruta_logo):
        if self.ticket_logo is None:
            return

        pixmap = self.cargar_pixmap_logo(ruta_logo, 110, 62)

        if pixmap:
            self.ticket_logo.setPixmap(pixmap)
            self.ticket_logo.setText("")
            self.ticket_logo.show()
            return

        self.ticket_logo.setPixmap(QPixmap())
        self.ticket_logo.setText("LOGO")
        self.ticket_logo.show()

    # ============================================================
    # CARGA Y GUARDADO
    # ============================================================

    def cargar_configuracion(self):
        self.bloqueando_cambios = True

        try:
            resultado = self.pos.obtener_configuracion()
        except Exception as error:
            resultado = {
                "ok": False,
                "mensaje": f"No se pudo obtener configuración: {error}",
                "data": None,
            }

        if not resultado.get("ok"):
            self.establecer_configuracion_default()
            self.config_original = self.obtener_datos_formulario()
            self.hay_cambios = False
            self.actualizar_todo_desde_formulario()
            self.actualizar_estado_operacion(
                resultado.get("mensaje", "No se encontró configuración. Puedes crearla guardando esta pantalla."),
                "alerta",
            )
            self.bloqueando_cambios = False
            self.actualizar_label_ultima_carga()
            self.actualizar_estado_botones()
            return

        config = resultado.get("data") or {}
        self.aplicar_configuracion_formulario(config)

        self.config_original = self.obtener_datos_formulario()
        self.hay_cambios = False

        self.actualizar_todo_desde_formulario()
        self.actualizar_estado_operacion("Configuración cargada correctamente.", "ok")

        self.bloqueando_cambios = False
        self.actualizar_label_ultima_carga()
        self.actualizar_estado_botones()

    def establecer_configuracion_default(self):
        self.input_nombre.setText("")
        self.input_rut.setText("")
        self.input_giro.setText("")
        self.input_direccion.setText("")
        self.input_comuna.setText("")
        self.input_ciudad.setText("")
        self.input_telefono.setText("")
        self.input_email.setText("")
        self.input_logo.setText("")
        self.input_moneda.setText("CLP")
        self.input_impuesto.setValue(19)
        self.input_mensaje_ticket.setPlainText("Gracias por su compra")

    def aplicar_configuracion_formulario(self, config):
        self.input_nombre.setText(str(config.get("nombre_negocio") or ""))
        self.input_rut.setText(str(config.get("rut") or ""))
        self.input_giro.setText(str(config.get("giro") or ""))
        self.input_direccion.setText(str(config.get("direccion") or ""))
        self.input_comuna.setText(str(config.get("comuna") or ""))
        self.input_ciudad.setText(str(config.get("ciudad") or ""))
        self.input_telefono.setText(str(config.get("telefono") or ""))
        self.input_email.setText(str(config.get("email") or ""))
        self.input_logo.setText(str(config.get("logo_url") or ""))
        self.input_moneda.setText(str(config.get("moneda") or "CLP"))

        try:
            impuesto = float(Decimal(str(config.get("impuesto_porcentaje") or 19)))
            self.input_impuesto.setValue(impuesto)
        except Exception:
            self.input_impuesto.setValue(19)

        self.input_mensaje_ticket.setPlainText(
            str(config.get("mensaje_ticket") or "Gracias por su compra")
        )

    def guardar_configuracion(self):
        valido, errores = self.validar_formulario()

        if not valido:
            QMessageBox.warning(
                self,
                "Revisar configuración",
                "\n".join(errores),
            )
            return

        datos = self.obtener_datos_formulario()

        try:
            resultado = self.pos.actualizar_configuracion(
                nombre_negocio=datos["nombre_negocio"],
                rut=datos["rut"],
                giro=datos["giro"],
                direccion=datos["direccion"],
                comuna=datos["comuna"],
                ciudad=datos["ciudad"],
                telefono=datos["telefono"],
                email=datos["email"],
                logo_url=datos["logo_url"],
                moneda=datos["moneda"],
                impuesto_porcentaje=datos["impuesto_porcentaje"],
                mensaje_ticket=datos["mensaje_ticket"],
            )
        except Exception as error:
            resultado = {
                "ok": False,
                "mensaje": f"No se pudo guardar configuración: {error}",
            }

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo guardar la configuración."),
            )
            return

        self.config_original = datos
        self.hay_cambios = False

        self.actualizar_todo_desde_formulario()
        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Configuración guardada correctamente."),
            "ok",
        )
        self.actualizar_estado_botones()

        QMessageBox.information(
            self,
            "Configuración guardada",
            resultado.get("mensaje", "Configuración guardada correctamente."),
        )

    def descartar_cambios(self):
        if self.hay_cambios:
            confirmar = QMessageBox.question(
                self,
                "Descartar cambios",
                "¿Seguro que deseas descartar los cambios no guardados?",
            )

            if confirmar != QMessageBox.StandardButton.Yes:
                return

        self.cargar_configuracion()

    # ============================================================
    # CAMBIOS EN VIVO
    # ============================================================

    def conectar_senales(self):
        inputs_texto = [
            self.input_nombre,
            self.input_rut,
            self.input_giro,
            self.input_direccion,
            self.input_comuna,
            self.input_ciudad,
            self.input_telefono,
            self.input_email,
            self.input_logo,
            self.input_moneda,
        ]

        for input_texto in inputs_texto:
            input_texto.textChanged.connect(self.marcar_cambios)

        self.input_impuesto.valueChanged.connect(self.marcar_cambios)
        self.input_mensaje_ticket.textChanged.connect(self.marcar_cambios)

    def marcar_cambios(self, *args):
        if self.bloqueando_cambios:
            return

        self.hay_cambios = True
        self.actualizar_todo_desde_formulario()
        self.actualizar_estado_operacion("Hay cambios sin guardar.", "alerta")
        self.actualizar_estado_botones()

    def actualizar_todo_desde_formulario(self):
        self.actualizar_cards()
        self.actualizar_preview_logo_negocio()
        self.actualizar_vista_ticket()
        self.actualizar_alertas()

    def actualizar_cards(self):
        datos = self.obtener_datos_formulario()

        nombre = datos["nombre_negocio"] or "-"
        rut = datos["rut"] or "-"
        ciudad = datos["ciudad"] or "-"
        moneda = datos["moneda"] or "CLP"
        impuesto = datos["impuesto_porcentaje"]
        telefono = datos["telefono"]
        email = datos["email"]
        mensaje = datos["mensaje_ticket"]

        contacto = "Completo" if telefono and email else "Parcial" if telefono or email else "Pendiente"
        ticket = "OK" if mensaje else "Pendiente"

        self.labels["negocio"].setText(self.recortar(nombre, 36))
        self.labels["rut"].setText(self.recortar(rut, 18))
        self.labels["ciudad"].setText(self.recortar(ciudad, 18))
        self.labels["moneda"].setText(self.recortar(moneda, 10))
        self.labels["impuesto"].setText(f"{impuesto:.2f}%")
        self.labels["contacto"].setText(contacto)
        self.labels["ticket"].setText(ticket)

        if self.hay_cambios:
            self.labels["estado"].setText("Sin guardar")
            self.cambiar_tipo_card("estado", "alerta")
        else:
            self.labels["estado"].setText("Sin cambios")
            self.cambiar_tipo_card("estado", "verde")

        if not datos["nombre_negocio"]:
            self.cambiar_tipo_card("negocio", "rojo")
        else:
            self.cambiar_tipo_card("negocio", "azul")

        if contacto == "Completo":
            self.cambiar_tipo_card("contacto", "verde")
        elif contacto == "Parcial":
            self.cambiar_tipo_card("contacto", "alerta")
        else:
            self.cambiar_tipo_card("contacto", "rojo")

        self.cambiar_tipo_card("ticket", "verde" if mensaje else "alerta")

    def actualizar_vista_ticket(self):
        datos = self.obtener_datos_formulario()

        nombre = datos["nombre_negocio"] or "NOMBRE NEGOCIO"
        giro = datos["giro"] or "Giro comercial"
        rut = datos["rut"] or "-"

        direccion_partes = [
            datos["direccion"],
            datos["comuna"],
            datos["ciudad"],
        ]
        direccion = ", ".join([parte for parte in direccion_partes if parte]) or "Dirección, comuna, ciudad"

        contacto_partes = [
            datos["telefono"],
            datos["email"],
        ]
        contacto = " / ".join([parte for parte in contacto_partes if parte]) or "Teléfono / Email"

        mensaje = datos["mensaje_ticket"] or "Gracias por su compra"
        impuesto = datos["impuesto_porcentaje"]
        logo = datos.get("logo_url") or ""

        self.actualizar_logo_ticket(logo)
        self.ticket_nombre.setText(nombre.upper())
        self.ticket_giro.setText(giro)
        self.ticket_rut.setText(f"RUT: {rut}")
        self.ticket_direccion.setText(direccion)
        self.ticket_contacto.setText(contacto)
        self.ticket_mensaje.setText(mensaje)
        self.ticket_impuesto.setText(f"Impuesto configurado: {impuesto:.2f}%")

    def actualizar_alertas(self):
        datos = self.obtener_datos_formulario()
        alertas = []

        if not datos["nombre_negocio"]:
            alertas.append("Falta el nombre del negocio.")

        if not datos["rut"]:
            alertas.append("RUT no ingresado.")

        if datos["email"] and "@" not in datos["email"]:
            alertas.append("El email no parece válido.")

        if not datos["telefono"] and not datos["email"]:
            alertas.append("No hay teléfono ni email de contacto.")

        if not datos["direccion"]:
            alertas.append("Dirección no ingresada.")

        if not datos["mensaje_ticket"]:
            alertas.append("Mensaje del ticket vacío.")

        if not alertas:
            self.label_alertas.setText("Configuración completa: datos principales listos para tickets y reportes.")
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de configuración: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def actualizar_estado_botones(self):
        if self.btn_guardar is not None:
            self.btn_guardar.setEnabled(self.hay_cambios)

        if self.btn_descartar is not None:
            self.btn_descartar.setEnabled(self.hay_cambios)

    def actualizar_label_ultima_carga(self):
        hora = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_carga.setText(f"Última carga: {hora}")

    # ============================================================
    # DATOS Y VALIDACIONES
    # ============================================================

    def obtener_datos_formulario(self):
        return {
            "nombre_negocio": self.input_nombre.text().strip(),
            "rut": self.input_rut.text().strip(),
            "giro": self.input_giro.text().strip(),
            "direccion": self.input_direccion.text().strip(),
            "comuna": self.input_comuna.text().strip(),
            "ciudad": self.input_ciudad.text().strip(),
            "telefono": self.input_telefono.text().strip(),
            "email": self.input_email.text().strip(),
            "logo_url": self.input_logo.text().strip(),
            "moneda": self.input_moneda.text().strip().upper() or "CLP",
            "impuesto_porcentaje": Decimal(str(self.input_impuesto.value())),
            "mensaje_ticket": self.input_mensaje_ticket.toPlainText().strip() or "Gracias por su compra",
        }

    def validar_formulario(self):
        datos = self.obtener_datos_formulario()
        errores = []

        if not datos["nombre_negocio"]:
            errores.append("Debe ingresar el nombre del negocio.")

        if datos["email"] and "@" not in datos["email"]:
            errores.append("El email ingresado no parece válido.")

        if not datos["moneda"]:
            errores.append("Debe ingresar la moneda del sistema.")

        if datos["impuesto_porcentaje"] < 0:
            errores.append("El impuesto no puede ser negativo.")

        logo = datos["logo_url"]

        if logo and not logo.lower().startswith(("http://", "https://")):
            if not Path(logo).exists():
                errores.append("La ruta del logo guardado no existe. Selecciona nuevamente el logo o quítalo.")

        return len(errores) == 0, errores

    def copiar_datos_ticket(self):
        datos = self.obtener_datos_formulario()

        texto = "\n".join([
            datos["nombre_negocio"] or "NOMBRE NEGOCIO",
            f"RUT: {datos['rut'] or '-'}",
            f"Giro: {datos['giro'] or '-'}",
            f"Dirección: {datos['direccion'] or '-'}",
            f"Comuna/Ciudad: {datos['comuna'] or '-'} / {datos['ciudad'] or '-'}",
            f"Teléfono: {datos['telefono'] or '-'}",
            f"Email: {datos['email'] or '-'}",
            f"Logo: {datos['logo_url'] or '-'}",
            f"Moneda: {datos['moneda']}",
            f"Impuesto: {datos['impuesto_porcentaje']:.2f}%",
            f"Mensaje ticket: {datos['mensaje_ticket']}",
        ])

        QApplication.clipboard().setText(texto)
        self.actualizar_estado_operacion("Datos del ticket copiados al portapapeles.", "ok")

    # ============================================================
    # UTILIDADES
    # ============================================================

    def recortar(self, texto, largo):
        texto = str(texto or "")

        if len(texto) <= largo:
            return texto

        return texto[:largo - 3] + "..."

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
            QWidget {
                background-color: #F1F5F9;
                color: #0F172A;
                font-family: Segoe UI, Arial;
            }

            QLabel#tituloPagina {
                color: #0F172A;
                font-size: 30px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#subtituloPagina {
                color: #64748B;
                font-size: 14px;
                font-weight: 600;
                background-color: transparent;
            }

            QFrame#panelConfiguracion,
            QFrame#panelTicket {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#subPanelConfig {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#panelLogoNegocio {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }

            QLabel#logoPreview {
                background-color: #F8FAFC;
                border: 1px dashed #94A3B8;
                border-radius: 12px;
                color: #64748B;
                font-size: 12px;
                font-weight: 800;
            }

            QFrame#controlSpinConfiguracion {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 14px;
            }

            QFrame#controlSpinConfiguracion:hover {
                border: 1px solid #94A3B8;
            }

            QFrame#cardConfig {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardConfig[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardConfig[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardConfig[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardConfig[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardConfig[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardConfig[tipo="neutro"] {
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
                font-size: 24px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#cardValorNegocio {
                color: #0F172A;
                font-size: 19px;
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
                font-size: 18px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#textoAyuda {
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
                background-color: transparent;
            }

            QLineEdit,
            QTextEdit,
            QDoubleSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px;
                color: #0F172A;
                font-size: 13px;
                font-weight: 600;
            }

            QLineEdit:read-only {
                background-color: #F8FAFC;
                color: #475569;
            }

            QLineEdit:focus,
            QTextEdit:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }

            QFormLayout QLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 700;
                background-color: transparent;
            }

            QPushButton {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 800;
            }

            QPushButton:hover {
                background-color: #F8FAFC;
                border: 1px solid #94A3B8;
            }

            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #94A3B8;
                border: 1px solid #CBD5E1;
            }

            QPushButton#botonPrincipal {
                background-color: #2563EB;
                color: #FFFFFF;
                border: 1px solid #1D4ED8;
            }

            QPushButton#botonPrincipal:hover {
                background-color: #1D4ED8;
            }

            QPushButton#botonMiniSpin {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 0px;
                font-size: 18px;
                font-weight: 900;
            }

            QPushButton#botonMiniSpin:hover {
                background-color: #E2E8F0;
            }

            QFrame#ticketPreview {
                background-color: #FFFFFF;
                border: 1px dashed #94A3B8;
                border-radius: 14px;
            }

            QLabel#ticketLogo {
                background-color: transparent;
                border: none;
                color: #94A3B8;
                font-size: 11px;
                font-weight: 900;
            }

            QLabel#ticketNombre {
                color: #0F172A;
                font-size: 16px;
                font-weight: 900;
                background-color: transparent;
            }

            QLabel#ticketTexto {
                color: #334155;
                font-size: 12px;
                font-weight: 600;
                background-color: transparent;
            }

            QLabel#ticketMensaje {
                color: #0F172A;
                font-size: 13px;
                font-weight: 800;
                background-color: transparent;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
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