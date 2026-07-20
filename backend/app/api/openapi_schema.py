"""
OpenAPI/Swagger Schema — Documentación APIs.

Genera Swagger UI automáticamente.
"""

from fastapi.openapi.utils import get_openapi


def get_openapi_schema(app):
    """Define OpenAPI schema para todas APIs."""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SellIA API",
        version="1.0.0",
        description="""
## SellIA — Autonomous AI Sales Agent

Complete automation para vendedores:
- Multi-platform orchestration (Mercado Libre, Amazon, Shopify)
- Payment processing (Stripe)
- Order fulfillment (DHL/FedEx)
- Customer communication (WhatsApp, Email)
- Analytics & Intelligence

### Authentication
Use Bearer token in Authorization header.

### Rate Limits
- 100 requests/minute for standard endpoints
- 1000 requests/minute for webhook endpoints

### Errors
All errors return standard format:
```json
{
  "status": "error",
  "error": "Human readable error message"
}
```
""",
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://sellias.com/logo.png"
    }

    # Documentación de endpoints principales
    openapi_schema["paths"]["/api/v1/payments/checkout"] = {
        "post": {
            "tags": ["Payments"],
            "summary": "Create checkout session",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "product": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "price": {"type": "number"},
                                        "description": {"type": "string"},
                                    },
                                },
                                "buyer": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "name": {"type": "string"},
                                        "phone": {"type": "string"},
                                    },
                                },
                            },
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Checkout session created",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "checkout_url": {"type": "string"},
                                    "session_id": {"type": "string"},
                                },
                            }
                        }
                    },
                }
            },
        }
    }

    openapi_schema["paths"]["/api/v1/analytics/overview"] = {
        "get": {
            "tags": ["Analytics"],
            "summary": "Get analytics overview",
            "parameters": [
                {
                    "name": "seller_id",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "name": "days",
                    "in": "query",
                    "schema": {"type": "integer", "default": 30},
                },
            ],
            "responses": {
                "200": {
                    "description": "Analytics data",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "total_revenue": {"type": "number"},
                                    "total_orders": {"type": "integer"},
                                    "conversion_rate": {"type": "number"},
                                    "customer_acquisition_cost": {"type": "number"},
                                    "lifetime_value": {"type": "number"},
                                },
                            }
                        }
                    },
                }
            },
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Agregar al main app:
# from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
#
# @app.get("/docs", include_in_schema=False)
# async def get_swagger_ui():
#     return get_swagger_ui_html(openapi_url="/openapi.json", title="SellIA API")
#
# @app.get("/redoc", include_in_schema=False)
# async def get_redoc():
#     return get_redoc_html(openapi_url="/openapi.json", title="SellIA API")
#
# app.openapi = lambda: get_openapi_schema(app)
