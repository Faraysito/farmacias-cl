import re
from typing import Tuple, Optional


def parsear_medicamento(nombre: str) -> Tuple[str, Optional[str]]:
    """
    Extrae principio activo y dosis del nombre comercial.
    
    Ejemplos:
      "Losartan Potasico 50 mg 30 Comprimidos" -> ("losartan potasico", "50mg")
      "Lopren Losartan Potasico 50 mg" -> ("losartan potasico", "50mg")
    
    Heurística simple: busca primer match de dosis (NN mg, NN ml, etc).
    Lo que está antes es nombre/marca, después es presentación.
    """
    nombre_lower = nombre.lower().strip()
    
    # Busca dosis: "50 mg", "500 mg", "5 ml", "12.5 mg"
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(mg|ml|mcg|g|ui)\b', nombre_lower)
    dosis = None
    if match:
        valor = match.group(1).replace(",", ".")
        unidad = match.group(2)
        dosis = f"{valor}{unidad}"
        # El principio activo está antes de la dosis
        principio = nombre_lower[:match.start()].strip()
    else:
        principio = nombre_lower
    
    # Limpiar: quitar palabras de marca comerciales comunes al inicio
    # (heurística básica, mejorable con dataset ISP)
    palabras = principio.split()
    # Quitar palabras muy cortas o que parecen marcas (1ra palabra capitalizada en original)
    return principio, dosis