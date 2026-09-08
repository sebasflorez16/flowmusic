/**
 * Popup de la extensión MusicFlow.
 *
 * Lee la información del video detectado por el content script (desde
 * chrome.storage) y muestra un botón para agregarlo a la playlist. La llamada
 * real al backend se conectará cuando exista el endpoint de música.
 */

/** Referencias a los elementos del DOM. */
const emptyEl = document.getElementById('empty')
const infoEl = document.getElementById('video-info')
const thumbEl = document.getElementById('thumb')
const titleEl = document.getElementById('video-title')
const metaEl = document.getElementById('video-meta')
const addBtn = document.getElementById('add-btn')
const statusEl = document.getElementById('status')

/** URL base del backend (configurable por el dueño). */
const API_BASE_URL = 'http://localhost:8000/api/v1'

/**
 * Renderiza el video detectado en el popup.
 * @param {object} info Información del video (desde chrome.storage).
 */
function renderVideo(info) {
  if (!info) {
    emptyEl.hidden = false
    infoEl.hidden = true
    addBtn.disabled = true
    return
  }

  emptyEl.hidden = true
  infoEl.hidden = false
  thumbEl.src = info.thumbnail_url
  titleEl.textContent = info.title
  metaEl.textContent = `ID: ${info.youtube_id}`
  addBtn.disabled = false
}

/**
 * Envía el video al backend. Por ahora es un placeholder que muestra la URL que
 * se usaría; se conecta al endpoint real de música cuando esté disponible.
 */
async function addToPlaylist() {
  const { currentVideo } = await chrome.storage.local.get('currentVideo')
  if (!currentVideo) return

  statusEl.textContent = 'Enviando…'
  try {
    const response = await fetch(`${API_BASE_URL}/music/playlist/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        youtube_id: currentVideo.youtube_id,
        title: currentVideo.title,
      }),
    })
    if (response.ok) {
      statusEl.textContent = '✓ Agregada a tu playlist'
    } else {
      statusEl.textContent = 'Endpoint no disponible aún'
    }
  } catch {
    statusEl.textContent = 'No se pudo conectar al backend'
  }
}

// Al abrir el popup, muestra el último video detectado.
chrome.storage.local.get('currentVideo', ({ currentVideo }) => {
  renderVideo(currentVideo)
})

addBtn.addEventListener('click', addToPlaylist)
