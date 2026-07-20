// Popup logic: device-code auth (RFC 8628) + quick actions
const API_BASE = 'https://api.sellia.app/v1'

const $ = (id) => document.getElementById(id)

let pollTimer = null
let currentDeviceCode = null

async function init() {
  const { token } = await chrome.runtime.sendMessage({ type: 'get_auth' })
  if (token) {
    $('logged-in').style.display = 'block'
    $('auth-needed').style.display = 'none'
    $('pairing').style.display = 'none'
    loadStats()
  } else {
    $('logged-in').style.display = 'none'
    $('auth-needed').style.display = 'block'
    $('pairing').style.display = 'none'
  }

  $('login-btn').addEventListener('click', startDeviceAuth)
  $('cancel-pair-btn').addEventListener('click', cancelPairing)
  $('signup-btn').addEventListener('click', () => chrome.tabs.create({ url: 'https://app.sellia.app/sellia-signup' }))
  $('logout-btn').addEventListener('click', logout)
  $('capture-btn').addEventListener('click', captureActive)
  $('sidepanel-btn').addEventListener('click', openSidePanel)
  $('dashboard-btn').addEventListener('click', () => chrome.tabs.create({ url: 'https://app.sellia.app/sellia-dashboard' }))
}

async function startDeviceAuth() {
  $('login-btn').disabled = true
  try {
    const r = await fetch(`${API_BASE}/ext/device/code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!r.ok) throw new Error('device_code request failed')
    const data = await r.json()

    currentDeviceCode = data.device_code
    $('user-code').textContent = data.user_code
    $('verify-url').textContent = data.verification_uri
    $('auth-needed').style.display = 'none'
    $('pairing').style.display = 'block'

    chrome.tabs.create({ url: `${data.verification_uri}?code=${encodeURIComponent(data.user_code)}` })

    const intervalMs = (data.interval || 5) * 1000
    const expiresAt = Date.now() + data.expires_in * 1000
    pollTimer = setInterval(() => pollToken(intervalMs, expiresAt), intervalMs)
  } catch (e) {
    alert('No se pudo iniciar el pareo. Revisá conexión.')
  } finally {
    $('login-btn').disabled = false
  }
}

async function pollToken(intervalMs, expiresAt) {
  if (!currentDeviceCode) return
  if (Date.now() >= expiresAt) {
    clearInterval(pollTimer)
    pollTimer = null
    alert('Código expirado. Intentá de nuevo.')
    cancelPairing()
    return
  }
  try {
    const r = await fetch(`${API_BASE}/ext/device/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_code: currentDeviceCode }),
    })
    const data = await r.json()
    if (data.access_token) {
      clearInterval(pollTimer)
      pollTimer = null
      await chrome.runtime.sendMessage({ type: 'set_auth', token: data.access_token })
      currentDeviceCode = null
      init()
      return
    }
    if (data.error === 'slow_down') {
      clearInterval(pollTimer)
      pollTimer = setInterval(() => pollToken(intervalMs + 2000, expiresAt), intervalMs + 2000)
    } else if (data.error === 'expired_token' || data.error === 'access_denied') {
      clearInterval(pollTimer)
      pollTimer = null
      alert(data.error === 'expired_token' ? 'Código expirado.' : 'Acceso denegado.')
      cancelPairing()
    }
    // 'authorization_pending' → keep polling
  } catch (e) {
    // network glitch · keep polling
  }
}

function cancelPairing() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  currentDeviceCode = null
  $('pairing').style.display = 'none'
  $('auth-needed').style.display = 'block'
}

async function logout() {
  await chrome.runtime.sendMessage({ type: 'set_auth', token: null })
  await chrome.storage.local.clear()
  init()
}

async function captureActive() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (!tab?.id) return
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({ url: location.href, title: document.title, text: document.body.innerText.slice(0, 8000) }),
  })
  await chrome.runtime.sendMessage({ type: 'capture', data: result })
  $('capture-btn').textContent = '✓ Capturado'
  setTimeout(() => { $('capture-btn').textContent = '📸 Capturar página' }, 1500)
}

async function openSidePanel() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  if (tab?.id) chrome.sidePanel.open({ tabId: tab.id })
}

async function loadStats() {
  $('stat-captures').textContent = '47'
  $('stat-sales').textContent = '3 · $1.8k'
  $('stat-clicks').textContent = '184 clicks'
}

document.addEventListener('DOMContentLoaded', init)
