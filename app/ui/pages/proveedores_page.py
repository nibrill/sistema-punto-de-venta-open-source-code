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


class ProveedorDialog(QDialog):
    def __init__(self, pos_service, proveedor=None, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.proveedor = proveedor

        self.setWindowTitle("Editar proveedor" if self.proveedor else "Crear proveedor")
        self.setMinimumWidth(620)

        self.input_nombre = None
        self.input_rut = None
        self.input_contacto = None
        self.input_telefono = None
        self.input_email = None
        self.input_direccion = None
        self.input_notas = None
        self.check_activo = None

        self.construir_interfaz()
        self.cargar_datos_si_corresponde()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo_texto = "Editar proveedor" if self.proveedor else "Crear proveedor"

        titulo = QLabel(titulo_texto)
        titulo.setStyleSheet("""
            QLabel {
                font-size: 25px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        ayuda = QLabel(
            "Registra los datos comerciales del proveedor. "
            "Nombre es obligatorio; RUT, contacto, teléfono y email ayudan a compras y reposición."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        layout.addWidget(titulo)
        layout.addWidget(ayuda)

        form = QFormLayout()
        form.setSpacing(12)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Distribuidora de Bebidas SpA")

        self.input_rut = QLineEdit()
        self.input_rut.setPlaceholderText("Ej: 11111111-1")

        self.input_contacto = QLineEdit()
        self.input_contacto.setPlaceholderText("Ej: Juan Pérez")

        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Ej: +56912345678")

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ej: ventas@proveedor.cl")

        self.input_direccion = QLineEdit()
        self.input_direccion.setPlaceholderText("Ej: Av. Principal 123")

        self.input_notas = QTextEdit()
        self.input_notas.setFixedHeight(95)
        self.input_notas.setPlaceholderText(
            "Notas internas: días de reparto, condiciones, vendedor asignado, etc."
        )

        self.check_activo = QCheckBox("Proveedor activo")
        self.check_activo.setChecked(True)

        for widget in [
            self.input_nombre,
            self.input_rut,
            self.input_contacto,
            self.input_telefono,
            self.input_email,
            self.input_direccion,
        ]:
            widget.setMinimumHeight(40)

        form.addRow("Nombre *:", self.input_nombre)
        form.addRow("RUT:", self.input_rut)
        form.addRow("Contacto:", self.input_contacto)
        form.addRow("Teléfono:", self.input_telefono)
        form.addRow("Email:", self.input_email)
        form.addRow("Dirección:", self.input_direccion)
        form.addRow("Notas:", self.input_notas)
        form.addRow("", self.check_activo)

        botones = QHBoxLayout()
        botones.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar proveedor")
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

    def cargar_datos_si_corresponde(self):
        if not self.proveedor:
            return

        self.input_nombre.setText(str(self.proveedor.get("nombre") or ""))
        self.input_rut.setText(str(self.proveedor.get("rut") or ""))
        self.input_contacto.setText(str(self.proveedor.get("contacto") or ""))
        self.input_telefono.setText(str(self.proveedor.get("telefono") or ""))
        self.input_email.setText(str(self.proveedor.get("email") or ""))
        self.input_direccion.setText(str(self.proveedor.get("direccion") or ""))
        self.input_notas.setPlainText(str(self.proveedor.get("notas") or ""))
        self.check_activo.setChecked(int(self.proveedor.get("activo") or 0) == 1)

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text().strip(),
            "rut": self.input_rut.text().strip(),
            "contacto": self.input_contacto.text().strip(),
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
                "Debe ingresar el nombre del proveedor."
            )
            self.input_nombre.setFocus()
            return

        if datos["email"] and "@" not in datos["email"]:
            QMessageBox.warning(
                self,
                "Email inválido",
                "El email ingresado no parece válido."
            )
            self.input_email.setFocus()
            return

        if self.proveedor:
            resultado = self.pos.actualizar_proveedor_sistema(
                proveedor_id=self.proveedor.get("id"),
                nombre=datos["nombre"],
                rut=datos["rut"],
                contacto=datos["contacto"],
                telefono=datos["telefono"],
                email=datos["email"],
                direccion=datos["direccion"],
                notas=datos["notas"],
                activo=datos["activo"],
            )
        else:
            resultado = self.pos.crear_proveedor_sistema(
                nombre=datos["nombre"],
                rut=datos["rut"],
                contacto=datos["contacto"],
                telefono=datos["telefono"],
                email=datos["email"],
                direccion=datos["direccion"],
                notas=datos["notas"],
            )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo guardar el proveedor.")
            )
            return

        QMessageBox.information(
            self,
            "Proveedor guardado",
            resultado.get("mensaje", "Proveedor guardado correctamente.")
        )
        self.accept()


class ProveedoresPage(QWidget):
    def __init__(self, pos_service):
        super().__init__()

        self.pos = pos_service

        self.actualizando_proveedores = False
        self.timer_proveedores = None

        self.proveedores_actuales = []
        self.proveedores_visibles = []

        self.input_busqueda = None
        self.check_mostrar_inactivos = None
        self.tabla_proveedores = QTableWidget()

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
        self.cargar_proveedores(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_proveedores = QTimer(self)
        self.timer_proveedores.timeout.connect(self.cargar_proveedores_automatico)
        self.timer_proveedores.start(10000)

    def cargar_proveedores_automatico(self):
        if self.actualizando_proveedores:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_proveedores(mostrar_mensaje=False)

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

        titulo = QLabel("Proveedores")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Administra distribuidores, contactos, teléfonos, emails, estado comercial y datos de compra."
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

        btn_nuevo = QPushButton("Nuevo proveedor")
        btn_nuevo.setObjectName("botonPrincipal")
        btn_nuevo.setMinimumHeight(46)
        btn_nuevo.setFixedWidth(190)
        btn_nuevo.clicked.connect(self.crear_proveedor)

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
            titulo="Total proveedores",
            valor="0",
            detalle="Registros comerciales creados",
            tipo="azul"
        )

        self.labels["activos"] = self.crear_card(
            cards, 0, 1,
            key="activos",
            titulo="Activos",
            valor="0",
            detalle="Disponibles para compras",
            tipo="verde"
        )

        self.labels["inactivos"] = self.crear_card(
            cards, 0, 2,
            key="inactivos",
            titulo="Inactivos",
            valor="0",
            detalle="Ocultos si no marcas mostrar inactivos",
            tipo="rojo"
        )

        self.labels["visibles"] = self.crear_card(
            cards, 0, 3,
            key="visibles",
            titulo="Resultados visibles",
            valor="0",
            detalle="Según búsqueda y filtros",
            tipo="neutro"
        )

        self.labels["con_telefono"] = self.crear_card(
            cards, 1, 0,
            key="con_telefono",
            titulo="Con teléfono",
            valor="0",
            detalle="Contactables por llamada o WhatsApp",
            tipo="neutro"
        )

        self.labels["con_email"] = self.crear_card(
            cards, 1, 1,
            key="con_email",
            titulo="Con email",
            valor="0",
            detalle="Contactables por correo",
            tipo="neutro"
        )

        self.labels["sin_contacto"] = self.crear_card(
            cards, 1, 2,
            key="sin_contacto",
            titulo="Sin contacto",
            valor="0",
            detalle="Sin teléfono ni email",
            tipo="alerta"
        )

        self.labels["completitud"] = self.crear_card(
            cards, 1, 3,
            key="completitud",
            titulo="Datos completos",
            valor="0%",
            detalle="Nombre + contacto + teléfono/email",
            tipo="morado"
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de proveedores...")
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
        panel_busqueda.setObjectName("panelBusquedaProveedores")

        barra = QHBoxLayout(panel_busqueda)
        barra.setContentsMargins(16, 14, 16, 14)
        barra.setSpacing(12)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText(
            "Buscar por nombre, RUT, contacto, teléfono, email o dirección..."
        )
        self.input_busqueda.setMinimumHeight(44)
        self.input_busqueda.textChanged.connect(self.aplicar_filtro)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setMinimumHeight(44)
        btn_limpiar.setFixedWidth(140)
        btn_limpiar.clicked.connect(self.limpiar_busqueda)

        self.check_mostrar_inactivos = QCheckBox("Mostrar inactivos")
        self.check_mostrar_inactivos.stateChanged.connect(
            lambda: self.cargar_proveedores(mostrar_mensaje=False)
        )

        barra.addWidget(self.input_busqueda, 1)
        barra.addWidget(btn_limpiar)
        barra.addWidget(self.check_mostrar_inactivos)

        layout.addWidget(panel_busqueda)

        titulo_tabla = QLabel("Listado de proveedores")
        titulo_tabla.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)
        layout.addWidget(titulo_tabla)

        self.tabla_proveedores.setColumnCount(8)
        self.tabla_proveedores.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "RUT",
            "Contacto",
            "Teléfono",
            "Email",
            "Dirección",
            "Estado",
        ])
        self.preparar_tabla()
        self.tabla_proveedores.itemSelectionChanged.connect(self.actualizar_botones_accion)
        self.tabla_proveedores.doubleClicked.connect(self.editar_proveedor)

        layout.addWidget(self.tabla_proveedores)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        self.btn_detalle = QPushButton("Ver detalle")
        self.btn_detalle.setMinimumHeight(44)
        self.btn_detalle.clicked.connect(self.ver_detalle)

        self.btn_editar = QPushButton("Editar proveedor")
        self.btn_editar.setObjectName("botonPrincipal")
        self.btn_editar.setMinimumHeight(44)
        self.btn_editar.clicked.connect(self.editar_proveedor)

        self.btn_copiar = QPushButton("Copiar datos")
        self.btn_copiar.setMinimumHeight(44)
        self.btn_copiar.clicked.connect(self.copiar_proveedor)

        self.btn_activar = QPushButton("Activar")
        self.btn_activar.setMinimumHeight(44)
        self.btn_activar.clicked.connect(self.activar_proveedor)

        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_desactivar.setObjectName("botonPeligro")
        self.btn_desactivar.setMinimumHeight(44)
        self.btn_desactivar.clicked.connect(self.desactivar_proveedor)

        acciones.addWidget(self.btn_detalle)
        acciones.addWidget(self.btn_editar)
        acciones.addWidget(self.btn_copiar)
        acciones.addWidget(self.btn_activar)
        acciones.addStretch()
        acciones.addWidget(self.btn_desactivar)

        layout.addLayout(acciones)

        self.label_estado_operacion = QLabel("Proveedores listos para administrar.")
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
        card.setObjectName("cardProveedor")
        card.setProperty("tipo", tipo)
        card.setMinimumHeight(126)
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
        self.tabla_proveedores.setAlternatingRowColors(True)
        self.tabla_proveedores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_proveedores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_proveedores.verticalHeader().setVisible(False)
        self.tabla_proveedores.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_proveedores.setMinimumHeight(390)
        self.tabla_proveedores.setShowGrid(True)

    def cargar_proveedores(self, mostrar_mensaje=False):
        if self.actualizando_proveedores:
            return

        self.actualizando_proveedores = True
        proveedor_id_anterior = self.obtener_id_seleccionado_silencioso()

        try:
            resultado = self.obtener_proveedores_desde_servicio()

            if not resultado.get("ok"):
                self.proveedores_actuales = []
                self.proveedores_visibles = []
                self.cargar_tabla([])
                self.actualizar_resumen([], [])
                self.actualizar_alertas([])
                self.actualizar_estado_operacion(
                    resultado.get("mensaje", "No se pudieron cargar los proveedores."),
                    "error"
                )
                return

            proveedores = resultado.get("data") or []

            if not self.check_mostrar_inactivos.isChecked():
                proveedores_base = [
                    proveedor for proveedor in proveedores
                    if int(proveedor.get("activo") or 0) == 1
                ]
            else:
                proveedores_base = proveedores

            self.proveedores_actuales = proveedores
            self.proveedores_visibles = self.filtrar_proveedores_local(
                proveedores_base,
                self.input_busqueda.text().strip()
            )

            self.cargar_tabla(self.proveedores_visibles)
            self.restaurar_seleccion(proveedor_id_anterior)

            self.actualizar_resumen(proveedores, self.proveedores_visibles)
            self.actualizar_alertas(proveedores)

            if mostrar_mensaje:
                self.actualizar_estado_operacion(
                    "Proveedores cargados correctamente.",
                    "ok"
                )

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar proveedores automáticamente: {error}",
                "error"
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_proveedores = False
            self.actualizar_botones_accion()

    def obtener_proveedores_desde_servicio(self):
        posibles_metodos = [
            "obtener_proveedores",
            "obtener_proveedores_sistema",
            "listar_proveedores_sistema",
            "listar_proveedores",
        ]

        ultimo_error = None

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(solo_activos=False)
            except TypeError:
                try:
                    resultado = metodo()
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
                "mensaje": "Proveedores cargados correctamente.",
                "data": resultado or [],
            }

        mensaje = "No existe un método para listar proveedores en pos_service."

        if ultimo_error is not None:
            mensaje += f" Último error: {ultimo_error}"

        return {
            "ok": False,
            "mensaje": mensaje,
            "data": [],
        }

    def aplicar_filtro(self):
        if self.actualizando_proveedores:
            return

        if not self.check_mostrar_inactivos.isChecked():
            proveedores_base = [
                proveedor for proveedor in self.proveedores_actuales
                if int(proveedor.get("activo") or 0) == 1
            ]
        else:
            proveedores_base = self.proveedores_actuales

        self.proveedores_visibles = self.filtrar_proveedores_local(
            proveedores_base,
            self.input_busqueda.text().strip()
        )

        self.cargar_tabla(self.proveedores_visibles)
        self.actualizar_resumen(self.proveedores_actuales, self.proveedores_visibles)
        self.actualizar_estado_operacion(
            f"Mostrando {len(self.proveedores_visibles)} proveedor(es).",
            "info"
        )
        self.actualizar_botones_accion()

    def limpiar_busqueda(self):
        self.input_busqueda.clear()
        self.input_busqueda.setFocus()
        self.aplicar_filtro()

    def filtrar_proveedores_local(self, proveedores, texto):
        texto = str(texto or "").lower().strip()

        if not texto:
            return list(proveedores)

        filtrados = []

        for proveedor in proveedores:
            campos = [
                proveedor.get("nombre"),
                proveedor.get("rut"),
                proveedor.get("contacto"),
                proveedor.get("telefono"),
                proveedor.get("email"),
                proveedor.get("direccion"),
            ]

            texto_completo = " ".join(str(campo or "").lower() for campo in campos)

            if texto in texto_completo:
                filtrados.append(proveedor)

        return filtrados

    def cargar_tabla(self, proveedores):
        self.tabla_proveedores.setRowCount(0)

        if not proveedores:
            self.tabla_proveedores.setRowCount(1)

            item = QTableWidgetItem("No hay proveedores para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_proveedores.setItem(0, 0, item)

            for columna in range(1, self.tabla_proveedores.columnCount()):
                self.tabla_proveedores.setItem(0, columna, QTableWidgetItem(""))

            return

        for fila, proveedor in enumerate(proveedores):
            self.tabla_proveedores.insertRow(fila)

            activo = int(proveedor.get("activo") or 0) == 1
            estado = "ACTIVO" if activo else "INACTIVO"

            valores = [
                proveedor.get("id"),
                proveedor.get("nombre"),
                proveedor.get("rut"),
                proveedor.get("contacto"),
                proveedor.get("telefono"),
                proveedor.get("email"),
                proveedor.get("direccion"),
                estado,
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor or ""))

                if columna == 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                item.setToolTip(str(valor or ""))

                if activo:
                    item.setForeground(QColor("#0F172A"))
                else:
                    item.setBackground(QColor("#FEF2F2"))
                    item.setForeground(QColor("#991B1B"))

                self.tabla_proveedores.setItem(fila, columna, item)

    def actualizar_resumen(self, proveedores_totales, proveedores_visibles):
        total = len(proveedores_totales)
        activos = 0
        inactivos = 0
        con_telefono = 0
        con_email = 0
        sin_contacto = 0
        completos = 0

        for proveedor in proveedores_totales:
            activo = int(proveedor.get("activo") or 0) == 1

            if activo:
                activos += 1
            else:
                inactivos += 1

            tiene_telefono = bool(str(proveedor.get("telefono") or "").strip())
            tiene_email = bool(str(proveedor.get("email") or "").strip())
            tiene_contacto = bool(str(proveedor.get("contacto") or "").strip())

            if tiene_telefono:
                con_telefono += 1

            if tiene_email:
                con_email += 1

            if not tiene_telefono and not tiene_email:
                sin_contacto += 1

            if proveedor.get("nombre") and tiene_contacto and (tiene_telefono or tiene_email):
                completos += 1

        completitud = 0

        if total > 0:
            completitud = round((completos / total) * 100)

        self.labels["total"].setText(str(total))
        self.labels["activos"].setText(str(activos))
        self.labels["inactivos"].setText(str(inactivos))
        self.labels["visibles"].setText(str(len(proveedores_visibles)))
        self.labels["con_telefono"].setText(str(con_telefono))
        self.labels["con_email"].setText(str(con_email))
        self.labels["sin_contacto"].setText(str(sin_contacto))
        self.labels["completitud"].setText(f"{completitud}%")

        self.cambiar_tipo_card("inactivos", "rojo" if inactivos > 0 else "verde")
        self.cambiar_tipo_card("sin_contacto", "alerta" if sin_contacto > 0 else "verde")
        self.cambiar_tipo_card("completitud", "verde" if completitud >= 80 else "alerta")

    def actualizar_alertas(self, proveedores):
        if not proveedores:
            self.label_alertas.setText(
                "No hay proveedores registrados. Crea proveedores para asociarlos a productos y compras."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))
            return

        sin_contacto = []
        inactivos = []

        for proveedor in proveedores:
            telefono = str(proveedor.get("telefono") or "").strip()
            email = str(proveedor.get("email") or "").strip()

            if not telefono and not email:
                sin_contacto.append(proveedor)

            if int(proveedor.get("activo") or 0) != 1:
                inactivos.append(proveedor)

        alertas = []

        if sin_contacto:
            alertas.append(f"{len(sin_contacto)} proveedor(es) sin teléfono ni email.")

        if inactivos:
            alertas.append(f"{len(inactivos)} proveedor(es) inactivo(s).")

        if not alertas:
            self.label_alertas.setText(
                "Proveedores en buen estado: todos tienen datos básicos de contacto."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de proveedores: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def obtener_id_seleccionado_silencioso(self):
        fila = self.tabla_proveedores.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla_proveedores.item(fila, 0)

        if item_id is None:
            return None

        try:
            return int(item_id.text())
        except Exception:
            return None

    def restaurar_seleccion(self, proveedor_id):
        if proveedor_id is None:
            return

        for fila in range(self.tabla_proveedores.rowCount()):
            item_id = self.tabla_proveedores.item(fila, 0)

            if item_id and item_id.text().isdigit() and int(item_id.text()) == proveedor_id:
                self.tabla_proveedores.selectRow(fila)
                return

    def obtener_proveedor_seleccionado(self, mostrar_mensaje=True):
        proveedor_id = self.obtener_id_seleccionado_silencioso()

        if proveedor_id is None:
            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Sin selección",
                    "Seleccione un proveedor de la tabla."
                )
            return None

        for proveedor in self.proveedores_actuales:
            try:
                if int(proveedor.get("id")) == proveedor_id:
                    return proveedor
            except Exception:
                continue

        if mostrar_mensaje:
            QMessageBox.warning(
                self,
                "Proveedor no encontrado",
                "No se pudo encontrar el proveedor seleccionado."
            )

        return None

    def crear_proveedor(self):
        dialogo = ProveedorDialog(
            pos_service=self.pos,
            proveedor=None,
            parent=self
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_proveedores(mostrar_mensaje=True)

    def editar_proveedor(self):
        proveedor = self.obtener_proveedor_seleccionado()

        if not proveedor:
            return

        dialogo = ProveedorDialog(
            pos_service=self.pos,
            proveedor=proveedor,
            parent=self
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_proveedores(mostrar_mensaje=True)

    def activar_proveedor(self):
        proveedor = self.obtener_proveedor_seleccionado()

        if not proveedor:
            return

        if int(proveedor.get("activo") or 0) == 1:
            self.actualizar_estado_operacion("El proveedor ya está activo.", "info")
            return

        resultado = self.pos.activar_proveedor_sistema(proveedor.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo activar el proveedor.")
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Proveedor activado correctamente."),
            "ok"
        )
        self.cargar_proveedores(mostrar_mensaje=False)

    def desactivar_proveedor(self):
        proveedor = self.obtener_proveedor_seleccionado()

        if not proveedor:
            return

        if int(proveedor.get("activo") or 0) != 1:
            self.actualizar_estado_operacion("El proveedor ya está inactivo.", "info")
            return

        confirmar = QMessageBox.question(
            self,
            "Desactivar proveedor",
            f"¿Seguro que deseas desactivar este proveedor?\n\n{proveedor.get('nombre')}"
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        resultado = self.pos.desactivar_proveedor_sistema(proveedor.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo desactivar el proveedor.")
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Proveedor desactivado correctamente."),
            "ok"
        )
        self.cargar_proveedores(mostrar_mensaje=False)

    def copiar_proveedor(self):
        proveedor = self.obtener_proveedor_seleccionado()

        if not proveedor:
            return

        estado = "ACTIVO" if int(proveedor.get("activo") or 0) == 1 else "INACTIVO"

        texto = "\n".join([
            "PROVEEDOR",
            "========================",
            f"ID: {proveedor.get('id')}",
            f"Nombre: {proveedor.get('nombre')}",
            f"RUT: {proveedor.get('rut') or ''}",
            f"Contacto: {proveedor.get('contacto') or ''}",
            f"Teléfono: {proveedor.get('telefono') or ''}",
            f"Email: {proveedor.get('email') or ''}",
            f"Dirección: {proveedor.get('direccion') or ''}",
            f"Estado: {estado}",
            "",
            f"Notas: {proveedor.get('notas') or ''}",
        ])

        QApplication.clipboard().setText(texto)

        self.actualizar_estado_operacion(
            "Datos del proveedor copiados al portapapeles.",
            "ok"
        )

    def ver_detalle(self):
        proveedor = self.obtener_proveedor_seleccionado()

        if not proveedor:
            return

        estado = "ACTIVO" if int(proveedor.get("activo") or 0) == 1 else "INACTIVO"

        mensaje = (
            f"ID: {proveedor.get('id')}\n"
            f"Nombre: {proveedor.get('nombre')}\n"
            f"RUT: {proveedor.get('rut') or ''}\n"
            f"Contacto: {proveedor.get('contacto') or ''}\n"
            f"Teléfono: {proveedor.get('telefono') or ''}\n"
            f"Email: {proveedor.get('email') or ''}\n"
            f"Dirección: {proveedor.get('direccion') or ''}\n"
            f"Estado: {estado}\n\n"
            f"Notas:\n{proveedor.get('notas') or ''}"
        )

        QMessageBox.information(self, "Detalle proveedor", mensaje)

    def actualizar_botones_accion(self):
        proveedor = self.obtener_proveedor_seleccionado(mostrar_mensaje=False)
        hay_seleccion = proveedor is not None

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

        activo = int(proveedor.get("activo") or 0) == 1

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
            QFrame#panelBusquedaProveedores {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardProveedor {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardProveedor[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardProveedor[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardProveedor[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardProveedor[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardProveedor[tipo="alerta"] {
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

            QTableWidget::item {
                padding: 8px;
            }
        """)