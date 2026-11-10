from app.database import obtener_conexion


def probar_conexion():
    conexion = obtener_conexion()

    if conexion is None:
        print("No se pudo conectar a la base de datos.")
        return

    cursor = conexion.cursor()

    cursor.execute("SELECT DATABASE();")
    resultado = cursor.fetchone()

    print("Conexión exitosa.")
    print(f"Base de datos conectada: {resultado[0]}")

    cursor.close()
    conexion.close()


if __name__ == "__main__":
    probar_conexion()