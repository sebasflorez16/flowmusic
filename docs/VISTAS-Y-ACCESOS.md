# MusicFlow — Vistas y Accesos (Guía interna)

> Documento para el dueño del negocio. Explica qué es cada parte del sistema,
> cómo acceder en local y las credenciales de prueba.

---

## Resumen de vistas (desarrollo local)

| Vista | URL | Qué es | Quién la usa |
|---|---|---|---|
| **Backend (API)** | `http://localhost:8000/` | API REST + base de datos | Todo (por debajo) |
| **Landing page** | `http://localhost:5177/` | Página de venta (clientes nuevos) | Público |
| **Dashboard dueño** | `http://localhost:5173/` | Panel del dueño de cada bar | Dueño del bar |
| **Vista cliente (móvil)** | `http://localhost:5174/` (celular: `http://192.168.18.13:5174/`) | Lo que ve el cliente al escanear el QR | Cliente del bar |
| **Vista TV** | `http://localhost:5175/tv/bar-el-faro` | Pantalla del televisor (reproduce la cola) | El bar (TV) |
| **Superadmin** | `http://localhost:5176/` | Panel financiero y de gestión (dueños del negocio) | Tú + tu socio |
| **Extensión Chrome** | `chrome://extensions` | Agregar canciones desde YouTube con un clic | Dueño del bar |

---

## Credenciales de prueba

| Rol | Email | Contraseña | Vista |
|---|---|---|---|
| **Superadmin (tú, dueño)** | `juansebastianflorezescobar@gmail.com` | `admin123` | Superadmin `:5176` |
| **Socio** | `socio@musicflow.com` | `socio123` | Superadmin `:5176` |
| **Dueño del bar** | `dueno@barelfaroc.com` | `demo12345` | Dashboard `:5173` |

---

## Qué hace cada vista

### 1. Backend (API) — `:8000`
- La base de todo. Guarda los datos y expone los endpoints.
- No se "ve" en el navegador (devuelve JSON).
- Endpoints principales:
  - `/api/v1/auth/` → login/registro.
  - `/api/v1/tables/`, `/music/`, `/marketing/`, `/analytics/` → datos del bar.
  - `/api/v1/client/` → lo que usa el celular y la TV.
  - `/api/v1/admin/` → lo que usa el superadmin (finanzas y gestión).

### 2. Landing page — `:5177`
- Página pública de venta. Aquí llega un bar nuevo y se registra.
- Se despliega en **Netlify** (build estático de la carpeta `landing/`).

### 3. Dashboard dueño — `:5173`
- Panel del **dueño de un bar** (no del dueño del negocio).
- Secciones: Resumen, Cola, Mesas (QR), Playlist, Marketing, Estadísticas, Configuración.
- Aquí el dueño del bar: aprueba canciones, crea mesas/QR, pone mensajes/cupones, ve sus stats.

### 4. Vista cliente (móvil) — `:5174`
- Lo que ve el **cliente** del bar al escanear el QR de su mesa.
- Muestra: bar, mesa, canción actual, cola, buscador de YouTube y promociones.
- En el **celular** se usa la IP local (`192.168.18.13:5174`), no `localhost`.

### 5. Vista TV — `:5175`
- La pantalla del **televisor** del bar (modo kiosco, pantalla completa).
- Reproduce la cola una por una en YouTube, muestra las próximas y los mensajes.
- Cuando la cola se vacía, el AutoDJ pone música del género del bar.

### 6. Superadmin — `:5176`
- Panel de los **dueños del negocio** (tú y tu socio).
- Secciones: Resumen financiero, Bares, Por cobrar, Cobros (efectivo), Gastos, Socios.
- Aquí se controla el dinero real: lo que entra y lo que sale.
- Crear socios requiere tu contraseña de verificación.

### 7. Extensión Chrome
- Se carga en `chrome://extensions` → "Cargar descomprimida" → carpeta `extension/`.
- En un video de YouTube, aparece el botón "＋ Agregar a MusicFlow" para mandarlo a la playlist.

---

## Cómo levantar los servidores (desarrollo)

```bash
# Backend
cd ~/projects/musicflow/backend
./.venv/bin/python manage.py runserver

# Dashboard dueño
cd ~/projects/musicflow/frontend/dashboard && npm run dev

# Vista cliente (móvil)
cd ~/projects/musicflow/frontend/client && npm run dev

# Vista TV
cd ~/projects/musicflow/frontend/tv && npm run dev

# Superadmin
cd ~/projects/musicflow/frontend/superadmin && npm run dev

# Landing
cd ~/projects/musicflow/landing && npm run dev
```

---

## El flujo completo (para entender el negocio)

1. Un bar nuevo llega por la **landing** (`:5177`) y se registra (elige plan y género).
2. Tú/socio **activas el plan** desde el superadmin (`:5176`) y cobras (efectivo o tarjeta).
3. El dueño del bar entra al **dashboard** (`:5173`), crea mesas con QR y configura su música.
4. El dueño imprime los QR y los pega en las mesas.
5. El cliente escanea el QR → abre la **vista móvil** (`:5174`) → pide canciones.
6. El dueño aprueba las canciones en el dashboard → entran a la cola.
7. La **TV** (`:5175`) reproduce la cola una por una; si se vacía, el AutoDJ sigue con el género del bar.
8. El **superadmin** (`:5176`) ve todo el dinero real (pagos, gastos, utilidad) y a quién cobrar.
