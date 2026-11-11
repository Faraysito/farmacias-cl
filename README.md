# Comparador de Farmacias Chile

> Plataforma para comparar precios de medicamentos entre las principales cadenas farmacéuticas de Chile (Cruz Verde, Salcobrand y Ahumada), agrupados por principio activo y dosis.

- Demo: https://farmacias-cl.vercel.app
- API: https://farmacias-cl-api.onrender.com

## El problema

En Chile, el mismo medicamento puede costar **20 veces más** dependiendo de la cadena y la marca. Un Losartán 50mg puede ir desde $1.495 hasta $32.207 por el mismo principio activo. La gente no compara porque no hay una forma fácil de hacerlo: cada cadena tiene su propio sitio, sus propios nombres comerciales y sus propios laboratorios.

Este proyecto resuelve eso: una sola búsqueda, las tres cadenas comparadas lado a lado, agrupadas por principio activo para que veas todas las alternativas (incluyendo bioequivalentes más baratos) y el **ahorro exacto**.

## Cómo funciona

1. El usuario busca un medicamento (ej. "losartan") o usa los chips/categorías del home
2. El autocomplete sugiere principios activos y nombres comerciales mientras escribe
3. El backend revisa si hay datos recientes en DB
4. Si la DB está vacía o tiene pocos resultados, dispara scraping **on-demand** de las cadenas activas en paralelo
5. Los resultados se normalizan: principio activo, dosis y se eliminan marcas/laboratorios del nombre
6. Se agrupan productos con el mismo principio activo + dosis y se calcula el ahorro
7. El frontend muestra cada grupo como una tarjeta "escalera de precios", de menor a mayor
8. El usuario puede filtrar, ordenar por ahorro, ver el histórico, crear una **alerta de precio** y comprar directo en la cadena

## Stack

### Backend
- **Python 3.12** + **FastAPI** (API REST async) con **slowapi** (rate limiting)
- **SQLAlchemy 2** + **Alembic** (ORM y migraciones)
- **PostgreSQL 16 + PostGIS** (DB con soporte geoespacial para fase futura) + **pg_trgm** (búsqueda)
- **psycopg 3** (driver Postgres)
- **Playwright** (Cruz Verde, requerido por Imperva/Incapsula)
- **httpx** + **BeautifulSoup** (Salcobrand y Ahumada)
- **Resend** (envío opcional de alertas por email)

### Frontend
- **Astro** (static site generator)
- **Tailwind CSS v4** (estilos, configuración CSS-first con `@theme`)
- **Alpine.js** (interactividad)
- **Chart.js** + **date-fns adapter** (histórico)
- Modo oscuro, estado en URL, Open Graph / JSON-LD

### Infra
- **Render** (backend, free tier) · **Vercel** (frontend) · **Neon** (Postgres serverless)
- **UptimeRobot** (ping cada 5 min anti cold-start)
- **GitHub Actions** (cron nocturno de scrape + CI de lint/tests/build)

## Decisiones técnicas clave

### Estrategia de scraping por cadena

| Cadena | Técnica | Razón |
|---|---|---|
| Cruz Verde | Playwright (browser) | API protegida por Imperva, requiere cookies de sesión generadas por JS |
| Salcobrand | httpx → Algolia API directa | Su buscador es Algolia público |
| Ahumada | httpx + BeautifulSoup | Server-side rendering (Salesforce Commerce Cloud) |

### Por qué Cruz Verde está deshabilitado en producción
Render free tier da 512MB de RAM; Playwright + Chromium requieren ~1GB. En producción `DISABLE_CRUZVERDE=1` y solo Salcobrand + Ahumada están activos. Cruz Verde funciona en local. _Pendiente: moverlo a un GitHub Action que escriba a la DB._

### Normalizador sin ISP
El dataset del ISP (para limpiar nombres y matchear bioequivalentes) está caído por un incidente de seguridad, así que se usa un normalizador propio (regex + listas negras). Cubre ~80% de los casos. Cuando vuelva el ISP, se reemplazará.

### On-demand scraping
Si buscas algo que no está en DB, se scrapea, se guarda y se devuelve. La primera búsqueda tarda 10-15s; las siguientes son instantáneas.

### Scheduler nocturno por GitHub Actions
Un workflow corre a las 04:00 UTC, despierta Render con un ping y llama a `/api/admin/scrape-top` con un token. Sin infra extra, gratis.

### Histórico con deduplicación diaria
Cada scrape guarda una fila por (medicamento, farmacia) **solo una vez al día**, lo que permite construir el gráfico sin ruido.

### Búsqueda con índices trigram
`LIKE '%q%'` se apoya en índices GIN `pg_trgm` (migración `a1f2c3d4e5f6`) en vez de escanear toda la tabla.

## Estructura del proyecto
~~~
farmacias-cl/
├── README.md
├── docker-compose.yml          # Postgres + PostGIS para dev local
├── .github/workflows/
│   ├── scrape-cron.yml         # Cron nocturno
│   └── ci.yml                  # Lint + tests + build
├── backend/
│   ├── alembic/                # Migraciones DB
│   ├── main.py                 # Entry point FastAPI (CORS, rate limit, headers)
│   ├── runtime.txt
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── ruff.toml
│   ├── pytest.ini
│   ├── .env.example
│   ├── app/
│   │   ├── config.py           # Settings desde entorno
│   │   ├── database.py
│   │   ├── ratelimit.py        # Limiter compartido (slowapi)
│   │   ├── models.py           # PrincipioActivo, Medicamento, Farmacia, Precio, AlertaPrecio
│   │   ├── schemas.py
│   │   ├── normalizador.py
│   │   ├── persistencia.py
│   │   ├── scrape_orchestrator.py
│   │   ├── api/
│   │   │   ├── busqueda.py      # GET /api/buscar (paginado + ahorro)
│   │   │   ├── home.py          # GET /api/home/categorias|top|stats
│   │   │   ├── autocomplete.py  # GET /api/autocomplete
│   │   │   ├── historico.py     # GET /api/historico/{id} (+ resumen)
│   │   │   ├── alertas.py       # POST/DELETE /api/alertas
│   │   │   └── admin.py         # POST /api/admin/scrape-top (token)
│   │   └── scrapers/
│   │       ├── base.py
│   │       ├── cruzverde.py
│   │       ├── salcobrand.py
│   │       └── ahumada.py
│   ├── scripts/
│   └── tests/                  # pytest (normalizador, schemas)
└── frontend/
    ├── package.json
    ├── astro.config.mjs
    ├── public/                 # favicon.svg, og.svg
    └── src/
        ├── layouts/Base.astro  # head, SEO/OG, fuentes, tema
        ├── pages/
        │   ├── index.astro     # Home + buscador + resultados
        │   ├── medicamento.astro   # Detalle compartible (?id=)
        │   └── acerca.astro    # Contexto + aviso legal
        └── styles/global.css   # Tokens, dark mode, animaciones
~~~

## Setup local

### Prerrequisitos
- Python 3.12 · Node.js 22+ · Docker Desktop · Git

### 1. Clonar y entrar
```bash
git clone https://github.com/Faraysito/farmacias-cl.git
cd farmacias-cl
```

### 2. Levantar la DB
```bash
docker compose up -d
```
Arranca Postgres + PostGIS en el puerto **5433**.

### 3. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1       # PowerShell
# source .venv/bin/activate       # Linux/Mac

pip install -r requirements.txt
playwright install chromium       # Solo si vas a usar Cruz Verde
```
Copia `.env.example` a `.env` y ajusta `ADMIN_TOKEN`. Luego:
```bash
alembic upgrade head
uvicorn main:app --reload
```
API en `http://localhost:8000` · Docs en `/docs`.

### 4. Frontend
```bash
cd ../frontend
npm install
npm run dev
```
Frontend en `http://localhost:4321`.

### 5. Poblar DB (opcional)
```bash
cd backend
$env:PYTHONPATH="."; python scripts/reset_y_scrape.py
```

### Tests y lint
```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
ruff check app tests
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/buscar?q=&pagina=&por_pagina=` | Búsqueda paginada con ahorro por grupo (scrape on-demand si hay pocos datos) |
| GET | `/api/autocomplete?q=` | Sugerencias por prefijo |
| GET | `/api/historico/{med_id}?dias=90` | Histórico por cadena + resumen (min/max/prom/tendencia) |
| GET | `/api/home/categorias\|top\|stats` | Datos del home |
| POST | `/api/alertas` | Crea alerta de precio (email) |
| DELETE | `/api/alertas/{id}` | Cancela alerta |
| POST | `/api/admin/scrape-top` | Scrape del top (header `X-Admin-Token`) |
| GET | `/api/health` | Health check |

## Deploy

### Backend en Render
- Web Service (free), región Oregon
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env: `DATABASE_URL` (Neon, `postgresql+psycopg://…?sslmode=require`), `DISABLE_CRUZVERDE=1`, `ADMIN_TOKEN`, y opcionalmente `RESEND_API_KEY`, `ALERTAS_FROM_EMAIL`.

### Frontend en Vercel
- Framework: Astro · Root: `frontend`
- Env: `PUBLIC_API_URL=https://farmacias-cl-api.onrender.com`

### DB en Neon
- Plan free · `CREATE EXTENSION IF NOT EXISTS postgis;` (pg_trgm lo crea la migración)

### Cron e infra
- `.github/workflows/scrape-cron.yml` (04:00 UTC) con secret `ADMIN_TOKEN`
- UptimeRobot pinga la API cada 5 min anti cold-start

## Roadmap

### Hecho
- [x] Scrapers de las 3 cadenas, normalizador, agrupación por principio activo
- [x] On-demand scraping, UI de comparación, deploy gratis 24/7
- [x] Home, autocomplete, filtros, histórico con gráficos
- [x] Scheduler nocturno por GitHub Actions
- [x] Cálculo de ahorro destacado
- [x] Alertas de precio por email (Resend)
- [x] Página de detalle compartible
- [x] Modo oscuro, SEO/OG, accesibilidad
- [x] Tests + CI

### Pendiente
- [ ] Integrar dataset ISP cuando vuelva online
- [ ] Cruz Verde en producción vía GitHub Action
- [ ] Farmacias independientes con PostGIS (mapa de cercanas)

### Deuda técnica conocida
- Normalizador es lista negra manual (se reemplaza por ISP)
- Matcheo de laboratorios es O(n) por producto; mover a SQL con catálogo grande
- Algunas marcas hacen ruido si Ahumada no manda el campo `brand` separado
