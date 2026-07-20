# SellIA Chrome Extension v1

MV3 extension · brazo del cerebro SellIA en el browser.

## Capabilities

- **Floating overlay** on supported stores (Amazon, ML, Shopify, WhatsApp, IG, LinkedIn, Etsy)
- **1-click capture** of any listing/conversation to brain
- **Cross-tab orchestration** via service worker + WebSocket
- **Side panel** with full SellIA dashboard embedded
- **Keyboard shortcut** Ctrl+Shift+K to capture page
- **Desktop notifications** triggered by brain events
- **DOM manipulation** for CUA-style actions (fill, click, capture)

## Architecture

```
manifest.json         · MV3 declaration
background.js         · service worker (WebSocket, alarms, command handler)
content.js            · injects overlay, observes DOM per platform
overlay.css           · floating UI styles (scoped, max z-index)
popup.html + popup.js · toolbar popup (auth, quick actions)
sidepanel.html        · full dashboard embed
```

## Install (dev)

1. Open `chrome://extensions`
2. Enable "Developer mode"
3. "Load unpacked" → select `extensions/chrome` folder
4. Pin SellIA to toolbar

## Build for Web Store

```bash
cd extensions/chrome
zip -r sellia-v0.1.0.zip . -x "*.git*" -x "README.md" -x "icons/source/*"
# Upload to https://chrome.google.com/webstore/devconsole
```

## Permissions justification (for Web Store review)

- `activeTab` · capture current page on user-click
- `storage` · persist auth token + offline queue
- `scripting` · inject overlay + extract structured data
- `cookies` · session continuation across SellIA domains
- `alarms` · periodic sync tick (every 5min)
- `notifications` · brain → user alerts
- `sidePanel` · embed dashboard

## Privacy

- Token stored in `chrome.storage.local` (not synced)
- Data sent only to `api.sellia.app` over WSS/HTTPS
- No tracking, no analytics SDKs, no third-party scripts

## Variants

- Edge: same code, manifest works as-is on Chromium-based browsers
- Firefox: change `manifest_version` rules + replace `service_worker` with `scripts`
- Safari: wrap in Xcode project · uses WKWebView · separate App Store submission
