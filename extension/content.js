/**
 * Content script de la extensión MusicFlow.
 *
 * Se ejecuta en páginas de video de YouTube (https://www.youtube.com/watch*).
 * Detecta el video actual (ID + título + miniatura), guarda la información en
 * `chrome.storage` e inyecta un botón flotante "Agregar a MusicFlow".
 */

const BUTTON_ID = 'musicflow-add-button'

/**
 * Extrae el ID del video desde la URL actual.
 * @returns {string|null} El ID del video (ej. "dQw4w9WgXcQ") o null si no hay.
 */
function getVideoId() {
  const params = new URLSearchParams(window.location.search)
  return params.get('v')
}

/**
 * Extrae el título del video desde el <title> de la pestaña.
 * El título de YouTube termina en "- YouTube"; se recorta ese sufijo.
 * @returns {string} Título limpio del video.
 */
function getVideoTitle() {
  return document.title.replace(/ - YouTube$/, '')
}

/**
 * Guarda la info del video en chrome.storage para que el popup la lea.
 */
function persistVideoInfo() {
  const videoId = getVideoId()
  if (!videoId) return

  const info = {
    youtube_id: videoId,
    title: getVideoTitle(),
    url: window.location.href,
    thumbnail_url: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
    captured_at: new Date().toISOString(),
  }

  chrome.storage.local.set({ currentVideo: info })
  return info
}

/**
 * Inyecta un botón flotante sobre la página de YouTube.
 * @param {object} info Información del video detectado.
 */
function injectButton(info) {
  if (document.getElementById(BUTTON_ID)) return

  const button = document.createElement('button')
  button.id = BUTTON_ID
  button.textContent = '＋ Agregar a MusicFlow'
  button.style.cssText = [
    'position: fixed',
    'bottom: 24px',
    'right: 24px',
    'z-index: 99999',
    'padding: 12px 18px',
    'border: none',
    'border-radius: 999px',
    'background: linear-gradient(120deg, #8b5cf6, #ec4899)',
    'color: #fff',
    'font-weight: 600',
    'font-size: 14px',
    'cursor: pointer',
    'box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4)',
  ].join(';')

  button.addEventListener('click', () => {
    // Abre el popup (el usuario confirma desde ahí) y resalta el botón.
    button.textContent = '✓ Guardado'
    button.style.background = '#10b981'
    setTimeout(() => {
      button.textContent = '＋ Agregar a MusicFlow'
      button.style.background = 'linear-gradient(120deg, #8b5cf6, #ec4899)'
    }, 1500)
  })

  document.body.appendChild(button)
}

/**
 * Punto de entrada del content script.
 *
 * YouTube es una SPA: al navegar entre videos sin recargar, se vuelve a
 * ejecutar la detección con un pequeño retardo.
 */
function main() {
  const info = persistVideoInfo()
  if (info && document.body) {
    injectButton(info)
  }
}

// Ejecuta al cargar y de nuevo al detectar cambios de navegación (SPA).
main()
let lastUrl = location.href
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href
    setTimeout(main, 800)
  }
}).observe(document, { subtree: true, childList: true })
