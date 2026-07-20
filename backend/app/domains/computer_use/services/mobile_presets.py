"""Computer Use — Mobile Emulation Presets

Perfiles predefinidos de dispositivos móviles populares para emulación
en sesiones de Computer Use.
"""

from typing import Dict, Any

MOBILE_PRESETS: Dict[str, Dict[str, Any]] = {
    "iphone_14": {
        "name": "iPhone 14",
        "viewport_width": 390,
        "viewport_height": 844,
        "device_scale_factor": 3,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "touch": True,
        "locale": "es-ES",
    },
    "iphone_14_pro_max": {
        "name": "iPhone 14 Pro Max",
        "viewport_width": 430,
        "viewport_height": 932,
        "device_scale_factor": 3,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "touch": True,
        "locale": "es-ES",
    },
    "ipad_pro": {
        "name": "iPad Pro 12.9",
        "viewport_width": 1024,
        "viewport_height": 1366,
        "device_scale_factor": 2,
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "touch": True,
        "locale": "es-ES",
    },
    "pixel_7": {
        "name": "Google Pixel 7",
        "viewport_width": 412,
        "viewport_height": 915,
        "device_scale_factor": 2.625,
        "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "touch": True,
        "locale": "es-ES",
    },
    "samsung_s23": {
        "name": "Samsung Galaxy S23",
        "viewport_width": 384,
        "viewport_height": 854,
        "device_scale_factor": 3,
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "touch": True,
        "locale": "es-ES",
    },
    "desktop_hd": {
        "name": "Desktop HD",
        "viewport_width": 1920,
        "viewport_height": 1080,
        "device_scale_factor": 1,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "touch": False,
        "locale": "es-ES",
    },
    "desktop_4k": {
        "name": "Desktop 4K",
        "viewport_width": 3840,
        "viewport_height": 2160,
        "device_scale_factor": 2,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "touch": False,
        "locale": "es-ES",
    },
}


def get_mobile_preset(preset_id: str) -> Dict[str, Any]:
    """Obtiene un preset por ID."""
    preset = MOBILE_PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Preset desconocido: {preset_id}. Disponibles: {list(MOBILE_PRESETS.keys())}")
    return preset


def list_presets() -> Dict[str, str]:
    """Lista todos los presets disponibles."""
    return {k: v["name"] for k, v in MOBILE_PRESETS.items()}
