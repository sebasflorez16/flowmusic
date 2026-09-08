# Extensión de Chrome — MusicFlow

Permite al dueño agregar videos de YouTube a su playlist con un clic.

## Cómo instalarla (desarrollo)

1. Abre Chrome y ve a `chrome://extensions`.
2. Activa el **"Modo de desarrollador"** (interruptor arriba a la derecha).
3. Haz clic en **"Cargar descomprimida"** (Load unpacked).
4. Selecciona esta carpeta: `musicflow/extension/`.

La extensión queda cargada. Ahora:

1. Abre cualquier video en `https://www.youtube.com/watch?v=...`.
2. Verás un botón flotante **"＋ Agregar a MusicFlow"** abajo a la derecha.
3. Al hacer clic, guarda el video; el popup muestra el video detectado.

## Estado

- `content.js` detecta el video (ID, título, miniatura) e inyecta el botón.
- `popup.js` muestra el video y tiene el placeholder para enviarlo al backend.

Pendiente: conectar el botón al endpoint real de música (`POST /api/v1/music/playlist/`)
cuando se implemente la API de música (Fase 2).

## Estructura

```
extension/
├── manifest.json   # MV3: permisos y content script en youtube.com/watch
├── content.js      # Detecta el video e inyecta el botón
├── popup.html      # UI del popup
└── popup.js        # Lógica del popup
```
