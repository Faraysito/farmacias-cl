from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import busqueda

app = FastAPI(title="Farmacias CL API")

# CORS: permite que el frontend (Astro) llame a esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(busqueda.router, prefix="/api", tags=["busqueda"])


@app.get("/")
def root():
    return {"ok": True, "msg": "Farmacias CL API"}