# Comparador de Farmacias Chile

> Plataforma para comparar precios de medicamentos entre las principales cadenas farmacéuticas de Chile (Cruz Verde, Salcobrand y Ahumada), agrupados por principio activo y dosis.

**🌐 Demo:** https://farmacias-cl.vercel.app
**⚙️ API:** https://farmacias-cl-api.onrender.com

---

## El problema

En Chile, el mismo medicamento puede costar **20 veces más** dependiendo de la cadena y la marca. Un Losartán 50mg puede ir desde $1.495 hasta $32.207 por el mismo principio activo. La gente no compara porque no hay una forma fácil de hacerlo: cada cadena tiene su propio sitio, sus propios nombres comerciales y sus propios laboratorios.

Este proyecto resuelve eso: una sola búsqueda, las tres cadenas comparadas lado a lado, agrupadas por principio activo para que veas todas las alternativas (incluyendo bioequivalentes más baratos).

---

## Cómo funciona

1. El usuario busca un medicamento (ej. "losartan")
2. El backend revisa si hay datos recientes en DB
3. Si la DB está vacía o tiene pocos resultados, dispara scraping **on-demand** de las 3 cadenas en paralelo
4. Los resultados se normalizan: se extrae principio activo, dosis y se eliminan marcas/laboratorios del nombre
5. Se agrupan productos con el mismo principio activo + dosis
6. El frontend muestra cada grupo como una card, con todas las ofertas ordenadas de menor a mayor precio

---

## Stack

### Backend
- **Python 3.12** + **FastAPI** (API REST async)
- **SQLAlchemy 2** + **Alembic** (ORM y migraciones)
- **PostgreSQL 16 + PostGIS** (DB con soporte geoespacial para fase futura de farmacias independientes)
- **psycopg 3** (driver Postgres)
- **Playwright** (scraping Cruz Verde, requerido por Imperva/Incapsula)
- **httpx** + **BeautifulSoup** (scraping Salcobrand y Ahumada)

### Frontend
- **Astro** (static site generator)
- **Tailwind CSS** (estilos)
- **Alpine.js** (interactividad mínima)

### Infra
- **Render** (backend, free tier)
- **Vercel** (frontend, free)
- **Neon** (Postgres serverless, free)
- **UptimeRobot** (ping cada 5 min para evitar cold starts de Render)

---

## Decisiones técnicas clave

### Estrategia de scraping por cadena

Cada cadena requiere una técnica distinta:

| Cadena | Técnica | Razón |
|---|---|---|
| Cruz Verde | Playwright (browser) | API protegida por Imperva, requiere cookies de sesión generadas por JS |
| Salcobrand | httpx → Algolia API directa | Su buscador es Algolia público, sin protección |
| Ahumada | httpx + BeautifulSoup | Server-side rendering (Salesforce Commerce Cloud), basta con parsear el HTML |

### Por qué Cruz Verde está deshabilitado en producción

Render free tier solo da 512MB de RAM. Playwright + Chromium requieren ~1GB. En producción se usa `DISABLE_CRUZVERDE=1` y solo Salcobrand + Ahumada están activos. Cruz Verde sigue funcionando en desarrollo local.

### Normalizador sin ISP

Originalmente se planeaba usar el dataset oficial del ISP (Instituto de Salud Pública) para limpiar nombres y matchear bioequivalentes. El sitio del ISP está caído por un incidente de seguridad, así que se implementó un normalizador propio basado en regex + listas negras de marcas y formas farmacéuticas. Cubre ~80% de los casos. Cuando vuelva el ISP, se reemplazará por matching contra el catálogo oficial.

### On-demand scraping

Si un usuario busca algo que no está en DB, el backend scrapea las cadenas activas, guarda los resultados y los devuelve. La primera búsqueda tarda 10-15 segundos. Las siguientes son instantáneas porque ya están cacheadas.

### Agrupación por principio activo + laboratorio

Para detectar que "Losartan 50mg de Labchile" en Salcobrand es el mismo producto que "Losartán 50mg" en Ahumada, se compara por (principio_activo, dosis, laboratorio_normalizado). Sin un dataset maestro (ISP), no es perfecto: cadenas distintas escriben los laboratorios con nombres distintos, por eso a veces aparecen como ofertas separadas dentro del mismo grupo de principio activo.

---

## Estructura del proyecto

```
farmacias-cl/
├── README.md
├── docker-compose.yml          # Postgres + Redis para dev local
├── backend/
│   ├── alembic/                # Migraciones DB
│   ├── alembic.ini
│   ├── main.py                 # Entry point FastAPI
│   ├── runtime.txt             # Pin de Python para Render
│   ├── requirements.txt
│   ├── .env                    # No commiteado
│   ├── .env.example
│   ├── app/
│   │   ├── config.py           # Feature flags (DISABLE_CRUZVERDE)
│   │   ├── database.py         # Engine SQLAlchemy
│   │   ├── models.py           # PrincipioActivo, Medicamento, Farmacia, Precio
│   │   ├── schemas.py          # Pydantic responses
│   │   ├── normalizador.py     # Limpieza de nombres → (principio, dosis)
│   │   ├── persistencia.py     # get_or_create + guardar_productos
│   │   ├── scrape_orchestrator.py  # Scrape paralelo de las 3 cadenas
│   │   ├── api/
│   │   │   └── busqueda.py     # GET /api/buscar?q=...
│   │   └── scrapers/
│   │       ├── base.py         # Dataclass ProductoRaw común
│   │       ├── cruzverde.py    # Playwright
│   │       ├── salcobrand.py   # httpx + Algolia
│   │       └── ahumada.py      # httpx + BeautifulSoup
│   └── scripts/
│       ├── scrape_cruzverde.py
│       ├── scrape_salcobrand.py
│       ├── scrape_ahumada.py
│       ├── reset_y_scrape.py   # Limpia DB y rescrapea desde 0
│       └── test_normalizador.py
└── frontend/
    ├── package.json
    ├── astro.config.mjs
    ├── tailwind.config.mjs
    └── src/
        ├── pages/
        │   └── index.astro     # Buscador + listado de grupos
        └── styles/
            └── global.css
```

---

## Setup local

### Prerrequisitos
- Python 3.12
- Node.js 20+
- Docker Desktop
- Git

### 1. Clonar y entrar

```bash
git clone https://github.com/Faraysito/farmacias-cl.git
cd farmacias-cl
```

### 2. Levantar DB y Redis

```bash
docker compose up -d
```

Esto arranca Postgres + PostGIS en el puerto **5433** (no 5432, para no chocar con Postgres nativo si lo tienes) y Redis en 6379.

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1       # PowerShell
# .venv/bin/activate              # Linux/Mac

pip install -r requirements.txt
playwright install chromium       # Solo si vas a usar Cruz Verde
```

Copia `.env.example` a `.env`:

```env
DATABASE_URL=postgresql+psycopg://farmacias:dev@localhost:5433/farmacias
REDIS_URL=redis://localhost:6379/0
DISABLE_CRUZVERDE=0
```

Aplicar migraciones:

```bash
alembic upgrade head
```

Levantar API:

```bash
uvicorn main:app --reload
```

API en `http://localhost:8000`. Docs interactivas en `http://localhost:8000/docs`.

### 4. Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend en `http://localhost:4321`.

### 5. Poblar DB con datos iniciales (opcional)

```bash
cd backend
python -m scripts.reset_y_scrape
```

Esto scrapea ~8 medicamentos comunes (losartan, metformina, atorvastatina, paracetamol, ibuprofeno, omeprazol, enalapril, amoxicilina) en las 3 cadenas y guarda en DB.

---

## Scripts útiles

```bash
# Scrapear una cadena específica
python -m scripts.scrape_cruzverde losartan
python -m scripts.scrape_salcobrand metformina
python -m scripts.scrape_ahumada paracetamol

# Limpiar DB y rescrapear todo
python -m scripts.reset_y_scrape

# Probar el normalizador con casos de ejemplo
python -m scripts.test_normalizador
```

---

## Endpoint principal

### `GET /api/buscar?q={query}`

Busca medicamentos por nombre comercial o principio activo. Si hay pocos resultados en DB, dispara scrape on-demand.

**Response:**

```json
[
  {
    "principio_activo": "losartan",
    "dosis": "50mg",
    "cantidad_medicamentos": 6,
    "medicamentos": [
      {
        "id": 12,
        "nombre_comercial": "Losartán (B) 50mg 30 Comprimidos",
        "laboratorio": "Losartán",
        "es_bioequivalente": true,
        "precios": [
          {
            "cadena": "salcobrand",
            "precio": 1495.0,
            "stock": true,
            "fecha_scrape": "2026-05-16T..."
          }
        ]
      }
    ]
  }
]
```

---

## Deploy

### Backend en Render

- Servicio: Web Service (free tier)
- Region: Oregon
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variables de entorno:
  - `DATABASE_URL` (Neon connection string con `postgresql+psycopg://` y `?sslmode=require`)
  - `DISABLE_CRUZVERDE=1`

### Frontend en Vercel

- Framework: Astro (auto-detectado)
- Root directory: `frontend`
- Variable de entorno:
  - `PUBLIC_API_URL=https://farmacias-cl-api.onrender.com`

### DB en Neon

- Plan free (0.5 GB, no expira)
- PostGIS habilitado: `CREATE EXTENSION IF NOT EXISTS postgis;`

### Mantener vivo Render free

UptimeRobot pinga `https://farmacias-cl-api.onrender.com` cada 5 min. Sin esto, Render se duerme tras 15 min idle y la primera llamada tarda ~50s.

---

## Roadmap

### Hecho
- [x] Scraper Cruz Verde (Playwright)
- [x] Scraper Salcobrand (Algolia API)
- [x] Scraper Ahumada (HTML parsing)
- [x] Normalizador de principio activo + dosis
- [x] Agrupación por principio + dosis + laboratorio
- [x] On-demand scraping cuando DB vacía
- [x] UI con comparación lado a lado
- [x] Deploy gratis 24/7

### Próximo
- [ ] Celery + scheduler nocturno para top 100 medicamentos crónicos
- [ ] Integrar dataset ISP cuando vuelva online
- [ ] Sistema de alertas por email (Resend) cuando baje el precio
- [ ] Filtros en UI: solo bioequivalentes, rango de precio, cadena
- [ ] Link directo a comprar en cada cadena
- [ ] Búsqueda con sugerencias (autocomplete)
- [ ] Farmacias independientes con PostGIS (mapa de cercanas)
- [ ] Histórico de precios (gráficos)

### Deuda técnica conocida
- Normalizador es lista negra manual; se reemplaza por ISP cuando vuelva
- Cruz Verde solo funciona en desarrollo (Playwright no entra en Render free)
- Algunas marcas hacen ruido en el principio activo si Ahumada no manda el campo `brand` separado
- No hay paginación en `/api/buscar`

---

## Licencia

MIT
