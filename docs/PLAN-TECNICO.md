# MusicFlow — Plan Técnico Detallado

> Documento de decisiones técnicas, arquitectura, modelos, endpoints y orden de implementación.
> Fecha: 2026-09-08 · Versión: 1.0

---

## 1. Resumen Ejecutivo

MusicFlow es un SaaS multi-tenant (schema-per-tenant) para bares y restaurantes. Convierte la
música ambiental en una herramienta de engagement y venta: los clientes piden canciones desde su
mesa por QR, un contador regresivo genera "estrés positivo" que incentiva el consumo, y el dueño
gestiona todo desde un dashboard con diseño Liquid Glass + Neumorfismo.

**Stack final:**
- Backend: Django 5.x + django-tenants + PostgreSQL 15 + DRF + Channels + Celery/Redis + django-cors-headers
- Frontend dashboard: React 18 + Vite + TailwindCSS + Shadcn/ui + Zustand + Recharts
- Frontend cliente (PWA): React 18 + Vite + Framer Motion
- Frontend TV: React 18 + Vite (modo kiosco)
- Pagos: Wompi (Colombia) — tokenización + suscripciones + webhooks
- Deploy: Railway + Cloudflare CDN + Sentry + Logtail

---

## 2. Correcciones Técnicas al Spec (Importante)

Estas son decisiones que se desvían de la propuesta original por motivos técnicos reales. Son
críticas y deben leerse antes de escribir la primera línea de código.

### 2.1 `django-tenant-schemas` está obsoleto → usar `django-tenants`
- `django-tenant-schemas` no se mantiene desde ~2021 y **no soporta Django 5.x**.
- El fork mantenido es **`django-tenants`** (misma API, compatible con Django 5 y PostgreSQL 15).
- Migración: `pip install django-tenants`. La configuración de `TENANT_MODEL`, `TENANT_DOMAIN_MODEL`,
  `SHARED_APPS` y `TENANT_APPS` es idéntica. No hay costo de cambio ahora, solo si se empieza con la
  librería vieja.

### 2.2 JWT en WebSockets no es automático
DRF (`djangorestframework-simplejwt`) protege HTTP, no sockets. Se necesita un **middleware custom
de Channels** que lea el token JWT (query string o header en el handshake) y lo valide antes de
aceptar la conexión. Alternativa recomendada para el cliente-móvil: **token de sesión efímero
firmado** generado al escanear el QR (no expone credenciales de usuario).

### 2.3 Wompi y "suscripciones" — realidad de la API
La API de Wompi tiene dos mecanismos relevantes:
- **Tokenización de tarjetas**: `POST /tokens/cards` → devuelve `token` (ya cubierto en el spec).
- **Suscripciones**: Wompi soporta cobros recurrentes vía su producto de suscripciones, pero la
  operativa real más usada es **"pagos con tarjeta tokenizada programados"** (cobro manual/mensual
  orquestado por Celery) más que una suscripción nativa gestionada enteramente por Wompi.
- Decisión: implementar un **servicio `SubscriptionService`** que abstraiga ambas opciones. La
  fuente de verdad del estado de suscripción vive en **nuestra base de datos** (campo en `Tenant`),
  y Wompi es solo el cobrador. Esto evita acoplarse a una sola modalidad y hace el webhook robusto.

### 2.4 YouTube Premium no es una licencia comercial
La integración con YouTube debe tratarse como **riesgo legal/producto**, no técnico:
- YouTube Premium elimina anuncios para el usuario *final*, no da licencia de uso público/comercial
  en locales.
- Para producción real se debe evaluar un proveedor de licencias musicales (Soundtrack Your Brand,
  Mood Media, etc.) y mantener YouTube como fuente del catálogo/video.
- Impacto técnico: abstraer el reproductor tras una interfaz `MediaProvider` (YouTube, Vimeo, audio
  con licencia) para no quedar atrapados en un solo proveedor.

### 2.5 El contador "estrés positivo" es estimación, no reloj exacto
El tiempo de espera se calcula sumando la duración de las canciones delante en la cola. Se debe
almacenar el `estimated_wait_seconds` calculado **y recalcularlo en cada cambio de cola** (no
recalcularlo en el cliente). La fuente de verdad es el backend; el cliente solo recibe el número por
WebSocket.

---

## 3. Arquitectura: Backend y Frontend Separados (vía CORS)

**Decisión confirmada:** backend y frontend viven como aplicaciones independientes y se comunican
por red (CORS para HTTP, WebSocket URL para tiempo real). Django **no** sirve los frontends.

- **`backend/`**: Django 5 expone únicamente API REST (`/api/v1/`) + WebSockets (Channels/Daphne).
- **`frontend/dashboard`**, **`frontend/client`**, **`frontend/tv`**, **`landing`**: builds Vite
  independientes, servidos por separado (Vercel/Cloudflare Pages/Railway static), que consumen la
  API por `VITE_API_URL` y el socket por `VITE_WS_URL`.
- **CORS**: `django-cors-headers` en el backend con allowlist explícita de orígenes por entorno
  (`CORS_ALLOWED_ORIGINS` en producción; `CORS_ALLOW_ALL_ORIGINS = DEBUG` en desarrollo).
- **Autenticación entre dominios**: el dashboard/TV usan JWT (`Authorization: Bearer`). El cliente
  móvil usa token de sesión firmado derivado del QR (no CORS-sensitive en el socket).

### 3.1 Matiz multi-tenant en frontends separados
`django-tenants` resuelve el schema por subdominio (`bar-el-faro.musicflow.com`) en el middleware
HTTP. Con frontends separados hay dos casos:
- **Dashboard y TV** se sirven bajo el subdominio del tenant → el middleware resuelve el schema
  automáticamente.
- **Cliente móvil (PWA)** es una app genérica (sin subdominio del tenant): el tenant se resuelve por
  el token firmado del QR, que codifica `tenant_slug` + `table_id`.
- **WebSockets NO pasan por el middleware de subdominio de HTTP**: el tenant se resuelve dentro del
  handshake del socket (JWT claim o token firmado del QR), nunca por el host del socket.

---

## 4. Estructura del Repositorio (Monorepo)

```
musicflow/
├── backend/                     # Django 5 + django-tenants (solo API + WS)
│   ├── manage.py
│   ├── config/                  # settings: base.py, development.py, production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py              # Channels + protocol router
│   │   └── celery.py
│   ├── apps/
│   │   ├── core/                # Tenant, Domain (SHARED_APP), modelos base
│   │   ├── tenants/             # apps de negocio por tenant
│   │   │   ├── music/           # PlaylistItem, PlaylistTemplate, QueueItem, SongRequest
│   │   │   ├── tables/          # Table, QR
│   │   │   ├── marketing/       # Coupon, DisplayMessage
│   │   │   └── analytics/       # SalesAnalytics
│   │   ├── payments/            # Wompi: tokenización, suscripciones, webhooks
│   │   └── users/               # auth (allauth + JWT), perfiles
│   ├── static/
│   ├── media/
│   ├── templates/
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   └── docker-compose.yml       # postgres, redis, backend (dev)
│
├── frontend/
│   ├── dashboard/               # React 18 + Vite (dueño)
│   │   └── src/
│   │       ├── components/ui/       # shadcn/ui
│   │       ├── components/dashboard/# QueueList, RequestManager, TableManager,
│   │       │                        #   CouponManager, MessageManager, StatsWidget
│   │       ├── components/layout/   # Sidebar, Header, GlassCard
│   │       ├── components/common/   # CountdownTimer, QRGenerator
│   │       ├── pages/               # Dashboard, Queue, Tables, Playlist, Marketing, Settings, Login
│   │       ├── hooks/               # useWebSocket, useQueue, useAuth
│   │       ├── lib/                 # api.ts, utils.ts
│   │       └── styles/
│   ├── client/                  # React 18 + Vite (PWA móvil)
│   │   └── src/
│   │       ├── components/      # CurrentSong, QueueList, SongSearch, Countdown, Coupons
│   │       └── pages/TableView.tsx
│   └── tv/                      # React 18 + Vite (TV kiosco)
│       └── src/
│           ├── components/      # YouTubePlayer, MessageOverlay, NextSongs
│           └── pages/TVScreen.tsx
│
├── extension/                   # Chrome extension (agregar videos desde YouTube)
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── content.js
│
├── landing/                     # Landing page (se puede unir a dashboard o separado)
├── docs/
│   └── PLAN-TECNICO.md
├── .github/workflows/           # CI/CD → Railway
└── README.md
```

**Decisión:** un monorepo único con `backend/`, `frontend/{dashboard,client,tv}`, `extension/` y
`landing/`. Facilita CI/CD y mantiene una sola fuente de verdad de versiones.

---

## 5. Modelos de Datos

### 4.1 SHARED_APPS (schema público)

**`core.Tenant`** (hereda de `django_tenants.TenantMixin`):
- `name` (CharField)
- `slug` (CharField, unique, index)
- `owner_email` (EmailField)
- `phone` (CharField, blank)
- `address` (TextField, blank)
- `logo_url` (URLField, blank)
- `plan` (CharField: `basic` | `pro` | `premium`, default `basic`)
- `subscription_status` (CharField: `active` | `past_due` | `canceled` | `trialing`, default `trialing`)
- `wompi_subscription_id` (CharField, blank, null)
- `wompi_card_token` (CharField, blank, null) — token, nunca datos de tarjeta
- `next_billing_date` (DateField, null)
- `max_tables` (PositiveIntegerField)
- `requests_per_hour_limit` (PositiveIntegerField, default 2)
- `crossfade_enabled` (BooleanField, default False)
- `autodj_enabled` (BooleanField, default False)
- `created_at` / `updated_at` (auto)

> Campos de configuración (max_tables, límites, crossfade, autodj) viven en `Tenant` porque son
> compartidos entre schema y dashboard. `auto_create_schema = True`.

**`core.Domain`** (hereda de `django_tenants.DomainMixin`):
- `domain` (CharField, unique, ej. `bar-el-faro.musicflow.com`)
- `tenant` (FK a `Tenant`)
- `is_primary` (BooleanField)

### 4.2 TENANT_APPS (schema por tenant)

**`tables.Table`**
- `number` (PositiveIntegerField)
- `qr_hash` (CharField, unique, index) — hash aleatorio, no expone info del tenant
- `qr_image_url` (URLField, blank)
- `is_active` (BooleanField, default True)
- `created_at`
- `Meta`: `unique_together = ('tenant', 'number')` (implícito por schema) — `unique_together = ('number',)`

**`music.PlaylistItem`**
- `youtube_id` (CharField, index)
- `title` (CharField)
- `artist` (CharField, blank)
- `duration_seconds` (PositiveIntegerField)
- `thumbnail_url` (URLField, blank)
- `autodj_approved` (BooleanField, default False)
- `play_count` (PositiveIntegerField, default 0)
- `created_at`
- `Meta`: `unique_together = ('youtube_id',)`

**`music.PlaylistTemplate`**
- `name` (CharField)
- `description` (TextField, blank)
- `items` (M2M → `PlaylistItem`)
- `is_favorite` (BooleanField, default False)
- `created_at`

**`music.QueueItem`**
- `playlist_item` (FK → `PlaylistItem`, on_delete CASCADE)
- `table` (FK → `Table`, null, blank) — null si la pidió el dueño/AutoDJ
- `requested_by` (CharField, blank) — nombre del cliente
- `status` (CharField: `pending` | `approved` | `playing` | `played` | `skipped` | `rejected`)
- `position` (PositiveIntegerField) — orden en cola
- `estimated_wait_seconds` (PositiveIntegerField, default 0)
- `started_at` / `played_at` (DateTimeField, null)
- `created_at`

**`music.SongRequest`**
- `table` (FK → `Table`)
- `playlist_item` (FK → `PlaylistItem`)
- `status` (CharField: `pending` | `approved` | `rejected`)
- `requested_at` (auto_now_add)
- `approved_at` (DateTimeField, null)
- `approved_by` (FK → user, null)

**`marketing.Coupon`**
- `code` (CharField, unique, index)
- `description` (TextField)
- `discount_type` (CharField: `percentage` | `fixed`)
- `value` (DecimalField)
- `valid_from` / `valid_until` (DateTimeField)
- `is_active` (BooleanField, default True)
- `max_uses` (PositiveIntegerField, null)
- `used_count` (PositiveIntegerField, default 0)
- `created_at`

**`marketing.DisplayMessage`**
- `text` (TextField)
- `message_type` (CharField: `promotion` | `birthday` | `anniversary` | `custom` | `happy_hour`)
- `valid_from` / `valid_until` (DateTimeField)
- `is_active` (BooleanField, default True)
- `created_at`

**`analytics.SalesAnalytics`**
- `date` (DateField)
- `total_requests` (PositiveIntegerField)
- `approved_requests` (PositiveIntegerField)
- `songs_played` (PositiveIntegerField)
- `avg_wait_seconds` (PositiveIntegerField)
- `top_songs` (JSONField) — `{youtube_id: count}`
- `estimated_sales` (DecimalField)
- `Meta`: `unique_together = ('date',)`

---

## 6. API REST (DRF)

Base: `/api/v1/`. Autenticación: JWT (`Authorization: Bearer <token>`). Todo bajo el schema del
tenant activo (resuelto por subdominio o header `X-Tenant`).

### 5.1 Auth (`/auth/`)
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/auth/register/` | Registro dueño (crea tenant provisional, estado `trialing`) |
| POST | `/auth/login/` | Devuelve JWT access + refresh |
| POST | `/auth/refresh/` | Refresh token |
| POST | `/auth/google/` | OAuth Google (allauth) |
| POST | `/auth/logout/` | Invalida token |

### 5.2 Mesas (`/tables/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/tables/` | Listar mesas |
| POST | `/tables/` | Crear mesa + generar QR |
| POST | `/tables/bulk/` | Crear N mesas en masa |
| GET/PATCH/DELETE | `/tables/{id}/` | Detalle / editar / eliminar |
| GET | `/tables/{id}/qr.png` | Descargar QR (PNG/SVG) |

### 5.3 Música (`/music/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/music/playlist/` | Catálogo de canciones aprobadas (filtro búsqueda) |
| POST | `/music/playlist/` | Agregar canción desde YouTube (por URL/ID) |
| DELETE | `/music/playlist/{id}/` | Eliminar canción |
| GET/POST | `/music/templates/` | Listar/crear playlist favorita |
| POST | `/music/templates/{id}/apply/` | Aplicar template (reemplaza catálogo) |
| GET | `/music/queue/` | Cola actual |
| PATCH | `/music/queue/{id}/` | Reordenar / aprobar / saltar (acciones) |

### 5.4 Peticiones (`/requests/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/requests/` | Listar peticiones (filtro por estado) |
| POST | `/requests/` | Cliente pide canción (valida límite/hora/mesa) |
| POST | `/requests/{id}/approve/` | Aprobar → crea QueueItem |
| POST | `/requests/{id}/reject/` | Rechazar (opcional mensaje al cliente) |

### 5.5 Marketing (`/marketing/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `/marketing/coupons/` | Listar/crear cupones |
| GET/PATCH/DELETE | `/marketing/coupons/{id}/` | Detalle/editar/eliminar |
| GET/POST | `/marketing/messages/` | Listar/crear mensajes de pantalla |
| GET/PATCH/DELETE | `/marketing/messages/{id}/` | Detalle/editar/eliminar |

### 5.6 Analytics (`/analytics/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/analytics/summary/` | Resumen (totales, top canciones, ventas) |
| GET | `/analytics/requests-by-day/` | Serie temporal peticiones/día |
| GET | `/analytics/top-songs/` | Canciones más pedidas |

### 5.7 Config (`/settings/`)
| Método | Endpoint | Descripción |
|---|---|---|
| GET/PATCH | `/settings/tenant/` | Editar datos del bar y config (AutoDJ, límites) |
| GET/PATCH | `/settings/subscription/` | Ver/actualizar plan y método de pago |

### 5.8 Pagos (`/payments/`)
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/payments/checkout/` | Crear sesión de pago Wompi (devuelve redirect/token) |
| POST | `/payments/webhook/` | Webhook de Wompi (firma verificada, público) |
| POST | `/payments/tokenize-card/` | Tokenizar tarjeta (front → Wompi directamente) |
| POST | `/payments/cancel-subscription/` | Cancelar suscripción |

### 5.9 Admin del sistema (superadmin, `public` schema)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/admin/tenants/` | Listar todos los tenants (global) |
| GET | `/admin/stats/` | Ingresos, tenants activos, top canciones global |

---

## 7. Tiempo Real (Django Channels + WebSockets)

### 6.1 Canales
- Grupo por tenant: `tenant_<slug>` (o `tenant_<id>`).
- Cliente móvil se une al grupo de su mesa: `tenant_<slug>_table_<id>` (para el contador individual).
- Dashboard y TV se unen a `tenant_<slug>`.

### 6.2 Eventos (payload JSON)
| Evento | Destino | Payload |
|---|---|---|
| `queue.updated` | dashboard, tv, clientes | lista completa de cola + tiempos estimados |
| `song.playing` | tv, clientes | `{video_id, title, artist, position, table}` |
| `request.created` | dashboard | `{request_id, table, title, artist}` |
| `request.approved` | cliente | `{request_id, queue_position, est_wait}` |
| `request.rejected` | cliente | `{request_id, reason?}` |
| `message.show` | tv | `{message_id, text, type}` |
| `coupon.applied` | dashboard | `{coupon_id, table}` |
| `countdown.update` | cliente (mesa) | `{queue_item_id, new_est_wait}` |

### 6.3 Autenticación del socket
- **Dashboard/TV**: JWT vía query string en el handshake (`?token=...`).
- **Cliente móvil**: token de sesión firmado (`?session=<signed-token>`) generado al escanear el QR.
- Middleware `JWTAuthMiddleware` (Channels) valida antes de aceptar.

### 6.4 Reconexión
Al reconectar, el servidor envía un snapshot completo (`queue.snapshot`) con el estado actual de la
cola y del reproductor para re-sincronizar al cliente.

---

## 8. Integración Wompi (Colombia)

### 7.1 Flujo de registro + pago
1. Dueño se registra (tenant provisional, `subscription_status = trialing`).
2. Selecciona plan → frontend tokeniza la tarjeta con la **clave pública** de Wompi
   (`POST https://production.wompi.co/v1/tokens/cards`).
3. Backend recibe el `card_token`, crea suscripción/cobro con la **clave privada**.
4. Webhook `transaction.updated` (estado `APPROVED`) → backend marca `subscription_status = active`,
   asigna `next_billing_date = +30 días`, envía email de bienvenida.
5. Cobro mensual recurrente: Celery beat dispara `charge_subscription` el día de facturación.

### 7.2 Eventos de webhook que escuchamos
| Evento | Acción |
|---|---|
| `transaction.updated` → APPROVED | Activar, actualizar `next_billing_date` |
| `transaction.updated` → DECLINED/ERROR | `subscription_status = past_due` + email al dueño |
| `subscription.canceled` | `subscription_status = canceled` + restringir acceso |

### 7.3 Seguridad
- Verificar firma del webhook (Checksum `X-Event-Checksum` con `events_secret_key`).
- Nunca persistir número de tarjeta; solo el `card_token`.
- Idempotencia: deduplicar webhooks por `transaction_id` / `event_id`.

---

## 9. Multi-tenant (django-tenants)

- **Schema público** (`public`): `core.Tenant`, `core.Domain`, tablas de auth de usuarios del sistema
  y `users` (superadmin).
- **Schema por tenant**: todas las apps de negocio (`tables`, `music`, `marketing`, `analytics`).
- **Resolución del tenant**: por subdominio (`bar-el-faro.musicflow.com`) usando
  `django-tenants` middleware; para la PWA cliente (sin subdominio propio) se usa el token firmado
  del QR que codifica el tenant.
- **Migraciones**: `migrate_schemas --shared` y `migrate_schemas` (por tenant). Nuevas migraciones se
  aplican a todos los schemas existentes.
- **Tradeoff a documentar**: schema-per-tenant da aislamiento fuerte pero aumenta complejidad
  operativa (miles de schemas, migraciones masivas). Aceptado por requisito de negocio.

---

## 10. Autenticación

- `django-allauth` para email/contraseña + Google OAuth (login social).
- `djangorestframework-simplejwt` para tokens JWT en la API.
- Contraseñas con hash por defecto de Django (PBKDF2; `bcrypt` opcional).
- Cliente móvil NO usa JWT de usuario: usa token de sesión firmado derivado del hash del QR.
- Roles: `owner` (dueño, por tenant), `superadmin` (tú, global).

---

## 11. Variables de Entorno

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=postgres://...
DATABASE_POOL_SIZE=
REDIS_URL=redis://...
WOMPI_PUBLIC_KEY=
WOMPI_PRIVATE_KEY=
WOMPI_EVENTS_SECRET_KEY=       # verificación de webhooks
WOMPI_INTEGRITY_KEY=
AWS_S3_ACCESS_KEY_ID=
AWS_S3_SECRET_ACCESS_KEY=
AWS_S3_BUCKET_NAME=
SENDGRID_API_KEY=              # o RESEND_API_KEY
VITE_API_URL=
VITE_WS_URL=
VITE_WOMPI_PUBLIC_KEY=
```

---

## 12. Docker Compose (desarrollo)

`backend/docker-compose.yml`:
- `db`: `postgres:15-alpine`
- `redis`: `redis:7-alpine`
- `backend`: imagen Django (build local), comando `runserver` + `daphne` para Channels
- (opcional) `worker`: Celery worker + `beat`: Celery beat

---

## 13. Plan de Implementación por Fases (orden concreto)

### Fase 1 — Fundación (Semana 1-2)
1. `backend/` Django 5 + `django-tenants` + PostgreSQL, settings `base/dev/prod`.
2. Modelos core: `Tenant`, `Domain` (shared), `Table`, `PlaylistItem`, `QueueItem`, `SongRequest`.
3. Auth: registro, login, Google OAuth (allauth) + JWT.
4. `frontend/dashboard` scaffold: Vite + React 18 + Tailwind + shadcn/ui + Zustand.
5. `docker-compose.yml` de desarrollo.

### Fase 2 — Flujo principal (Semana 3-4)
1. Dashboard básico: gestión de mesas + generación QR (qrcode.react).
2. Vista cliente móvil: lista de canciones + petición (límite 2/hora/mesa).
3. Vista TV: iframe YouTube embebido.
4. CRUD REST completo (tables, music, requests).
5. Cola simple sin WebSockets (polling temporal aceptable).

### Fase 3 — Tiempo real + pagos (Semana 5-6)
1. Django Channels: WebSockets + eventos de cola/contador.
2. Reconexión con snapshot.
3. Wompi: tokenización, cobro, webhooks, estados de suscripción.
4. Restricción de acceso por estado de suscripción.

### Fase 4 — Marketing y analíticas (Semana 7-8)
1. Cupones y descuentos.
2. Mensajes en pantalla (DisplayMessage).
3. Playlists favoritas (PlaylistTemplate + apply).
4. Dashboard de estadísticas (Recharts).
5. Contador regresivo avanzado.

### Fase 5 — UI/UX y optimización (Semana 9-10)
1. Liquid Glass + Neumorfismo en los tres frontends.
2. Micro-interacciones (ripple, glow, partículas canvas, parallax).
3. Lazy loading, caching, pruebas de carga multi-tenant.

### Fase 6 — Extensión Chrome (Semana 11-12)
1. `manifest.json` (MV3), popup, content script.
2. "Agregar a playlist" desde YouTube.
3. Publicación en Chrome Web Store + testing E2E.

### Fase 7 — Lanzamiento (Semana 13-14)
1. Dominio principal + subdominios dinámicos.
2. Deploy Railway + GitHub Actions CI/CD.
3. Sentry + Logtail + health checks.
4. Landing page con checkout Wompi integrado.

---

## 14. Riesgos y Consideraciones

1. **Licencias musicales**: YouTube como fuente tiene riesgo legal en locales comerciales. Abstraer
   el reproductor con `MediaProvider` y evaluar proveedores de licencia para producción.
2. **Complejidad schema-per-tenant**: miles de schemas requieren estrategia de migraciones masivas y
   monitoreo de tamaño. Aceptado por requisito.
3. **Wompi cambia su API**: abstraer en `payments/services.py` para aislar el resto del sistema.
4. **Estimación del contador**: es una estimación basada en duraciones; documentar que el tiempo real
   puede variar por pausas/saltos.
5. **WebSocket a escala**: Redis Channel Layer obligatorio (no in-memory) desde el día 1 para
   soportar múltiples instancias.

---

## 15. Siguientes Pasos Inmediatos

1. Validar este plan (especialmente §2 correcciones).
2. Inicializar git en `~/projects/musicflow`.
3. Fase 1, paso 1: scaffold `backend/` con Django + django-tenants.
4. Fase 1, paso 4: scaffold `frontend/dashboard`.
