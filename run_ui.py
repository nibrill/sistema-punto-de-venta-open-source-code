import sys

from PySide6.QtWidgets import QApplication, QDialog

from app.auth_manager import AuthManager
from app.backup import respaldar_en_segundo_plano
from app.ui.login_dialog import LoginDialog
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLE

try:
    from app.services import PosService
except ImportError:
    from app.services import POSService as PosService


def configurar_usuario_en_servicio(pos, usuario, auth):
    pos.auth = auth

    if hasattr(pos, "set_usuario_actual"):
        pos.set_usuario_actual(usuario)
        return

    pos.usuario_actual = usuario

    def obtener_usuario_actual():
        return {
            "ok": True,
            "mensaje": "Usuario actual.",
            "data": pos.usuario_actual
        }

    def obtener_usuario_actual_id():
        return pos.usuario_actual.get("id")

    pos.obtener_usuario_actual = obtener_usuario_actual
    pos.obtener_usuario_actual_id = obtener_usuario_actual_id


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    auth = AuthManager()

    login = LoginDialog(auth)

    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    usuario = login.usuario

    respaldar_en_segundo_plano()

    pos = PosService()
    configurar_usuario_en_servicio(pos, usuario, auth)

    ventana = MainWindow(pos)
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()