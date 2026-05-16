from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import busqueda, home, autocomplete, historico, admin

app = FastAPI(title="Farmacias CL API")

ALLOWED_ORIGINS = [
    "http://localhost:4321",
    "http://localhost:3000",
    "https://farmacias-cl.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://farmacias-cl-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(busqueda.router, prefix="/api", tags=["busqueda"])
app.include_router(home.router, prefix="/api", tags=["home"])
app.include_router(autocomplete.router, prefix="/api", tags=["autocomplete"])
app.include_router(historico.router, prefix="/api", tags=["historico"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.get("/")
def root():
    return {"ok": True, "msg": "Farmacias CL API"}