# Procesador de precios de cerezas

Aplicacion de consola en Python para procesar archivos `.txt` con mensajes comerciales de cerezas y agregar los registros a un unico archivo Excel.

## 1. Resumen del diseno

El sistema ahora trabaja por carpetas:

1. El usuario deja archivos `.txt` en `Input/Entrada`.
2. Ejecuta el programa desde consola.
3. El programa pide un `identificador_sistema`.
4. Procesa todos los `.txt` encontrados.
5. Agrega las filas al archivo `Salida/salida_cerezas.xlsx`.
6. Mueve cada archivo procesado correctamente a `Procesado`.
7. Si un archivo falla, queda en `Input/Entrada` para revision.

Decision asumida: el identificador de sistema se guarda como columna `identificador_sistema` en cada fila generada. Tambien se agrega `archivo_origen` para saber de que `.txt` viene cada registro.

Decision asumida: cada linea comercial representa un lote principal. Si una linea contiene varias combinaciones de calibre y precio, se crea un registro por cada combinacion. En lineas como `79P 50P/DOLE/...`, se toma como cantidad de referencia la cantidad mas cercana a la exportadora, es decir `50P`.

## 2. Estructura de archivos

```text
proyecto_cerezas/
    main.py
    parser_cerezas.py
    interfaz.py
    utilidades.py
    diccionarios.json
    ejemplo_entrada.txt
    requirements.txt
    README.md
    cerezas_parser.spec
    Input/
        Entrada/
    Procesado/
    Salida/
        salida_cerezas.xlsx
```

## 3. Archivos principales

- `main.py`: punto de entrada.
- `interfaz.py`: interfaz por consola.
- `parser_cerezas.py`: normalizacion, segmentacion, extraccion y validacion.
- `utilidades.py`: carpetas, lectura de archivos, Excel, rutas de PyInstaller y movimiento a `Procesado`.
- `diccionarios.json`: diccionarios editables para exportadoras, variedades, empaques, calibres y embarques.

## 4. requirements.txt

```text
openpyxl>=3.1
pyinstaller>=6.0
```

Instalacion:

```bash
pip install -r requirements.txt
```

## 5. Como ejecutar

Desde la carpeta del proyecto:

```bash
cd proyecto_cerezas
python main.py
```

En Windows:

```bat
cd proyecto_cerezas
py main.py
```

El programa mostrara las rutas de trabajo y pedira:

```text
Ingrese identificador de sistema:
```

Ejemplo:

```text
SISTEMA_GZ_001
```

## 6. Ejemplo de entrada

Hay un ejemplo en `ejemplo_entrada.txt`. Para probarlo:

```bash
cp ejemplo_entrada.txt Input/Entrada/
python main.py
```

En Windows:

```bat
copy ejemplo_entrada.txt Input\Entrada\
py main.py
```

## 7. Ejemplo de salida

El archivo final se crea o actualiza en:

```text
Salida/salida_cerezas.xlsx
```

Cada ejecucion agrega filas al mismo Excel. No borra las filas anteriores.

Columnas generadas:

```text
identificador_sistema
archivo_origen
fecha
mercado
exportadora
variedad
empaque
calibre
precio_min
precio_max
tipo_embarque
cantidad_referencia
texto_origen
observaciones
```

## 8. Instrucciones de PyInstaller

### Instalar PyInstaller

```bash
pip install pyinstaller
```

O:

```bash
pip install -r requirements.txt
```

### Opcion onedir recomendada

En Windows:

```bat
pyinstaller --console --name ProcesadorCerezas --add-data "diccionarios.json;." main.py
```

En macOS o Linux:

```bash
pyinstaller --console --name ProcesadorCerezas --add-data "diccionarios.json:." main.py
```

Explicacion:

- `--console`: mantiene abierta una consola para ingresar el identificador y ver logs.
- `--name ProcesadorCerezas`: nombre del ejecutable.
- `--add-data "diccionarios.json;."`: incluye el diccionario en el paquete.
- `main.py`: archivo principal.

El ejecutable queda en:

```text
dist/ProcesadorCerezas/
```

Al ejecutar el `.exe`, el sistema creara junto al ejecutable:

```text
Input/Entrada
Procesado
Salida
```

### Opcion onefile

En Windows:

```bat
pyinstaller --onefile --console --name ProcesadorCerezas --add-data "diccionarios.json;." main.py
```

En macOS o Linux:

```bash
pyinstaller --onefile --console --name ProcesadorCerezas --add-data "diccionarios.json:." main.py
```

`--onefile` genera un solo ejecutable. Las carpetas `Input/Entrada`, `Procesado` y `Salida` se crean junto al ejecutable.

### Como encuentra archivos auxiliares

`diccionarios.json` se busca con `ruta_recurso()`, que funciona tanto en desarrollo como dentro de PyInstaller.

Las carpetas de trabajo se crean con `ruta_base()`. En desarrollo quedan junto a los `.py`; en ejecutable quedan junto al `.exe`.

### Usar archivo .spec

Tambien se incluye `cerezas_parser.spec`:

```bash
pyinstaller cerezas_parser.spec
```

### Errores comunes

Si aparece un error de `diccionarios.json`, revise que el comando tenga `--add-data` o use el `.spec`.

Si aparece `ModuleNotFoundError: openpyxl`, ejecute:

```bash
pip install -r requirements.txt
```

Si el Excel esta abierto, puede fallar el guardado. Cierre `Salida/salida_cerezas.xlsx` antes de ejecutar nuevamente.

Si no procesa nada, revise que los archivos tengan extension `.txt` y esten dentro de `Input/Entrada`.

## 9. Archivo .spec

El `.spec` incluye:

```python
datas=[("diccionarios.json", ".")]
```

Esto agrega el diccionario al ejecutable.

## 10. Sugerencias futuras de mejora

- Crear un archivo de log en `Salida`.
- Agregar una columna `estado` con `OK` o `REVISAR`.
- Evitar duplicados si se procesa el mismo archivo dos veces.
- Permitir configurar el nombre del Excel de salida.
- Agregar pruebas automaticas para formatos nuevos.
