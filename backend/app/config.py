import os

# Si DISABLE_CRUZVERDE=1, no se intenta scrapear Cruz Verde (para deploy sin Playwright)
DISABLE_CRUZVERDE = os.getenv("DISABLE_CRUZVERDE", "0") == "1"

# Cadenas activas en este entorno
CADENAS_ACTIVAS = ["salcobrand", "ahumada"]
if not DISABLE_CRUZVERDE:
    CADENAS_ACTIVAS.insert(0, "cruzverde")