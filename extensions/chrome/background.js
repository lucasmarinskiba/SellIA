// SellIA Service Worker · MV3
// Long-lived background process for cross-tab orchestration, alarms, WS.

const API_BASE = 'https://api.sellia.app/v1'
const WS_BASE = 'wss://api.sellia.app/ws'

let socket = null
let authToken = null

// ─── Init on install ──────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  console.log('[SellIA] installed', reason)
  await chrome.alarms.create('sync-tick', { periodInMinutes: 5 })

  if (reason === 'install') {
    await chrome.tabs.create({ url: 'https://sellia.app/welcome' })
  }
})

// ─── Auth ──────────────────────────────────────────────────────────────────────

async function loadAuth() {
  const { token } = await chrome.storage.local.get('token')
  authToken = token || null
  return authToken
}

async function setAuth(token) {
  await chrome.storage.local.set({ token })
  authToken = token
  reconnectWS()
}

// ─── WebSocket to brain ────────────────────────────────────────────────────────

function reconnectWS() {
  if (socket) {
    try { socket.close() } catch (e) {}
    socket = null
  }
  if (!authToken) return

  socket = new WebSocket(`${WS_BASE}?token=${encodeURIComponent(authToken)}`)

  socket.onopen = () => {
    console.log('[SellIA] WS connected')
    chrome.action.setBadgeText({ text: '●' })
    chrome.action.setBadgeBackgroundColor({ color: '#22c55e' })
  }

  socket.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data)
      handleBrainEvent(msg)
    } catch (e) {
      console.warn('[SellIA] bad WS msg', e)
    }
  }

  socket.onclose = () => {
    console.log('[SellIA] WS closed · reconnecting in 5s')
    chrome.action.setBadgeText({ text: '' })
    setTimeout(reconnectWS, 5000)
  }

  socket.onerror = (e) => console.error('[SellIA] WS error', e)
}

function sendToBrain(payload) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload))
  } else {
    // Queue in storage for retry
    chrome.storage.local.get('queue', ({ queue = [] }) => {
      queue.push(payload)
      chrome.storage.local.set({ queue: queue.slice(-100) })
    })
  }
}

// ─── Handle brain events ──────────────────────────────────────────────────────

function handleBrainEvent(msg) {
  switch (msg.type) {
    case 'notification':
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: msg.title || 'SellIA',
        message: msg.body,
        priority: msg.priority || 1,
      })
      break

    case 'execute_action':
      // Brain asks extension to perform something (CUA-style)
      executeAction(msg.action)
      break

    case 'badge':
      chrome.action.setBadgeText({ text: String(msg.count || '') })
      break
  }
}

async function executeAction(action) {
  switch (action.kind) {
    case 'fill_form':
      await chrome.scripting.executeScript({
        target: { tabId: action.tab_id },
        func: (sel, val) => { const el = document.querySelector(sel); if (el) { el.value = val; el.dispatchEvent(new Event('input', { bubbles: true })) } },
        args: [action.selector, action.value],
      })
      break

    case 'click':
      await chrome.scripting.executeScript({
        target: { tabId: action.tab_id },
        func: (sel) => document.querySelector(sel)?.click(),
        args: [action.selector],
      })
      break

    case 'capture_dom':
      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: action.tab_id },
        func: () => document.documentElement.outerHTML,
      })
      sendToBrain({ type: 'dom_captured', tab_id: action.tab_id, html: result })
      break
  }
}

// ─── Alarms (periodic sync) ───────────────────────────────────────────────────

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'sync-tick') {
    await flushQueue()
    await loadAuth()
    if (authToken && (!socket || socket.readyState !== WebSocket.OPEN)) reconnectWS()
  }
})

async function flushQueue() {
  const { queue = [] } = await chrome.storage.local.get('queue')
  if (!queue.length) return
  if (socket?.readyState !== WebSocket.OPEN) return
  for (const item of queue) socket.send(JSON.stringify(item))
  await chrome.storage.local.set({ queue: [] })
}

// ─── Messages from content scripts + popup ────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'capture') {
    sendToBrain({ type: 'page_capture', url: sender.tab?.url, data: msg.data })
    sendResponse({ ok: true })
  } else if (msg.type === 'set_auth') {
    setAuth(msg.token).then(() => sendResponse({ ok: true }))
    return true
  } else if (msg.type === 'get_auth') {
    loadAuth().then((t) => sendResponse({ token: t }))
    return true
  } else if (msg.type === 'open_sidepanel' && sender.tab?.id) {
    chrome.sidePanel.open({ tabId: sender.tab.id })
  }
})

// ─── Keyboard command ─────────────────────────────────────────────────────────

chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'capture-page') {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (!tab?.id) return
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({
        url: location.href,
        title: document.title,
        text: document.body.innerText.slice(0, 5000),
      }),
    }).then((results) => {
      const data = results[0]?.result
      if (data) sendToBrain({ type: 'page_capture', ...data })
    })
  }
})

// Boot
loadAuth().then(() => { if (authToken) reconnectWS() })
