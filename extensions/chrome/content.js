// SellIA Content Script · runs on supported stores/sites.
// Injects floating overlay + observes DOM for sales-relevant events.

(function () {
  if (window.__selliaInjected) return
  window.__selliaInjected = true

  console.log('[SellIA] content script loaded', location.href)

  // Detect platform
  const platform = detectPlatform()
  if (!platform) return

  // Inject overlay
  injectOverlay(platform)

  // Setup observers per platform
  if (platform === 'whatsapp') observeWhatsApp()
  else if (platform === 'amazon') observeAmazon()
  else if (platform === 'mercadolibre') observeMercadoLibre()
  else if (platform === 'shopify') observeShopify()
  else if (platform === 'linkedin') observeLinkedIn()
  else if (platform === 'instagram') observeInstagram()
  else if (platform === 'etsy') observeEtsy()

  // ─── Platform detection ─────────────────────────────────────────────────────

  function detectPlatform() {
    const h = location.hostname
    if (h.includes('web.whatsapp.com')) return 'whatsapp'
    if (h.includes('sellercentral.amazon')) return 'amazon-seller'
    if (h.includes('amazon.')) return 'amazon'
    if (h.includes('mercadolibre.')) return 'mercadolibre'
    if (h.includes('shopify.com')) return 'shopify'
    if (h.includes('etsy.com')) return 'etsy'
    if (h.includes('instagram.com')) return 'instagram'
    if (h.includes('linkedin.com')) return 'linkedin'
    return null
  }

  // ─── Floating overlay ───────────────────────────────────────────────────────

  function injectOverlay(platform) {
    const panel = document.createElement('div')
    panel.id = 'sellia-overlay'
    panel.innerHTML = `
      <div class="sellia-handle">
        <span class="sellia-dot"></span>
        <span class="sellia-label">SellIA</span>
        <span class="sellia-platform">${platform}</span>
      </div>
      <div class="sellia-actions">
        <button data-action="capture" title="Capturar página">📸</button>
        <button data-action="analyze" title="Analizar competencia">🔍</button>
        <button data-action="suggest" title="Sugerencias IA">✨</button>
        <button data-action="sidepanel" title="Abrir panel">📋</button>
      </div>
    `
    document.documentElement.appendChild(panel)

    panel.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-action]')
      if (!btn) return
      const action = btn.dataset.action
      handleAction(action, platform)
    })
  }

  // ─── Action handlers ────────────────────────────────────────────────────────

  function handleAction(action, platform) {
    switch (action) {
      case 'capture':
        captureCurrentPage(platform)
        break
      case 'analyze':
        analyzeCompetitor(platform)
        break
      case 'suggest':
        chrome.runtime.sendMessage({ type: 'open_sidepanel' })
        break
      case 'sidepanel':
        chrome.runtime.sendMessage({ type: 'open_sidepanel' })
        break
    }
  }

  function captureCurrentPage(platform) {
    const data = {
      platform,
      url: location.href,
      title: document.title,
      text: document.body.innerText.slice(0, 8000),
      timestamp: Date.now(),
    }

    // Platform-specific structured extraction
    if (platform === 'amazon' || platform === 'amazon-seller') {
      data.product = extractAmazonProduct()
    } else if (platform === 'mercadolibre') {
      data.product = extractMLProduct()
    } else if (platform === 'shopify') {
      data.product = extractShopifyProduct()
    }

    chrome.runtime.sendMessage({ type: 'capture', data })
    flash('Capturado ✓')
  }

  function analyzeCompetitor(platform) {
    flash('Analizando competencia…')
    captureCurrentPage(platform)
  }

  // ─── Platform-specific extractors ───────────────────────────────────────────

  function extractAmazonProduct() {
    return {
      title: document.querySelector('#productTitle')?.innerText?.trim(),
      price: document.querySelector('.a-price .a-offscreen')?.innerText,
      rating: document.querySelector('[data-hook="average-star-rating"]')?.innerText,
      reviews: document.querySelector('[data-hook="total-review-count"]')?.innerText,
      bullets: Array.from(document.querySelectorAll('#feature-bullets li span')).map(el => el.innerText.trim()),
      image: document.querySelector('#landingImage')?.src,
    }
  }

  function extractMLProduct() {
    return {
      title: document.querySelector('.ui-pdp-title')?.innerText,
      price: document.querySelector('.andes-money-amount__fraction')?.innerText,
      sold: document.querySelector('.ui-pdp-subtitle')?.innerText,
      seller: document.querySelector('.ui-pdp-seller__link-trigger')?.innerText,
    }
  }

  function extractShopifyProduct() {
    return {
      title: document.querySelector('h1.product__title, [class*="product-title"]')?.innerText,
      price: document.querySelector('[class*="price"]')?.innerText,
      desc: document.querySelector('[class*="description"]')?.innerText?.slice(0, 1000),
    }
  }

  // ─── Observers (DOM mutations · sales signals) ──────────────────────────────

  function observeWhatsApp() {
    // Detect new incoming messages
    const targetSelector = '[data-testid="conversation-panel-messages"]'
    const observer = new MutationObserver(() => {
      // Sync conversation state to brain (rate-limited)
    })

    const tryAttach = () => {
      const target = document.querySelector(targetSelector)
      if (target) observer.observe(target, { childList: true, subtree: true })
      else setTimeout(tryAttach, 2000)
    }
    tryAttach()
  }

  function observeAmazon() { /* TBD: detect "Add to cart" form submit */ }
  function observeMercadoLibre() { /* TBD: detect new questions on listing */ }
  function observeShopify() { /* TBD: detect new orders in admin */ }
  function observeLinkedIn() { /* TBD: detect new connection requests */ }
  function observeInstagram() { /* TBD: detect new DMs */ }
  function observeEtsy() { /* TBD */ }

  // ─── UX helpers ─────────────────────────────────────────────────────────────

  function flash(msg) {
    const toast = document.createElement('div')
    toast.className = 'sellia-toast'
    toast.textContent = msg
    document.documentElement.appendChild(toast)
    setTimeout(() => toast.remove(), 2400)
  }
})()
