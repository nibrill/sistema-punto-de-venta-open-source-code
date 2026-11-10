from app.database import ejecutar_consulta


def buscar_producto_por_codigo(codigo_barra):
    consulta = """
        SELECT
            p.id,
            p.categoria_id,
            p.proveedor_id,
            p.codigo_barra,
            p.sku,
            p.nombre,
            p.descripcion,
            p.tipo_producto,
            p.unidad_medida,
            p.precio_compra,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.permite_venta_sin_stock,
            p.requiere_mayoria_edad,
            p.activo,
            c.nombre AS categoria,
            pr.nombre AS proveedor
        FROM productos p
        LEFT JOIN categorias c
            ON c.id = p.categoria_id
        LEFT JOIN proveedores pr
            ON pr.id = p.proveedor_id
        WHERE p.codigo_barra = %s
          AND p.activo = 1
        LIMIT 1;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(codigo_barra,),
        obtener_uno=True
    )


def buscar_producto_por_id(producto_id):
    consulta = """
        SELECT
            p.id,
            p.categoria_id,
            p.proveedor_id,
            p.codigo_barra,
            p.sku,
            p.nombre,
            p.descripcion,
            p.tipo_producto,
            p.unidad_medida,
            p.precio_compra,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.permite_venta_sin_stock,
            p.requiere_mayoria_edad,
            p.activo,
            c.nombre AS categoria,
            pr.nombre AS proveedor
        FROM productos p
        LEFT JOIN categorias c
            ON c.id = p.categoria_id
        LEFT JOIN proveedores pr
            ON pr.id = p.proveedor_id
        WHERE p.id = %s
          AND p.activo = 1
        LIMIT 1;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(producto_id,),
        obtener_uno=True
    )


def listar_productos():
    consulta = """
        SELECT
            p.id,
            p.categoria_id,
            p.proveedor_id,
            p.codigo_barra,
            p.sku,
            p.nombre,
            p.descripcion,
            p.tipo_producto,
            p.unidad_medida,
            c.nombre AS categoria,
            pr.nombre AS proveedor,
            p.precio_compra,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.permite_venta_sin_stock,
            p.requiere_mayoria_edad,
            p.activo
        FROM productos p
        LEFT JOIN categorias c
            ON c.id = p.categoria_id
        LEFT JOIN proveedores pr
            ON pr.id = p.proveedor_id
        WHERE p.activo = 1
        ORDER BY p.nombre ASC;
    """

    return ejecutar_consulta(
        consulta,
        obtener_todos=True
    )


def buscar_productos_por_nombre(texto):
    texto = str(texto or "").strip()

    consulta = """
        SELECT
            p.id,
            p.categoria_id,
            p.proveedor_id,
            p.codigo_barra,
            p.sku,
            p.nombre,
            p.descripcion,
            p.tipo_producto,
            p.unidad_medida,
            c.nombre AS categoria,
            pr.nombre AS proveedor,
            p.precio_compra,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.permite_venta_sin_stock,
            p.requiere_mayoria_edad,
            p.activo
        FROM productos p
        LEFT JOIN categorias c
            ON c.id = p.categoria_id
        LEFT JOIN proveedores pr
            ON pr.id = p.proveedor_id
        WHERE (
            p.nombre LIKE %s
            OR p.codigo_barra LIKE %s
            OR p.sku LIKE %s
            OR c.nombre LIKE %s
            OR pr.nombre LIKE %s
        )
          AND p.activo = 1
        ORDER BY p.nombre ASC;
    """

    texto_busqueda = f"%{texto}%"

    return ejecutar_consulta(
        consulta,
        parametros=(
            texto_busqueda,
            texto_busqueda,
            texto_busqueda,
            texto_busqueda,
            texto_busqueda,
        ),
        obtener_todos=True
    )


def crear_producto(
    categoria_id,
    proveedor_id,
    codigo_barra,
    sku,
    nombre,
    descripcion,
    tipo_producto,
    unidad_medida,
    precio_compra,
    precio_venta,
    stock_actual,
    stock_minimo,
    permite_venta_sin_stock,
    requiere_mayoria_edad
):
    consulta = """
        INSERT INTO productos (
            categoria_id,
            proveedor_id,
            codigo_barra,
            sku,
            nombre,
            descripcion,
            tipo_producto,
            unidad_medida,
            precio_compra,
            precio_venta,
            stock_actual,
            stock_minimo,
            permite_venta_sin_stock,
            requiere_mayoria_edad,
            activo
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1
        );
    """

    parametros = (
        categoria_id,
        proveedor_id,
        codigo_barra,
        sku,
        nombre,
        descripcion,
        tipo_producto,
        unidad_medida,
        precio_compra,
        precio_venta,
        stock_actual,
        stock_minimo,
        permite_venta_sin_stock,
        requiere_mayoria_edad
    )

    return ejecutar_consulta(
        consulta,
        parametros=parametros
    )


def actualizar_producto(
    producto_id,
    categoria_id,
    proveedor_id,
    codigo_barra,
    sku,
    nombre,
    descripcion,
    tipo_producto,
    unidad_medida,
    precio_compra,
    precio_venta,
    stock_minimo,
    permite_venta_sin_stock,
    requiere_mayoria_edad
):
    consulta = """
        UPDATE productos
        SET
            categoria_id = %s,
            proveedor_id = %s,
            codigo_barra = %s,
            sku = %s,
            nombre = %s,
            descripcion = %s,
            tipo_producto = %s,
            unidad_medida = %s,
            precio_compra = %s,
            precio_venta = %s,
            stock_minimo = %s,
            permite_venta_sin_stock = %s,
            requiere_mayoria_edad = %s,
            updated_at = NOW()
        WHERE id = %s
          AND activo = 1;
    """

    parametros = (
        categoria_id,
        proveedor_id,
        codigo_barra,
        sku,
        nombre,
        descripcion,
        tipo_producto,
        unidad_medida,
        precio_compra,
        precio_venta,
        stock_minimo,
        permite_venta_sin_stock,
        requiere_mayoria_edad,
        producto_id
    )

    return ejecutar_consulta(
        consulta,
        parametros=parametros
    )


def actualizar_stock(producto_id, nuevo_stock):
    consulta = """
        UPDATE productos
        SET
            stock_actual = %s,
            updated_at = NOW()
        WHERE id = %s
          AND activo = 1;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(nuevo_stock, producto_id)
    )


def descontar_stock(producto_id, cantidad):
    consulta = """
        UPDATE productos
        SET
            stock_actual = stock_actual - %s,
            updated_at = NOW()
        WHERE id = %s
          AND activo = 1;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(cantidad, producto_id)
    )


def aumentar_stock(producto_id, cantidad):
    consulta = """
        UPDATE productos
        SET
            stock_actual = stock_actual + %s,
            updated_at = NOW()
        WHERE id = %s
          AND activo = 1;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(cantidad, producto_id)
    )


def productos_bajo_stock():
    consulta = """
        SELECT
            p.id,
            p.categoria_id,
            p.proveedor_id,
            p.codigo_barra,
            p.sku,
            p.nombre,
            c.nombre AS categoria,
            pr.nombre AS proveedor,
            p.precio_compra,
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            p.activo
        FROM productos p
        LEFT JOIN categorias c
            ON c.id = p.categoria_id
        LEFT JOIN proveedores pr
            ON pr.id = p.proveedor_id
        WHERE p.stock_actual <= p.stock_minimo
          AND p.activo = 1
        ORDER BY p.stock_actual ASC;
    """

    return ejecutar_consulta(
        consulta,
        obtener_todos=True
    )


def desactivar_producto(producto_id):
    consulta = """
        UPDATE productos
        SET
            activo = 0,
            updated_at = NOW()
        WHERE id = %s;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(producto_id,)
    )


def activar_producto(producto_id):
    consulta = """
        UPDATE productos
        SET
            activo = 1,
            updated_at = NOW()
        WHERE id = %s;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(producto_id,)
    )


def eliminar_producto_definitivo(producto_id):
    consulta = """
        DELETE FROM productos
        WHERE id = %s;
    """

    return ejecutar_consulta(
        consulta,
        parametros=(producto_id,)
    )