"""Configuración central, leída desde variables de entorno."""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip() in {"1", "true", "True", "yes"}


# --- Feature flags ---
# Si DISABLE_CRUZVERDE=1, no se intenta scrapear Cruz Verde (deploy sin Playwright).
DISABLE_CRUZVERDE = _bool("DISABLE_CRUZVERDE")

# Cadenas activas en este entorno (orden = prioridad de display).
CADENAS_ACTIVAS = ["salcobrand", "ahumada"]
if not DISABLE_CRUZVERDE:
    CADENAS_ACTIVAS.insert(0, "cruzverde")

# --- Seguridad ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# --- CORS ---
BASE_CORS_ORIGINS = [
    "http://localhost:4321",
    "http://localhost:3000",
    "https://farmacias-cl.vercel.app",
]
_extra = os.getenv("EXTRA_CORS_ORIGINS", "")
EXTRA_CORS_ORIGINS = [o.strip() for o in _extra.split(",") if o.strip()]
ALLOWED_ORIGINS = BASE_CORS_ORIGINS + EXTRA_CORS_ORIGINS

# --- Rate limiting ---
RATE_LIMIT_BUSCAR = os.getenv("RATE_LIMIT_BUSCAR", "20/minute")
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")

# --- Scraper Salcobrand (claves públicas de búsqueda Algolia) ---
SALCOBRAND_ALGOLIA_APP_ID = os.getenv("SALCOBRAND_ALGOLIA_APP_ID", "GM3RP06HJG")
SALCOBRAND_ALGOLIA_API_KEY = os.getenv(
    "SALCOBRAND_ALGOLIA_API_KEY", "0259fe250b3be4b1326eb85e47aa7d81"
)

# --- Alertas de precio (Resend) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
ALERTAS_FROM_EMAIL = os.getenv("ALERTAS_FROM_EMAIL", "alertas@tudominio.cl")
