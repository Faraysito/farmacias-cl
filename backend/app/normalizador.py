"""Normaliza nombres de medicamentos a (principio_activo, dosis_mg)."""
import re
import unicodedata

# Sufijos de forma farmacéutica a ignorar
FORMAS = {
    "comprimidos", "comprimido", "recubiertos", "recubierto",
    "recubiertas", "recubierta",
    "capsulas", "capsula", "cápsulas", "cápsula",
    "tabletas", "tableta",
    "jarabe", "suspension", "solucion", "gotas",
    "crema", "gel", "ungüento", "unguento",
    "inyectable", "ampolla", "ampollas",
    "sobre", "sobres", "polvo", "polvos",
    "grageas",
    "prolongadas", "prolongada", "prolongado", "prolongados",
    "granulos", "gránulos",
    "entericos", "entericas", "enterico", "enterica",
    "recubrimiento",
    "liberacion", "liberación",
    "masticables", "masticable",
    "efervescentes", "efervescente",
}

# Palabras de ruido, modificadores de sal y sufijos de laboratorio
RUIDO = {
    "potasico", "potásico", "sodico", "sódico", "calcico", "cálcico",
    "monohidratada", "monohidratado", "hidratado", "anhidro",
    "dihidrato", "trihidrato",
    "cenabast", "labchile", "mintlab", "saval", "andromaco",
    "laboratorios", "laboratorio", "genericos", "generico", "pharma", "spa",
    "chile", "ltda", "limitada", "sa",
    "b", "g", "r",
    "del", "de", "la", "el", "x", "con", "sin", "para",
}


def _sin_tildes(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def normalizar(nombre_comercial: str, marca: str | None = None) -> tuple[str, int | None]:
    """
    Devuelve (principio_activo_normalizado, dosis_mg).
    Si se pasa la marca, se elimina del nombre antes de procesar.
    Ej: ('Cozaar (R) Losartán 50mg 30 Comprimidos', 'Cozaar') -> ('losartan', 50)
    """
    s = _sin_tildes(nombre_comercial.lower())

    # Quitar la marca si viene
    if marca:
        marca_norm = _sin_tildes(marca.lower())
        s = s.replace(marca_norm, " ")
        for tok in re.findall(r"[a-z]+", marca_norm):
            if len(tok) > 2:
                s = re.sub(rf"\b{tok}\b", " ", s)

    # Extraer dosis (primer "Xmg" encontrado)
    dosis_match = re.search(r"(\d+(?:[.,]\d+)?)\s*mg\b", s)
    dosis = None
    if dosis_match:
        try:
            dosis = int(float(dosis_match.group(1).replace(",", ".")))
        except ValueError:
            pass

    # Quitar paréntesis y su contenido
    s = re.sub(r"\([^)]*\)", " ", s)
    # Quitar números con unidades
    s = re.sub(r"\d+(?:[.,]\d+)?\s*(?:mg|ml|mcg|µg|ug|g|%)\b", " ", s)
    # Quitar números sueltos
    s = re.sub(r"\b\d+\b", " ", s)
    # Quitar barras y guiones
    s = re.sub(r"[\/\-\.]", " ", s)

    tokens = re.findall(r"[a-z]+", s)
    descartar = FORMAS | RUIDO
    limpios = [t for t in tokens if t not in descartar and len(t) > 2]

    return " ".join(limpios).strip(), dosis