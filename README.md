# CorePOS Community

Punto de venta de escritorio para pymes (Windows), hecho en Python + PySide6 + MySQL.
Edición comunitaria y gratuita, con IVA 19 % (Chile).

## Incluye
Ventas, productos, inventario, compras, proveedores, clientes, caja, reportes y gráficos,
usuarios con roles (ADMIN, VENDEDOR, ENCARGADO_STOCK) y API local para escáner móvil.

## No incluye
Boleta/factura electrónica SII, licenciamiento, instalador y soporte. Esas funciones
pertenecen a la edición comercial.

## Instalación (desarrollo)
1. Python 3.12+ y MySQL 8.
2. `pip install -r requirements.txt`
3. Cree la base de datos: edite `sql/00_crear_base_usuario.sql` (reemplace `@@DB_PASSWORD@@`),
   genere el hash del admin con `python scripts/generar_hash.py` y péguelo en
   `sql/99_datos_iniciales.sql` (`@@ADMIN_HASH@@`). Luego ejecute en orden:
   `00_crear_base_usuario.sql`, todos los de `sql/tables/` y `99_datos_iniciales.sql`.
4. Copie `.env.example` a `.env` y complete las credenciales.
5. `python run_ui.py`

## Seguridad
- Nunca suba su `.env`.
- La API local solo acepta conexiones desde el mismo equipo; para usar el celular defina
  `POS_API_TOKEN` y envíelo en el encabezado `X-POS-Token`.

## Licencia
MIT. Ver [LICENSE](LICENSE).
