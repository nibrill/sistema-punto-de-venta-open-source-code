import hashlib
import os
from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QFrame,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor


# ============================================================
# IMPORTS FLEXIBLES
# ============================================================

try:
    from app.security import ROLES_DISPONIBLES
except Exception:
    ROLES_DISPONIBLES = ["ADMIN", "VENDEDOR", "CAJERO", "ENCARGADO_STOCK"]


try:
    from app.auth_manager import AuthManager
except Exception:
    AuthManager = None


try:
    from app.usuarios import (
        listar_usuarios,
        crear_usuario,
        cambiar_password,
        activar_usuario,
        desactivar_usuario,
        generar_hash_password,
    )
except Exception:
    listar_usuarios = None
    crear_usuario = None
    cambiar_password = None
    activar_usuario = None
    desactivar_usuario = None
    generar_hash_password = None


try:
    from app.database import obtener_conexion
except Exception:
    obtener_conexion = None


# ============================================================
# UTILIDADES BACKEND
# ============================================================

def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data,
    }


def _generar_hash_password_local(password):
    if not password or len(password.strip()) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")

    salt = os.urandom(16)
    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,
    )

    return f"{salt.hex()}${hash_password.hex()}"


def _hash_password(password):
    if callable(generar_hash_password):
        return generar_hash_password(password)

    return _generar_hash_password_local(password)


def _valor_fecha_orden(valor):
    if not valor:
        return 0

    try:
        return valor.timestamp()
    except Exception:
        texto = str(valor).strip()

        if not texto or texto in ["None", "0000-00-00 00:00:00"]:
            return 0

        formatos = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        from datetime import datetime

        for formato in formatos:
            try:
                return datetime.strptime(texto, formato).timestamp()
            except Exception:
                pass

    return 0


class ItemUsuarioOrdenable(QTableWidgetItem):
    def __lt__(self, otro):
        valor_actual = self.data(Qt.ItemDataRole.UserRole)
        valor_otro = otro.data(Qt.ItemDataRole.UserRole)

        if valor_actual is not None and valor_otro is not None:
            try:
                return Decimal(str(valor_actual)) < Decimal(str(valor_otro))
            except Exception:
                return str(valor_actual).lower() < str(valor_otro).lower()

        return self.text().lower() < otro.text().lower()


class UsuariosServiceAdapter:
    def __init__(self, pos_service=None):
        self.pos = pos_service
        self.auth = getattr(pos_service, "auth", None) if pos_service else None

        if self.auth is None and AuthManager is not None:
            try:
                self.auth = AuthManager()

                if self.pos is not None:
                    self.pos.auth = self.auth
            except Exception:
                self.auth = None

        self.roles = self.obtener_roles()

    def obtener_roles(self):
        roles = []

        for rol in ROLES_DISPONIBLES:
            rol_normalizado = str(rol or "").strip().upper()

            if rol_normalizado and rol_normalizado not in roles:
                roles.append(rol_normalizado)

        for rol in ["ADMIN", "VENDEDOR", "CAJERO", "ENCARGADO_STOCK"]:
            if rol not in roles:
                roles.append(rol)

        return roles

    def normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return _respuesta(True, mensaje_ok, resultado)

    def listar_usuarios_sistema(self):
        metodos = [
            (self.auth, "listar_usuarios"),
            (self.pos, "listar_usuarios"),
            (self.pos, "obtener_usuarios"),
            (self.pos, "obtener_usuarios_sistema"),
        ]

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo()
                    return self.normalizar_respuesta(resultado, "Usuarios obtenidos correctamente.")
                except Exception:
                    continue

        if callable(listar_usuarios):
            try:
                return listar_usuarios()
            except Exception as error:
                return _respuesta(False, f"Error al listar usuarios: {error}", [])

        return self.listar_usuarios_directo()

    def crear_usuario_sistema(self, nombre, usuario, password, rol):
        metodos = [
            (self.auth, "crear_usuario"),
            (self.pos, "crear_usuario"),
            (self.pos, "crear_usuario_sistema"),
        ]

        ultimo_resultado = None

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(
                    nombre=nombre,
                    usuario=usuario,
                    password=password,
                    rol=rol,
                )
            except TypeError:
                try:
                    resultado = metodo(nombre, usuario, password, rol)
                except Exception as error:
                    ultimo_resultado = _respuesta(False, str(error))
                    continue
            except Exception as error:
                ultimo_resultado = _respuesta(False, str(error))
                continue

            resultado = self.normalizar_respuesta(resultado, "Usuario creado correctamente.")

            if resultado.get("ok"):
                return resultado

            ultimo_resultado = resultado

        if callable(crear_usuario):
            try:
                resultado = crear_usuario(nombre, usuario, password, rol)
                resultado = self.normalizar_respuesta(resultado, "Usuario creado correctamente.")

                if resultado.get("ok"):
                    return resultado

                ultimo_resultado = resultado
            except Exception as error:
                ultimo_resultado = _respuesta(False, str(error))

        resultado_directo = self.crear_usuario_directo(nombre, usuario, password, rol)

        if resultado_directo.get("ok"):
            return resultado_directo

        return ultimo_resultado or resultado_directo

    def actualizar_usuario_sistema(self, usuario_id, nombre, usuario, password, rol, activo):
        metodos = [
            (self.auth, "actualizar_usuario"),
            (self.pos, "actualizar_usuario"),
            (self.pos, "actualizar_usuario_sistema"),
        ]

        ultimo_resultado = None

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(
                    usuario_id=usuario_id,
                    nombre=nombre,
                    usuario=usuario,
                    password=password if password else None,
                    rol=rol,
                    activo=activo,
                )
            except TypeError:
                try:
                    resultado = metodo(
                        usuario_id,
                        nombre,
                        usuario,
                        password if password else None,
                        rol,
                        activo,
                    )
                except Exception as error:
                    ultimo_resultado = _respuesta(False, str(error))
                    continue
            except Exception as error:
                ultimo_resultado = _respuesta(False, str(error))
                continue

            resultado = self.normalizar_respuesta(resultado, "Usuario actualizado correctamente.")

            if resultado.get("ok"):
                return resultado

            ultimo_resultado = resultado

        resultado_directo = self.actualizar_usuario_directo(
            usuario_id=usuario_id,
            nombre=nombre,
            usuario=usuario,
            password=password,
            rol=rol,
            activo=activo,
        )

        if resultado_directo.get("ok"):
            return resultado_directo

        return ultimo_resultado or resultado_directo

    def cambiar_password_sistema(self, usuario_id, nuevo_password):
        metodos = [
            (self.auth, "cambiar_password"),
            (self.auth, "cambiar_contrasena"),
            (self.pos, "cambiar_password"),
            (self.pos, "cambiar_password_sistema"),
            (self.pos, "cambiar_contrasena_usuario"),
        ]

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo(usuario_id=usuario_id, nuevo_password=nuevo_password)
            except TypeError:
                try:
                    resultado = metodo(usuario_id, nuevo_password)
                except Exception:
                    continue
            except Exception:
                continue

            resultado = self.normalizar_respuesta(resultado, "Contraseña actualizada correctamente.")

            if resultado.get("ok"):
                return resultado

        if callable(cambiar_password):
            try:
                return cambiar_password(usuario_id, nuevo_password)
            except Exception as error:
                return _respuesta(False, f"Error al cambiar contraseña: {error}")

        return self.cambiar_password_directo(usuario_id, nuevo_password)

    def activar_usuario_sistema(self, usuario_id):
        metodos = [
            (self.auth, "activar_usuario"),
            (self.pos, "activar_usuario"),
            (self.pos, "activar_usuario_sistema"),
        ]

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo(usuario_id)
                    return self.normalizar_respuesta(resultado, "Usuario activado correctamente.")
                except Exception:
                    continue

        if callable(activar_usuario):
            return activar_usuario(usuario_id)

        return self.cambiar_estado_directo(usuario_id, 1)

    def desactivar_usuario_sistema(self, usuario_id):
        metodos = [
            (self.auth, "desactivar_usuario"),
            (self.pos, "desactivar_usuario"),
            (self.pos, "desactivar_usuario_sistema"),
        ]

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo(usuario_id)
                    return self.normalizar_respuesta(resultado, "Usuario desactivado correctamente.")
                except Exception:
                    continue

        if callable(desactivar_usuario):
            return desactivar_usuario(usuario_id)

        return self.cambiar_estado_directo(usuario_id, 0)

    def eliminar_usuario_sistema(self, usuario_id):
        metodos = [
            (self.auth, "eliminar_usuario"),
            (self.pos, "eliminar_usuario"),
            (self.pos, "eliminar_usuario_sistema"),
        ]

        for objeto, nombre_metodo in metodos:
            metodo = getattr(objeto, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo(usuario_id)
                    return self.normalizar_respuesta(resultado, "Usuario eliminado correctamente.")
                except Exception:
                    continue

        return self.eliminar_usuario_directo(usuario_id)

    # ============================================================
    # SQL DIRECTO DE RESPALDO
    # ============================================================

    def obtener_conexion_segura(self):
        if not callable(obtener_conexion):
            return None

        return obtener_conexion()

    def listar_usuarios_directo(self):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.", [])

        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    usuario,
                    rol,
                    activo,
                    ultimo_login,
                    created_at
                FROM usuarios
                ORDER BY nombre ASC;
            """)

            return _respuesta(True, "Usuarios obtenidos correctamente.", cursor.fetchall())

        except Exception as error:
            return _respuesta(False, f"Error al listar usuarios: {error}", [])

        finally:
            cursor.close()
            conexion.close()

    def crear_usuario_directo(self, nombre, usuario, password, rol):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.")

        cursor = conexion.cursor(dictionary=True)

        try:
            password_hash = _hash_password(password)

            cursor.execute("""
                INSERT INTO usuarios (
                    nombre,
                    usuario,
                    password_hash,
                    rol,
                    activo
                ) VALUES (
                    %s, %s, %s, %s, 1
                );
            """, (
                nombre.strip(),
                usuario.strip().lower(),
                password_hash,
                rol.strip().upper(),
            ))

            conexion.commit()

            return _respuesta(True, "Usuario creado correctamente.", {
                "usuario_id": cursor.lastrowid,
            })

        except Exception as error:
            conexion.rollback()
            return _respuesta(False, f"Error al crear usuario: {error}")

        finally:
            cursor.close()
            conexion.close()

    def actualizar_usuario_directo(self, usuario_id, nombre, usuario, password, rol, activo):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.")

        cursor = conexion.cursor(dictionary=True)

        try:
            if password:
                password_hash = _hash_password(password)

                cursor.execute("""
                    UPDATE usuarios
                    SET
                        nombre = %s,
                        usuario = %s,
                        password_hash = %s,
                        rol = %s,
                        activo = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                """, (
                    nombre.strip(),
                    usuario.strip().lower(),
                    password_hash,
                    rol.strip().upper(),
                    1 if activo else 0,
                    usuario_id,
                ))
            else:
                cursor.execute("""
                    UPDATE usuarios
                    SET
                        nombre = %s,
                        usuario = %s,
                        rol = %s,
                        activo = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                """, (
                    nombre.strip(),
                    usuario.strip().lower(),
                    rol.strip().upper(),
                    1 if activo else 0,
                    usuario_id,
                ))

            conexion.commit()

            if cursor.rowcount == 0:
                return _respuesta(False, "Usuario no encontrado.")

            return _respuesta(True, "Usuario actualizado correctamente.")

        except Exception as error:
            conexion.rollback()
            return _respuesta(False, f"Error al actualizar usuario: {error}")

        finally:
            cursor.close()
            conexion.close()

    def cambiar_password_directo(self, usuario_id, nuevo_password):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.")

        cursor = conexion.cursor(dictionary=True)

        try:
            password_hash = _hash_password(nuevo_password)

            cursor.execute("""
                UPDATE usuarios
                SET
                    password_hash = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                password_hash,
                usuario_id,
            ))

            conexion.commit()

            if cursor.rowcount == 0:
                return _respuesta(False, "Usuario no encontrado.")

            return _respuesta(True, "Contraseña actualizada correctamente.")

        except Exception as error:
            conexion.rollback()
            return _respuesta(False, f"Error al cambiar contraseña: {error}")

        finally:
            cursor.close()
            conexion.close()

    def cambiar_estado_directo(self, usuario_id, activo):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.")

        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute("""
                UPDATE usuarios
                SET
                    activo = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                1 if activo else 0,
                usuario_id,
            ))

            conexion.commit()

            if cursor.rowcount == 0:
                return _respuesta(False, "Usuario no encontrado.")

            mensaje = "Usuario activado correctamente." if activo else "Usuario desactivado correctamente."
            return _respuesta(True, mensaje)

        except Exception as error:
            conexion.rollback()
            return _respuesta(False, f"Error al actualizar estado: {error}")

        finally:
            cursor.close()
            conexion.close()

    def eliminar_usuario_directo(self, usuario_id):
        conexion = self.obtener_conexion_segura()

        if conexion is None:
            return _respuesta(False, "No se pudo conectar a la base de datos.")

        cursor = conexion.cursor(dictionary=True)

        try:
            cursor.execute("""
                DELETE FROM usuarios
                WHERE id = %s;
            """, (usuario_id,))

            conexion.commit()

            if cursor.rowcount == 0:
                return _respuesta(False, "Usuario no encontrado.")

            return _respuesta(True, "Usuario eliminado correctamente.")

        except Exception as error:
            conexion.rollback()
            return _respuesta(
                False,
                "No se pudo eliminar definitivamente. "
                f"Puede tener ventas, caja o movimientos asociados. Error: {error}"
            )

        finally:
            cursor.close()
            conexion.close()


# ============================================================
# DIÁLOGOS
# ============================================================

class UsuarioDialog(QDialog):
    def __init__(self, service, usuario=None, parent=None):
        super().__init__(parent)

        self.service = service
        self.usuario = usuario

        self.setWindowTitle("Editar usuario" if usuario else "Crear usuario")
        self.setMinimumWidth(620)

        self.input_nombre = QLineEdit()
        self.input_usuario = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password_confirmacion = QLineEdit()
        self.combo_rol = QComboBox()
        self.check_activo = QCheckBox("Usuario activo")
        self.label_seguridad = QLabel("Seguridad: pendiente")

        self.construir_interfaz()
        self.cargar_datos()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Editar usuario" if self.usuario else "Crear nuevo usuario")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 25px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        ayuda = QLabel(
            "Configura el acceso del usuario, su rol operativo y estado dentro del POS."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        self.input_nombre.setPlaceholderText("Nombre completo")
        self.input_usuario.setPlaceholderText("Usuario de acceso")
        self.input_password.setPlaceholderText(
            "Nueva contraseña opcional" if self.usuario else "Contraseña"
        )
        self.input_password_confirmacion.setPlaceholderText(
            "Confirmar nueva contraseña" if self.usuario else "Confirmar contraseña"
        )

        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)

        self.input_password.textChanged.connect(self.actualizar_seguridad_password)

        self.combo_rol.addItems(self.service.roles)
        self.combo_rol.setMinimumHeight(42)

        self.check_activo.setChecked(True)

        for widget in [
            self.input_nombre,
            self.input_usuario,
            self.input_password,
            self.input_password_confirmacion,
        ]:
            widget.setMinimumHeight(42)

        self.label_seguridad.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 12px;
                color: #334155;
                font-size: 13px;
                font-weight: 800;
            }
        """)

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Nombre *:", self.input_nombre)
        form.addRow("Usuario *:", self.input_usuario)
        form.addRow("Rol *:", self.combo_rol)
        form.addRow("Contraseña:", self.input_password)
        form.addRow("Confirmar:", self.input_password_confirmacion)
        form.addRow("Seguridad:", self.label_seguridad)
        form.addRow("", self.check_activo)

        if self.usuario:
            ayuda_password = QLabel("Deja la contraseña vacía si no quieres cambiarla.")
            ayuda_password.setStyleSheet("color: #64748B; font-size: 13px;")
            form.addRow("", ayuda_password)

        botones = QHBoxLayout()
        botones.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar usuario")
        btn_guardar.setObjectName("botonPrincipal")
        btn_guardar.clicked.connect(self.guardar)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilos()

    def cargar_datos(self):
        if not self.usuario:
            self.actualizar_seguridad_password()
            return

        self.input_nombre.setText(str(self.usuario.get("nombre") or ""))
        self.input_usuario.setText(str(self.usuario.get("usuario") or ""))

        rol = str(self.usuario.get("rol") or "VENDEDOR").upper()
        index = self.combo_rol.findText(rol)

        if index >= 0:
            self.combo_rol.setCurrentIndex(index)

        self.check_activo.setChecked(int(self.usuario.get("activo") or 0) == 1)
        self.actualizar_seguridad_password()

    def actualizar_seguridad_password(self):
        password = self.input_password.text().strip()

        if self.usuario and not password:
            self.label_seguridad.setText("Seguridad: no se cambiará la contraseña")
            self.label_seguridad.setStyleSheet(self.estilo_seguridad("info"))
            return

        if not password:
            self.label_seguridad.setText("Seguridad: pendiente")
            self.label_seguridad.setStyleSheet(self.estilo_seguridad("info"))
            return

        puntaje = 0

        if len(password) >= 4:
            puntaje += 1

        if len(password) >= 8:
            puntaje += 1

        if any(c.isdigit() for c in password):
            puntaje += 1

        if any(c.isupper() for c in password):
            puntaje += 1

        if any(not c.isalnum() for c in password):
            puntaje += 1

        if puntaje <= 2:
            self.label_seguridad.setText("Seguridad: baja")
            self.label_seguridad.setStyleSheet(self.estilo_seguridad("error"))
        elif puntaje <= 4:
            self.label_seguridad.setText("Seguridad: media")
            self.label_seguridad.setStyleSheet(self.estilo_seguridad("alerta"))
        else:
            self.label_seguridad.setText("Seguridad: alta")
            self.label_seguridad.setStyleSheet(self.estilo_seguridad("ok"))

    def guardar(self):
        nombre = self.input_nombre.text().strip()
        usuario = self.input_usuario.text().strip().lower()
        password = self.input_password.text().strip()
        password_confirmacion = self.input_password_confirmacion.text().strip()
        rol = self.combo_rol.currentText().strip().upper()
        activo = self.check_activo.isChecked()

        if not nombre:
            QMessageBox.warning(self, "Dato obligatorio", "Debe ingresar el nombre.")
            self.input_nombre.setFocus()
            return

        if not usuario:
            QMessageBox.warning(self, "Dato obligatorio", "Debe ingresar el usuario.")
            self.input_usuario.setFocus()
            return

        if not self.usuario and not password:
            QMessageBox.warning(self, "Dato obligatorio", "Debe ingresar una contraseña.")
            self.input_password.setFocus()
            return

        if password and len(password) < 4:
            QMessageBox.warning(
                self,
                "Contraseña inválida",
                "La contraseña debe tener al menos 4 caracteres.",
            )
            self.input_password.setFocus()
            return

        if password and password != password_confirmacion:
            QMessageBox.warning(
                self,
                "Contraseña no coincide",
                "La confirmación de contraseña no coincide.",
            )
            self.input_password_confirmacion.setFocus()
            return

        if self.usuario:
            resultado = self.service.actualizar_usuario_sistema(
                usuario_id=self.usuario.get("id"),
                nombre=nombre,
                usuario=usuario,
                password=password if password else None,
                rol=rol,
                activo=activo,
            )
        else:
            resultado = self.service.crear_usuario_sistema(
                nombre=nombre,
                usuario=usuario,
                password=password,
                rol=rol,
            )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo guardar el usuario."),
            )
            return

        QMessageBox.information(
            self,
            "Usuario guardado",
            resultado.get("mensaje", "Usuario guardado correctamente."),
        )
        self.accept()

    def estilo_seguridad(self, tipo):
        estilos = {
            "ok": """
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 10px;
                    padding: 10px 12px;
                    color: #166534;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
            "alerta": """
                QLabel {
                    background-color: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 10px;
                    padding: 10px 12px;
                    color: #92400E;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
            "error": """
                QLabel {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 10px;
                    padding: 10px 12px;
                    color: #B91C1C;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
            "info": """
                QLabel {
                    background-color: #F8FAFC;
                    border: 1px solid #E5E7EB;
                    border-radius: 10px;
                    padding: 10px 12px;
                    color: #334155;
                    font-size: 13px;
                    font-weight: 800;
                }
            """,
        }

        return estilos.get(tipo, estilos["info"])

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QLineEdit,
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus {
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


class CambiarPasswordDialog(QDialog):
    def __init__(self, service, usuario, parent=None):
        super().__init__(parent)

        self.service = service
        self.usuario = usuario

        self.setWindowTitle("Cambiar contraseña")
        self.setMinimumWidth(520)

        self.input_password = QLineEdit()
        self.input_confirmacion = QLineEdit()
        self.label_seguridad = QLabel("Seguridad: pendiente")

        self.construir_interfaz()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Cambiar contraseña")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 25px;
                font-weight: 900;
                color: #0F172A;
            }
        """)

        usuario_info = QLabel(
            f"Usuario: {self.usuario.get('nombre')} | Acceso: {self.usuario.get('usuario')}"
        )
        usuario_info.setWordWrap(True)
        usuario_info.setStyleSheet("""
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

        self.input_password.setPlaceholderText("Nueva contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setMinimumHeight(42)
        self.input_password.textChanged.connect(self.actualizar_seguridad)

        self.input_confirmacion.setPlaceholderText("Confirmar contraseña")
        self.input_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirmacion.setMinimumHeight(42)

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Nueva contraseña:", self.input_password)
        form.addRow("Confirmar:", self.input_confirmacion)
        form.addRow("Seguridad:", self.label_seguridad)

        botones = QHBoxLayout()
        botones.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Actualizar contraseña")
        btn_guardar.setObjectName("botonPrincipal")
        btn_guardar.clicked.connect(self.guardar)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addWidget(titulo)
        layout.addWidget(usuario_info)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilos()
        self.actualizar_seguridad()

    def actualizar_seguridad(self):
        password = self.input_password.text().strip()
        puntaje = 0

        if len(password) >= 4:
            puntaje += 1

        if len(password) >= 8:
            puntaje += 1

        if any(c.isdigit() for c in password):
            puntaje += 1

        if any(c.isupper() for c in password):
            puntaje += 1

        if any(not c.isalnum() for c in password):
            puntaje += 1

        if not password:
            texto = "Seguridad: pendiente"
            estilo = self.estilo_label("info")
        elif puntaje <= 2:
            texto = "Seguridad: baja"
            estilo = self.estilo_label("error")
        elif puntaje <= 4:
            texto = "Seguridad: media"
            estilo = self.estilo_label("alerta")
        else:
            texto = "Seguridad: alta"
            estilo = self.estilo_label("ok")

        self.label_seguridad.setText(texto)
        self.label_seguridad.setStyleSheet(estilo)

    def guardar(self):
        password = self.input_password.text().strip()
        confirmacion = self.input_confirmacion.text().strip()

        if len(password) < 4:
            QMessageBox.warning(
                self,
                "Contraseña inválida",
                "La contraseña debe tener al menos 4 caracteres.",
            )
            return

        if password != confirmacion:
            QMessageBox.warning(
                self,
                "Contraseña no coincide",
                "La confirmación no coincide.",
            )
            return

        resultado = self.service.cambiar_password_sistema(
            usuario_id=self.usuario.get("id"),
            nuevo_password=password,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo cambiar la contraseña."),
            )
            return

        QMessageBox.information(
            self,
            "Contraseña actualizada",
            resultado.get("mensaje", "Contraseña actualizada correctamente."),
        )
        self.accept()

    def estilo_label(self, tipo):
        if tipo == "ok":
            return """
                QLabel {
                    background-color: #ECFDF5;
                    border: 1px solid #BBF7D0;
                    border-radius: 10px;
                    padding: 10px 12px;
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
                    border-radius: 10px;
                    padding: 10px 12px;
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
                    border-radius: 10px;
                    padding: 10px 12px;
                    color: #92400E;
                    font-size: 13px;
                    font-weight: 800;
                }
            """

        return """
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 12px;
                color: #334155;
                font-size: 13px;
                font-weight: 800;
            }
        """

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px;
                color: #0F172A;
                font-size: 14px;
            }

            QLineEdit:focus {
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
            }

            QPushButton#botonPrincipal:hover {
                background-color: #1D4ED8;
            }
        """)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

class UsuariosPage(QWidget):
    def __init__(self, pos_service=None):
        super().__init__()

        self.pos = pos_service
        self.service = UsuariosServiceAdapter(pos_service)

        self.actualizando_usuarios = False
        self.timer_usuarios = None

        self.usuarios_actuales = []
        self.usuarios_visibles = []

        self.filtro_columna = None
        self.filtro_valor = None

        self.input_busqueda = QLineEdit()
        self.check_inactivos = QCheckBox("Mostrar inactivos")
        self.tabla = QTableWidget()

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.labels = {}
        self.cards = {}

        self.btn_detalle = None
        self.btn_editar = None
        self.btn_password = None
        self.btn_activar = None
        self.btn_desactivar = None
        self.btn_eliminar = None
        self.btn_copiar = None

        self.construir_interfaz()
        self.cargar_usuarios(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    # ============================================================
    # ACTUALIZACIÓN AUTOMÁTICA
    # ============================================================

    def iniciar_actualizacion_automatica(self):
        self.timer_usuarios = QTimer(self)
        self.timer_usuarios.timeout.connect(self.cargar_usuarios_automatico)
        self.timer_usuarios.start(10000)

    def cargar_usuarios_automatico(self):
        if self.actualizando_usuarios:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_usuarios(mostrar_mensaje=False)

    def actualizar_label_ultima_actualizacion(self):
        if self.label_ultima_actualizacion is None:
            return

        hora = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.label_ultima_actualizacion.setText(f"Última revisión: {hora}")

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

        titulo = QLabel("Usuarios")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Administra accesos, roles, contraseñas y seguridad operativa del POS."
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

        btn_nuevo = QPushButton("Nuevo usuario")
        btn_nuevo.setObjectName("botonPrincipal")
        btn_nuevo.setFixedWidth(180)
        btn_nuevo.setMinimumHeight(46)
        btn_nuevo.clicked.connect(self.crear_usuario)

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
            titulo="Total usuarios",
            valor="0",
            detalle="Registros creados",
            tipo="azul",
        )

        self.labels["activos"] = self.crear_card(
            cards, 0, 1,
            key="activos",
            titulo="Activos",
            valor="0",
            detalle="Pueden iniciar sesión",
            tipo="verde",
        )

        self.labels["inactivos"] = self.crear_card(
            cards, 0, 2,
            key="inactivos",
            titulo="Inactivos",
            valor="0",
            detalle="Acceso bloqueado",
            tipo="rojo",
        )

        self.labels["admin"] = self.crear_card(
            cards, 0, 3,
            key="admin",
            titulo="Admin",
            valor="0",
            detalle="Acceso total al sistema",
            tipo="morado",
        )

        self.labels["vendedores"] = self.crear_card(
            cards, 0, 4,
            key="vendedores",
            titulo="Vendedores",
            valor="0",
            detalle="Operación de ventas",
            tipo="neutro",
        )

        self.labels["cajeros"] = self.crear_card(
            cards, 1, 0,
            key="cajeros",
            titulo="Cajeros",
            valor="0",
            detalle="Caja y ventas",
            tipo="neutro",
        )

        self.labels["stock"] = self.crear_card(
            cards, 1, 1,
            key="stock",
            titulo="Stock",
            valor="0",
            detalle="Inventario y reposición",
            tipo="neutro",
        )

        self.labels["sin_login"] = self.crear_card(
            cards, 1, 2,
            key="sin_login",
            titulo="Sin login",
            valor="0",
            detalle="Nunca han iniciado sesión",
            tipo="alerta",
        )

        self.labels["recientes"] = self.crear_card(
            cards, 1, 3,
            key="recientes",
            titulo="Login reciente",
            valor="0",
            detalle="Usuarios con acceso usado",
            tipo="verde",
        )

        self.labels["visibles"] = self.crear_card(
            cards, 1, 4,
            key="visibles",
            titulo="Resultados visibles",
            valor="0",
            detalle="Según búsqueda y filtros",
            tipo="neutro",
        )

        for columna in range(5):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de usuarios...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_alertas)

        panel_busqueda = QFrame()
        panel_busqueda.setObjectName("panelBusquedaUsuarios")

        barra = QHBoxLayout(panel_busqueda)
        barra.setContentsMargins(16, 14, 16, 14)
        barra.setSpacing(12)

        self.input_busqueda.setPlaceholderText("Buscar por nombre, usuario o rol...")
        self.input_busqueda.setMinimumHeight(44)
        self.input_busqueda.textChanged.connect(self.aplicar_filtro)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setMinimumHeight(44)
        btn_limpiar.setFixedWidth(140)
        btn_limpiar.clicked.connect(self.limpiar_busqueda)

        self.check_inactivos.setChecked(False)
        self.check_inactivos.stateChanged.connect(self.aplicar_filtro)

        barra.addWidget(self.input_busqueda, 1)
        barra.addWidget(btn_limpiar)
        barra.addWidget(self.check_inactivos)

        layout.addWidget(panel_busqueda)

        titulo_tabla = QLabel("Listado de usuarios")
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

        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Usuario",
            "Rol",
            "Estado",
            "Último login",
            "Creado",
            "Seguridad",
        ])
        self.preparar_tabla()
        self.tabla.itemSelectionChanged.connect(self.actualizar_botones_accion)
        self.tabla.cellDoubleClicked.connect(self.filtrar_por_celda)

        layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        acciones.setSpacing(12)

        self.btn_detalle = QPushButton("Ver detalle")
        self.btn_detalle.setMinimumHeight(44)
        self.btn_detalle.clicked.connect(self.ver_detalle)

        self.btn_editar = QPushButton("Editar usuario")
        self.btn_editar.setObjectName("botonPrincipal")
        self.btn_editar.setMinimumHeight(44)
        self.btn_editar.clicked.connect(self.editar_usuario)

        self.btn_password = QPushButton("Cambiar contraseña")
        self.btn_password.setMinimumHeight(44)
        self.btn_password.clicked.connect(self.cambiar_password)

        self.btn_copiar = QPushButton("Copiar datos")
        self.btn_copiar.setMinimumHeight(44)
        self.btn_copiar.clicked.connect(self.copiar_usuario)

        self.btn_activar = QPushButton("Activar")
        self.btn_activar.setMinimumHeight(44)
        self.btn_activar.clicked.connect(self.activar_usuario)

        self.btn_desactivar = QPushButton("Desactivar")
        self.btn_desactivar.setMinimumHeight(44)
        self.btn_desactivar.clicked.connect(self.desactivar_usuario)

        self.btn_eliminar = QPushButton("Eliminar definitivo")
        self.btn_eliminar.setObjectName("botonPeligro")
        self.btn_eliminar.setMinimumHeight(44)
        self.btn_eliminar.clicked.connect(self.eliminar_usuario)

        acciones.addWidget(self.btn_detalle)
        acciones.addWidget(self.btn_editar)
        acciones.addWidget(self.btn_password)
        acciones.addWidget(self.btn_copiar)
        acciones.addWidget(self.btn_activar)
        acciones.addWidget(self.btn_desactivar)
        acciones.addStretch()
        acciones.addWidget(self.btn_eliminar)

        layout.addLayout(acciones)

        self.label_estado_operacion = QLabel("Usuarios listos para administrar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_estado_operacion)

        self.aplicar_estilos()
        self.actualizar_botones_accion()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardUsuario")
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

    def preparar_tabla(self):
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setMinimumHeight(390)
        self.tabla.setShowGrid(True)

        self.tabla.setSortingEnabled(True)
        self.tabla.horizontalHeader().setSectionsClickable(True)
        self.tabla.horizontalHeader().setSortIndicatorShown(True)
        self.tabla.horizontalHeader().sectionClicked.connect(self.aviso_ordenamiento_tabla)

    # ============================================================
    # CARGA Y FILTRO
    # ============================================================

    def cargar_usuarios(self, mostrar_mensaje=False):
        if self.actualizando_usuarios:
            return

        self.actualizando_usuarios = True
        usuario_id_anterior = self.obtener_id_seleccionado_silencioso()

        try:
            resultado = self.service.listar_usuarios_sistema()

            if not resultado.get("ok"):
                self.usuarios_actuales = []
                self.usuarios_visibles = []
                self.cargar_tabla([])
                self.actualizar_resumen([], [])
                self.actualizar_alertas([])
                self.actualizar_estado_operacion(
                    resultado.get("mensaje", "No se pudieron cargar usuarios."),
                    "error",
                )
                return

            self.usuarios_actuales = resultado.get("data") or []
            self.aplicar_filtro_silencioso()
            self.restaurar_seleccion(usuario_id_anterior)

            self.actualizar_resumen(self.usuarios_actuales, self.usuarios_visibles)
            self.actualizar_alertas(self.usuarios_actuales)

            if mostrar_mensaje:
                self.actualizar_estado_operacion("Usuarios cargados correctamente.", "ok")

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar usuarios automáticamente: {error}",
                "error",
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_usuarios = False
            self.actualizar_botones_accion()

    def aplicar_filtro(self):
        if self.actualizando_usuarios:
            return

        self.aplicar_filtro_silencioso()
        self.actualizar_resumen(self.usuarios_actuales, self.usuarios_visibles)
        self.actualizar_alertas(self.usuarios_actuales)
        self.actualizar_estado_operacion(
            f"Mostrando {len(self.usuarios_visibles)} usuario(s).",
            "info",
        )
        self.actualizar_botones_accion()

    def aplicar_filtro_silencioso(self):
        texto = self.input_busqueda.text().strip().lower()
        mostrar_inactivos = self.check_inactivos.isChecked()

        usuarios_filtrados = []

        for usuario in self.usuarios_actuales:
            activo = int(usuario.get("activo") or 0) == 1

            if not mostrar_inactivos and not activo:
                continue

            estado = "ACTIVO" if activo else "INACTIVO"
            ultimo_login = self.formato_fecha(usuario.get("ultimo_login"), nunca=True)
            creado = self.formato_fecha(usuario.get("created_at"))
            seguridad = self.calcular_estado_seguridad(usuario)

            campos = [
                usuario.get("id"),
                usuario.get("nombre"),
                usuario.get("usuario"),
                usuario.get("rol"),
                estado,
                ultimo_login,
                creado,
                seguridad,
            ]

            texto_usuario = " ".join(str(campo or "").lower() for campo in campos)

            if texto and texto not in texto_usuario:
                continue

            if self.filtro_columna is not None and self.filtro_valor is not None:
                valor_visible, _ = self.obtener_valor_columna_usuario(
                    usuario,
                    self.filtro_columna,
                )

                if str(valor_visible).strip() != str(self.filtro_valor).strip():
                    continue

            usuarios_filtrados.append(usuario)

        self.usuarios_visibles = usuarios_filtrados
        self.cargar_tabla(self.usuarios_visibles)

    def limpiar_busqueda(self):
        self.input_busqueda.clear()
        self.filtro_columna = None
        self.filtro_valor = None
        self.input_busqueda.setFocus()
        self.aplicar_filtro()

        self.actualizar_estado_operacion(
            "Filtros limpiados. Mostrando todos los usuarios disponibles.",
            "info",
        )

    def cargar_tabla(self, usuarios):
        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(0)

        if not usuarios:
            self.tabla.setRowCount(1)

            item = QTableWidgetItem("No hay usuarios para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(0, 0, item)

            for columna in range(1, self.tabla.columnCount()):
                self.tabla.setItem(0, columna, QTableWidgetItem(""))

            self.tabla.setSortingEnabled(False)
            return

        for fila, usuario in enumerate(usuarios):
            self.tabla.insertRow(fila)

            activo = int(usuario.get("activo") or 0) == 1
            seguridad = self.calcular_estado_seguridad(usuario)
            rol = str(usuario.get("rol") or "").upper()

            for columna in range(self.tabla.columnCount()):
                valor_visible, valor_orden = self.obtener_valor_columna_usuario(
                    usuario,
                    columna,
                )

                item = ItemUsuarioOrdenable(str(valor_visible or ""))
                item.setData(Qt.ItemDataRole.UserRole, valor_orden)

                if columna in [1, 2]:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                item.setToolTip(str(valor_visible or ""))

                if not activo:
                    item.setBackground(QColor("#FEF2F2"))
                    item.setForeground(QColor("#991B1B"))
                elif rol == "ADMIN":
                    item.setBackground(QColor("#F5F3FF"))
                    item.setForeground(QColor("#5B21B6"))
                elif "STOCK" in rol:
                    item.setBackground(QColor("#EFF6FF"))
                    item.setForeground(QColor("#1D4ED8"))
                elif seguridad == "SIN LOGIN":
                    item.setBackground(QColor("#FFFBEB"))
                    item.setForeground(QColor("#92400E"))
                else:
                    item.setBackground(QColor("#FFFFFF"))
                    item.setForeground(QColor("#0F172A"))

                self.tabla.setItem(fila, columna, item)

        self.tabla.setSortingEnabled(True)

    def obtener_valor_columna_usuario(self, usuario, columna):
        activo = int(usuario.get("activo") or 0) == 1
        estado = "ACTIVO" if activo else "INACTIVO"
        ultimo_login = self.formato_fecha(usuario.get("ultimo_login"), nunca=True)
        creado = self.formato_fecha(usuario.get("created_at"))
        seguridad = self.calcular_estado_seguridad(usuario)

        if columna == 0:
            valor = usuario.get("id") or 0
            try:
                return valor, int(valor)
            except Exception:
                return valor, 0

        if columna == 1:
            valor = usuario.get("nombre") or ""
            return valor, str(valor).lower()

        if columna == 2:
            valor = usuario.get("usuario") or ""
            return valor, str(valor).lower()

        if columna == 3:
            valor = usuario.get("rol") or ""
            return valor, str(valor).lower()

        if columna == 4:
            return estado, str(estado).lower()

        if columna == 5:
            return ultimo_login, _valor_fecha_orden(usuario.get("ultimo_login"))

        if columna == 6:
            return creado, _valor_fecha_orden(usuario.get("created_at"))

        if columna == 7:
            return seguridad, str(seguridad).lower()

        return "", ""

    def filtrar_por_celda(self, fila, columna):
        item = self.tabla.item(fila, columna)

        if item is None:
            return

        valor = item.text().strip()

        if not valor or valor == "No hay usuarios para mostrar.":
            return

        encabezado = self.tabla.horizontalHeaderItem(columna)

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
        encabezado = self.tabla.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.actualizar_estado_operacion(
            f"Tabla ordenada por: {encabezado.text()}.",
            "info",
        )

    def actualizar_resumen(self, usuarios_totales, usuarios_visibles):
        total = len(usuarios_totales)
        activos = 0
        inactivos = 0
        admins = 0
        vendedores = 0
        cajeros = 0
        stock = 0
        sin_login = 0
        recientes = 0

        for usuario in usuarios_totales:
            activo = int(usuario.get("activo") or 0) == 1
            rol = str(usuario.get("rol") or "").upper()
            ultimo_login = usuario.get("ultimo_login")

            if activo:
                activos += 1
            else:
                inactivos += 1

            if rol == "ADMIN":
                admins += 1
            elif rol == "VENDEDOR":
                vendedores += 1
            elif rol == "CAJERO":
                cajeros += 1
            elif "STOCK" in rol:
                stock += 1

            if not ultimo_login:
                sin_login += 1
            else:
                recientes += 1

        self.labels["total"].setText(str(total))
        self.labels["activos"].setText(str(activos))
        self.labels["inactivos"].setText(str(inactivos))
        self.labels["admin"].setText(str(admins))
        self.labels["vendedores"].setText(str(vendedores))
        self.labels["cajeros"].setText(str(cajeros))
        self.labels["stock"].setText(str(stock))
        self.labels["sin_login"].setText(str(sin_login))
        self.labels["recientes"].setText(str(recientes))
        self.labels["visibles"].setText(str(len(usuarios_visibles)))

        self.cambiar_tipo_card("activos", "verde" if activos > 0 else "alerta")
        self.cambiar_tipo_card("inactivos", "rojo" if inactivos > 0 else "verde")
        self.cambiar_tipo_card("admin", "morado" if admins > 0 else "rojo")
        self.cambiar_tipo_card("sin_login", "alerta" if sin_login > 0 else "verde")
        self.cambiar_tipo_card("recientes", "verde" if recientes > 0 else "neutro")

    def actualizar_alertas(self, usuarios):
        alertas = []

        admins_activos = [
            usuario for usuario in usuarios
            if int(usuario.get("activo") or 0) == 1
            and str(usuario.get("rol") or "").upper() == "ADMIN"
        ]

        usuarios_sin_login = [
            usuario for usuario in usuarios
            if int(usuario.get("activo") or 0) == 1
            and not usuario.get("ultimo_login")
        ]

        inactivos = [
            usuario for usuario in usuarios
            if int(usuario.get("activo") or 0) != 1
        ]

        if not usuarios:
            alertas.append("No hay usuarios registrados.")

        if not admins_activos:
            alertas.append("No hay administradores activos.")

        if usuarios_sin_login:
            alertas.append(f"{len(usuarios_sin_login)} usuario(s) activo(s) nunca han iniciado sesión.")

        if inactivos:
            alertas.append(f"{len(inactivos)} usuario(s) inactivo(s).")

        if not alertas:
            self.label_alertas.setText(
                "Usuarios en buen estado: hay administradores activos y accesos disponibles."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de usuarios: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    # ============================================================
    # SELECCIÓN
    # ============================================================

    def obtener_id_seleccionado_silencioso(self):
        fila = self.tabla.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla.item(fila, 0)

        if item_id is None:
            return None

        try:
            return int(item_id.text())
        except Exception:
            return None

    def restaurar_seleccion(self, usuario_id):
        if usuario_id is None:
            return

        for fila in range(self.tabla.rowCount()):
            item_id = self.tabla.item(fila, 0)

            if item_id and item_id.text().isdigit() and int(item_id.text()) == usuario_id:
                self.tabla.selectRow(fila)
                return

    def obtener_usuario_seleccionado(self, mostrar_mensaje=True):
        usuario_id = self.obtener_id_seleccionado_silencioso()

        if usuario_id is None:
            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Sin selección",
                    "Seleccione un usuario de la tabla.",
                )
            return None

        for usuario in self.usuarios_actuales:
            try:
                if int(usuario.get("id")) == usuario_id:
                    return usuario
            except Exception:
                continue

        if mostrar_mensaje:
            QMessageBox.warning(
                self,
                "Usuario no encontrado",
                "No se pudo encontrar el usuario seleccionado.",
            )

        return None

    # ============================================================
    # ACCIONES
    # ============================================================

    def crear_usuario(self):
        dialogo = UsuarioDialog(
            service=self.service,
            usuario=None,
            parent=self,
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_usuarios(mostrar_mensaje=True)

    def editar_usuario(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        dialogo = UsuarioDialog(
            service=self.service,
            usuario=usuario,
            parent=self,
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_usuarios(mostrar_mensaje=True)

    def cambiar_password(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        dialogo = CambiarPasswordDialog(
            service=self.service,
            usuario=usuario,
            parent=self,
        )

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_usuarios(mostrar_mensaje=True)

    def activar_usuario(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        if int(usuario.get("activo") or 0) == 1:
            self.actualizar_estado_operacion("El usuario ya está activo.", "info")
            return

        resultado = self.service.activar_usuario_sistema(usuario.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo activar el usuario."),
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Usuario activado correctamente."),
            "ok",
        )
        self.cargar_usuarios(mostrar_mensaje=False)

    def desactivar_usuario(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        if int(usuario.get("activo") or 0) != 1:
            self.actualizar_estado_operacion("El usuario ya está inactivo.", "info")
            return

        confirmar = QMessageBox.question(
            self,
            "Desactivar usuario",
            f"¿Seguro que deseas desactivar este usuario?\n\n{usuario.get('nombre')}",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        resultado = self.service.desactivar_usuario_sistema(usuario.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo desactivar el usuario."),
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Usuario desactivado correctamente."),
            "ok",
        )
        self.cargar_usuarios(mostrar_mensaje=False)

    def eliminar_usuario(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        confirmar = QMessageBox.question(
            self,
            "Eliminar usuario definitivamente",
            "Esta acción intentará borrar el usuario de la base de datos.\n\n"
            "Si el usuario tiene ventas, cajas o movimientos asociados, puede fallar.\n"
            "Para operación normal, se recomienda desactivar en vez de eliminar.\n\n"
            f"¿Seguro que deseas eliminar a {usuario.get('nombre')}?",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        resultado = self.service.eliminar_usuario_sistema(usuario.get("id"))

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "No se pudo eliminar",
                resultado.get("mensaje", "No se pudo eliminar el usuario."),
            )
            return

        self.actualizar_estado_operacion(
            resultado.get("mensaje", "Usuario eliminado correctamente."),
            "ok",
        )
        self.cargar_usuarios(mostrar_mensaje=False)

    def copiar_usuario(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        estado = "ACTIVO" if int(usuario.get("activo") or 0) == 1 else "INACTIVO"

        texto = "\n".join([
            "USUARIO POS",
            "========================",
            f"ID: {usuario.get('id')}",
            f"Nombre: {usuario.get('nombre')}",
            f"Usuario: {usuario.get('usuario')}",
            f"Rol: {usuario.get('rol')}",
            f"Estado: {estado}",
            f"Último login: {self.formato_fecha(usuario.get('ultimo_login'), nunca=True)}",
            f"Creado: {self.formato_fecha(usuario.get('created_at'))}",
        ])

        QApplication.clipboard().setText(texto)

        self.actualizar_estado_operacion(
            "Datos del usuario copiados al portapapeles.",
            "ok",
        )

    def ver_detalle(self):
        usuario = self.obtener_usuario_seleccionado()

        if not usuario:
            return

        estado = "ACTIVO" if int(usuario.get("activo") or 0) == 1 else "INACTIVO"

        mensaje = (
            f"ID: {usuario.get('id')}\n"
            f"Nombre: {usuario.get('nombre')}\n"
            f"Usuario: {usuario.get('usuario')}\n"
            f"Rol: {usuario.get('rol')}\n"
            f"Estado: {estado}\n"
            f"Último login: {self.formato_fecha(usuario.get('ultimo_login'), nunca=True)}\n"
            f"Creado: {self.formato_fecha(usuario.get('created_at'))}\n"
            f"Seguridad: {self.calcular_estado_seguridad(usuario)}"
        )

        QMessageBox.information(self, "Detalle usuario", mensaje)

    def actualizar_botones_accion(self):
        usuario = self.obtener_usuario_seleccionado(mostrar_mensaje=False)
        hay_usuario = usuario is not None

        for boton in [
            self.btn_detalle,
            self.btn_editar,
            self.btn_password,
            self.btn_copiar,
            self.btn_activar,
            self.btn_desactivar,
            self.btn_eliminar,
        ]:
            if boton is not None:
                boton.setEnabled(hay_usuario)

        if not hay_usuario:
            return

        activo = int(usuario.get("activo") or 0) == 1

        self.btn_activar.setEnabled(not activo)
        self.btn_desactivar.setEnabled(activo)

    # ============================================================
    # UTILIDADES
    # ============================================================

    def calcular_estado_seguridad(self, usuario):
        if not usuario.get("ultimo_login"):
            return "SIN LOGIN"

        if int(usuario.get("activo") or 0) != 1:
            return "BLOQUEADO"

        return "OK"

    def formato_fecha(self, fecha, nunca=False):
        if not fecha:
            return "Nunca" if nunca else "-"

        try:
            return fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            texto = str(fecha)

            if texto in ["None", "", "0000-00-00 00:00:00"]:
                return "Nunca" if nunca else "-"

            return texto

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
            QFrame#panelBusquedaUsuarios {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardUsuario {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardUsuario[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardUsuario[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardUsuario[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardUsuario[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardUsuario[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardUsuario[tipo="neutro"] {
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