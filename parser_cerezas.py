import re
from typing import Dict, List, Tuple


CAMPOS_SALIDA = [
    "identificador_sistema",
    "archivo_origen",
    "fecha",
    "mercado",
    "exportadora",
    "variedad",
    "empaque",
    "calibre",
    "precio_min",
    "precio_max",
    "tipo_embarque",
    "cantidad_referencia",
    "texto_origen",
    "observaciones",
]


def normalizar_texto(texto: str) -> str:
    """Limpia espacios sin perder la estructura por lineas."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = texto.replace("，", ",").replace("；", ";")

    lineas = []
    for linea in texto.split("\n"):
        linea = re.sub(r"\s+", " ", linea).strip()
        if linea:
            lineas.append(linea)

    return "\n".join(lineas)


def procesar_texto(texto: str, diccionarios: Dict) -> Tuple[List[Dict], List[str]]:
    """Procesa el texto completo y devuelve registros mas mensajes de log."""
    logs = []
    texto_normalizado = normalizar_texto(texto)

    if not texto_normalizado:
        return [], ["No hay texto para procesar."]

    fecha = detectar_fecha(texto_normalizado)
    mercado = detectar_mercado(texto_normalizado)
    tipo_embarque = detectar_por_diccionario(texto_normalizado, diccionarios, "embarques")

    if fecha:
        logs.append(f"Fecha detectada: {fecha}")
    else:
        logs.append("No se detecto fecha.")

    if mercado:
        logs.append(f"Mercado detectado: {mercado}")
    else:
        logs.append("No se detecto mercado.")

    segmentos = segmentar_texto(texto_normalizado)
    logs.append(f"Segmentos analizables encontrados: {len(segmentos)}")

    registros = []
    for segmento in segmentos:
        registros_segmento = extraer_registros_de_segmento(
            segmento=segmento,
            fecha=fecha,
            mercado=mercado,
            tipo_embarque=tipo_embarque,
            diccionarios=diccionarios,
        )
        registros.extend(registros_segmento)

    if not registros:
        logs.append("No se generaron registros. Revise el formato del texto.")
    else:
        logs.append(f"Registros generados: {len(registros)}")

    return registros, logs


def detectar_fecha(texto: str) -> str:
    patron = re.search(r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b", texto)
    if not patron:
        return ""

    partes = re.split(r"[-/]", patron.group(1))
    anio, mes, dia = partes
    return f"{int(anio):04d}-{int(mes):02d}-{int(dia):02d}"


def detectar_mercado(texto: str) -> str:
    for linea in texto.split("\n"):
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", linea):
            continue

        coincidencia = re.match(r"^([A-Z]{2,5})\b", linea.strip())
        if coincidencia:
            return coincidencia.group(1)

    return ""


def segmentar_texto(texto: str) -> List[str]:
    """Divide por lineas utiles. Cada linea comercial suele representar un lote."""
    segmentos = []
    for linea in texto.split("\n"):
        if not linea:
            continue
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", linea):
            continue

        tiene_lote = bool(re.search(r"(^|\s)\d+\s*P\s*/", linea, flags=re.IGNORECASE))
        tiene_precio = bool(re.search(r"/\s*\d+(?:\s*-\s*\d+)?", linea))

        if tiene_lote or tiene_precio:
            segmentos.append(linea)

    return segmentos


def extraer_registros_de_segmento(
    segmento: str,
    fecha: str,
    mercado: str,
    tipo_embarque: str,
    diccionarios: Dict,
) -> List[Dict]:
    exportadora = detectar_por_diccionario(segmento, diccionarios, "exportadoras")
    variedad = detectar_por_diccionario(segmento, diccionarios, "variedades")
    empaque = detectar_por_diccionario(segmento, diccionarios, "empaques")
    tipo_embarque_linea = detectar_por_diccionario(segmento, diccionarios, "embarques") or tipo_embarque
    cantidad = detectar_cantidad_referencia(segmento)
    observaciones = extraer_observaciones(segmento)
    pares_precio = extraer_pares_calibre_precio(segmento, diccionarios)

    registros = []

    if pares_precio:
        for calibre, precio_min, precio_max in pares_precio:
            registro = crear_registro_base(
                fecha=fecha,
                mercado=mercado,
                exportadora=exportadora,
                variedad=variedad,
                empaque=empaque,
                calibre=calibre,
                precio_min=precio_min,
                precio_max=precio_max,
                tipo_embarque=tipo_embarque_linea,
                cantidad=cantidad,
                texto_origen=segmento,
                observaciones=observaciones,
            )
            registros.append(validar_registro(registro))
    else:
        registro = crear_registro_base(
            fecha=fecha,
            mercado=mercado,
            exportadora=exportadora,
            variedad=variedad,
            empaque=empaque,
            calibre="",
            precio_min="",
            precio_max="",
            tipo_embarque=tipo_embarque_linea,
            cantidad=cantidad,
            texto_origen=segmento,
            observaciones=observaciones,
        )
        registros.append(validar_registro(registro))

    return registros


def crear_registro_base(
    fecha: str,
    mercado: str,
    exportadora: str,
    variedad: str,
    empaque: str,
    calibre: str,
    precio_min: str,
    precio_max: str,
    tipo_embarque: str,
    cantidad: str,
    texto_origen: str,
    observaciones: str,
) -> Dict:
    return {
        "identificador_sistema": "",
        "archivo_origen": "",
        "fecha": fecha,
        "mercado": mercado,
        "exportadora": exportadora,
        "variedad": variedad,
        "empaque": empaque,
        "calibre": calibre,
        "precio_min": precio_min,
        "precio_max": precio_max,
        "tipo_embarque": tipo_embarque,
        "cantidad_referencia": cantidad,
        "texto_origen": texto_origen,
        "observaciones": observaciones,
    }


def validar_registro(registro: Dict) -> Dict:
    faltantes = []
    for campo in ["exportadora", "variedad", "empaque", "calibre", "precio_min"]:
        if not registro.get(campo):
            faltantes.append(campo)

    if faltantes:
        mensaje = "REVISAR MANUALMENTE: faltan " + ", ".join(faltantes)
        if registro["observaciones"]:
            registro["observaciones"] = mensaje + " | " + registro["observaciones"]
        else:
            registro["observaciones"] = mensaje

    return registro


def detectar_cantidad_referencia(segmento: str) -> str:
    coincidencias = re.findall(r"(?:^|\s)(\d+\s*P)\s*/", segmento, flags=re.IGNORECASE)
    if coincidencias:
        return coincidencias[-1].replace(" ", "").upper()

    coincidencia = re.match(r"^(\d+\s*P)\b", segmento, flags=re.IGNORECASE)
    if coincidencia:
        return coincidencia.group(1).replace(" ", "").upper()

    return ""


def extraer_pares_calibre_precio(segmento: str, diccionarios: Dict) -> List[Tuple[str, str, str]]:
    calibres = obtener_aliases(diccionarios, "calibres")
    if not calibres:
        calibres = ["4JD", "3JD", "2JD", "JD", "JL", "JJJ", "JJ", "J", "XL", "L"]

    aliases = sorted(calibres, key=len, reverse=True)
    patron_calibres = "|".join(re.escape(alias) for alias in aliases)
    patron = re.compile(
        rf"(?<![A-Z0-9])(?P<calibre>{patron_calibres})\s*/\s*(?P<precio>\d+(?:\s*-\s*\d+)?)",
        flags=re.IGNORECASE,
    )

    pares = []
    for coincidencia in patron.finditer(segmento.upper()):
        calibre = normalizar_valor_diccionario(coincidencia.group("calibre"), diccionarios, "calibres")
        precio_min, precio_max = separar_precio(coincidencia.group("precio"))
        pares.append((calibre, precio_min, precio_max))

    return pares


def separar_precio(precio: str) -> Tuple[str, str]:
    precio = precio.replace(" ", "")
    if "-" in precio:
        minimo, maximo = precio.split("-", 1)
        return minimo, maximo

    return precio, precio


def extraer_observaciones(segmento: str) -> str:
    coincidencias = list(re.finditer(r"/\s*\d+(?:\s*-\s*\d+)?", segmento))
    if not coincidencias:
        return ""

    fin_ultimo_precio = coincidencias[-1].end()
    observacion = segmento[fin_ultimo_precio:]
    observacion = observacion.strip(" ,;")
    return observacion


def detectar_por_diccionario(texto: str, diccionarios: Dict, categoria: str) -> str:
    texto_normalizado = texto.upper()
    candidatos = []

    for item in diccionarios.get(categoria, []):
        valor, aliases = leer_item_diccionario(item)
        for alias in aliases:
            alias_normalizado = alias.upper()
            if not alias_normalizado:
                continue
            if alias_normalizado in texto_normalizado:
                candidatos.append((len(alias_normalizado), valor))

    if not candidatos:
        return ""

    candidatos.sort(reverse=True)
    return candidatos[0][1]


def normalizar_valor_diccionario(alias: str, diccionarios: Dict, categoria: str) -> str:
    alias_normalizado = alias.upper()
    for item in diccionarios.get(categoria, []):
        valor, aliases = leer_item_diccionario(item)
        if alias_normalizado in [a.upper() for a in aliases]:
            return valor
    return alias


def obtener_aliases(diccionarios: Dict, categoria: str) -> List[str]:
    aliases = []
    for item in diccionarios.get(categoria, []):
        _, item_aliases = leer_item_diccionario(item)
        aliases.extend(item_aliases)
    return aliases


def leer_item_diccionario(item) -> Tuple[str, List[str]]:
    if isinstance(item, str):
        return item, [item]

    valor = item.get("valor", "")
    aliases = item.get("aliases", [])

    if valor and valor not in aliases:
        aliases.append(valor)

    return valor, aliases
