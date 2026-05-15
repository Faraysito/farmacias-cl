# Farmacias CL

Comparador de precios de medicamentos en cadenas chilenas (Cruz Verde, Salcobrand, Ahumada).

## Stack

- **Backend**: FastAPI + SQLAlchemy + Postgres/PostGIS + Redis + Celery
- **Scrapers**: Playwright (Python)
- **Frontend**: Astro + Tailwind + Alpine.js

## Setup local

Requiere Docker, Python 3.12, Node 20.

```bash
docker compose up -d
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
alembic upgrade head

# Scrapear datos
python -m scripts.scrape_cruzverde losartan

# Levantar API
uvicorn main:app --reload

# Frontend (otra terminal)
cd frontend && npm install && npm run dev
```

Variables de entorno: copiar `.env.example` a `.env`.

## Estado

- [x] Scraper Cruz Verde
- [x] API REST con búsqueda
- [x] Frontend con UI básica
- [ ] Scraper Salcobrand
- [ ] Scraper Ahumada
- [ ] Datos ISP (bioequivalentes)
- [ ] Celery scheduler
- [ ] Alertas por email
- [ ] Deploy