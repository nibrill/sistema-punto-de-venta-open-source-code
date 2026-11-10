USE pos_pymes;

INSERT INTO negocio_config (
    id,
    nombre_negocio,
    rut,
    giro,
    direccion,
    comuna,
    ciudad,
    telefono,
    email,
    logo_url,
    moneda,
    impuesto_porcentaje,
    mensaje_ticket
)
VALUES (
    1,
    'Negocio sin configurar',
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    'CLP',
    19.00,
    'Gracias por su compra'
)
ON DUPLICATE KEY UPDATE
    nombre_negocio = nombre_negocio;

INSERT INTO usuarios (
    id,
    nombre,
    usuario,
    password_hash,
    rol,
    activo
)
VALUES (
    1,
    'Administrador',
    'admin',
    '@@ADMIN_HASH@@',
    'ADMIN',
    1
)
ON DUPLICATE KEY UPDATE
    id = id;