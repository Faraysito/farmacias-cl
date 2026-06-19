from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import admin, alertas, autocomplete, busqueda, historico, home
from app.config import ALLOWED_ORIGINS
from app.ratelimit import limiter

app = FastAPI(title="Farmacias CL API", version="1.0.0")

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://farmacias-cl-.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --- Cabeceras de seguridad básicas ---
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(busqueda.router, prefix="/api", tags=["busqueda"])
app.include_router(home.router, prefix="/api", tags=["home"])
app.include_router(autocomplete.router, prefix="/api", tags=["autocomplete"])
app.include_router(historico.router, prefix="/api", tags=["historico"])
app.include_router(alertas.router, prefix="/api", tags=["alertas"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.get("/")
def root():
    return {"ok": True, "msg": "Farmacias CL API"}


@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})
