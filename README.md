# CorePOS Community

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)
![MySQL](https://img.shields.io/badge/DB-MySQL%208-4479A1?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)
![CI](https://github.com/nibrill/corepos-community/actions/workflows/ci.yml/badge.svg)

Punto de venta de escritorio para pymes (Windows), hecho en **Python + PySide6 + MySQL**.
Edición comunitaria y gratuita, con IVA 19 % (Chile).

## Funcionalidades
| Área | Detalle |
|---|---|
| Ventas | Carrito, pago en efectivo / tarjeta / transferencia / mixto, anulación con devolución de stock |
| Caja | Apertura y cierre de turnos, control de movimientos |
| Productos e inventario | Catálogo, categorías, código de barras, movimientos de stock |
| Compras y proveedores | Registro de compras con detalle y actualización de stock |
| Clientes | Ficha y historial |
| Reportes | Dashboard, gráficos (matplotlib) y exportación a Excel |
| Usuarios y roles | `ADMIN`, `VENDEDOR`, `ENCARGADO_STOCK` con permisos por módulo |
| Escáner móvil | API local (FastAPI) para usar el celular como lector de códigos |
| Respaldo | Utilidad de backup de la base de datos |

## Arquitectura
```
app/
├── ui/            Interfaz PySide6 (ventana principal, páginas por módulo, estilos)
├── api/           API local FastAPI para el escáner móvil
├── ventas.py …    Lógica de negocio por módulo (ventas, caja, inventario, compras…)
├── database.py    Acceso a MySQL
├── security.py    Hash de contraseñas y permisos por rol
sql/               Esquema (una tabla por archivo) y datos iniciales
scripts/           Utilidades (generar hash del admin)
```
La lógica de negocio está separada de la interfaz: cada módulo de `app/` expone funciones
que las páginas de `app/ui/pages/` consumen.

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
- CORS cerrado por defecto; orígenes permitidos vía `POS_API_ALLOWED_ORIGINS`.

## Edición comunitaria vs. comercial
La edición comunitaria **no incluye** boleta/factura electrónica SII, licenciamiento,
instalador ni soporte. Esas funciones pertenecen a la edición comercial.

## Roadmap
- [ ] Tests automatizados de la capa de negocio con base de datos de prueba
- [ ] Capturas de pantalla y demo en video
- [ ] Release con ejecutable para Windows
- [ ] Internacionalización (otros países / impuestos)

## Contribuir
Lea [CONTRIBUTING.md](CONTRIBUTING.md). Los issues con la etiqueta `good first issue` son un buen punto de partida.

## Licencia
MIT. Ver [LICENSE](LICENSE).
