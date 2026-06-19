# CAMBIOS

Resumen de las mejoras aplicadas para llevar el proyecto a nivel comercial / portafolio.

## Correcciones (bugs reales)
- **`backend/requirements.txt`**: estaba codificado en **UTF-16** (artefacto de PowerShell) → reescrito en **UTF-8**. Antes podía romper `pip install` en Render/Linux.
- **Dependencias muertas eliminadas**: Celery, Redis, kombu, billiard, amqp, vine (el README ya decía que Celery fue reemplazado por GitHub Actions, pero seguían en `requirements` y en `docker-compose`). Redis quitado también del `docker-compose.yml`.
- **`beautifulsoup4`** ahora va con versión fijada.
- **`datetime.utcnow()`** (deprecado en 3.12) → `datetime.now(timezone.utc)` en modelos y persistencia.
- **README**: documentaba un `tailwind.config.mjs` inexistente (Tailwind v4 usa `@import` en CSS). Corregido.

## Seguridad
- **Claves de Algolia** (Salcobrand) movidas de hardcode a variables de entorno (con fallback).
- **`ADMIN_TOKEN`**: comparación en tiempo constante con `secrets.compare_digest` (antes `!=`, vulnerable a timing).
- **Rate limiting** con `slowapi` (`/api/buscar` limitado; límite global por IP).
- **Cabeceras de seguridad** (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- CORS: `allow_credentials` desactivado (no se usan cookies) y orígenes configurables por env.

## Funcionalidades nuevas
- **Cálculo de ahorro** por grupo (`ahorro_abs`, `ahorro_pct`, `precio_min`, `precio_max`) — el gancho comercial, destacado en la UI.
- **Alertas de precio por email** (`POST /api/alertas`, `DELETE /api/alertas/{id}`) con integración opcional a **Resend**. Nueva tabla `alertas_precio` + migración.
- **Página de detalle compartible** `/medicamento?id=…` (precio actual por cadena + histórico + alerta).
- **Histórico enriquecido**: mínimo, máximo, promedio y tendencia (`/api/historico` ahora devuelve `resumen`).
- **Paginación** en `/api/buscar` (`pagina`, `por_pagina`); respuesta ahora es un objeto `{query,total,pagina,por_pagina,grupos}`.
- **Orden por mayor ahorro** además de por precio.
- **Compartir búsqueda** (copia enlace con estado en la URL `?q=`).
- **`/api/health`** para health checks.

## Diseño / UX
- **Identidad visual propia**: sistema de tokens semánticos (jade = barato, clay = caro), tipografías Bricolage Grotesque + Plus Jakarta Sans + JetBrains Mono. Se eliminó el degradado emerald genérico.
- **Modo oscuro** con toggle persistente y sin parpadeo (no-flash).
- **Tarjetas tipo "escalera de precios"** con barra de spread y ahorro destacado (elemento de firma).
- **Skeleton loaders** en vez de texto "Buscando…".
- **Iconos SVG** en lugar de emojis como UI.
- **Estado en la URL** (`?q=`) con soporte de back/forward.
- **Accesibilidad**: labels, foco visible, `aria` en modales, `prefers-reduced-motion`.
- **SEO**: meta description, Open Graph, Twitter Card, imagen `og.svg`, JSON-LD (Schema.org), favicon propio.
- **Páginas** nuevas: `/acerca` (contexto + stack + aviso legal) y detalle de medicamento.
- **Aviso legal** (precios referenciales, no es consejo médico) en footer y en /acerca.

## Calidad / infraestructura
- **Tests reales con pytest** (normalizador + schemas) reemplazando el script de `print`.
- **CI en GitHub Actions** (`.github/workflows/ci.yml`): lint con ruff + pytest (backend) y build de Astro (frontend).
- **`ruff.toml`** y **`requirements-dev.txt`**.
- **Índices trigram (pg_trgm)** para que las búsquedas `LIKE '%q%'` usen índice en vez de escaneo completo (migración nueva).
- **`.env.example`** ampliado documentando todas las variables.

## Deuda técnica que queda (documentada, no resuelta aquí)
- Cruz Verde sigue deshabilitado en producción por la RAM de Render free (Playwright). Alternativa sugerida: correr ese scraper desde un GitHub Action que escriba a la DB.
- El matcheo de laboratorios sigue siendo `O(n)` por producto; con catálogo grande conviene moverlo a SQL.
- Falta integrar el dataset del ISP cuando vuelva online.
