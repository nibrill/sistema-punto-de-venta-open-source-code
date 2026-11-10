from pathlib import Path
from datetime import datetime
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter


COLOR_AZUL = "1F4E78"
COLOR_AZUL_OSCURO = "17365D"
COLOR_GRIS = "F3F4F6"
COLOR_BLANCO = "FFFFFF"
COLOR_VERDE = "D9EAD3"
COLOR_ROJO = "F4CCCC"
COLOR_AMARILLO = "FFF2CC"

BORDE_FINO = Side(style="thin", color="D9E2F3")


def _asegurar_carpeta(ruta_archivo):
    ruta = Path(ruta_archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)


def _convertir_valor(valor):
    if isinstance(valor, Decimal):
        return float(valor)

    return valor


def _formatear_hoja(ws):
    ws.freeze_panes = "A2"

    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="center")
            cell.border = Border(
                left=BORDE_FINO,
                right=BORDE_FINO,
                top=BORDE_FINO,
                bottom=BORDE_FINO
            )

    for cell in ws[1]:
        cell.font = Font(bold=True, color=COLOR_BLANCO)
        cell.fill = PatternFill("solid", fgColor=COLOR_AZUL)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for column_cells in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)

        for cell in column_cells:
            value = cell.value

            if value is None:
                continue

            max_length = max(max_length, len(str(value)))

        width = min(max(max_length + 3, 12), 38)
        ws.column_dimensions[column_letter].width = width


def _crear_hoja_tabla(wb, nombre_hoja, headers, filas):
    ws = wb.create_sheet(nombre_hoja)

    ws.append(headers)

    for fila in filas:
        ws.append([_convertir_valor(valor) for valor in fila])

    _formatear_hoja(ws)

    return ws


def _crear_hoja_resumen(wb, resumen, fecha_inicio=None, fecha_fin=None):
    ws = wb.create_sheet("Resumen")

    ws["A1"] = "REPORTE POS PYMES"
    ws["A1"].font = Font(bold=True, size=18, color=COLOR_BLANCO)
    ws["A1"].fill = PatternFill("solid", fgColor=COLOR_AZUL_OSCURO)
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A1:D1")

    datos = [
        ("Fecha generación", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Desde", fecha_inicio or ""),
        ("Hasta", fecha_fin or ""),
        ("Cantidad ventas", resumen.get("cantidad_ventas", 0)),
        ("Total neto", _convertir_valor(resumen.get("total_neto", 0))),
        ("IVA", _convertir_valor(resumen.get("total_impuesto", resumen.get("impuesto_total", 0)))),
        ("Total vendido", _convertir_valor(resumen.get("total_vendido", 0))),
        ("Total efectivo", _convertir_valor(resumen.get("total_efectivo", 0))),
        ("Total tarjeta", _convertir_valor(resumen.get("total_tarjeta", 0))),
        ("Total transferencia", _convertir_valor(resumen.get("total_transferencia", 0))),
        ("Ganancia estimada", _convertir_valor(resumen.get("ganancia_estimada", 0)))
    ]

    fila_excel = 3

    for concepto, valor in datos:
        ws.cell(row=fila_excel, column=1, value=concepto)
        ws.cell(row=fila_excel, column=2, value=valor)

        ws.cell(row=fila_excel, column=1).font = Font(bold=True)
        ws.cell(row=fila_excel, column=1).fill = PatternFill("solid", fgColor=COLOR_GRIS)

        fila_excel += 1

    for row in ws.iter_rows(min_row=3, max_row=fila_excel - 1, min_col=1, max_col=2):
        for cell in row:
            cell.border = Border(
                left=BORDE_FINO,
                right=BORDE_FINO,
                top=BORDE_FINO,
                bottom=BORDE_FINO
            )
            cell.alignment = Alignment(vertical="center")

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 22

    for row in range(7, 12):
        ws.cell(row=row, column=2).number_format = '$#,##0'

    return ws


def exportar_reporte_completo_excel(
    ruta_archivo,
    resumen,
    ventas,
    productos_mas_vendidos,
    ganancia,
    caja_actual,
    bajo_stock,
    fecha_inicio=None,
    fecha_fin=None
):
    _asegurar_carpeta(ruta_archivo)

    wb = Workbook()
    hoja_default = wb.active
    wb.remove(hoja_default)

    resumen_completo = dict(resumen or {})
    resumen_completo["ganancia_estimada"] = (ganancia or {}).get("ganancia_estimada", 0)

    _crear_hoja_resumen(
        wb=wb,
        resumen=resumen_completo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    ventas_filas = []

    for venta in ventas or []:
        ventas_filas.append([
            venta.get("numero_venta"),
            venta.get("fecha_venta"),
            venta.get("cajero"),
            venta.get("metodo_pago"),
            venta.get("subtotal"),
            venta.get("descuento_total"),
            venta.get("impuesto_total"),
            venta.get("total"),
            venta.get("estado")
        ])

    _crear_hoja_tabla(
        wb,
        "Ventas",
        ["Número", "Fecha", "Cajero", "Método pago", "Subtotal neto", "Descuento", "IVA", "Total", "Estado"],
        ventas_filas
    )

    productos_filas = []

    for producto in productos_mas_vendidos or []:
        productos_filas.append([
            producto.get("nombre_producto"),
            producto.get("cantidad_vendida"),
            producto.get("total_vendido"),
            producto.get("ganancia_estimada")
        ])

    _crear_hoja_tabla(
        wb,
        "Top productos",
        ["Producto", "Cantidad vendida", "Total vendido", "Ganancia estimada"],
        productos_filas
    )

    ganancia_filas = [
        ["Cantidad ventas", (ganancia or {}).get("cantidad_ventas", 0)],
        ["Total vendido", (ganancia or {}).get("total_vendido", 0)],
        ["Total neto", (ganancia or {}).get("total_neto", 0)],
        ["IVA", (ganancia or {}).get("impuesto_total", 0)],
        ["Costo total", (ganancia or {}).get("costo_total", 0)],
        ["Ganancia estimada", (ganancia or {}).get("ganancia_estimada", 0)]
    ]

    _crear_hoja_tabla(
        wb,
        "Ganancia",
        ["Concepto", "Valor"],
        ganancia_filas
    )

    caja_filas = []

    if caja_actual:
        caja_filas = [
            ["ID caja", caja_actual.get("id")],
            ["Estado", caja_actual.get("estado")],
            ["Usuario apertura", caja_actual.get("usuario_apertura")],
            ["Fecha apertura", caja_actual.get("fecha_apertura")],
            ["Monto inicial", caja_actual.get("monto_inicial")],
            ["Ventas efectivo", caja_actual.get("monto_ventas_efectivo")],
            ["Ventas tarjeta", caja_actual.get("monto_ventas_tarjeta")],
            ["Ventas transferencia", caja_actual.get("monto_ventas_transferencia")],
            ["Ventas total", caja_actual.get("monto_ventas_total")],
            ["Ingresos extra", caja_actual.get("monto_ingresos_extra")],
            ["Retiros", caja_actual.get("monto_retiros")],
            ["Monto esperado", caja_actual.get("monto_esperado_caja")]
        ]
    else:
        caja_filas = [["Estado", "No hay caja abierta"]]

    _crear_hoja_tabla(
        wb,
        "Caja actual",
        ["Concepto", "Valor"],
        caja_filas
    )

    bajo_stock_filas = []

    for producto in bajo_stock or []:
        bajo_stock_filas.append([
            producto.get("id"),
            producto.get("codigo_barra"),
            producto.get("nombre"),
            producto.get("categoria"),
            producto.get("stock_actual"),
            producto.get("stock_minimo"),
            producto.get("precio_venta")
        ])

    _crear_hoja_tabla(
        wb,
        "Bajo stock",
        ["ID", "Código", "Producto", "Categoría", "Stock actual", "Stock mínimo", "Precio venta"],
        bajo_stock_filas
    )

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, (int, float)):
                    if "stock" not in str(ws.title).lower():
                        cell.number_format = '$#,##0'

    wb.save(ruta_archivo)

    return {
        "ok": True,
        "mensaje": "Reporte exportado correctamente.",
        "data": {
            "ruta_archivo": str(ruta_archivo)
        }
    }


def exportar_tabla_simple_excel(ruta_archivo, nombre_hoja, headers, filas):
    _asegurar_carpeta(ruta_archivo)

    wb = Workbook()
    ws = wb.active
    ws.title = nombre_hoja[:31]

    ws.append(headers)

    for fila in filas:
        ws.append([_convertir_valor(valor) for valor in fila])

    _formatear_hoja(ws)

    wb.save(ruta_archivo)

    return {
        "ok": True,
        "mensaje": "Archivo Excel exportado correctamente.",
        "data": {
            "ruta_archivo": str(ruta_archivo)
        }
    }