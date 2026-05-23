import os

from parser_cerezas import procesar_texto
from utilidades import (
    agregar_registros_excel,
    cargar_diccionarios,
    leer_archivo_texto,
    listar_archivos_entrada,
    mover_a_procesado,
    preparar_carpetas,
)


def pedir_identificador_sistema() -> str:
    while True:
        identificador = input("Ingrese identificador de sistema: ").strip()
        if identificador:
            return identificador

        print("El identificador no puede estar vacio.")


def imprimir_encabezado():
    print("=" * 60)
    print("Procesador de precios de cerezas")
    print("=" * 60)
    print("Flujo:")
    print("1. Deje archivos .txt en Input/Entrada")
    print("2. Ejecute el programa")
    print("3. El sistema agregara filas en Salida/salida_cerezas.xlsx")
    print("4. Los archivos leidos se moveran a Procesado")
    print("=" * 60)


def iniciar_app():
    imprimir_encabezado()

    rutas = preparar_carpetas()
    print(f"Carpeta de entrada: {rutas['entrada']}")
    print(f"Carpeta de procesados: {rutas['procesado']}")
    print(f"Archivo Excel de salida: {rutas['excel']}")
    print()

    identificador = pedir_identificador_sistema()

    try:
        diccionarios = cargar_diccionarios()
    except Exception as error:
        print(f"Error al cargar diccionarios.json: {error}")
        input("Presione Enter para cerrar...")
        return

    archivos = listar_archivos_entrada(rutas["entrada"])
    if not archivos:
        print("No hay archivos .txt para procesar.")
        print("Coloque archivos en Input/Entrada y ejecute nuevamente.")
        input("Presione Enter para cerrar...")
        return

    total_registros = 0
    archivos_ok = 0
    archivos_con_error = 0

    for ruta_archivo in archivos:
        nombre_archivo = os.path.basename(ruta_archivo)
        print(f"\nProcesando: {nombre_archivo}")

        try:
            texto = leer_archivo_texto(ruta_archivo)
            registros, logs = procesar_texto(texto, diccionarios)

            for registro in registros:
                registro["identificador_sistema"] = identificador
                registro["archivo_origen"] = nombre_archivo

            if registros:
                agregar_registros_excel(registros, rutas["excel"])

            destino = mover_a_procesado(ruta_archivo, rutas["procesado"])
            total_registros += len(registros)
            archivos_ok += 1

            for log in logs:
                print(f"  - {log}")
            print(f"  Archivo movido a: {destino}")

        except Exception as error:
            archivos_con_error += 1
            print(f"  Error: {error}")
            print("  El archivo queda en Input/Entrada para revision.")

    print("\nResumen final")
    print("-" * 60)
    print(f"Archivos procesados correctamente: {archivos_ok}")
    print(f"Archivos con error: {archivos_con_error}")
    print(f"Registros agregados al Excel: {total_registros}")
    print(f"Salida: {rutas['excel']}")
    input("Presione Enter para cerrar...")
