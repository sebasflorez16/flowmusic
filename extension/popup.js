/**
 * Popup de la extensión MusicFlow.
 *
 * Flujo:
 * 1. El dueño se conecta con email/contraseña (obtiene un JWT del backend).
 * 2. El content script detecta el video de YouTube y lo guarda en storage.
 * 3. Al pulsar "Agregar", se envía el video al endpoint de música con el JWT.
 */

/** URL base del backend (localhost en desarrollo). */
const API_BASE_URL = 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'musicflow_token'

// Referencias al DOM.
const loginForm = document.getElementById('login-form')
const connectedStatus = document.getElementById('connected-status')
const emailInput = document.getElementById('email')
const passwordInput = document.getElementById('password')
const loginBtn = document.getElementById('login-btn')
const emptyEl = document.getElementById('empty')
const infoEl = document.getElementById('video-info')
const thumbEl = document.getElementById('thumb')
const titleEl = document.getElementById('video-title')
const metaEl = document.getElementById('video-meta')
const addBtn = document.getElementById('add-btn')
const statusEl = document.getElementById('status')

/**
 * Muestra un mensaje de estado con color (ok/error).
 * @param {string} message Texto del mensaje.
 * @param {boolean} isError Si es true, usa color de error.
 */
function setStatus(message, isError = false) {
  statusEl.textContent = message
  statusEl.className = 'status ' + (isError ? 'err' : 'ok')
}

/**
 * Obtiene el token guardado en chrome.storage.
 * @returns {Promise<string|null>} El token o null.
 */
async function getToken() {
  const data = await chrome.storage.local.get(TOKEN_KEY)
  return data[TOKEN_KEY] || null
}

/**
 * Refresca la UI según haya o no sesión activa.
 */
async function renderAuthState() {
  const token = await getToken()
  if (token) {
    loginForm.hidden = true
    connectedStatus.hidden = false
    connectedStatus.textContent = '✓ Conectado a MusicFlow'
    addBtn.disabled = false
  } else {
    loginForm.hidden = false
    connectedStatus.hidden = true
    addBtn.disabled = true
  }
}

/**
 * Inicia sesión contra el backend y guarda el token.
 */
async function login() {
  const email = emailInput.value.trim()
  const password = passwordInput.value

  if (!email || !password) {
    setStatus('Ingresa email y contraseña', true)
    return
  }

  loginBtn.disabled = true
  setStatus('Conectando…')

  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || data.non_field_errors?.[0] || 'Error al conectar')
    }
    await chrome.storage.local.set({ [TOKEN_KEY]: data.access })
    setStatus('Conectado correctamente')
    renderAuthState()
  } catch (err) {
    setStatus(err.message || 'No se pudo conectar', true)
  } finally {
    loginBtn.disabled = false
  }
}

/**
 * Renderiza el video detectado.
 * @param {object} info Información del video (desde chrome.storage).
 */
function renderVideo(info) {
  if (!info) {
    emptyEl.hidden = false
    infoEl.hidden = true
    return
  }
  emptyEl.hidden = true
  infoEl.hidden = false
  thumbEl.src = info.thumbnail_url
  titleEl.textContent = info.title
  metaEl.textContent = `ID: ${info.youtube_id}`
}

/**
 * Envía el video detectado a la playlist del bar.
 */
async function addToPlaylist() {
  const token = await getToken()
  const { currentVideo } = await chrome.storage.local.get('currentVideo')

  if (!token) {
    setStatus('Conéctate primero con tu email', true)
    return
  }
  if (!currentVideo) {
    setStatus('Abre un video de YouTube primero', true)
    return
  }

  addBtn.disabled = true
  setStatus('Agregando…')

  try {
    const response = await fetch(`${API_BASE_URL}/music/playlist/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        youtube_id: currentVideo.youtube_id,
        title: currentVideo.title,
        thumbnail_url: currentVideo.thumbnail_url,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || data.non_field_errors?.[0] || 'Error al agregar')
    }
    setStatus(`✓ "${data.title}" agregada a la playlist`)
  } catch (err) {
    setStatus(err.message || 'No se pudo agregar', true)
  } finally {
    addBtn.disabled = false
  }
}

// Inicialización del popup.
renderAuthState()
chrome.storage.local.get('currentVideo', ({ currentVideo }) => renderVideo(currentVideo))

loginBtn.addEventListener('click', login)
addBtn.addEventListener('click', addToPlaylist)
