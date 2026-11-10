import os
import secrets
from decimal import Decimal
from html import escape
from datetime import datetime
from queue import Queue

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.productos import buscar_producto_por_codigo


api = FastAPI(title="POS Local API")

# Sin CORS abierto: la API solo debe ser usada por el POS local o por el
# celular escáner mediante token. Para habilitar orígenes concretos use
# POS_API_ALLOWED_ORIGINS="https://a.com,https://b.com".
_origenes = [o.strip() for o in os.getenv("POS_API_ALLOWED_ORIGINS", "").split(",") if o.strip()]
if _origenes:
    api.add_middleware(
        CORSMiddleware,
        allow_origins=_origenes,
        allow_methods=["GET", "POST"],
        allow_headers=["X-POS-Token"],
    )

# Token de acceso. Si no se define POS_API_TOKEN la API solo acepta
# conexiones desde la propia máquina (127.0.0.1).
API_TOKEN = os.getenv("POS_API_TOKEN", "").strip()


def verificar_acceso(request: Request):
    token = (request.headers.get("X-POS-Token") or request.query_params.get("token") or "").strip()

    if API_TOKEN:
        if secrets.compare_digest(token, API_TOKEN):
            return
        raise HTTPException(status_code=401, detail="Token inválido.")

    cliente = request.client.host if request.client else ""
    if cliente not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Acceso solo local.")

scans_pendientes = Queue()


def convertir_decimal(valor):
    try:
        if isinstance(valor, Decimal):
            return float(valor)

        return float(valor or 0)
    except Exception:
        return 0.0


def formato_pesos(valor):
    try:
        numero = int(Decimal(str(valor or 0)))
        return f"${numero:,.0f}".replace(",", ".")
    except Exception:
        return "$0"


def formato_stock(valor):
    try:
        numero = Decimal(str(valor or 0))

        if numero == numero.to_integral():
            return str(int(numero))

        return f"{numero:.3f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


def normalizar_producto(producto):
    if not producto:
        return None

    return {
        "id": producto.get("id"),
        "codigo_barra": producto.get("codigo_barra"),
        "sku": producto.get("sku"),
        "nombre": producto.get("nombre"),
        "descripcion": producto.get("descripcion"),
        "categoria": producto.get("categoria"),
        "proveedor": producto.get("proveedor"),
        "tipo_producto": producto.get("tipo_producto"),
        "unidad_medida": producto.get("unidad_medida"),
        "precio_compra": convertir_decimal(producto.get("precio_compra")),
        "precio_venta": convertir_decimal(producto.get("precio_venta")),
        "stock_actual": convertir_decimal(producto.get("stock_actual")),
        "stock_minimo": convertir_decimal(producto.get("stock_minimo")),
        "permite_venta_sin_stock": producto.get("permite_venta_sin_stock"),
        "requiere_mayoria_edad": producto.get("requiere_mayoria_edad"),
        "activo": producto.get("activo"),
    }


def guardar_scan_pendiente(codigo):
    codigo = str(codigo or "").strip()

    if not codigo:
        return {
            "ok": False,
            "mensaje": "Código vacío.",
            "codigo": codigo,
            "producto": None,
        }

    producto = buscar_producto_por_codigo(codigo)

    scans_pendientes.put({
        "codigo": codigo,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "producto_encontrado": True if producto else False,
    })

    return {
        "ok": True,
        "mensaje": "Código recibido por el POS.",
        "codigo": codigo,
        "producto": producto,
        "producto_encontrado": True if producto else False,
    }


@api.get("/", dependencies=[Depends(verificar_acceso)])
def home():
    return {
        "ok": True,
        "mensaje": "Servidor POS Local funcionando",
        "endpoints": {
            "producto_json": "/producto/{codigo}",
            "producto_html": "/ver-producto/{codigo}",
            "registrar_scan_get": "/registrar-scan/{codigo}",
            "registrar_scan_post": "/registrar-scan",
            "obtener_scan": "/obtener-scan",
            "estado": "/health",
        },
    }


@api.get("/health")
def health():
    return {
        "ok": True,
        "mensaje": "API activa",
    }


@api.get("/producto/{codigo}", dependencies=[Depends(verificar_acceso)])
def obtener_producto_json(codigo: str):
    codigo = str(codigo or "").strip()

    if not codigo:
        return {
            "ok": False,
            "mensaje": "Debe ingresar un código de barra.",
        }

    producto = buscar_producto_por_codigo(codigo)

    if not producto:
        return {
            "ok": False,
            "mensaje": "Producto no encontrado.",
            "codigo": codigo,
        }

    return {
        "ok": True,
        "mensaje": "Producto encontrado.",
        "producto": normalizar_producto(producto),
    }


@api.get("/ver-producto/{codigo}", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso)])
def ver_producto(codigo: str):
    codigo = str(codigo or "").strip()

    if not codigo:
        return """
        <html>
            <body style="font-family: Arial; padding:25px;">
                <h1>Código inválido</h1>
                <p>Debe ingresar un código de barra.</p>
            </body>
        </html>
        """

    producto = buscar_producto_por_codigo(codigo)

    if not producto:
        return f"""
        <html>
            <body style="font-family: Arial; padding:25px;">
                <h1>Producto no encontrado</h1>
                <p>Código consultado: <strong>{escape(codigo)}</strong></p>
            </body>
        </html>
        """

    nombre = escape(str(producto.get("nombre") or "Sin nombre"))
    codigo_barra = escape(str(producto.get("codigo_barra") or codigo))
    sku = escape(str(producto.get("sku") or "Sin SKU"))
    categoria = escape(str(producto.get("categoria") or "Sin categoría"))
    proveedor = escape(str(producto.get("proveedor") or "Sin proveedor"))

    precio_venta = formato_pesos(producto.get("precio_venta"))
    precio_compra = formato_pesos(producto.get("precio_compra"))
    stock_actual = formato_stock(producto.get("stock_actual"))
    stock_minimo = formato_stock(producto.get("stock_minimo"))

    return f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{nombre}</title>
        </head>

        <body style="
            font-family: Arial, sans-serif;
            background-color: #F8FAFC;
            padding: 25px;
            color: #0F172A;
        ">
            <div style="
                max-width: 520px;
                margin: auto;
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                padding: 24px;
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
            ">
                <p style="
                    margin: 0 0 10px 0;
                    color: #2563EB;
                    font-weight: bold;
                    font-size: 13px;
                    text-transform: uppercase;
                ">
                    Producto POS
                </p>

                <h1 style="margin: 0 0 12px 0; font-size: 28px;">
                    {nombre}
                </h1>

                <div style="
                    background-color: #EFF6FF;
                    border: 1px solid #BFDBFE;
                    border-radius: 14px;
                    padding: 16px;
                    margin-bottom: 16px;
                ">
                    <h2 style="margin: 0; color: #1D4ED8;">
                        Precio venta: {precio_venta}
                    </h2>
                </div>

                <p><strong>Código:</strong> {codigo_barra}</p>
                <p><strong>SKU:</strong> {sku}</p>
                <p><strong>Categoría:</strong> {categoria}</p>
                <p><strong>Proveedor:</strong> {proveedor}</p>
                <p><strong>Precio compra:</strong> {precio_compra}</p>
                <p><strong>Stock actual:</strong> {stock_actual}</p>
                <p><strong>Stock mínimo:</strong> {stock_minimo}</p>
            </div>
        </body>
    </html>
    """


@api.get("/registrar-scan/{codigo}", response_class=HTMLResponse, dependencies=[Depends(verificar_acceso)])
def registrar_scan_get(codigo: str):
    resultado = guardar_scan_pendiente(codigo)

    if not resultado["ok"]:
        return """
        <html>
            <body style="font-family: Arial; padding:25px;">
                <h2>Código vacío</h2>
                <p>No se pudo enviar nada al POS.</p>
            </body>
        </html>
        """

    producto = resultado.get("producto")
    codigo = resultado.get("codigo")

    if producto:
        nombre = escape(str(producto.get("nombre") or "Producto"))
        precio = formato_pesos(producto.get("precio_venta"))

        return f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial; padding:25px; background:#ECFDF5; color:#166534;">
                <h2>Código enviado al POS</h2>
                <p><strong>{nombre}</strong></p>
                <p>Precio: <strong>{precio}</strong></p>
                <p>Código: {escape(codigo)}</p>
            </body>
        </html>
        """

    return f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial; padding:25px; background:#FFFBEB; color:#92400E;">
            <h2>Código enviado al POS</h2>
            <p>El POS intentará buscar este código.</p>
            <p>Código: <strong>{escape(codigo)}</strong></p>
            <p>Advertencia: no se encontró previamente en productos.</p>
        </body>
    </html>
    """


@api.post("/registrar-scan", dependencies=[Depends(verificar_acceso)])
async def registrar_scan_post(request: Request):
    cuerpo = await request.body()
    texto = cuerpo.decode("utf-8").strip()

    codigo = ""

    if texto.startswith("codigo="):
        codigo = texto.replace("codigo=", "", 1).strip()
    else:
        codigo = texto.strip()

    codigo = codigo.replace("%7Bcode%7D", "").strip()
    codigo = codigo.replace("{code}", "").strip()

    resultado = guardar_scan_pendiente(codigo)

    if not resultado["ok"]:
        return {
            "ok": False,
            "mensaje": "Código vacío.",
            "codigo": codigo,
        }

    return {
        "ok": True,
        "mensaje": "Código recibido por el POS.",
        "codigo": resultado.get("codigo"),
        "producto_encontrado": resultado.get("producto_encontrado"),
    }


@api.get("/obtener-scan", dependencies=[Depends(verificar_acceso)])
def obtener_scan():
    if scans_pendientes.empty():
        return {
            "ok": False,
            "mensaje": "No hay códigos pendientes.",
        }

    scan = scans_pendientes.get()

    return {
        "ok": True,
        "mensaje": "Código pendiente obtenido.",
        "scan": scan,
    }


app = api