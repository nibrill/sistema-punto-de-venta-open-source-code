from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from app.database import ejecutar_consulta


class LoginDialog(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)

        self.auth = auth_manager
        self.usuario = None
        self.config_negocio = self.obtener_configuracion_negocio_segura()

        self.setWindowTitle("Ingreso al POS")
        self.setFixedSize(430, 460)

        self.logo_label = None
        self.titulo = None
        self.subtitulo = None

        self.input_usuario = QLineEdit()
        self.input_password = QLineEdit()

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

    def cargar_pixmap_logo(self, ruta_logo, ancho=140, alto=82):
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
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(18)

        card = QFrame()
        card.setObjectName("cardLogin")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(14)

        self.logo_label = QLabel()
        self.logo_label.setObjectName("logoLogin")
        self.logo_label.setFixedSize(150, 86)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ruta_logo = self.obtener_logo_negocio()
        pixmap_logo = self.cargar_pixmap_logo(ruta_logo)

        if pixmap_logo:
            self.logo_label.setPixmap(pixmap_logo)
            self.logo_label.setText("")
        else:
            self.logo_label.setText("POS")

        self.titulo = QLabel(self.obtener_nombre_negocio())
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo.setWordWrap(True)
        self.titulo.setObjectName("tituloLogin")

        self.subtitulo = QLabel("Ingresa con tu usuario para comenzar")
        self.subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitulo.setWordWrap(True)
        self.subtitulo.setObjectName("subtituloLogin")

        self.input_usuario.setPlaceholderText("Usuario")
        self.input_usuario.setMinimumHeight(42)

        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setMinimumHeight(42)
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.returnPressed.connect(self.iniciar_sesion)

        btn_login = QPushButton("Entrar al POS")
        btn_login.setObjectName("botonPrincipal")
        btn_login.setMinimumHeight(46)
        btn_login.clicked.connect(self.iniciar_sesion)

        ayuda = QLabel("CorePOS Community")
        ayuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ayuda.setWordWrap(True)
        ayuda.setObjectName("ayudaLogin")

        card_layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.titulo)
        card_layout.addWidget(self.subtitulo)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.input_usuario)
        card_layout.addWidget(self.input_password)
        card_layout.addWidget(btn_login)
        card_layout.addWidget(ayuda)

        layout.addWidget(card)

        self.setStyleSheet("""
            QDialog {
                background-color: #F3F4F6;
            }

            QFrame#cardLogin {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 18px;
            }

            QLabel#logoLogin {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                color: #2563EB;
                font-size: 28px;
                font-weight: 900;
            }

            QLabel#tituloLogin {
                color: #0F172A;
                font-size: 23px;
                font-weight: 900;
                background: transparent;
            }

            QLabel#subtituloLogin {
                color: #64748B;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }

            QLabel#ayudaLogin {
                color: #94A3B8;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 12px;
                color: #0F172A;
                font-size: 14px;
                font-weight: 600;
            }

            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }

            QPushButton {
                background-color: #111827;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 15px;
                font-weight: 800;
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

        self.input_usuario.setFocus()

    def iniciar_sesion(self):
        usuario = self.input_usuario.text().strip()
        password = self.input_password.text().strip()

        if not usuario:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "Ingresa el usuario."
            )
            self.input_usuario.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "Ingresa la contraseña."
            )
            self.input_password.setFocus()
            return

        resultado = self.auth.login(usuario, password)

        if not resultado["ok"]:
            QMessageBox.warning(self, "Acceso denegado", resultado["mensaje"])
            self.input_password.clear()
            self.input_password.setFocus()
            return

        self.usuario = resultado["data"]
        self.accept()