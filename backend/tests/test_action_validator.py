"""Tests para ActionValidator — cobertura de las acciones DOM-precisas.

Antes estas 5 acciones (click_selector, click_text, fill, wait_for_selector,
press_key) caían a `validator = None` → pasaban sin validar. Estos tests fijan
la validación de selector/texto/valor/tecla.
"""

from app.domains.computer_use.services.action_validator import ActionValidator


def _v():
    return ActionValidator()


# ── click_selector ──────────────────────────────────────────────────────
def test_click_selector_valid():
    ok, err = _v().validate_action("click_selector", {"selector": "button[type=submit]"})
    assert ok is True and err is None


def test_click_selector_empty_rejected():
    ok, err = _v().validate_action("click_selector", {"selector": "   "})
    assert ok is False
    assert "vac" in err.lower()


def test_click_selector_too_long_rejected():
    ok, err = _v().validate_action("click_selector", {"selector": "a" * 3000})
    assert ok is False
    assert "largo" in err.lower()


# ── click_text ──────────────────────────────────────────────────────────
def test_click_text_valid():
    ok, err = _v().validate_action("click_text", {"text": "Aceptar", "exact": False})
    assert ok is True and err is None


def test_click_text_empty_rejected():
    ok, err = _v().validate_action("click_text", {"text": ""})
    assert ok is False


# ── fill ─────────────────────────────────────────────────────────────────
def test_fill_valid():
    ok, err = _v().validate_action(
        "fill", {"selector": "input[name=email]", "value": "user@acme.com"}
    )
    assert ok is True and err is None


def test_fill_missing_selector_rejected():
    ok, err = _v().validate_action("fill", {"value": "x"})
    assert ok is False


def test_fill_missing_value_rejected():
    ok, err = _v().validate_action("fill", {"selector": "input"})
    assert ok is False


def test_fill_empty_value_allowed():
    # Vaciar un campo es legítimo.
    ok, err = _v().validate_action("fill", {"selector": "input", "value": ""})
    assert ok is True and err is None


def test_fill_sensitive_value_warns_not_blocks():
    # Tarjeta de crédito → loguea warning pero no bloquea (puede ser legítimo).
    ok, err = _v().validate_action(
        "fill", {"selector": "input", "value": "4111 1111 1111 1111"}
    )
    assert ok is True and err is None


# ── wait_for_selector ────────────────────────────────────────────────────
def test_wait_for_selector_valid():
    ok, err = _v().validate_action(
        "wait_for_selector", {"selector": ".results", "timeout_ms": 8000}
    )
    assert ok is True and err is None


def test_wait_for_selector_no_timeout_ok():
    ok, err = _v().validate_action("wait_for_selector", {"selector": ".x"})
    assert ok is True and err is None


def test_wait_for_selector_excessive_timeout_rejected():
    ok, err = _v().validate_action(
        "wait_for_selector", {"selector": ".x", "timeout_ms": 999999}
    )
    assert ok is False


def test_wait_for_selector_empty_rejected():
    ok, err = _v().validate_action("wait_for_selector", {"selector": ""})
    assert ok is False


# ── press_key ─────────────────────────────────────────────────────────────
def test_press_key_special_valid():
    ok, err = _v().validate_action("press_key", {"key": "Enter"})
    assert ok is True and err is None


def test_press_key_combination_valid():
    ok, err = _v().validate_action("press_key", {"key": "Control+A"})
    assert ok is True and err is None


def test_press_key_single_char_valid():
    ok, err = _v().validate_action("press_key", {"key": "a"})
    assert ok is True and err is None


def test_press_key_empty_rejected():
    ok, err = _v().validate_action("press_key", {"key": ""})
    assert ok is False


def test_press_key_unknown_rejected():
    ok, err = _v().validate_action("press_key", {"key": "NotARealKey"})
    assert ok is False
