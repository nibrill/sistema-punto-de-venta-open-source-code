from decimal import Decimal
from mysql.connector import Error

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
    QDoubleSpinBox,
    QAbstractSpinBox,
    QTextEdit,
    QCheckBox,
    QFrame,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor

from app.database import obtener_conexion

from app.inventario import (
    ingresar_stock,
    ajustar_stock,
    registrar_merma,
    actualizar_precio_producto,
    obtener_movimientos_stock,
    sugerir_reposicion_stock,
)

from app.productos import (
    listar_productos,
    buscar_producto_por_codigo,
    buscar_productos_por_nombre,
)


def _respuesta(ok, mensaje, data=None):
    return {
        "ok": ok,
        "mensaje": mensaje,
        "data": data,
    }


def _decimal(valor):
    try:
        return Decimal(str(valor or 0))
    except Exception:
        return Decimal("0")


def formato_numero_general(valor):
    try:
        numero = Decimal(str(valor or 0))

        if numero == numero.to_integral():
            return str(int(numero))

        return f"{numero:.3f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


def _formato_pesos(valor):
    try:
        valor = int(Decimal(str(valor or 0)))
        return f"${valor:,.0f}".replace(",", ".")
    except Exception:
        return "$0"


def _obtener_columnas_tabla(cursor, tabla):
    cursor.execute(f"SHOW COLUMNS FROM {tabla};")
    filas = cursor.fetchall() or []
    columnas = set()

    for fila in filas:
        if isinstance(fila, dict):
            columnas.add(fila.get("Field"))
        else:
            columnas.add(fila[0])

    return columnas


def crear_categoria_bd(nombre, descripcion=""):
    nombre = str(nombre or "").strip()
    descripcion = str(descripcion or "").strip()

    if not nombre:
        return _respuesta(False, "Debe ingresar el nombre de la categoría.")

    if len(nombre) < 2:
        return _respuesta(False, "El nombre de la categoría debe tener al menos 2 caracteres.")

    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas_tabla(cursor, "categorias")
        filtro_activo = "AND activo = 1" if "activo" in columnas else ""

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
            {filtro_activo}
            LIMIT 1;
        """, (nombre,))

        existente = cursor.fetchone()

        if existente:
            return _respuesta(
                False,
                f"Ya existe una categoría llamada '{existente.get('nombre')}'."
            )

        campos = ["nombre"]
        valores = [nombre]
        placeholders = ["%s"]

        if "descripcion" in columnas:
            campos.append("descripcion")
            valores.append(descripcion)
            placeholders.append("%s")

        if "activo" in columnas:
            campos.append("activo")
            valores.append(1)
            placeholders.append("%s")

        if "created_at" in columnas:
            campos.append("created_at")
            placeholders.append("NOW()")

        if "updated_at" in columnas:
            campos.append("updated_at")
            placeholders.append("NOW()")

        cursor.execute(f"""
            INSERT INTO categorias ({", ".join(campos)})
            VALUES ({", ".join(placeholders)});
        """, tuple(valores))

        conexion.commit()

        return _respuesta(True, "Categoría creada correctamente.", {
            "id": cursor.lastrowid,
            "nombre": nombre,
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al crear categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


def actualizar_nombre_categoria_bd(categoria_id, nuevo_nombre):
    nuevo_nombre = str(nuevo_nombre or "").strip()

    if not categoria_id:
        return _respuesta(False, "No se recibió el ID de la categoría.")

    if not nuevo_nombre:
        return _respuesta(False, "Debe ingresar el nuevo nombre de la categoría.")

    if len(nuevo_nombre) < 2:
        return _respuesta(False, "El nombre de la categoría debe tener al menos 2 caracteres.")

    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas_tabla(cursor, "categorias")
        filtro_activo = "AND activo = 1" if "activo" in columnas else ""

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE id = %s
            {filtro_activo}
            LIMIT 1;
        """, (categoria_id,))

        categoria = cursor.fetchone()

        if not categoria:
            return _respuesta(False, "Categoría no encontrada o inactiva.")

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND id <> %s
            {filtro_activo}
            LIMIT 1;
        """, (nuevo_nombre, categoria_id))

        duplicada = cursor.fetchone()

        if duplicada:
            return _respuesta(
                False,
                f"Ya existe otra categoría llamada '{duplicada.get('nombre')}'."
            )

        sets = ["nombre = %s"]
        valores = [nuevo_nombre]

        if "updated_at" in columnas:
            sets.append("updated_at = NOW()")

        valores.append(categoria_id)

        cursor.execute(f"""
            UPDATE categorias
            SET {", ".join(sets)}
            WHERE id = %s;
        """, tuple(valores))

        conexion.commit()

        return _respuesta(True, "Categoría actualizada correctamente.", {
            "id": categoria_id,
            "nombre_anterior": categoria.get("nombre"),
            "nombre_nuevo": nuevo_nombre,
        })

    except Error as error:
        conexion.rollback()
        return _respuesta(False, f"Error al editar categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


def obtener_categoria_id_por_nombre_bd(nombre):
    nombre = str(nombre or "").strip()

    if not nombre or nombre.lower() == "sin categoría":
        return _respuesta(False, "El producto seleccionado no tiene categoría asignada.")

    conexion = obtener_conexion()

    if conexion is None:
        return _respuesta(False, "No se pudo conectar a la base de datos.")

    cursor = conexion.cursor(dictionary=True)

    try:
        columnas = _obtener_columnas_tabla(cursor, "categorias")
        filtro_activo = "AND activo = 1" if "activo" in columnas else ""

        cursor.execute(f"""
            SELECT id, nombre
            FROM categorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
            {filtro_activo}
            LIMIT 1;
        """, (nombre,))

        categoria = cursor.fetchone()

        if not categoria:
            return _respuesta(False, "No se encontró la categoría del producto seleccionado.")

        return _respuesta(True, "Categoría encontrada.", categoria)

    except Error as error:
        return _respuesta(False, f"Error al buscar categoría: {error}")

    finally:
        cursor.close()
        conexion.close()


class ItemInventarioOrdenable(QTableWidgetItem):
    def __lt__(self, otro):
        valor_actual = self.data(Qt.ItemDataRole.UserRole)
        valor_otro = otro.data(Qt.ItemDataRole.UserRole)

        if valor_actual is not None and valor_otro is not None:
            try:
                return Decimal(str(valor_actual)) < Decimal(str(valor_otro))
            except Exception:
                return str(valor_actual).lower() < str(valor_otro).lower()

        return self.text().lower() < otro.text().lower()


class InventarioServiceAdapter:
    def __init__(self, usuario_id=1):
        self.usuario_id = usuario_id

    def _normalizar_respuesta(self, resultado, mensaje_ok="Operación realizada correctamente."):
        if isinstance(resultado, dict) and "ok" in resultado:
            return resultado

        return {
            "ok": True,
            "mensaje": mensaje_ok,
            "data": resultado,
        }

    def formato_pesos(self, valor):
        return _formato_pesos(valor)

    def formato_fecha(self, fecha):
        if not fecha:
            return "-"

        try:
            return fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(fecha)

    def obtener_productos(self):
        resultado = listar_productos()
        return self._normalizar_respuesta(resultado, "Productos cargados correctamente.")

    def buscar_producto_codigo(self, codigo):
        resultado = buscar_producto_por_codigo(codigo)

        if not resultado:
            return {
                "ok": False,
                "mensaje": "Producto no encontrado.",
                "data": None,
            }

        return self._normalizar_respuesta(resultado, "Producto encontrado correctamente.")

    def buscar_producto_nombre(self, texto):
        resultado = buscar_productos_por_nombre(texto)
        return self._normalizar_respuesta(resultado, "Búsqueda realizada correctamente.")

    def ingresar_stock_producto(
        self,
        producto_id,
        cantidad,
        precio_compra=None,
        comentario="Ingreso de stock",
        actualizar_precio_compra=True,
    ):
        return ingresar_stock(
            producto_id=producto_id,
            usuario_id=self.usuario_id,
            cantidad=cantidad,
            precio_compra=precio_compra,
            comentario=comentario,
            actualizar_precio_compra=actualizar_precio_compra,
        )

    def ajustar_stock_producto(
        self,
        producto_id,
        nuevo_stock,
        comentario="Ajuste manual de stock",
    ):
        return ajustar_stock(
            producto_id=producto_id,
            usuario_id=self.usuario_id,
            nuevo_stock=nuevo_stock,
            comentario=comentario,
        )

    def registrar_merma_producto(
        self,
        producto_id,
        cantidad,
        comentario="Merma de producto",
    ):
        return registrar_merma(
            producto_id=producto_id,
            usuario_id=self.usuario_id,
            cantidad=cantidad,
            comentario=comentario,
        )

    def actualizar_precio_producto_sistema(
        self,
        producto_id,
        nuevo_precio_venta,
        nuevo_precio_compra=None,
    ):
        return actualizar_precio_producto(
            producto_id=producto_id,
            nuevo_precio_venta=nuevo_precio_venta,
            nuevo_precio_compra=nuevo_precio_compra,
        )

    def obtener_movimientos_inventario(self, producto_id=None, limite=100):
        return obtener_movimientos_stock(
            producto_id=producto_id,
            limite=limite,
        )

    def obtener_sugerencia_reposicion(self):
        return sugerir_reposicion_stock()

    def crear_categoria(self, nombre):
        return crear_categoria_bd(nombre)

    def actualizar_nombre_categoria(self, categoria_id, nuevo_nombre):
        return actualizar_nombre_categoria_bd(categoria_id, nuevo_nombre)

    def obtener_categoria_id_por_nombre(self, nombre):
        return obtener_categoria_id_por_nombre_bd(nombre)


class DialogoBaseInventario(QDialog):
    def aplicar_estilo_dialogo(self):
        self.setStyleSheet("""
            QFrame#panelFormularioCategoria {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

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

            QFrame#controlSpinInventario {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 14px;
            }

            QFrame#controlSpinInventario:hover {
                border: 1px solid #94A3B8;
            }

            QDoubleSpinBox {
                background-color: transparent;
                border: none;
                padding: 0px 6px;
                color: #0F172A;
                font-size: 14px;
                font-weight: 800;
            }

            QDoubleSpinBox:focus {
                background-color: transparent;
                border: none;
            }

            QPushButton#botonMiniSpin {
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 900;
                padding: 0px;
                margin: 0px;
                min-width: 38px;
                max-width: 38px;
                min-height: 38px;
                max-height: 38px;
            }

            QPushButton#botonMiniSpin:hover {
                background-color: #DBEAFE;
                border: 1px solid #BFDBFE;
                color: #1D4ED8;
            }

            QPushButton#botonMiniSpin:pressed {
                background-color: #2563EB;
                border: 1px solid #2563EB;
                color: white;
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

            QPushButton#botonPeligro {
                background-color: #DC2626;
            }

            QPushButton#botonPeligro:hover {
                background-color: #B91C1C;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }
        """)

    def configurar_spinbox_inventario(
        self,
        spinbox,
        decimales=0,
        minimo=0,
        maximo=999999999,
        paso=1,
        prefijo="",
        ancho=190,
    ):
        spinbox.setMinimum(minimo)
        spinbox.setMaximum(maximo)
        spinbox.setDecimals(decimales)
        spinbox.setSingleStep(paso)
        spinbox.setPrefix(prefijo)
        spinbox.setFixedWidth(ancho)
        spinbox.setMinimumHeight(38)
        spinbox.setMaximumHeight(38)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setAccelerated(True)
        spinbox.setKeyboardTracking(False)
        spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

    def crear_control_spinbox(self, spinbox):
        contenedor = QFrame()
        contenedor.setObjectName("controlSpinInventario")
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
        btn_menos.clicked.connect(lambda: spinbox.stepDown() if spinbox.isEnabled() else None)

        btn_mas = QPushButton("+")
        btn_mas.setObjectName("botonMiniSpin")
        btn_mas.setFixedSize(38, 38)
        btn_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_mas.clicked.connect(lambda: spinbox.stepUp() if spinbox.isEnabled() else None)

        layout.addWidget(btn_menos)
        layout.addWidget(spinbox, 1)
        layout.addWidget(btn_mas)

        return contenedor

    def crear_input_stock(self, valor=1, minimo=0.001):
        input_stock = QDoubleSpinBox()

        self.configurar_spinbox_inventario(
            input_stock,
            decimales=3,
            minimo=minimo,
            maximo=999999999,
            paso=1,
            prefijo="",
            ancho=190,
        )

        input_stock.setValue(float(Decimal(str(valor or 0))))

        return input_stock

    def crear_input_monto(self, valor=0):
        input_monto = QDoubleSpinBox()

        self.configurar_spinbox_inventario(
            input_monto,
            decimales=0,
            minimo=0,
            maximo=999999999,
            paso=100,
            prefijo="$ ",
            ancho=190,
        )

        input_monto.setValue(float(Decimal(str(valor or 0))))

        return input_monto


class IngresoStockDialog(DialogoBaseInventario):
    def __init__(self, pos_service, producto, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.producto = producto

        self.setWindowTitle("Ingresar stock")
        self.setMinimumWidth(560)

        self.input_cantidad = None
        self.input_precio_compra = None
        self.check_actualizar_precio = None
        self.input_comentario = None
        self.label_total_estimado = None

        self.construir_interfaz()
        self.actualizar_total_estimado()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Ingresar stock")
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        producto = QLabel(
            f"Producto: {self.producto.get('nombre')}\n"
            f"Stock actual: {self.formato_numero(self.producto.get('stock_actual'))}"
        )
        producto.setWordWrap(True)
        producto.setStyleSheet("""
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

        form = QFormLayout()
        form.setSpacing(12)

        self.input_cantidad = self.crear_input_stock(1, 0.001)
        self.input_precio_compra = self.crear_input_monto(self.producto.get("precio_compra"))

        self.input_cantidad.valueChanged.connect(self.actualizar_total_estimado)
        self.input_precio_compra.valueChanged.connect(self.actualizar_total_estimado)

        self.check_actualizar_precio = QCheckBox("Actualizar precio de compra del producto")
        self.check_actualizar_precio.setChecked(True)

        self.label_total_estimado = QLabel("Total ingreso: $0")
        self.label_total_estimado.setStyleSheet("""
            QLabel {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
                padding: 10px 12px;
                color: #166534;
                font-size: 14px;
                font-weight: 800;
            }
        """)

        self.input_comentario = QTextEdit()
        self.input_comentario.setFixedHeight(90)
        self.input_comentario.setPlaceholderText("Ej: Ingreso por compra, reposición, recepción de proveedor")

        form.addRow("Cantidad a ingresar:", self.crear_control_spinbox(self.input_cantidad))
        form.addRow("Precio compra:", self.crear_control_spinbox(self.input_precio_compra))
        form.addRow("", self.check_actualizar_precio)
        form.addRow("Total estimado:", self.label_total_estimado)
        form.addRow("Comentario:", self.input_comentario)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Confirmar ingreso")
        btn_confirmar.setObjectName("botonPrincipal")
        btn_confirmar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(producto)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilo_dialogo()

    def actualizar_total_estimado(self):
        if self.label_total_estimado is None:
            return

        cantidad = Decimal(str(self.input_cantidad.value()))
        precio = Decimal(str(self.input_precio_compra.value()))
        total = cantidad * precio

        self.label_total_estimado.setText(f"Total ingreso: {self.pos.formato_pesos(total)}")

    def obtener_datos(self):
        actualizar_precio = self.check_actualizar_precio.isChecked()

        if actualizar_precio:
            precio_compra = Decimal(str(self.input_precio_compra.value()))
        else:
            precio_compra = None

        return {
            "cantidad": Decimal(str(self.input_cantidad.value())),
            "precio_compra": precio_compra,
            "actualizar_precio_compra": actualizar_precio,
            "comentario": self.input_comentario.toPlainText().strip() or "Ingreso de stock",
        }

    def formato_numero(self, valor):
        return formato_numero_general(valor)


class AjusteStockDialog(DialogoBaseInventario):
    def __init__(self, producto, parent=None):
        super().__init__(parent)

        self.producto = producto

        self.setWindowTitle("Ajustar stock")
        self.setMinimumWidth(560)

        self.input_nuevo_stock = None
        self.input_comentario = None
        self.label_diferencia = None

        self.construir_interfaz()
        self.actualizar_diferencia()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Ajustar stock físico")
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        stock_actual = _decimal(self.producto.get("stock_actual"))

        producto = QLabel(
            f"Producto: {self.producto.get('nombre')}\n"
            f"Stock actual en sistema: {formato_numero_general(stock_actual)}"
        )
        producto.setWordWrap(True)
        producto.setStyleSheet("""
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

        form = QFormLayout()
        form.setSpacing(12)

        self.input_nuevo_stock = self.crear_input_stock(stock_actual, 0)
        self.input_nuevo_stock.valueChanged.connect(self.actualizar_diferencia)

        self.label_diferencia = QLabel("Diferencia: 0")
        self.label_diferencia.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 12px;
                color: #334155;
                font-size: 14px;
                font-weight: 800;
            }
        """)

        self.input_comentario = QTextEdit()
        self.input_comentario.setFixedHeight(90)
        self.input_comentario.setPlaceholderText("Ej: Ajuste por conteo físico, diferencia de inventario")

        form.addRow("Nuevo stock:", self.crear_control_spinbox(self.input_nuevo_stock))
        form.addRow("Diferencia:", self.label_diferencia)
        form.addRow("Comentario:", self.input_comentario)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Confirmar ajuste")
        btn_confirmar.setObjectName("botonPrincipal")
        btn_confirmar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(producto)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilo_dialogo()

    def actualizar_diferencia(self):
        if self.label_diferencia is None:
            return

        stock_actual = _decimal(self.producto.get("stock_actual"))
        nuevo_stock = Decimal(str(self.input_nuevo_stock.value()))
        diferencia = nuevo_stock - stock_actual

        if diferencia > 0:
            texto = f"Diferencia: +{formato_numero_general(diferencia)} unidades"
            color = "#166534"
            fondo = "#ECFDF5"
            borde = "#BBF7D0"
        elif diferencia < 0:
            texto = f"Diferencia: {formato_numero_general(diferencia)} unidades"
            color = "#B91C1C"
            fondo = "#FEF2F2"
            borde = "#FECACA"
        else:
            texto = "Diferencia: 0 unidades"
            color = "#334155"
            fondo = "#F8FAFC"
            borde = "#E5E7EB"

        self.label_diferencia.setText(texto)
        self.label_diferencia.setStyleSheet(f"""
            QLabel {{
                background-color: {fondo};
                border: 1px solid {borde};
                border-radius: 10px;
                padding: 10px 12px;
                color: {color};
                font-size: 14px;
                font-weight: 800;
            }}
        """)

    def obtener_datos(self):
        return {
            "nuevo_stock": Decimal(str(self.input_nuevo_stock.value())),
            "comentario": self.input_comentario.toPlainText().strip() or "Ajuste manual de stock",
        }


class MermaDialog(DialogoBaseInventario):
    def __init__(self, producto, parent=None):
        super().__init__(parent)

        self.producto = producto

        self.setWindowTitle("Registrar merma")
        self.setMinimumWidth(560)

        self.input_cantidad = None
        self.input_comentario = None

        self.construir_interfaz()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Registrar merma")
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        producto = QLabel(
            f"Producto: {self.producto.get('nombre')}\n"
            f"Stock actual: {formato_numero_general(self.producto.get('stock_actual'))}"
        )
        producto.setWordWrap(True)
        producto.setStyleSheet("""
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

        form = QFormLayout()
        form.setSpacing(12)

        self.input_cantidad = self.crear_input_stock(1, 0.001)

        self.input_comentario = QTextEdit()
        self.input_comentario.setFixedHeight(90)
        self.input_comentario.setPlaceholderText("Ej: Producto vencido, roto, dañado, pérdida o merma operacional")

        form.addRow("Cantidad merma:", self.crear_control_spinbox(self.input_cantidad))
        form.addRow("Comentario:", self.input_comentario)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Registrar merma")
        btn_confirmar.setObjectName("botonPeligro")
        btn_confirmar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(producto)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilo_dialogo()

    def obtener_datos(self):
        return {
            "cantidad": Decimal(str(self.input_cantidad.value())),
            "comentario": self.input_comentario.toPlainText().strip() or "Merma de producto",
        }


class PrecioDialog(DialogoBaseInventario):
    def __init__(self, pos_service, producto, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.producto = producto

        self.setWindowTitle("Actualizar precio")
        self.setMinimumWidth(560)

        self.input_precio_venta = None
        self.input_precio_compra = None
        self.check_precio_compra = None
        self.label_margen = None

        self.construir_interfaz()
        self.actualizar_margen()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        titulo = QLabel("Actualizar precio")
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        producto = QLabel(f"Producto: {self.producto.get('nombre')}")
        producto.setWordWrap(True)
        producto.setStyleSheet("""
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

        form = QFormLayout()
        form.setSpacing(12)

        self.input_precio_venta = self.crear_input_monto(self.producto.get("precio_venta"))
        self.input_precio_compra = self.crear_input_monto(self.producto.get("precio_compra"))

        self.input_precio_venta.valueChanged.connect(self.actualizar_margen)
        self.input_precio_compra.valueChanged.connect(self.actualizar_margen)

        self.check_precio_compra = QCheckBox("Actualizar también precio de compra")
        self.check_precio_compra.setChecked(False)
        self.check_precio_compra.stateChanged.connect(self.actualizar_estado_precio_compra)

        self.input_precio_compra.setEnabled(False)

        self.label_margen = QLabel("Margen estimado: $0")
        self.label_margen.setStyleSheet("""
            QLabel {
                background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 12px;
                color: #334155;
                font-size: 14px;
                font-weight: 800;
            }
        """)

        form.addRow("Nuevo precio venta:", self.crear_control_spinbox(self.input_precio_venta))
        form.addRow("", self.check_precio_compra)
        form.addRow("Nuevo precio compra:", self.crear_control_spinbox(self.input_precio_compra))
        form.addRow("Margen:", self.label_margen)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Actualizar precio")
        btn_confirmar.setObjectName("botonPrincipal")
        btn_confirmar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(producto)
        layout.addLayout(form)
        layout.addLayout(botones)

        self.aplicar_estilo_dialogo()

    def actualizar_estado_precio_compra(self):
        self.input_precio_compra.setEnabled(self.check_precio_compra.isChecked())
        self.actualizar_margen()

    def actualizar_margen(self):
        if self.label_margen is None:
            return

        venta = Decimal(str(self.input_precio_venta.value()))

        if self.check_precio_compra and self.check_precio_compra.isChecked():
            compra = Decimal(str(self.input_precio_compra.value()))
        else:
            compra = _decimal(self.producto.get("precio_compra"))

        margen = venta - compra
        porcentaje = Decimal("0")

        if venta > 0:
            porcentaje = (margen / venta) * Decimal("100")

        texto = f"Margen estimado: {self.pos.formato_pesos(margen)} ({porcentaje:.1f}%)"

        if margen < 0:
            color = "#B91C1C"
            fondo = "#FEF2F2"
            borde = "#FECACA"
        elif margen == 0:
            color = "#92400E"
            fondo = "#FFFBEB"
            borde = "#FDE68A"
        else:
            color = "#166534"
            fondo = "#ECFDF5"
            borde = "#BBF7D0"

        self.label_margen.setText(texto)
        self.label_margen.setStyleSheet(f"""
            QLabel {{
                background-color: {fondo};
                border: 1px solid {borde};
                border-radius: 10px;
                padding: 10px 12px;
                color: {color};
                font-size: 14px;
                font-weight: 800;
            }}
        """)

    def obtener_datos(self):
        if self.check_precio_compra.isChecked():
            precio_compra = Decimal(str(self.input_precio_compra.value()))
        else:
            precio_compra = None

        return {
            "nuevo_precio_venta": Decimal(str(self.input_precio_venta.value())),
            "nuevo_precio_compra": precio_compra,
        }


class CategoriaDialog(DialogoBaseInventario):
    def __init__(self, categoria=None, parent=None):
        super().__init__(parent)

        self.categoria = categoria or {}
        self.es_edicion = bool(self.categoria.get("id"))

        if self.es_edicion:
            self.setWindowTitle("Editar categoría")
        else:
            self.setWindowTitle("Nueva categoría")

        self.setMinimumWidth(560)

        self.input_nombre = None

        self.construir_interfaz()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        if self.es_edicion:
            titulo_texto = "Editar nombre de categoría"
            ayuda_texto = (
                "Cambia el nombre de la categoría seleccionada. "
                "Este cambio se verá reflejado en todos los productos que usen esta categoría."
            )
            boton_texto = "Guardar cambios"
        else:
            titulo_texto = "Crear nueva categoría"
            ayuda_texto = "Agrega una categoría para organizar mejor los productos del inventario."
            boton_texto = "Guardar categoría"

        titulo = QLabel(titulo_texto)
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        ayuda = QLabel(ayuda_texto)
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px; font-weight: 700;")

        panel = QFrame()
        panel.setObjectName("panelFormularioCategoria")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Bebidas, Snacks, Abarrotes, Aseo")
        self.input_nombre.setMinimumHeight(42)
        self.input_nombre.setMaxLength(100)

        if self.es_edicion:
            self.input_nombre.setText(str(self.categoria.get("nombre") or ""))

        form.addRow("Nombre categoría:", self.input_nombre)

        panel_layout.addLayout(form)

        botones = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton(boton_texto)
        btn_guardar.setObjectName("botonPrincipal")
        btn_guardar.clicked.connect(self.accept)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addWidget(panel)
        layout.addLayout(botones)

        self.aplicar_estilo_dialogo()

        self.input_nombre.setFocus()
        self.input_nombre.selectAll()

    def accept(self):
        nombre = self.input_nombre.text().strip()

        if not nombre:
            QMessageBox.warning(
                self,
                "Dato obligatorio",
                "Debe ingresar el nombre de la categoría.",
            )
            self.input_nombre.setFocus()
            return

        if len(nombre) < 2:
            QMessageBox.warning(
                self,
                "Nombre inválido",
                "El nombre de la categoría debe tener al menos 2 caracteres.",
            )
            self.input_nombre.setFocus()
            return

        super().accept()

    def obtener_datos(self):
        return {
            "nombre": self.input_nombre.text().strip(),
        }


class ReposicionDialog(QDialog):
    def __init__(self, pos_service, productos, parent=None):
        super().__init__(parent)

        self.pos = pos_service
        self.productos = productos

        self.setWindowTitle("Sugerencia de reposición")
        self.resize(900, 520)

        self.tabla = QTableWidget()

        self.construir_interfaz()

    def construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("Sugerencia de reposición")
        titulo.setStyleSheet("font-size: 25px; font-weight: 900; color: #0F172A;")

        ayuda = QLabel(
            "Productos cuyo stock actual está igual o bajo el stock mínimo. "
            "La cantidad sugerida apunta a dejar el stock al doble del mínimo."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color: #64748B; font-size: 14px;")

        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Código",
            "Producto",
            "Stock actual",
            "Stock mínimo",
            "Cantidad sugerida",
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.cargar_tabla()

        botones = QHBoxLayout()

        btn_copiar = QPushButton("Copiar sugerencia")
        btn_copiar.clicked.connect(self.copiar_sugerencia)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        botones.addWidget(btn_copiar)
        botones.addStretch()
        botones.addWidget(btn_cerrar)

        layout.addWidget(titulo)
        layout.addWidget(ayuda)
        layout.addWidget(self.tabla)
        layout.addLayout(botones)

        self.setStyleSheet("""
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
        """)

    def cargar_tabla(self):
        self.tabla.setRowCount(0)

        for fila, producto in enumerate(self.productos):
            self.tabla.insertRow(fila)

            valores = [
                producto.get("id"),
                producto.get("codigo_barra"),
                producto.get("nombre"),
                formato_numero_general(producto.get("stock_actual")),
                formato_numero_general(producto.get("stock_minimo")),
                formato_numero_general(producto.get("cantidad_sugerida")),
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor or ""))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, columna, item)

    def copiar_sugerencia(self):
        if not self.productos:
            return

        lineas = [
            "SUGERENCIA DE REPOSICIÓN",
            "==============================",
        ]

        for producto in self.productos:
            lineas.append(
                f"{producto.get('nombre')} | Código: {producto.get('codigo_barra')} | "
                f"Stock: {formato_numero_general(producto.get('stock_actual'))} | "
                f"Mínimo: {formato_numero_general(producto.get('stock_minimo'))} | "
                f"Sugerido: {formato_numero_general(producto.get('cantidad_sugerida'))}"
            )

        QApplication.clipboard().setText("\n".join(lineas))
        QMessageBox.information(self, "Copiado", "Sugerencia copiada al portapapeles.")


class InventarioPage(QWidget):
    def __init__(self, pos_service=None, usuario_id=1):
        super().__init__()

        self.backend = InventarioServiceAdapter(usuario_id=usuario_id)
        self.pos = pos_service or self.backend

        self.actualizando_inventario = False
        self.timer_inventario = None

        self.productos_cache = []
        self.productos_visibles = []
        self.movimientos_cache = []
        self.movimientos_visibles = []

        self.filtro_producto_columna = None
        self.filtro_producto_valor = None
        self.filtro_movimiento_columna = None
        self.filtro_movimiento_valor = None

        self.input_busqueda = None
        self.tabla_productos = QTableWidget()
        self.tabla_movimientos = QTableWidget()

        self.label_ultima_actualizacion = None
        self.label_alertas = None
        self.label_estado_operacion = None

        self.labels = {}
        self.cards = {}

        self.btn_ingresar = None
        self.btn_ajustar = None
        self.btn_merma = None
        self.btn_precio = None
        self.btn_movimientos = None
        self.btn_copiar = None
        self.btn_nueva_categoria = None
        self.btn_editar_categoria = None
        self.btn_reposicion = None

        self.construir_interfaz()
        self.cargar_datos(mostrar_mensaje=True)
        self.iniciar_actualizacion_automatica()

    def iniciar_actualizacion_automatica(self):
        self.timer_inventario = QTimer(self)
        self.timer_inventario.timeout.connect(self.cargar_datos_automatico)
        self.timer_inventario.start(10000)

    def cargar_datos_automatico(self):
        if self.actualizando_inventario:
            return

        if QApplication.activeModalWidget():
            return

        self.cargar_datos(mostrar_mensaje=False)

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

        titulo = QLabel("Inventario")
        titulo.setObjectName("tituloPagina")
        titulo.setStyleSheet("font-size: 30px; font-weight: 900; color: #0F172A;")

        subtitulo = QLabel(
            "Controla ingresos, ajustes, mermas, precios, categorías, reposición y movimientos de stock."
        )
        subtitulo.setObjectName("subtituloPagina")
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("font-size: 14px; color: #64748B; font-weight: 700;")

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

        layout.addLayout(encabezado)

        cards = QGridLayout()
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(16)
        cards.setVerticalSpacing(14)

        self.labels["total_productos"] = self.crear_card(
            cards, 0, 0,
            "total_productos",
            "Productos activos",
            "0",
            "Productos disponibles en inventario",
            "azul",
        )

        self.labels["bajo_stock"] = self.crear_card(
            cards, 0, 1,
            "bajo_stock",
            "Bajo stock",
            "0",
            "Requieren reposición",
            "alerta",
        )

        self.labels["sin_stock"] = self.crear_card(
            cards, 0, 2,
            "sin_stock",
            "Sin stock",
            "0",
            "Productos agotados",
            "rojo",
        )

        self.labels["producto_seleccionado"] = self.crear_card(
            cards, 0, 3,
            "producto_seleccionado",
            "Producto seleccionado",
            "-",
            "Producto activo para acciones",
            "neutro",
        )

        self.labels["valor_costo"] = self.crear_card(
            cards, 1, 0,
            "valor_costo",
            "Inventario al costo",
            "$0",
            "Stock valorizado a precio compra",
            "neutro",
        )

        self.labels["valor_venta"] = self.crear_card(
            cards, 1, 1,
            "valor_venta",
            "Venta proyectada",
            "$0",
            "Stock valorizado a precio venta",
            "verde",
        )

        self.labels["margen_estimado"] = self.crear_card(
            cards, 1, 2,
            "margen_estimado",
            "Margen estimado",
            "$0",
            "Diferencia entre venta y costo",
            "morado",
        )

        self.labels["movimientos"] = self.crear_card(
            cards, 1, 3,
            "movimientos",
            "Movimientos cargados",
            "0",
            "Últimos movimientos visibles",
            "neutro",
        )

        for columna in range(4):
            cards.setColumnStretch(columna, 1)

        layout.addLayout(cards)

        self.label_alertas = QLabel("Cargando alertas de inventario...")
        self.label_alertas.setWordWrap(True)
        self.label_alertas.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_alertas)

        panel_busqueda = QFrame()
        panel_busqueda.setObjectName("panelBusquedaInventario")

        barra = QHBoxLayout(panel_busqueda)
        barra.setContentsMargins(16, 14, 16, 14)
        barra.setSpacing(12)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText(
            "Buscar producto por nombre, código de barra o categoría..."
        )
        self.input_busqueda.setMinimumHeight(44)
        self.input_busqueda.textChanged.connect(self.aplicar_filtro)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setMinimumHeight(44)
        btn_limpiar.setFixedWidth(140)
        btn_limpiar.clicked.connect(self.limpiar_busqueda)

        barra.addWidget(self.input_busqueda, 1)
        barra.addWidget(btn_limpiar)

        layout.addWidget(panel_busqueda)

        titulo_productos = QLabel("Productos")
        titulo_productos.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)
        layout.addWidget(titulo_productos)

        ayuda_productos = QLabel(
            "Click en un encabezado para ordenar. Doble click en una celda para filtrar por ese valor."
        )
        ayuda_productos.setWordWrap(True)
        ayuda_productos.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }
        """)
        layout.addWidget(ayuda_productos)

        self.tabla_productos.setColumnCount(10)
        self.tabla_productos.setHorizontalHeaderLabels([
            "ID",
            "Código",
            "Producto",
            "Categoría",
            "Precio compra",
            "Precio venta",
            "Margen",
            "Stock actual",
            "Stock mínimo",
            "Estado stock",
        ])
        self.preparar_tabla(self.tabla_productos)
        self.tabla_productos.setMinimumHeight(330)
        self.tabla_productos.itemSelectionChanged.connect(self.actualizar_producto_seleccionado)
        self.tabla_productos.cellDoubleClicked.connect(self.filtrar_producto_por_celda)

        layout.addWidget(self.tabla_productos)

        panel_acciones = QFrame()
        panel_acciones.setObjectName("panelAccionesInventario")

        acciones_principal = QVBoxLayout(panel_acciones)
        acciones_principal.setContentsMargins(16, 14, 16, 14)
        acciones_principal.setSpacing(12)

        fila_stock = QHBoxLayout()
        fila_stock.setSpacing(10)

        label_stock = QLabel("Stock y precios")
        label_stock.setFixedWidth(120)
        label_stock.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        label_stock.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 900;
                background: transparent;
            }
        """)

        self.btn_ingresar = QPushButton("Ingresar stock")
        self.btn_ingresar.setObjectName("botonPrincipal")
        self.btn_ingresar.setMinimumHeight(42)
        self.btn_ingresar.setMinimumWidth(145)
        self.btn_ingresar.clicked.connect(self.ingresar_stock)

        self.btn_ajustar = QPushButton("Ajustar stock")
        self.btn_ajustar.setMinimumHeight(42)
        self.btn_ajustar.setMinimumWidth(135)
        self.btn_ajustar.clicked.connect(self.ajustar_stock)

        self.btn_merma = QPushButton("Registrar merma")
        self.btn_merma.setMinimumHeight(42)
        self.btn_merma.setMinimumWidth(150)
        self.btn_merma.clicked.connect(self.registrar_merma)

        self.btn_precio = QPushButton("Actualizar precio")
        self.btn_precio.setMinimumHeight(42)
        self.btn_precio.setMinimumWidth(150)
        self.btn_precio.clicked.connect(self.actualizar_precio)

        self.btn_movimientos = QPushButton("Ver movimientos")
        self.btn_movimientos.setMinimumHeight(42)
        self.btn_movimientos.setMinimumWidth(150)
        self.btn_movimientos.clicked.connect(self.cargar_movimientos_producto)

        fila_stock.addWidget(label_stock)
        fila_stock.addWidget(self.btn_ingresar)
        fila_stock.addWidget(self.btn_ajustar)
        fila_stock.addWidget(self.btn_merma)
        fila_stock.addWidget(self.btn_precio)
        fila_stock.addWidget(self.btn_movimientos)
        fila_stock.addStretch()

        fila_gestion = QHBoxLayout()
        fila_gestion.setSpacing(10)

        label_gestion = QLabel("Gestión")
        label_gestion.setFixedWidth(120)
        label_gestion.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        label_gestion.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 900;
                background: transparent;
            }
        """)

        self.btn_copiar = QPushButton("Copiar producto")
        self.btn_copiar.setMinimumHeight(42)
        self.btn_copiar.setMinimumWidth(145)
        self.btn_copiar.clicked.connect(self.copiar_producto)

        self.btn_nueva_categoria = QPushButton("Nueva categoría")
        self.btn_nueva_categoria.setMinimumHeight(42)
        self.btn_nueva_categoria.setMinimumWidth(150)
        self.btn_nueva_categoria.clicked.connect(self.abrir_dialogo_crear_categoria)

        self.btn_editar_categoria = QPushButton("Editar categoría")
        self.btn_editar_categoria.setMinimumHeight(42)
        self.btn_editar_categoria.setMinimumWidth(145)
        self.btn_editar_categoria.clicked.connect(self.editar_categoria_seleccionada)

        self.btn_reposicion = QPushButton("Sugerencia reposición")
        self.btn_reposicion.setObjectName("botonPrincipal")
        self.btn_reposicion.setMinimumHeight(42)
        self.btn_reposicion.setMinimumWidth(185)
        self.btn_reposicion.clicked.connect(self.mostrar_sugerencia_reposicion)

        fila_gestion.addWidget(label_gestion)
        fila_gestion.addWidget(self.btn_copiar)
        fila_gestion.addWidget(self.btn_nueva_categoria)
        fila_gestion.addWidget(self.btn_editar_categoria)
        fila_gestion.addStretch()
        fila_gestion.addWidget(self.btn_reposicion)

        acciones_principal.addLayout(fila_stock)
        acciones_principal.addLayout(fila_gestion)

        layout.addWidget(panel_acciones)

        titulo_movimientos = QLabel("Últimos movimientos de stock")
        titulo_movimientos.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 20px;
                font-weight: 900;
                background: transparent;
            }
        """)
        layout.addWidget(titulo_movimientos)

        ayuda_movimientos = QLabel(
            "Click en un encabezado para ordenar movimientos. Doble click en una celda para filtrar esa tabla."
        )
        ayuda_movimientos.setWordWrap(True)
        ayuda_movimientos.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }
        """)
        layout.addWidget(ayuda_movimientos)

        self.tabla_movimientos.setColumnCount(9)
        self.tabla_movimientos.setHorizontalHeaderLabels([
            "Fecha",
            "Producto",
            "Tipo",
            "Anterior",
            "Movimiento",
            "Nuevo",
            "Precio compra",
            "Usuario",
            "Comentario",
        ])
        self.preparar_tabla(self.tabla_movimientos)
        self.tabla_movimientos.setMinimumHeight(260)
        self.tabla_movimientos.cellDoubleClicked.connect(self.filtrar_movimiento_por_celda)

        layout.addWidget(self.tabla_movimientos)

        self.label_estado_operacion = QLabel("Inventario listo para administrar.")
        self.label_estado_operacion.setWordWrap(True)
        self.label_estado_operacion.setStyleSheet(self.estilo_alerta("info"))
        layout.addWidget(self.label_estado_operacion)

        self.aplicar_estilos()
        self.actualizar_botones_accion()

    def crear_card(self, grid, fila, columna, key, titulo, valor, detalle, tipo="neutro"):
        card = QFrame()
        card.setObjectName("cardInventario")
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

    def preparar_tabla(self, tabla):
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setShowGrid(True)

        tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tabla.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        tabla.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        tabla.setSortingEnabled(True)
        tabla.horizontalHeader().setSectionsClickable(True)
        tabla.horizontalHeader().setSortIndicatorShown(True)

        if tabla is self.tabla_productos:
            tabla.horizontalHeader().sectionClicked.connect(self.aviso_ordenamiento_productos)

        if tabla is self.tabla_movimientos:
            tabla.horizontalHeader().sectionClicked.connect(self.aviso_ordenamiento_movimientos)

    def cargar_datos(self, mostrar_mensaje=False):
        if self.actualizando_inventario:
            return

        self.actualizando_inventario = True
        producto_id_anterior = self.obtener_id_producto_seleccionado_silencioso()

        try:
            self.cargar_productos()
            self.cargar_movimientos()

            self.restaurar_seleccion_producto(producto_id_anterior)
            self.actualizar_alertas()

            if mostrar_mensaje:
                self.actualizar_estado_operacion(
                    "Inventario cargado correctamente.",
                    "ok",
                )

        except Exception as error:
            self.actualizar_estado_operacion(
                f"No se pudo actualizar inventario automáticamente: {error}",
                "error",
            )

        finally:
            self.actualizar_label_ultima_actualizacion()
            self.actualizando_inventario = False
            self.actualizar_botones_accion()

    def cargar_productos(self):
        resultado = self.obtener_productos_backend()

        if not resultado.get("ok"):
            self.productos_cache = []
            self.productos_visibles = []
            self.cargar_tabla_productos([])
            self.actualizar_resumen_productos([])
            self.actualizar_estado_operacion(
                resultado.get("mensaje", "No se pudieron cargar los productos."),
                "error",
            )
            return

        self.productos_cache = resultado.get("data") or []
        self.productos_visibles = self.filtrar_productos_local(
            self.productos_cache,
            self.input_busqueda.text().strip(),
        )

        self.cargar_tabla_productos(self.productos_visibles)
        self.actualizar_resumen_productos(self.productos_cache)

    def obtener_productos_backend(self):
        posibles_metodos = [
            "obtener_productos",
            "listar_productos_sistema",
            "obtener_productos_sistema",
            "listar_productos",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                resultado = metodo()
            except Exception:
                continue

            if isinstance(resultado, dict) and "ok" in resultado:
                return resultado

            return {
                "ok": True,
                "mensaje": "Productos cargados correctamente.",
                "data": resultado or [],
            }

        return self.backend.obtener_productos()

    def aplicar_filtro(self):
        self.productos_visibles = self.filtrar_productos_local(
            self.productos_cache,
            self.input_busqueda.text().strip(),
        )

        self.cargar_tabla_productos(self.productos_visibles)
        self.actualizar_estado_operacion(
            f"Mostrando {len(self.productos_visibles)} producto(s).",
            "info",
        )
        self.actualizar_botones_accion()

    def limpiar_busqueda(self):
        self.input_busqueda.clear()

        self.filtro_producto_columna = None
        self.filtro_producto_valor = None
        self.filtro_movimiento_columna = None
        self.filtro_movimiento_valor = None

        self.input_busqueda.setFocus()
        self.aplicar_filtro()

        self.movimientos_visibles = self.movimientos_cache
        self.cargar_tabla_movimientos(self.movimientos_visibles)

        self.actualizar_estado_operacion(
            "Filtros limpiados. Mostrando productos y movimientos disponibles.",
            "info",
        )

    def filtrar_productos_local(self, productos, texto):
        texto = str(texto or "").lower().strip()
        filtrados = []

        for producto in productos:
            campos = [
                producto.get("id"),
                producto.get("codigo_barra"),
                producto.get("nombre"),
                producto.get("categoria"),
                producto.get("sku"),
                self.calcular_estado_stock(producto),
            ]

            texto_producto = " ".join(str(campo or "").lower() for campo in campos)

            if texto and texto not in texto_producto:
                continue

            if self.filtro_producto_columna is not None and self.filtro_producto_valor is not None:
                valor_visible, _ = self.obtener_valor_columna_producto(
                    producto,
                    self.filtro_producto_columna,
                )

                if str(valor_visible).strip() != str(self.filtro_producto_valor).strip():
                    continue

            filtrados.append(producto)

        return filtrados

    def cargar_tabla_productos(self, productos):
        self.tabla_productos.setSortingEnabled(False)
        self.tabla_productos.setRowCount(0)

        if not productos:
            self.tabla_productos.setRowCount(1)
            item = QTableWidgetItem("No hay productos para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_productos.setItem(0, 0, item)

            for columna in range(1, self.tabla_productos.columnCount()):
                self.tabla_productos.setItem(0, columna, QTableWidgetItem(""))

            self.tabla_productos.setSortingEnabled(False)
            return

        for fila, producto in enumerate(productos):
            self.tabla_productos.insertRow(fila)

            estado_stock = self.calcular_estado_stock(producto)

            for columna in range(self.tabla_productos.columnCount()):
                valor_visible, valor_orden = self.obtener_valor_columna_producto(
                    producto,
                    columna,
                )

                item = ItemInventarioOrdenable(str(valor_visible or ""))
                item.setData(Qt.ItemDataRole.UserRole, valor_orden)

                if columna in [0, 4, 5, 6, 7, 8, 9]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )

                item.setToolTip(str(valor_visible or ""))

                if estado_stock == "SIN STOCK":
                    item.setBackground(QColor("#FEF2F2"))
                    item.setForeground(QColor("#991B1B"))
                elif estado_stock == "BAJO STOCK":
                    item.setBackground(QColor("#FFFBEB"))
                    item.setForeground(QColor("#92400E"))
                else:
                    item.setBackground(QColor("#FFFFFF"))
                    item.setForeground(QColor("#0F172A"))

                self.tabla_productos.setItem(fila, columna, item)

        self.tabla_productos.setSortingEnabled(True)

    def obtener_valor_columna_producto(self, producto, columna):
        precio_compra = self.decimal(producto.get("precio_compra"))
        precio_venta = self.decimal(producto.get("precio_venta"))
        margen = precio_venta - precio_compra
        stock = self.decimal(producto.get("stock_actual"))
        stock_minimo = self.decimal(producto.get("stock_minimo"))
        estado_stock = self.calcular_estado_stock(producto)

        if columna == 0:
            valor = producto.get("id") or 0
            try:
                return valor, int(valor)
            except Exception:
                return valor, 0

        if columna == 1:
            valor = producto.get("codigo_barra") or ""
            return valor, str(valor).lower()

        if columna == 2:
            valor = producto.get("nombre") or ""
            return valor, str(valor).lower()

        if columna == 3:
            valor = producto.get("categoria") or "Sin categoría"
            return valor, str(valor).lower()

        if columna == 4:
            return self.formato_pesos(precio_compra), precio_compra

        if columna == 5:
            return self.formato_pesos(precio_venta), precio_venta

        if columna == 6:
            return self.formato_pesos(margen), margen

        if columna == 7:
            return self.formato_numero(stock), stock

        if columna == 8:
            return self.formato_numero(stock_minimo), stock_minimo

        if columna == 9:
            return estado_stock, str(estado_stock).lower()

        return "", ""

    def filtrar_producto_por_celda(self, fila, columna):
        item = self.tabla_productos.item(fila, columna)

        if item is None:
            return

        valor = item.text().strip()

        if not valor or valor == "No hay productos para mostrar.":
            return

        encabezado = self.tabla_productos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.filtro_producto_columna = columna
        self.filtro_producto_valor = valor
        self.aplicar_filtro()

        self.actualizar_estado_operacion(
            f"Filtro aplicado en productos: {encabezado.text()} = {valor}. Presiona Limpiar para volver a ver todo.",
            "info",
        )

    def aviso_ordenamiento_productos(self, columna):
        encabezado = self.tabla_productos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.actualizar_estado_operacion(
            f"Tabla de productos ordenada por: {encabezado.text()}.",
            "info",
        )

    def actualizar_resumen_productos(self, productos):
        total_productos = len(productos)
        bajo_stock = 0
        sin_stock = 0
        valor_costo = Decimal("0")
        valor_venta = Decimal("0")

        for producto in productos:
            stock = self.decimal(producto.get("stock_actual"))
            minimo = self.decimal(producto.get("stock_minimo"))
            precio_compra = self.decimal(producto.get("precio_compra"))
            precio_venta = self.decimal(producto.get("precio_venta"))

            if stock <= 0:
                sin_stock += 1

            if stock <= minimo:
                bajo_stock += 1

            valor_costo += stock * precio_compra
            valor_venta += stock * precio_venta

        margen_estimado = valor_venta - valor_costo

        self.labels["total_productos"].setText(str(total_productos))
        self.labels["bajo_stock"].setText(str(bajo_stock))
        self.labels["sin_stock"].setText(str(sin_stock))
        self.labels["valor_costo"].setText(self.formato_pesos(valor_costo))
        self.labels["valor_venta"].setText(self.formato_pesos(valor_venta))
        self.labels["margen_estimado"].setText(self.formato_pesos(margen_estimado))

        self.cambiar_tipo_card("bajo_stock", "alerta" if bajo_stock > 0 else "verde")
        self.cambiar_tipo_card("sin_stock", "rojo" if sin_stock > 0 else "verde")
        self.cambiar_tipo_card("margen_estimado", "verde" if margen_estimado >= 0 else "rojo")

    def calcular_estado_stock(self, producto):
        stock = self.decimal(producto.get("stock_actual"))
        minimo = self.decimal(producto.get("stock_minimo"))

        if stock <= 0:
            return "SIN STOCK"

        if stock <= minimo:
            return "BAJO STOCK"

        return "OK"

    def cargar_movimientos(self):
        resultado = self.obtener_movimientos_backend(producto_id=None, limite=70)

        if not resultado.get("ok"):
            self.movimientos_cache = []
            self.cargar_tabla_movimientos([])
            self.actualizar_estado_operacion(
                resultado.get("mensaje", "No se pudieron cargar los movimientos."),
                "error",
            )
            return

        self.movimientos_cache = resultado.get("data") or []
        self.movimientos_visibles = self.filtrar_movimientos_local(self.movimientos_cache)
        self.cargar_tabla_movimientos(self.movimientos_visibles)

    def obtener_movimientos_backend(self, producto_id=None, limite=100):
        posibles_metodos = [
            "obtener_movimientos_inventario",
            "obtener_movimientos_stock",
            "listar_movimientos_stock",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if not callable(metodo):
                continue

            try:
                return metodo(producto_id=producto_id, limite=limite)
            except TypeError:
                try:
                    return metodo(producto_id, limite)
                except Exception:
                    continue
            except Exception:
                continue

        return self.backend.obtener_movimientos_inventario(producto_id=producto_id, limite=limite)

    def cargar_movimientos_producto(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        resultado = self.obtener_movimientos_backend(
            producto_id=producto.get("id"),
            limite=100,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudieron cargar los movimientos del producto."),
            )
            return

        movimientos = resultado.get("data") or []
        self.movimientos_cache = movimientos
        self.filtro_movimiento_columna = None
        self.filtro_movimiento_valor = None
        self.movimientos_visibles = self.filtrar_movimientos_local(self.movimientos_cache)
        self.cargar_tabla_movimientos(self.movimientos_visibles)

        self.actualizar_estado_operacion(
            f"Mostrando movimientos de: {producto.get('nombre')}",
            "info",
        )

    def cargar_tabla_movimientos(self, movimientos):
        self.tabla_movimientos.setSortingEnabled(False)
        self.tabla_movimientos.setRowCount(0)

        if not movimientos:
            self.tabla_movimientos.setRowCount(1)
            item = QTableWidgetItem("No hay movimientos para mostrar.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_movimientos.setItem(0, 0, item)

            for columna in range(1, self.tabla_movimientos.columnCount()):
                self.tabla_movimientos.setItem(0, columna, QTableWidgetItem(""))

            self.labels["movimientos"].setText("0")
            self.tabla_movimientos.setSortingEnabled(False)
            return

        for fila, movimiento in enumerate(movimientos):
            self.tabla_movimientos.insertRow(fila)

            tipo = str(movimiento.get("tipo_movimiento") or "").upper()

            for columna in range(self.tabla_movimientos.columnCount()):
                valor_visible, valor_orden = self.obtener_valor_columna_movimiento(
                    movimiento,
                    columna,
                )

                item = ItemInventarioOrdenable(str(valor_visible or ""))
                item.setData(Qt.ItemDataRole.UserRole, valor_orden)

                if columna in [1, 8]:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if tipo in ["ENTRADA", "AJUSTE_POSITIVO"]:
                    item.setForeground(QColor("#166534"))
                elif tipo in ["MERMA", "VENTA", "AJUSTE_NEGATIVO"]:
                    item.setForeground(QColor("#B91C1C"))
                else:
                    item.setForeground(QColor("#0F172A"))

                item.setToolTip(str(valor_visible or ""))
                self.tabla_movimientos.setItem(fila, columna, item)

        self.labels["movimientos"].setText(str(len(movimientos)))
        self.tabla_movimientos.setSortingEnabled(True)

    def filtrar_movimientos_local(self, movimientos):
        filtrados = []

        for movimiento in movimientos:
            if self.filtro_movimiento_columna is not None and self.filtro_movimiento_valor is not None:
                valor_visible, _ = self.obtener_valor_columna_movimiento(
                    movimiento,
                    self.filtro_movimiento_columna,
                )

                if str(valor_visible).strip() != str(self.filtro_movimiento_valor).strip():
                    continue

            filtrados.append(movimiento)

        return filtrados

    def obtener_valor_columna_movimiento(self, movimiento, columna):
        if columna == 0:
            valor = self.formato_fecha(movimiento.get("created_at"))
            fecha_original = movimiento.get("created_at")

            try:
                return valor, fecha_original.timestamp()
            except Exception:
                return valor, str(valor).lower()

        if columna == 1:
            valor = movimiento.get("producto") or ""
            return valor, str(valor).lower()

        if columna == 2:
            valor = movimiento.get("tipo_movimiento") or ""
            return valor, str(valor).lower()

        if columna == 3:
            valor = self.decimal(movimiento.get("cantidad_anterior"))
            return self.formato_numero(valor), valor

        if columna == 4:
            valor = self.decimal(movimiento.get("cantidad_movimiento"))
            return self.formato_numero(valor), valor

        if columna == 5:
            valor = self.decimal(movimiento.get("cantidad_nueva"))
            return self.formato_numero(valor), valor

        if columna == 6:
            valor = self.decimal(movimiento.get("precio_compra"))
            return self.formato_pesos(valor), valor

        if columna == 7:
            valor = movimiento.get("usuario") or ""
            return valor, str(valor).lower()

        if columna == 8:
            valor = movimiento.get("comentario") or ""
            return valor, str(valor).lower()

        return "", ""

    def filtrar_movimiento_por_celda(self, fila, columna):
        item = self.tabla_movimientos.item(fila, columna)

        if item is None:
            return

        valor = item.text().strip()

        if not valor or valor == "No hay movimientos para mostrar.":
            return

        encabezado = self.tabla_movimientos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.filtro_movimiento_columna = columna
        self.filtro_movimiento_valor = valor
        self.movimientos_visibles = self.filtrar_movimientos_local(self.movimientos_cache)
        self.cargar_tabla_movimientos(self.movimientos_visibles)

        self.actualizar_estado_operacion(
            f"Filtro aplicado en movimientos: {encabezado.text()} = {valor}. Presiona Limpiar para volver a ver todo.",
            "info",
        )

    def aviso_ordenamiento_movimientos(self, columna):
        encabezado = self.tabla_movimientos.horizontalHeaderItem(columna)

        if encabezado is None:
            return

        self.actualizar_estado_operacion(
            f"Tabla de movimientos ordenada por: {encabezado.text()}.",
            "info",
        )

    def actualizar_alertas(self):
        alertas = []

        bajo_stock = int(self.labels["bajo_stock"].text() or 0)
        sin_stock = int(self.labels["sin_stock"].text() or 0)

        if sin_stock > 0:
            alertas.append(f"{sin_stock} producto(s) sin stock.")

        if bajo_stock > 0:
            alertas.append(f"{bajo_stock} producto(s) bajo stock.")

        if not self.productos_cache:
            alertas.append("No hay productos cargados en inventario.")

        if not alertas:
            self.label_alertas.setText(
                "Inventario normal: no hay alertas importantes de stock."
            )
            self.label_alertas.setStyleSheet(self.estilo_alerta("ok"))
            return

        self.label_alertas.setText("Alertas de inventario: " + " | ".join(alertas))
        self.label_alertas.setStyleSheet(self.estilo_alerta("alerta"))

    def obtener_id_producto_seleccionado_silencioso(self):
        fila = self.tabla_productos.currentRow()

        if fila < 0:
            return None

        item_id = self.tabla_productos.item(fila, 0)

        if item_id is None:
            return None

        try:
            return int(item_id.text())
        except Exception:
            return None

    def restaurar_seleccion_producto(self, producto_id):
        if producto_id is None:
            return

        for fila in range(self.tabla_productos.rowCount()):
            item_id = self.tabla_productos.item(fila, 0)

            if item_id and item_id.text().isdigit() and int(item_id.text()) == producto_id:
                self.tabla_productos.selectRow(fila)
                return

    def seleccionar_producto_externo(self, producto):
        if not producto:
            return

        producto_id = producto.get("id")
        codigo = producto.get("codigo_barra")
        nombre = producto.get("nombre")

        texto_busqueda = str(codigo or nombre or producto_id or "").strip()

        self.filtro_producto_columna = None
        self.filtro_producto_valor = None

        if self.input_busqueda is not None:
            self.input_busqueda.blockSignals(True)
            self.input_busqueda.setText(texto_busqueda)
            self.input_busqueda.blockSignals(False)

        self.productos_visibles = self.filtrar_productos_local(
            self.productos_cache,
            texto_busqueda,
        )

        if not self.productos_visibles and producto_id is not None:
            self.productos_visibles = [
                p for p in self.productos_cache
                if str(p.get("id")) == str(producto_id)
            ]

        self.cargar_tabla_productos(self.productos_visibles)

        seleccionado = False

        if producto_id is not None:
            seleccionado = self.seleccionar_fila_producto_por_columna(
                columna=0,
                valor_buscado=str(producto_id),
            )

        if not seleccionado and codigo:
            seleccionado = self.seleccionar_fila_producto_por_columna(
                columna=1,
                valor_buscado=str(codigo),
            )

        if not seleccionado and nombre:
            seleccionado = self.seleccionar_fila_producto_por_columna(
                columna=2,
                valor_buscado=str(nombre),
            )

        self.actualizar_producto_seleccionado()
        self.actualizar_botones_accion()

        if seleccionado:
            self.actualizar_estado_operacion(
                f"Producto seleccionado desde Productos: {nombre or codigo or producto_id}.",
                "ok",
            )
        else:
            self.actualizar_estado_operacion(
                "Llegaste desde Productos, pero no se pudo seleccionar automáticamente el producto. "
                "Búscalo manualmente en Inventario.",
                "alerta",
            )

    def seleccionar_fila_producto_por_columna(self, columna, valor_buscado):
        valor_buscado = str(valor_buscado or "").strip().lower()

        if not valor_buscado:
            return False

        for fila in range(self.tabla_productos.rowCount()):
            item = self.tabla_productos.item(fila, columna)

            if item is None:
                continue

            valor_item = item.text().strip().lower()

            if valor_item == valor_buscado:
                self.tabla_productos.selectRow(fila)
                self.tabla_productos.scrollToItem(item)
                return True

        return False

    def obtener_producto_seleccionado(self, mostrar_mensaje=True):
        producto_id = self.obtener_id_producto_seleccionado_silencioso()

        if producto_id is None:
            if mostrar_mensaje:
                QMessageBox.warning(
                    self,
                    "Sin selección",
                    "Selecciona un producto de la tabla.",
                )
            return None

        for producto in self.productos_cache:
            try:
                if int(producto.get("id")) == producto_id:
                    return producto
            except Exception:
                continue

        if mostrar_mensaje:
            QMessageBox.warning(
                self,
                "Producto no encontrado",
                "No se pudo encontrar el producto seleccionado.",
            )

        return None

    def actualizar_producto_seleccionado(self):
        producto = self.obtener_producto_seleccionado(mostrar_mensaje=False)

        if not producto:
            self.labels["producto_seleccionado"].setText("-")
            self.cambiar_tipo_card("producto_seleccionado", "neutro")
            self.actualizar_botones_accion()
            return

        nombre = str(producto.get("nombre") or "-")
        stock = self.formato_numero(producto.get("stock_actual"))

        texto = f"{nombre} | Stock: {stock}"

        if len(texto) > 42:
            texto = texto[:39] + "..."

        self.labels["producto_seleccionado"].setText(texto)

        estado = self.calcular_estado_stock(producto)

        if estado == "OK":
            self.cambiar_tipo_card("producto_seleccionado", "verde")
        elif estado == "BAJO STOCK":
            self.cambiar_tipo_card("producto_seleccionado", "alerta")
        else:
            self.cambiar_tipo_card("producto_seleccionado", "rojo")

        self.actualizar_botones_accion()

    def ingresar_stock(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        dialogo = IngresoStockDialog(
            pos_service=self.pos,
            producto=producto,
            parent=self,
        )

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.ingresar_stock_backend(
            producto_id=producto.get("id"),
            cantidad=datos["cantidad"],
            precio_compra=datos["precio_compra"],
            comentario=datos["comentario"],
            actualizar_precio_compra=datos["actualizar_precio_compra"],
        )

        if not resultado.get("ok"):
            QMessageBox.warning(self, "Error", resultado.get("mensaje", "No se pudo ingresar stock."))
            return

        QMessageBox.information(
            self,
            "Stock ingresado",
            resultado.get("mensaje", "Stock ingresado correctamente."),
        )
        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion("Stock ingresado correctamente.", "ok")

    def ajustar_stock(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        dialogo = AjusteStockDialog(
            producto=producto,
            parent=self,
        )

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.ajustar_stock_backend(
            producto_id=producto.get("id"),
            nuevo_stock=datos["nuevo_stock"],
            comentario=datos["comentario"],
        )

        if not resultado.get("ok"):
            QMessageBox.warning(self, "Error", resultado.get("mensaje", "No se pudo ajustar stock."))
            return

        QMessageBox.information(
            self,
            "Stock ajustado",
            resultado.get("mensaje", "Stock ajustado correctamente."),
        )
        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion("Stock ajustado correctamente.", "ok")

    def registrar_merma(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        confirmar = QMessageBox.question(
            self,
            "Registrar merma",
            f"¿Deseas registrar una merma para este producto?\n\n{producto.get('nombre')}",
        )

        if confirmar != QMessageBox.StandardButton.Yes:
            return

        dialogo = MermaDialog(
            producto=producto,
            parent=self,
        )

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.registrar_merma_backend(
            producto_id=producto.get("id"),
            cantidad=datos["cantidad"],
            comentario=datos["comentario"],
        )

        if not resultado.get("ok"):
            QMessageBox.warning(self, "Error", resultado.get("mensaje", "No se pudo registrar merma."))
            return

        QMessageBox.information(
            self,
            "Merma registrada",
            resultado.get("mensaje", "Merma registrada correctamente."),
        )
        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion("Merma registrada correctamente.", "ok")

    def actualizar_precio(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        dialogo = PrecioDialog(
            pos_service=self.pos,
            producto=producto,
            parent=self,
        )

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.actualizar_precio_backend(
            producto_id=producto.get("id"),
            nuevo_precio_venta=datos["nuevo_precio_venta"],
            nuevo_precio_compra=datos["nuevo_precio_compra"],
        )

        if not resultado.get("ok"):
            QMessageBox.warning(self, "Error", resultado.get("mensaje", "No se pudo actualizar precio."))
            return

        QMessageBox.information(
            self,
            "Precio actualizado",
            resultado.get("mensaje", "Precio actualizado correctamente."),
        )
        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion("Precio actualizado correctamente.", "ok")

    def abrir_dialogo_crear_categoria(self):
        dialogo = CategoriaDialog(parent=self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        resultado = self.crear_categoria_backend(datos["nombre"])

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo crear la categoría."),
            )
            return

        QMessageBox.information(
            self,
            "Categoría creada",
            resultado.get("mensaje", "Categoría creada correctamente."),
        )

        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion(
            f"Categoría creada correctamente: {datos['nombre']}",
            "ok",
        )

    def editar_categoria_seleccionada(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        categoria_id = producto.get("categoria_id")
        categoria_nombre = str(producto.get("categoria") or "").strip()

        if not categoria_id and categoria_nombre:
            resultado_categoria = self.obtener_categoria_id_por_nombre_backend(categoria_nombre)

            if resultado_categoria.get("ok"):
                categoria_id = resultado_categoria.get("data", {}).get("id")
                categoria_nombre = resultado_categoria.get("data", {}).get("nombre") or categoria_nombre

        if not categoria_id:
            QMessageBox.warning(
                self,
                "Sin categoría editable",
                "El producto seleccionado no tiene una categoría asignada o no se pudo obtener el ID de la categoría.",
            )
            return

        if not categoria_nombre:
            categoria_nombre = "Sin nombre"

        dialogo = CategoriaDialog(
            categoria={
                "id": categoria_id,
                "nombre": categoria_nombre,
            },
            parent=self,
        )

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()
        nuevo_nombre = datos["nombre"]

        if nuevo_nombre.strip().lower() == categoria_nombre.strip().lower():
            self.actualizar_estado_operacion(
                "No se realizaron cambios: el nombre de la categoría es el mismo.",
                "info",
            )
            return

        resultado = self.actualizar_nombre_categoria_backend(
            categoria_id=categoria_id,
            nuevo_nombre=nuevo_nombre,
        )

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo editar la categoría."),
            )
            return

        QMessageBox.information(
            self,
            "Categoría actualizada",
            resultado.get("mensaje", "Categoría actualizada correctamente."),
        )

        self.cargar_datos(mostrar_mensaje=False)
        self.actualizar_estado_operacion(
            f"Categoría actualizada: {categoria_nombre} → {nuevo_nombre}",
            "ok",
        )

    def crear_categoria_backend(self, nombre):
        posibles_metodos = [
            "crear_categoria",
            "crear_categoria_sistema",
            "crear_categoria_producto",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if callable(metodo):
                resultado = metodo(nombre)

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Categoría creada correctamente.",
                    "data": resultado,
                }

        return self.backend.crear_categoria(nombre)

    def actualizar_nombre_categoria_backend(self, categoria_id, nuevo_nombre):
        posibles_metodos = [
            "actualizar_nombre_categoria",
            "actualizar_categoria",
            "editar_categoria",
            "editar_nombre_categoria",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo(categoria_id, nuevo_nombre)
                except TypeError:
                    try:
                        resultado = metodo(
                            categoria_id=categoria_id,
                            nuevo_nombre=nuevo_nombre,
                        )
                    except Exception:
                        continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Categoría actualizada correctamente.",
                    "data": resultado,
                }

        return self.backend.actualizar_nombre_categoria(
            categoria_id=categoria_id,
            nuevo_nombre=nuevo_nombre,
        )

    def obtener_categoria_id_por_nombre_backend(self, nombre):
        posibles_metodos = [
            "obtener_categoria_id_por_nombre",
            "buscar_categoria_por_nombre",
        ]

        for nombre_metodo in posibles_metodos:
            metodo = getattr(self.pos, nombre_metodo, None)

            if callable(metodo):
                try:
                    resultado = metodo(nombre)
                except Exception:
                    continue

                if isinstance(resultado, dict) and "ok" in resultado:
                    return resultado

                return {
                    "ok": True,
                    "mensaje": "Categoría encontrada.",
                    "data": resultado,
                }

        return self.backend.obtener_categoria_id_por_nombre(nombre)

    def mostrar_sugerencia_reposicion(self):
        resultado = self.sugerencia_reposicion_backend()

        if not resultado.get("ok"):
            QMessageBox.warning(
                self,
                "Error",
                resultado.get("mensaje", "No se pudo generar sugerencia de reposición."),
            )
            return

        productos = resultado.get("data") or []

        if not productos:
            QMessageBox.information(
                self,
                "Reposición",
                "No hay productos que necesiten reposición.",
            )
            return

        dialogo = ReposicionDialog(
            pos_service=self.pos,
            productos=productos,
            parent=self,
        )
        dialogo.exec()

    def copiar_producto(self):
        producto = self.obtener_producto_seleccionado()

        if not producto:
            return

        texto = "\n".join([
            "PRODUCTO INVENTARIO",
            "========================",
            f"ID: {producto.get('id')}",
            f"Código: {producto.get('codigo_barra')}",
            f"Nombre: {producto.get('nombre')}",
            f"Categoría: {producto.get('categoria') or 'Sin categoría'}",
            f"Precio compra: {self.formato_pesos(producto.get('precio_compra'))}",
            f"Precio venta: {self.formato_pesos(producto.get('precio_venta'))}",
            f"Stock actual: {self.formato_numero(producto.get('stock_actual'))}",
            f"Stock mínimo: {self.formato_numero(producto.get('stock_minimo'))}",
            f"Estado stock: {self.calcular_estado_stock(producto)}",
        ])

        QApplication.clipboard().setText(texto)

        self.actualizar_estado_operacion(
            "Datos del producto copiados al portapapeles.",
            "ok",
        )

    def actualizar_botones_accion(self):
        producto = self.obtener_producto_seleccionado(mostrar_mensaje=False)
        hay_producto = producto is not None

        for boton in [
            self.btn_ingresar,
            self.btn_ajustar,
            self.btn_merma,
            self.btn_precio,
            self.btn_movimientos,
            self.btn_copiar,
        ]:
            if boton is not None:
                boton.setEnabled(hay_producto)

        if self.btn_nueva_categoria is not None:
            self.btn_nueva_categoria.setEnabled(True)

        if self.btn_editar_categoria is not None:
            tiene_categoria = False

            if producto:
                tiene_categoria = bool(producto.get("categoria_id") or producto.get("categoria"))

            self.btn_editar_categoria.setEnabled(hay_producto and tiene_categoria)

        if self.btn_reposicion is not None:
            self.btn_reposicion.setEnabled(True)

    def ingresar_stock_backend(self, producto_id, cantidad, precio_compra, comentario, actualizar_precio_compra):
        metodo = getattr(self.pos, "ingresar_stock_producto", None)

        if callable(metodo):
            return metodo(
                producto_id=producto_id,
                cantidad=cantidad,
                precio_compra=precio_compra,
                comentario=comentario,
                actualizar_precio_compra=actualizar_precio_compra,
            )

        return self.backend.ingresar_stock_producto(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_compra=precio_compra,
            comentario=comentario,
            actualizar_precio_compra=actualizar_precio_compra,
        )

    def ajustar_stock_backend(self, producto_id, nuevo_stock, comentario):
        metodo = getattr(self.pos, "ajustar_stock_producto", None)

        if callable(metodo):
            return metodo(
                producto_id=producto_id,
                nuevo_stock=nuevo_stock,
                comentario=comentario,
            )

        return self.backend.ajustar_stock_producto(
            producto_id=producto_id,
            nuevo_stock=nuevo_stock,
            comentario=comentario,
        )

    def registrar_merma_backend(self, producto_id, cantidad, comentario):
        metodo = getattr(self.pos, "registrar_merma_producto", None)

        if callable(metodo):
            return metodo(
                producto_id=producto_id,
                cantidad=cantidad,
                comentario=comentario,
            )

        return self.backend.registrar_merma_producto(
            producto_id=producto_id,
            cantidad=cantidad,
            comentario=comentario,
        )

    def actualizar_precio_backend(self, producto_id, nuevo_precio_venta, nuevo_precio_compra):
        metodo = getattr(self.pos, "actualizar_precio_producto_sistema", None)

        if callable(metodo):
            return metodo(
                producto_id=producto_id,
                nuevo_precio_venta=nuevo_precio_venta,
                nuevo_precio_compra=nuevo_precio_compra,
            )

        return self.backend.actualizar_precio_producto_sistema(
            producto_id=producto_id,
            nuevo_precio_venta=nuevo_precio_venta,
            nuevo_precio_compra=nuevo_precio_compra,
        )

    def sugerencia_reposicion_backend(self):
        metodo = getattr(self.pos, "obtener_sugerencia_reposicion", None)

        if callable(metodo):
            return metodo()

        return self.backend.obtener_sugerencia_reposicion()

    def decimal(self, valor):
        return _decimal(valor)

    def formato_pesos(self, valor):
        metodo = getattr(self.pos, "formato_pesos", None)

        if callable(metodo):
            try:
                return metodo(valor)
            except Exception:
                pass

        return self.backend.formato_pesos(valor)

    def formato_fecha(self, fecha):
        metodo = getattr(self.pos, "formato_fecha", None)

        if callable(metodo):
            try:
                return metodo(fecha)
            except Exception:
                pass

        return self.backend.formato_fecha(fecha)

    def formato_numero(self, valor):
        return formato_numero_general(valor)

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

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QFrame#panelBusquedaInventario {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#panelAccionesInventario {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardInventario {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }

            QFrame#cardInventario[tipo="verde"] {
                background-color: #ECFDF5;
                border: 1px solid #BBF7D0;
            }

            QFrame#cardInventario[tipo="rojo"] {
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
            }

            QFrame#cardInventario[tipo="azul"] {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }

            QFrame#cardInventario[tipo="morado"] {
                background-color: #F5F3FF;
                border: 1px solid #DDD6FE;
            }

            QFrame#cardInventario[tipo="alerta"] {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
            }

            QFrame#cardInventario[tipo="neutro"] {
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