from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QApplication,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.ui.styles import APP_STYLE
from app.security import tiene_permiso, normalizar_rol

from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.ventas_page import VentasPage
from app.ui.pages.productos_page import ProductosPage
from app.ui.pages.proveedores_page import ProveedoresPage
from app.ui.pages.clientes_page import ClientesPage
from app.ui.pages.compras_page import ComprasPage
from app.ui.pages.inventario_page import InventarioPage
from app.ui.pages.caja_page import CajaPage
from app.ui.pages.reportes_page import ReportesPage
from app.ui.pages.configuracion_page import ConfiguracionPage
from app.ui.pages.graficos_page import GraficosPage
from app.ui.pages.usuarios_page import UsuariosPage

from app.licensing.license_validator import validate_license


class MainWindow(QMainWindow):
    def __init__(self, pos_service):
        super().__init__()

        self.pos = pos_service

        self.paginas = {}
        self.paginas_originales = {}
        self.botones = {}
        self.botones_menu = self.botones
        self.indices_paginas = {}
        self.mapa_paginas = self.indices_paginas

        self.usuario_actual = self.obtener_usuario_actual_seguro()
        self.rol_actual = normalizar_rol(self.usuario_actual.get("rol"))

        self.licencia_valida = False
        self.mensaje_licencia = ""
        self.licencia_payload = {}
        self.modulos_permitidos = []

        self.modulos_por_pagina = {
            "Dashboard": "ventas",
            "Gráficos": "reportes",
            "Ventas": "ventas",
            "Productos": "productos",
            "Proveedores": "proveedores",
            "Clientes": "clientes",
            "Compras": "compras",
            "Inventario": "inventario",
            "Caja": "caja",
            "Reportes": "reportes",
            "Usuarios": "configuracion",
        }

        self.setWindowTitle("POS Pymes - Sistema de Punto de Venta")
        self.resize(1360, 820)
        self.setMinimumSize(1100, 700)

        self.construir_interfaz()

    def obtener_usuario_actual_seguro(self):
        try:
            usuario_response = self.pos.obtener_usuario_actual()
            usuario = usuario_response.get("data") or {}

            if usuario:
                return usuario

        except Exception:
            pass

        return {
            "id": None,
            "nombre": "Usuario",
            "usuario": "",
            "rol": "VENDEDOR",
        }

    def construir_interfaz(self):
        contenedor = QWidget()

        layout_principal = QHBoxLayout(contenedor)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.menu_lateral = QFrame()
        self.menu_lateral.setFixedWidth(250)
        self.menu_lateral.setObjectName("menuLateral")

        layout_menu = QVBoxLayout(self.menu_lateral)
        layout_menu.setContentsMargins(16, 22, 16, 22)
        layout_menu.setSpacing(10)

        titulo = QLabel("POS PYMES")
        titulo.setObjectName("tituloMenu")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nombre_usuario = self.usuario_actual.get("nombre", "Usuario")
        subtitulo = QLabel(f"{nombre_usuario} | {self.rol_actual}")
        subtitulo.setObjectName("subtituloMenu")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout_menu.addWidget(titulo)
        layout_menu.addWidget(subtitulo)
        layout_menu.addSpacing(18)

        self.contenido = QStackedWidget()
        self.contenido.setObjectName("contenidoPrincipal")

        self.stack = self.contenido
        self.stacked_widget = self.contenido
        self.paginas_stack = self.contenido

        paginas_disponibles = [
            ("Dashboard", DashboardPage),
            ("Gráficos", GraficosPage),
            ("Ventas", VentasPage),
            ("Productos", ProductosPage),
            ("Proveedores", ProveedoresPage),
            ("Clientes", ClientesPage),
            ("Compras", ComprasPage),
            ("Inventario", InventarioPage),
            ("Caja", CajaPage),
            ("Reportes", ReportesPage),
            ("Configuración", ConfiguracionPage),
            ("Usuarios", UsuariosPage),
        ]

        for nombre_pagina, clase_pagina in paginas_disponibles:
            if not tiene_permiso(self.rol_actual, nombre_pagina):
                continue

            try:
                pagina = clase_pagina(self.pos)
            except TypeError:
                pagina = clase_pagina()

            self.agregar_pagina(nombre_pagina, pagina)

            boton = QPushButton(nombre_pagina)
            boton.setMinimumHeight(42)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setProperty("activo", "false")

            boton.clicked.connect(
                lambda checked=False, pagina_actual=nombre_pagina: self.abrir_pagina(pagina_actual)
            )

            self.botones[nombre_pagina] = boton
            layout_menu.addWidget(boton)

        layout_menu.addStretch()

        btn_salir = QPushButton("Cerrar POS")
        btn_salir.setMinimumHeight(42)
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.clicked.connect(QApplication.quit)
        layout_menu.addWidget(btn_salir)

        layout_principal.addWidget(self.menu_lateral)
        layout_principal.addWidget(self.contenido, 1)

        self.setCentralWidget(contenedor)
        self.setStyleSheet(APP_STYLE)

        self.verificar_licencia_inicial(mostrar_mensaje=True)

        if not self.licencia_valida and "Configuración" in self.botones:
            self._mostrar_pagina_sin_validar("Configuración")
        else:
            self.abrir_primera_pagina_disponible()

    def agregar_pagina(self, nombre, pagina):
        pagina_scroll = self.envolver_con_scroll(pagina)
        indice = self.contenido.addWidget(pagina_scroll)

        self.paginas[nombre] = pagina_scroll
        self.paginas_originales[nombre] = pagina
        self.indices_paginas[nombre] = indice

    def envolver_con_scroll(self, pagina):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setObjectName("scrollPagina")

        pagina.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.MinimumExpanding,
        )

        scroll.setWidget(pagina)

        return scroll

    # ============================================================
    # LICENCIA
    # ============================================================

    def verificar_licencia_inicial(self, mostrar_mensaje=False):
        result = validate_license()

        self.licencia_valida = bool(result.get("valid"))
        self.mensaje_licencia = result.get("message", "")
        self.licencia_payload = result.get("payload") or {}

        if self.licencia_valida:
            self.modulos_permitidos = self.licencia_payload.get("modulos", []) or []
        else:
            self.modulos_permitidos = []

        if not self.licencia_valida:
            self.bloquear_modulos_por_licencia()

            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Software no activado",
                    "Este software no está activado o la licencia no es válida.\n\n"
                    f"Detalle: {self.mensaje_licencia}\n\n"
                    "Debe ir a Configuración > Activar software / Licencia."
                )

            return False

        self.habilitar_modulos_por_licencia()
        return True

    def bloquear_modulos_por_licencia(self):
        for nombre_pagina, boton in self.botones.items():
            if nombre_pagina == "Configuración":
                boton.setEnabled(True)
            else:
                boton.setEnabled(False)

            self.actualizar_estilo_boton(boton)

    def habilitar_modulos_por_licencia(self):
        for nombre_pagina, boton in self.botones.items():
            if nombre_pagina == "Configuración":
                boton.setEnabled(True)
            else:
                modulo = self.modulos_por_pagina.get(nombre_pagina)

                if modulo is None:
                    boton.setEnabled(True)
                else:
                    boton.setEnabled(modulo in self.modulos_permitidos)

            self.actualizar_estilo_boton(boton)

    def pagina_permitida_por_licencia(self, nombre_pagina):
        if nombre_pagina == "Configuración":
            return True

        if not self.licencia_valida:
            self.bloquear_modulos_por_licencia()
            return False

        modulo = self.modulos_por_pagina.get(nombre_pagina)

        if modulo is None:
            return True

        return modulo in self.modulos_permitidos

    def refrescar_licencia(self):
        licencia_ok = self.verificar_licencia_inicial(mostrar_mensaje=False)

        if licencia_ok:
            self.abrir_primera_pagina_disponible()
        else:
            if "Configuración" in self.paginas:
                self._mostrar_pagina_sin_validar("Configuración")

    # ============================================================
    # NAVEGACIÓN
    # ============================================================

    def abrir_primera_pagina_disponible(self):
        if "Dashboard" in self.botones and self.botones["Dashboard"].isEnabled():
            self.abrir_pagina("Dashboard")
            return

        for nombre_pagina, boton in self.botones.items():
            if boton.isEnabled():
                self.abrir_pagina(nombre_pagina)
                return

    def abrir_pagina(self, nombre):
        nombre = str(nombre or "").strip()

        if not nombre:
            return

        if not tiene_permiso(self.rol_actual, nombre):
            return

        if not self.pagina_permitida_por_licencia(nombre):
            QMessageBox.warning(
                self,
                "Licencia requerida",
                "Debe activar el software para usar este módulo.\n\n"
                "Vaya a Configuración > Activar software / Licencia."
            )

            if "Configuración" in self.paginas:
                self._mostrar_pagina_sin_validar("Configuración")

            return

        self._mostrar_pagina_sin_validar(nombre)

    def _mostrar_pagina_sin_validar(self, nombre):
        pagina = self.paginas.get(nombre)

        if pagina is not None:
            self.contenido.setCurrentWidget(pagina)

        for nombre_boton, boton in self.botones.items():
            activo = nombre_boton == nombre
            boton.setProperty("activo", "true" if activo else "false")
            self.actualizar_estilo_boton(boton)

    def actualizar_estilo_boton(self, boton):
        boton.style().unpolish(boton)
        boton.style().polish(boton)
        boton.update()

    def cambiar_pagina(self, nombre):
        self.abrir_pagina(nombre)

    def mostrar_pagina(self, nombre):
        self.abrir_pagina(nombre)

    def navegar_a(self, nombre):
        self.abrir_pagina(nombre)

    def ir_a_pagina(self, nombre):
        self.abrir_pagina(nombre)

    def set_pagina_actual(self, nombre):
        self.abrir_pagina(nombre)

    def obtener_pagina_original(self, nombre):
        return self.paginas_originales.get(nombre)