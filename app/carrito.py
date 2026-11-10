from decimal import Decimal, ROUND_HALF_UP

from app.productos import buscar_producto_por_codigo
from app.impuestos import calcular_totales_venta


def _decimal(valor):
    return Decimal(str(valor or 0))


def _dinero(valor):
    return _decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


class CarritoPOS:
    def __init__(self):
        self.items = []

    def esta_vacio(self):
        return len(self.items) == 0

    def vaciar(self):
        self.items = []

        return {
            "ok": True,
            "mensaje": "Carrito vaciado correctamente.",
            "data": None
        }

    def agregar_producto(self, codigo_barra, cantidad=1, descuento_linea=0):
        codigo_barra = str(codigo_barra or "").strip()
        cantidad = _decimal(cantidad)
        descuento_linea = _dinero(descuento_linea)

        if not codigo_barra:
            return {
                "ok": False,
                "mensaje": "Debe ingresar un código de barra.",
                "data": None
            }

        if cantidad <= 0:
            return {
                "ok": False,
                "mensaje": "La cantidad debe ser mayor a cero.",
                "data": None
            }

        producto = buscar_producto_por_codigo(codigo_barra)

        if not producto:
            return {
                "ok": False,
                "mensaje": "Producto no encontrado o inactivo.",
                "data": None
            }

        item_existente = self._buscar_item_por_codigo(codigo_barra)

        if item_existente:
            nueva_cantidad = item_existente["cantidad"] + cantidad

            validacion = self._validar_stock(producto, nueva_cantidad)

            if not validacion["ok"]:
                return validacion

            item_existente["cantidad"] = nueva_cantidad
            item_existente["descuento_linea"] = item_existente["descuento_linea"] + descuento_linea
            self._recalcular_item(item_existente)

            return {
                "ok": True,
                "mensaje": "Cantidad actualizada en el carrito.",
                "data": item_existente
            }

        validacion = self._validar_stock(producto, cantidad)

        if not validacion["ok"]:
            return validacion

        item = {
            "producto_id": producto["id"],
            "codigo_barra": producto["codigo_barra"],
            "sku": producto.get("sku"),
            "nombre": producto["nombre"],
            "categoria": producto.get("categoria"),
            "precio_unitario": _dinero(producto["precio_venta"]),
            "precio_compra_unitario": _dinero(producto["precio_compra"]),
            "cantidad": cantidad,
            "descuento_linea": descuento_linea,
            "stock_actual": _decimal(producto["stock_actual"]),
            "permite_venta_sin_stock": int(producto["permite_venta_sin_stock"] or 0),
            "requiere_mayoria_edad": int(producto["requiere_mayoria_edad"] or 0),
            "subtotal_linea": Decimal("0")
        }

        self._recalcular_item(item)
        self.items.append(item)

        return {
            "ok": True,
            "mensaje": "Producto agregado al carrito.",
            "data": item
        }

    def eliminar_item(self, indice):
        try:
            indice = int(indice)
        except Exception:
            return {
                "ok": False,
                "mensaje": "Índice inválido.",
                "data": None
            }

        if indice < 0 or indice >= len(self.items):
            return {
                "ok": False,
                "mensaje": "El producto no existe en el carrito.",
                "data": None
            }

        item = self.items.pop(indice)

        return {
            "ok": True,
            "mensaje": "Producto eliminado del carrito.",
            "data": item
        }

    def actualizar_cantidad(self, indice, nueva_cantidad):
        try:
            indice = int(indice)
        except Exception:
            return {
                "ok": False,
                "mensaje": "Índice inválido.",
                "data": None
            }

        nueva_cantidad = _decimal(nueva_cantidad)

        if nueva_cantidad <= 0:
            return {
                "ok": False,
                "mensaje": "La cantidad debe ser mayor a cero.",
                "data": None
            }

        if indice < 0 or indice >= len(self.items):
            return {
                "ok": False,
                "mensaje": "El producto no existe en el carrito.",
                "data": None
            }

        item = self.items[indice]

        producto = buscar_producto_por_codigo(item["codigo_barra"])

        if not producto:
            return {
                "ok": False,
                "mensaje": "El producto ya no existe o fue desactivado.",
                "data": None
            }

        validacion = self._validar_stock(producto, nueva_cantidad)

        if not validacion["ok"]:
            return validacion

        item["cantidad"] = nueva_cantidad
        self._recalcular_item(item)

        return {
            "ok": True,
            "mensaje": "Cantidad actualizada correctamente.",
            "data": item
        }

    def actualizar_descuento_linea(self, indice, descuento_linea):
        try:
            indice = int(indice)
        except Exception:
            return {
                "ok": False,
                "mensaje": "Índice inválido.",
                "data": None
            }

        descuento_linea = _dinero(descuento_linea)

        if descuento_linea < 0:
            return {
                "ok": False,
                "mensaje": "El descuento no puede ser negativo.",
                "data": None
            }

        if indice < 0 or indice >= len(self.items):
            return {
                "ok": False,
                "mensaje": "El producto no existe en el carrito.",
                "data": None
            }

        item = self.items[indice]
        item["descuento_linea"] = descuento_linea

        subtotal_sin_descuento = _dinero(item["precio_unitario"] * item["cantidad"])

        if descuento_linea > subtotal_sin_descuento:
            return {
                "ok": False,
                "mensaje": "El descuento no puede superar el subtotal del producto.",
                "data": None
            }

        self._recalcular_item(item)

        return {
            "ok": True,
            "mensaje": "Descuento actualizado correctamente.",
            "data": item
        }

    def obtener_detalle(self):
        return self.items

    def obtener_resumen(self):
        subtotal = Decimal("0")
        descuento_total = Decimal("0")
        total_unidades = Decimal("0")
        requiere_mayoria_edad = False

        for item in self.items:
            subtotal += _dinero(item["precio_unitario"] * item["cantidad"])
            descuento_total += _dinero(item["descuento_linea"])
            total_unidades += _decimal(item["cantidad"])

            if int(item.get("requiere_mayoria_edad") or 0) == 1:
                requiere_mayoria_edad = True

        totales = calcular_totales_venta(
            subtotal=subtotal,
            descuento_total=descuento_total
        )

        return {
            "ok": True,
            "mensaje": "Resumen del carrito generado correctamente.",
            "data": {
                "cantidad_items": len(self.items),
                "total_unidades": total_unidades,
                "subtotal": totales["subtotal"],
                "subtotal_neto": totales["subtotal"],
                "descuento_total": totales["descuento_total"],
                "neto_gravado": totales["neto_gravado"],
                "impuesto_porcentaje": totales["impuesto_porcentaje"],
                "impuesto_total": totales["impuesto_total"],
                "total": totales["total"],
                "requiere_mayoria_edad": requiere_mayoria_edad
            }
        }

    def obtener_items_para_venta(self):
        items_venta = []

        for item in self.items:
            items_venta.append({
                "codigo_barra": item["codigo_barra"],
                "cantidad": item["cantidad"],
                "descuento_linea": item["descuento_linea"]
            })

        return items_venta

    def _buscar_item_por_codigo(self, codigo_barra):
        for item in self.items:
            if item["codigo_barra"] == codigo_barra:
                return item

        return None

    def _validar_stock(self, producto, cantidad_total):
        stock_actual = _decimal(producto["stock_actual"])
        permite_sin_stock = int(producto["permite_venta_sin_stock"] or 0)

        if permite_sin_stock == 0 and cantidad_total > stock_actual:
            return {
                "ok": False,
                "mensaje": f"Stock insuficiente para {producto['nombre']}.",
                "data": {
                    "producto": producto["nombre"],
                    "stock_actual": stock_actual,
                    "cantidad_solicitada": cantidad_total
                }
            }

        return {
            "ok": True,
            "mensaje": "Stock validado correctamente.",
            "data": None
        }

    def _recalcular_item(self, item):
        subtotal_sin_descuento = _dinero(item["precio_unitario"] * item["cantidad"])
        subtotal_linea = _dinero(subtotal_sin_descuento - item["descuento_linea"])

        if subtotal_linea < 0:
            subtotal_linea = Decimal("0")

        item["subtotal_linea"] = subtotal_linea