# MusicFlow

Plataforma SaaS multi-tenant para bares y restaurantes. Convierte la música del local en una
máquina de engagement que vende más bebidas: los clientes piden canciones desde su mesa por QR, un
contador regresivo genera "estrés positivo", y el dueño gestiona todo desde un dashboard con diseño
Liquid Glass + Neumorfismo.

## Arquitectura

Backend y frontend separados, comunicados vía CORS (HTTP) y WebSockets (tiempo real).

| Módulo | Stack | Descripción |
|---|---|---|
| `backend/` | Django 5 + django-tenants + PostgreSQL 15 + DRF + Channels + Celery/Redis | API REST + WebSockets (multi-tenant schema-per-tenant) |
| `frontend/dashboard/` | React 18 + Vite + Tailwind + shadcn/ui + Zustand + Recharts | SPA del dueño |
| `frontend/client/` | React 18 + Vite + Framer Motion (PWA) | Vista móvil del cliente (escaneo QR) |
| `frontend/tv/` | React 18 + Vite | Vista TV en modo kiosco |
| `landing/` | Vite (static) | Landing page con checkout Wompi |
| `extension/` | Chrome MV3 | Agregar videos desde YouTube a la playlist |

Pagos: Wompi (Colombia) — tokenización de tarjetas + suscripciones recurrentes + webhooks.

## Documentación

- `docs/PLAN-TECNICO.md` — decisiones técnicas, modelos, endpoints, eventos WS y plan por fases.

## Estado

Fase 1 (Fundación) — en preparación.
