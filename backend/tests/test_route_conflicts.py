"""Two registered routes must never share a method + path.

Starlette answers a request with the FIRST route that matches, in registration
order, so a second handler on the same method + path is dead code that only looks
live. That is how the signup-time 2FA endpoints (user_id + secret taken from the
request body, no session) sat behind the authenticated /auth/2fa/* handlers: the
signup page called the dead ones, got 422, and nobody could finish enrolling.

Path parameter NAMES are ignored (`/x/{id}` and `/x/{name}` collide); converters
are kept (`{id:int}` vs `{id}`). HEAD and OPTIONS are ignored.
"""

import re
from collections import defaultdict

from app.main import app

_PARAM = re.compile(r"\{[^}:]*(:[^}]*)?\}")

# Conflicts that already existed when this test was added. Do not add to this list:
# fix the new conflict instead (delete the dead handler, or give it its own path).
# Value = what to know before cleaning it up; the first handler is the one answering.
KNOWN_CONFLICTS: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/analytics/dashboard/{}"):
        "advanced_automation.get_seller_dashboard answers; enterprise_analytics."
        "get_performance_dashboard is shadowed",
    ("GET", "/api/v1/platforms/status"):
        "platforms_integration.platforms_status answers; platforms.get_platforms_status "
        "is shadowed",
    ("POST", "/api/v1/sequences/cold-email"):
        "sellbot.generate_cold_email_sequence answers; email_sequences."
        "create_cold_email_sequence is shadowed",
    ("POST", "/api/v1/webhooks/whatsapp"):
        "sellbot.whatsapp_webhook answers; whatsapp_webhook.whatsapp_receive is shadowed",
}


def _route_table() -> dict[tuple[str, str], list[str]]:
    """(method, normalised path) -> handlers, in registration (= matching) order."""
    table: dict[tuple[str, str], list[str]] = defaultdict(list)
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        if not methods or path is None or endpoint is None:
            continue  # mounts, websockets
        normalised = _PARAM.sub(lambda m: "{" + (m.group(1) or "") + "}", path)
        for method in sorted(methods - {"HEAD", "OPTIONS"}):
            table[(method, normalised)].append(f"{endpoint.__module__}.{endpoint.__name__}")
    return table


def test_no_two_routes_share_method_and_path() -> None:
    conflicts = {
        key: handlers
        for key, handlers in _route_table().items()
        if len(handlers) > 1 and key not in KNOWN_CONFLICTS
    }

    assert not conflicts, "\n".join(
        [
            "Routes registered more than once (the first handler answers, the rest never run):",
            *(
                f"  {method} {path}: {' > '.join(handlers)}"
                for (method, path), handlers in sorted(conflicts.items())
            ),
        ]
    )


def test_two_factor_enrolment_is_a_single_authenticated_flow() -> None:
    """/auth/2fa/{setup,verify,disable} live in auth.py only; the signup-time copy is gone."""
    table = _route_table()

    for action in ("setup", "verify", "disable"):
        handlers = table.get(("POST", f"/api/v1/auth/2fa/{action}"), [])
        assert len(handlers) == 1, f"POST /api/v1/auth/2fa/{action} served by {handlers}"
        assert handlers[0].startswith("app.api.v1.auth."), handlers

    # The retired unauthenticated enrolment took a user_id from the client.
    assert ("POST", "/api/v1/auth/2fa/enable") not in table
