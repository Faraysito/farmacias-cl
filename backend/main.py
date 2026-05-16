from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api import busqueda

app = FastAPI(title="Farmacias CL API")

# CORS
ALLOWED_ORIGINS = [
    "http://localhost:4321",
    "http://localhost:3000",
    "https://farmacias-cl.vercel.app",
]

# Permitir previews de Vercel (*.vercel.app de tu proyecto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://farmacias-cl-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(busqueda.router, prefix="/api", tags=["busqueda"])


@app.get("/")
def root():
    return {"ok": True, "msg": "Farmacias CL API"}