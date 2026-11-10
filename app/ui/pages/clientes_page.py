from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QCheckBox,
    QFrame,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.clientes import (
    listar_clientes,
    buscar_clientes,
    crear_cliente,
    actualizar_cliente,
    activar_cliente,
    desactivar_cliente,
)


class ItemClienteOrdenable(QTableWidgetItem):
    def __lt__(self, otro):
        valor_actual = self.data(Qt.ItemDataRole.UserRole)
        valor_otro = otro.data(Qt.ItemDataRole.UserRole)

        if valor_actual is not None and valor_otro is not None:
            try:
                return Decimal(str(valor_actual)) < Decimal(str(valor_otro))
            except Exception:
                return str(valor_actual).lower() < str(valor_otro).lower()

        return self.text().lower() < otro.text().lower()


class ClientesServiceAdapter:
    def _normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return {
            "ok": True,
            "mensaje": mensaje_ok,
            "data": resultado,
        }

    def obtener_clientes(self, texto="", solo_activos=True):
        texto = str(texto or "").strip()

        if texto:
            resultado = buscar_clientes(texto=texto, solo_activos=solo_activos)
        else:
            resultado = listar_clientes(solo_activos=solo_activos)

        return self._normalizar_respuesta(
            resultado,
            "Clientes obtenidos correctamente.",
        )

    def crear_cliente_sistema(
        self,
        nombre,
        rut=None,
        telefono=None,
        email=None,
        direccion=None,
        notas=None,
    ):
        resultado = crear_cliente(
            nombre=nombre,
            rut=rut,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
        )

        return self._normalizar_respuesta(
            resultado,
            "Cliente creado correctamente.",
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
        activo=1,
    ):
        resultado = actualizar_cliente(
            cliente_id=cliente_id,
            nombre=nombre,
            rut=rut,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
            activo=activo,
        )

        return self._normalizar_respuesta(
            resultado,
            "Cliente actualizado correctamente.",
        )

    def activar_cliente_sistema(self, cliente_id):
        resultado = activar_cliente(cliente_id)
        return self._normalizar_respuesta(
            resultado,
            "Cliente activado correctamente.",
        )

    def desactivar_cliente_sistema(self, cliente_id):
        resultado = desactivar_cliente(cliente_id)
        return self._normalizar_respuesta(
            resultado,
            "Cliente desactivado correctamente.",
        )


class ClienteDialog(QDialog):
    def __init__(self, pos_service, cliente=None, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.cliente = cliente

        self.setWindowTitle("Editar cliente" if cliente else "Crear cliente")
        self.setMinimumWidth(620)

        self.input_nombre = None
        self.input_rut = None
        self.input_telefono = None
        self.input_email = None
        self.input_direccion = None
        self.input_notas = None
        self.check_activo = None

        self.construir_interfaz()
        self.cargar_datos()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo_texto = "Editar cliente" if self.cliente else "Crear cliente"

        titulo = QLabel(titulo_texto)
        titulo.setStyleSheet("""
            QLabel {
                font-size: 25px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        ayuda = QLabel(
            "Registra los datos del cliente para futuras ventas, contacto y seguimiento comercial."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        layout.addWidget(titulo)
        layout.addWidget(ayuda)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Cliente Test 01")

        self.input_rut = QLineEdit()
        self.input_rut.setPlaceholderText("Ej: 11111111-1")

        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Ej: +56912345678")

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ej: cliente@email.cl")

        self.input_direccion = QLineEdit()
        self.input_direccion.setPlaceholderText("Ej: Calle Cliente 123")

        self.input_notas = QTextEdit()
        self.input_notas.setFixedHeight(95)
        self.input_notas.setPlaceholderText(
            "Notas internas: preferencias, historial futuro, observaciones comerciales, etc."
        )

        self.check_activo = QCheckBox("Cliente activo")
        self.check_activo.setChecked(True)

        for widget in [
            self.input_nombre,
            self.input_rut,
            self.input_telefono,
            self.input_email,
            self.input_direccion,
        ]:
            widget.setMinimumHeight(40)

        form.addRow("Nombre *:", self.input_nombre)
        form.addRow("RUT:", self.input_rut)
        form.addRow("Teléfono:", self.input_telefono)
        form.addRow("Email:", self.input_email)
        form.addRow("Dirección:", self.input_direccion)
        form.addRow("Notas:", self.input_notas)
        form.addRow("", self.check_activo)

        botones = QHBoxLayout()
        botones.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar cliente")
        btn_guardar.setObjectName("botonPrincipal")
        btn_guardar.clicked.connect(self.guardar)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addLayout(form)
        layout.addLayout(botones)

        self.setStyleSheet("""
            QLineEdit,
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus,
            QTextEdit:focus {
                border: 1px solid #2563EB;
            }

            QCheckBox {
                color: #334155;
                font-size: 14px;
                font-weight: 700;
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
        """)

    def cargar_datos(self):
        if not self.cliente:
            return

        self.input_nombre.setText(str(self.cliente.get("nombre") or ""))
        self.input_rut.setText(str(self.cliente.get("rut") or ""))
        self.input_telefono.setText(str(self.cliente.get("telefono") or ""))
        self.input_email.setText(str(self.cliente.get("email") or ""))
        self.input_direccion.setText(str(self.cliente.get("direccion") or ""))
        self.input_notas.setPlainText(str(self.cliente.get("notas") or ""))
        self.check_activo.setChecked(int(self.cliente.get("activo") or 0) == 1)

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text().strip(),
            "rut": self.input_rut.text().strip(),
            "telefono": self.input_telefono.text().strip(),
            "email": self.input_email.text().strip(),
            "direccion": self.input_direccion.text().strip(),
            "notas": self.input_notas.toPlainText().strip(),
            "activo": 1 if self.check_activo.isChecked() else 0,
        }

    def guardar(self):
        datos = self.obtener_datos()

        if not datos["nombre"]:
            QMessageBox.warning(
                self,
                "Dato obligatorio",
                "Debe ingresar el nombre del cliente.",
            )
            self.input_nombre.setFocus()
            return

        if datos["email"] and "@" not in datos["email"]:
            QMessageBox.warning(
                self,
                "Email inválido",
                "El email ingresado no parece válido.",
            )
            self.input_email.setFocus()
            return

        if self.cliente:
            resultado = self.pos.actualizar_cliente_sistema(
                cliente_id=self.cliente.get("id"),
                nombre=datos["nombre"],
                rut=datos["rut"],
                telefono=datos["telefono"],
                email=datos["email"],
                direccion=datos["direccion"],
                notas=datos["notas"],
                activo=datos["activo"],
            )
        else:
            resultado = self.pos.crear_cliente_sistema(
                nombre=datos["nombre"],
                rut=datos["rut"],
                telefono=datos["telefono"],
                email=datos["email"],
                direccion=datos["direccion"],
                notas=datos["notas"],
            )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo guardar el cliente."),
            )
            return

        QMessageBox.information(
            self,
            "Cliente guardado",
            resultado.get("mensaje", "Cliente guardado correctamente."),
        )
        self.accept()


class ClientesPage(QWidget):
    def __init__(self, pos_service=None):
        super().__init__()

        self.pos = pos_service or ClientesServiceAdapter()

        self.actualizando_clientes = False
        self.timer_clientes = None

        self.clientes_actuales = []
        self.clientes_visibles = []
        self.filtro_columna = None
        self.filtro_valor = None

        self.input_busqueda = None
        self.check_mostrar_inactivos = None
        self.tabla_clientes = QTableWidget()

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.labels = {}
        self.cards = {}

        self.btn_detalle = None
        self.btn_editar = None
        self.btn_activar = None
        self.btn_desactivar = None
        self.btn_copiar = None

        self.construir_interfaz()
        self.cargar_clientes(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_clientes = QTimer(self)
        self.timer_clientes.timeout.connect(self.cargar_clientes_automatico)
        self.timer_clientes.start(10000)

    def cargar_clientes_automatico(self):
        if self.actualizando_clientes:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_clientes(mostrar_mensaje=False)

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

        titulo = QLabel("Clientes")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Administra clientes frecuentes, datos de contacto, estado comercial y seguimiento futuro."
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

        btn_nuevo = QPushButton("Nuevo cliente")
        btn_nuevo.setObjectName("botonPrincipal")
        btn_nuevo.setMinimumHeight(46)
        btn_nuevo.setFixedWidth(180)
        btn_nuevo.clicked.connect(self.crear_cliente)

        encabezado.addLayout(textos, 1)
        encabezado.addStretch()
        encabezado.addLayout(estado_actualizacion)
        encabezado.addSpacing(12)
        encabezado.addWidget(btn_nuevo)

        layout.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["total"] = self.crear_card(
            cards, 0, 0,
            key="total",
            titulo="Total clientes",
            valor="0",
            detalle="Clientes registrados",
            tipo="azul",
        )

        self.labels["activos"] = self.crear_card(
            cards, 0, 1,
            key="activos",
            titulo="Activos",
            valor="0",
            detalle="Disponibles para ventas futuras",
            tipo="verde",
        )

        self.labels["inactivos"] = self.crear_card(
            cards, 0, 2,
            key="inactivos",
            titulo="Inactivos",
            valor="0",
            detalle="Ocultos si no marcas mostrar inactivos",
            tipo="rojo",
        )

        self.labels["visibles"] = self.crear_card(
            cards, 0, 3,
            key="visibles",
            titulo="Resultados visibles",
            valor="0",
            detalle="Según búsqueda y filtros",
            tipo="neutro",
        )

        self.labels["con_telefono"] = self.crear_card(
            cards, 1, 0,
            key="con_telefono",
            titulo="Con teléfono",
            valor="0",
            detalle="Contactables por llamada o WhatsApp",
            tipo="neutro",
        )

        self.labels["con_email"] = self.crear_card(
            cards, 1, 1,
            key="con_email",
            titulo="Con email",
            valor="0",
            detalle="Contactables por correo",
            tipo="neutro",
        )

        self.labels["sin_contacto"] = self.crear_card(
            cards, 1, 2,
            key="sin_contacto",
            titulo="Sin contacto",
            valor="0",
            detalle="Sin teléfono ni email",
            tipo="alerta",
        )

        self.labels["completitud"] = self.crear_card(
            cards, 1, 3,
            key="completitud",
            titulo="Datos completos",
            valor="0%",
            detalle="Nombre + teléfono/email",
            tipo="morado",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de clientes...")
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

        panel_busqueda = QFrame()
        panel_busqueda.setObjectName("panelBusquedaClientes")

        barra = QHBoxLayout(panel_busqueda)
        barra.setContentsMargins(16, 14, 16, 14)
        barra.setSpacing(12)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText(
            "Buscar por nombre, RUT, teléfono, email o dirección..."
        )
        self.input_busqueda.setMinimumHeight(44)
        self.input_busqueda.textChanged.connect(self.aplicar_filtro)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setMinimumHeight(44)
        btn_limpiar.setFixedWidth(140)
        btn_limpiar.clicked.connect(self.limpiar_busqueda)

        self.check_mostrar_inactivos = QCheckBox("Mostrar inactivos")
        self.check_mostrar_inactivos.stateChanged.connect(
            lambda: self.cargar_clientes(mostrar_mensaje=False)
        )

        barra.addWidget(self.input_busqueda, 1)
        barra.addWidget(btn_limpiar)
        barra.addWidget(self.check_mostrar_inactivos)

        layout.addWidget(panel_busqueda)

        titulo_tabla = QLabel("Listado de clientes")
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

        self.tabla_clientes.setColumnCount(7)
        self.tabla_clientes.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "RUT",
            "Teléfono",
            "Email",
            "Dirección",
            "Estado",
        ])
        self.preparar_tabla()
        self.tabla_clientes.itemSelectionChanged.connect(self.actualizar_botones_accion)
        self.tabla_clientes.cellDoubleClicked.connect(self.filtrar_por_celda)

        layout.addWidget(self.tabla_clientes)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        self.btn_detalle = QPushButton("Ver detalle")
        self.btn_detalle.setMinimumHeight(44)
        self.btn_detalle.clicked.connect(self.ver_detalle)

        self.btn_editar = QPushButton("Editar cliente")
        self.btn_editar.setObjectName("botonPrincipal")
        self.btn_editar.setMinimumHeight(44)
        self.btn_editar.clicked.connect(self.editar_cliente)

        self.btn_copiar = QPushButton("Copiar datos")
        self.btn_copiar.setMinimumHeight(44)
        self.btn_copiar.clicked.connect(self.copiar_cliente)

        self.btn_activar = QPushButton("Activar")
        self.btn_activar.setMinimumHeight(44)
        self.btn_activar.clicked.connect(self.activar_cliente)

        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_desactivar.setObjectName("botonPeligro")
        self.btn_desactivar.setMinimumHeight(44)
        self.btn_desactivar.clicked.connect(self.desactivar_cliente)

        acciones.addWidget(self.btn_detalle)
        acciones.addWidget(self.btn_editar)
        acciones.addWidget(self.btn_copiar)
        acciones.addWidget(self.btn_activar)
        acciones.addStretch()
        acciones.addWidget(self.btn_desactivar)

        layout.addLayout(acciones)

        self.label_estado_operacion = QLabel("Clientes listos para administrar.")
        self.label_estado_operacion.setWordWrap(True)
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

        self.aplicar_estilos()
        self.actualizar_botones_accion()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardCliente")
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
        self.tabla_clientes.setAlternatingRowColors(True)
        self.tabla_clientes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_clientes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_clientes.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_clientes.verticalHeader().setVisible(False)
        self.tabla_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_clientes.setMinimumHeight(390)
        self.tabla_clientes.setShowGrid(True)

        self.tabla_clientes.setSortingEnabled(True)
        self.tabla_clientes.horizontalHeader().setSectionsClickable(True)
        self.tabla_clientes.horizontalHeader().setSortIndicatorShown(True)
        self.tabla_clientes.horizontalHeader().sectionClicked.connect(self.aviso_ordenamiento_tabla)

    def cargar_clientes(self, mostrar_mensaje=False):
        if self.actualizando_clientes:
            return

        self.actualizando_clientes = True
        cliente_id_anterior = self.obtener_id_seleccionado_silencioso()

        try:
            resultado = self.obtener_clientes_desde_servicio()

            if not resultado.get("ok"):
                self.clientes_actuales = []
                self.clientes_visibles = []
                self.cargar_tabla([])
                self.actualizar_resumen([], [])
                self.actualizar_alertas([])
                self.actualizar_estado_operacion(
                    resultado.get("mensaje", "No se pudieron cargar los clientes."),
                    "error",
                )
                return

            clientes = resultado.get("data") or []

            if not self.check_mostrar_inactivos.isChecked():
                clientes_base = [
                    cliente for cliente in clientes
                    if int(cliente.get("activo") or 0) == 1
                ]
            else:
                clientes_base = clientes

            self.clientes_actuales = clientes
            self.clientes_visibles = self.filtrar_clientes_local(
                clientes_base,
                self.input_busqueda.text().strip(),
            )

            self.cargar_tabla(self.clientes_visibles)
            self.restaurar_seleccion(cliente_id_anterior)

            self.actualizar_resumen(clientes, self.clientes_visibles)
            self.actualizar_alertas(clientes)

            if mostrar_mensaje:
                self.actualizar_estado_operacion(
                    "Clientes cargados correctamente.",
                    "ok",
                )

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar clientes automáticamente: {error}",
                "error",
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_clientes = False
            self.actualizar_botones_accion()

    def obtener_clientes_desde_servicio(self):
        texto = ""
        solo_activos = False

        posibles_metodos = [
            "obtener_clientes",
            "obtener_clientes_sistema",
            "listar_clientes_sistema",
            "listar_clientes",
        ]

        ultimo_error = None

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(texto=texto, solo_activos=solo_activos)
            except TypeError:
                try:
                    resultado = metodo(solo_activos=solo_activos)
                except TypeError:
                    try:
                        resultado = metodo()
                    except Exception as error:
                        ultimo_error = error
                        continue
                except Exception as error:
                    ultimo_error = error
                    continue
            except Exception as error:
                ultimo_error = error
                continue

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            return {
                "ok": True,
                "mensaje": "Clientes cargados correctamente.",
                "data": resultado or [],
            }

        mensaje = "No existe un método para listar clientes en pos_service."

        if ultimo_error is not None:
            mensaje += f" Último error: {ultimo_error}"

        return {
            "ok": False,
            "mensaje": mensaje,
            "data": [],
        }

    def aplicar_filtro(self):
        if self.actualizando_clientes:
            return

        if not self.check_mostrar_inactivos.isChecked():
            clientes_base = [
                cliente for cliente in self.clientes_actuales
                if int(cliente.get("activo") or 0) == 1
            ]
        else:
            clientes_base = self.clientes_actuales

        self.clientes_visibles = self.filtrar_clientes_local(
            clientes_base,
            self.input_busqueda.text().strip(),
        )

        self.cargar_tabla(self.clientes_visibles)
        self.actualizar_resumen(self.clientes_actuales, self.clientes_visibles)
        self.actualizar_estado_operacion(
            f"Mostrando {len(self.clientes_visibles)} cliente(s).",
            "info",
        )
        self.actualizar_botones_accion()

    def limpiar_busqueda(self):
        self.input_busqueda.clear()
        self.filtro_columna = None
        self.filtro_valor = None
        self.input_busqueda.setFocus()
        self.aplicar_filtro()

        self.actualizar_estado_operacion(
            "Filtros limpiados. Mostrando todos los clientes.",
            "info",
        )

    def filtrar_clientes_local(self, clientes, texto):
        texto = str(texto or "").lower().strip()
        filtrados = []

        for cliente in clientes:
            campos = [
                cliente.get("id"),
                cliente.get("nombre"),
                cliente.get("rut"),
                cliente.get("telefono"),
                cliente.get("email"),
                cliente.get("direccion"),
                cliente.get("notas"),
                "ACTIVO" if int(cliente.get("activo") or 0) == 1 else "INACTIVO",
            ]

            texto_completo = " ".join(str(campo or "").lower() for campo in campos)

            if texto and texto not in texto_completo:
                continue

            if self.filtro_columna is not None and self.filtro_valor is not None:
                valor_visible, _ = self.obtener_valor_columna_cliente(
                    cliente,
                    self.filtro_columna,
                )

                if str(valor_visible).strip() != str(self.filtro_valor).strip():
                    continue

            filtrados.append(cliente)

        return filtrados

    def cargar_tabla(self, clientes):
        self.tabla_clientes.setSortingEnabled(False)
        self.tabla_clientes.setRowCount(0)

        if not clientes:
            self.tabla_clientes.setRowCount(1)

            item = QTableWidgetItem("No hay clientes para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_clientes.setItem(0, 0, item)

            for columna in range(1, self.tabla_clientes.columnCount()):
                self.tabla_clientes.setItem(0, columna, QTableWidgetItem(""))

            self.tabla_clientes.setSortingEnabled(False)
            return

        for fila, cliente in enumerate(clientes):
            self.tabla_clientes.insertRow(fila)

            activo = int(cliente.get("activo") or 0) == 1

            for columna in range(self.tabla_clientes.columnCount()):
                valor_visible, valor_orden = self.obtener_valor_columna_cliente(
                    cliente,
                    columna,
                )

                item = ItemClienteOrdenable(str(valor_visible or ""))
                item.setData(Qt.ItemDataRole.UserRole, valor_orden)

                if columna == 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                item.setToolTip(str(valor_visible or ""))

                if activo:
                    item.setBackground(QColor("#FFFFFF"))
                    item.setForeground(QColor("#0F172A"))
                else:
                    item.setBackground(QColor("#FEF2F2"))
                    item.setForeground(QColor("#991B1B"))

                self.tabla_clientes.setItem(fila, columna, item)

        self.tabla_clientes.setSortingEnabled(True)

    def obtener_valor_columna_cliente(self, cliente, columna):
        activo = int(cliente.get("activo") or 0) == 1
        estado = "ACTIVO" if activo else "INACTIVO"

        if columna == 0:
            valor = cliente.get("id") or 0
            try:
                return valor, int(valor)
            except Exception:
                return valor, 0

        if columna == 1:
            valor = cliente.get("nombre") or ""
            return valor, str(valor).lower()

        if columna == 2:
            valor = cliente.get("rut") or ""
            return valor, str(valor).lower()

        if columna == 3:
            valor = cliente.get("telefono") or ""
            return valor, str(valor).lower()

        if columna == 4:
            valor = cliente.get("email") or ""
            return valor, str(valor).lower()

        if columna == 5:
            valor = cliente.get("direccion") or ""
            return valor, str(valor).lower()

        if columna == 6:
            return estado, str(estado).lower()

        return "", ""

    def filtrar_por_celda(self, fila, columna):
        item = self.tabla_clientes.item(fila, columna)

        if item is None:
            return

        valor = item.text().strip()

        if not valor or valor == "No hay clientes para mostrar.":
            return

        encabezado = self.tabla_clientes.horizontalHeaderItem(columna)

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
        encabezado = self.tabla_clientes.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.actualizar_estado_operacion(
            f"Tabla ordenada por: {encabezado.text()}.",
            "info",
        )

    def actualizar_resumen(self, clientes_totales, clientes_visibles):
        total = len(clientes_totales)
        activos = 0
        inactivos = 0
        con_telefono = 0
        con_email = 0
        sin_contacto = 0
        completos = 0

        for cliente in clientes_totales:
            activo = int(cliente.get("activo") or 0) == 1

            if activo:
                activos += 1
            else:
                inactivos += 1

            tiene_telefono = bool(str(cliente.get("telefono") or "").strip())
            tiene_email = bool(str(cliente.get("email") or "").strip())

            if tiene_telefono:
                con_telefono += 1

            if tiene_email:
                con_email += 1

            if not tiene_telefono and not tiene_email:
                sin_contacto += 1

            if cliente.get("nombre") and (tiene_telefono or tiene_email):
                completos += 1

        completitud = 0

        if total > 0:
            completitud = round((completos / total) * 100)

        self.labels["total"].setText(str(total))
        self.labels["activos"].setText(str(activos))
        self.labels["inactivos"].setText(str(inactivos))
        self.labels["visibles"].setText(str(len(clientes_visibles)))
        self.labels["con_telefono"].setText(str(con_telefono))
        self.labels["con_email"].setText(str(con_email))
        self.labels["sin_contacto"].setText(str(sin_contacto))
        self.labels["completitud"].setText(f"{completitud}%")

        self.cambiar_tipo_card("inactivos", "rojo" if inactivos > 0 else "verde")
        self.cambiar_tipo_card("sin_contacto", "alerta" if sin_contacto > 0 else "verde")
        self.cambiar_tipo_card("completitud", "verde" if completitud >= 80 else "alerta")

    def actualizar_alertas(self, clientes):
        if not clientes:
            self.label_alertas.setText(
                "No hay clientes registrados. Crea clientes para asociarlos a ventas futuras."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))
            return

        sin_contacto = []
        inactivos = []

        for cliente in clientes:
            telefono = str(cliente.get("telefono") or "").strip()
            email = str(cliente.get("email") or "").strip()

            if not telefono and not email:
                sin_contacto.append(cliente)

            if int(cliente.get("activo") or 0) != 1:
                inactivos.append(cliente)

        alertas = []

        if sin_contacto:
            alertas.append(f"{len(sin_contacto)} cliente(s) sin teléfono ni email.")

        if inactivos:
            alertas.append(f"{len(inactivos)} cliente(s) inactivo(s).")

        if not alertas:
            self.label_alertas.setText(
                "Clientes en buen estado: todos tienen datos básicos de contacto."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de clientes: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def obtener_id_seleccionado_silencioso(self):
        fila = self.tabla_clientes.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla_clientes.item(fila, 0)

        if item_id is None:
            return None

        try:
            return int(item_id.text())
        except Exception:
            return None

    def restaurar_seleccion(self, cliente_id):
        if cliente_id is None:
            return

        for fila in range(self.tabla_clientes.rowCount()):
            item_id = self.tabla_clientes.item(fila, 0)

            if item_id and item_id.text().isdigit() and int(item_id.text()) == cliente_id:
                self.tabla_clientes.selectRow(fila)
                return

    def obtener_cliente_seleccionado(self, mostrar_mensaje=True):
        cliente_id = self.obtener_id_seleccionado_silencioso()

        if cliente_id is None:
            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Sin selección",
                    "Seleccione un cliente de la tabla.",
                )
            return None

        for cliente in self.clientes_actuales:
            try:
                if int(cliente.get("id")) == cliente_id:
                    return cliente
            except Exception:
                continue

        if mostrar_mensaje:
            QMessageBox.warning(
                self,
                "Cliente no encontrado",
                "No se pudo encontrar el cliente seleccionado.",
            )

        return None

    def crear_cliente(self):
        dialogo = ClienteDialog(
            pos_service=self.pos,
            cliente=None,
            parent=self,
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_clientes(mostrar_mensaje=True)

    def editar_cliente(self):
        cliente = self.obtener_cliente_seleccionado()

        if not cliente:
            return

        dialogo = ClienteDialog(
            pos_service=self.pos,
            cliente=cliente,
            parent=self,
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_clientes(mostrar_mensaje=True)

    def activar_cliente(self):
        cliente = self.obtener_cliente_seleccionado()

        if not cliente:
            return

        if int(cliente.get("activo") or 0) == 1:
            self.actualizar_estado_operacion("El cliente ya está activo.", "info")
            return

        resultado = self.pos.activar_cliente_sistema(cliente.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo activar el cliente."),
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Cliente activado correctamente."),
            "ok",
        )
        self.cargar_clientes(mostrar_mensaje=False)

    def desactivar_cliente(self):
        cliente = self.obtener_cliente_seleccionado()

        if not cliente:
            return

        if int(cliente.get("activo") or 0) != 1:
            self.actualizar_estado_operacion("El cliente ya está inactivo.", "info")
            return

        confirmar = QMessageBox.question(
            self,
            "Desactivar cliente",
            f"¿Seguro que deseas desactivar este cliente?\n\n{cliente.get('nombre')}",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        resultado = self.pos.desactivar_cliente_sistema(cliente.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo desactivar el cliente."),
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Cliente desactivado correctamente."),
            "ok",
        )
        self.cargar_clientes(mostrar_mensaje=False)

    def copiar_cliente(self):
        cliente = self.obtener_cliente_seleccionado()

        if not cliente:
            return

        estado = "ACTIVO" if int(cliente.get("activo") or 0) == 1 else "INACTIVO"

        texto = "\n".join([
            "CLIENTE",
            "========================",
            f"ID: {cliente.get('id')}",
            f"Nombre: {cliente.get('nombre')}",
            f"RUT: {cliente.get('rut') or ''}",
            f"Teléfono: {cliente.get('telefono') or ''}",
            f"Email: {cliente.get('email') or ''}",
            f"Dirección: {cliente.get('direccion') or ''}",
            f"Estado: {estado}",
            "",
            f"Notas: {cliente.get('notas') or ''}",
        ])

        QApplication.clipboard().setText(texto)

        self.actualizar_estado_operacion(
            "Datos del cliente copiados al portapapeles.",
            "ok",
        )

    def ver_detalle(self):
        cliente = self.obtener_cliente_seleccionado()

        if not cliente:
            return

        estado = "ACTIVO" if int(cliente.get("activo") or 0) == 1 else "INACTIVO"

        mensaje = (
            f"ID: {cliente.get('id')}\n"
            f"Nombre: {cliente.get('nombre')}\n"
            f"RUT: {cliente.get('rut') or ''}\n"
            f"Teléfono: {cliente.get('telefono') or ''}\n"
            f"Email: {cliente.get('email') or ''}\n"
            f"Dirección: {cliente.get('direccion') or ''}\n"
            f"Estado: {estado}\n\n"
            f"Notas:\n{cliente.get('notas') or ''}"
        )

        QMessageBox.information(self, "Detalle cliente", mensaje)

    def actualizar_botones_accion(self):
        cliente = self.obtener_cliente_seleccionado(mostrar_mensaje=False)
        hay_seleccion = cliente is not None

        for boton in [
            self.btn_detalle,
            self.btn_editar,
            self.btn_copiar,
            self.btn_activar,
            self.btn_desactivar,
        ]:
            if boton is not None:
                boton.setEnabled(hay_seleccion)

        if not hay_seleccion:
            return

        activo = int(cliente.get("activo") or 0) == 1

        self.btn_activar.setEnabled(not activo)
        self.btn_desactivar.setEnabled(activo)

    def actualizar_estado_operacion(self, texto, tipo="info"):
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

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QFrame#panelBusquedaClientes {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardCliente {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardCliente[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardCliente[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardCliente[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardCliente[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardCliente[tipo="alerta"] {
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

            QCheckBox {
                color: #334155;
                font-size: 14px;
                font-weight: 700;
                padding: 4px;
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
        """)