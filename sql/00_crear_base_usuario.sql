CREATE DATABASE IF NOT EXISTS pos_pymes
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'pos_user'@'localhost'
IDENTIFIED BY '@@DB_PASSWORD@@';

ALTER USER 'pos_user'@'localhost'
IDENTIFIED BY '@@DB_PASSWORD@@';

GRANT ALL PRIVILEGES ON pos_pymes.* TO 'pos_user'@'localhost';

FLUSH PRIVILEGES;