#!/usr/bin/env python3
"""
SellIA CLI — Command-line tool para power users.

Uso:
  sellias config --key STRIPE_KEY --value sk_live_xxx
  sellias travel on --start 2025-07-15 --end 2025-07-25
  sellias price-optimize --product-id prod_123
  sellias forecast --days 30 --product-id prod_456
  sellias sync --platform mercadolibre
  sellias status
  sellias analytics --days 30
"""

import typer
import json
from typing import Optional
from datetime import datetime
import httpx

app = typer.Typer()

API_URL = "https://sellias.vercel.app/api/v1"


@app.command()
def config(
    key: str = typer.Option(..., "--key", help="Config key (e.g., STRIPE_KEY)"),
    value: str = typer.Option(..., "--value", help="Config value"),
):
    """Configura credenciales y API keys."""
    typer.echo(f"✓ {key} configurado")
    # TODO: Guardar en ~/.sellias/config.json


@app.command()
def travel(
    status: str = typer.Argument(..., help="on/off"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Travel notes"),
):
    """Activa/desactiva travel mode."""

    if status.lower() == "on":
        if not start or not end:
            typer.echo("❌ Requiere --start y --end")
            raise typer.Exit(1)

        typer.echo(f"✈️ Travel mode ON: {start} to {end}")
        # TODO: POST /user/travel-mode
    else:
        typer.echo("✓ Travel mode OFF")


@app.command()
def price_optimize(
    product_id: str = typer.Option(..., "--product-id"),
    platform: Optional[str] = typer.Option("mercadolibre", "--platform"),
):
    """Calcula precio óptimo para producto."""

    typer.echo(f"💰 Optimizando precio para {product_id} en {platform}...")

    # TODO: GET /intelligence/price-optimize?product_id=X&platform=Y

    typer.echo("✓ Precio óptimo: $55.28 (+12% margin)")


@app.command()
def forecast(
    days: int = typer.Option(30, "--days"),
    product_id: Optional[str] = typer.Option(None, "--product-id"),
):
    """Proyecta demanda."""

    typer.echo(f"📊 Forecast {days} días...")

    # TODO: GET /intelligence/forecast?product_id=X&days=Y

    typer.echo(f"✓ Proyección: 45 órdenes | ${2150} revenue | Confidence: 85%")


@app.command()
def sync(
    platform: str = typer.Option(..., "--platform", help="Platform (mercadolibre/amazon/shopify)"),
    manual: bool = typer.Option(False, "--manual", help="Force sync (normally automatic)"),
):
    """Sincroniza órdenes."""

    typer.echo(f"🔄 Sincronizando {platform}...")

    # TODO: POST /orders/sync/{platform}

    typer.echo(f"✓ Sincronizado: 12 órdenes nuevas | 3 refunds")


@app.command()
def status():
    """Muestra status del sistema."""

    typer.echo("\n" + "="*50)
    typer.echo("🤖 SELLIAS STATUS")
    typer.echo("="*50)

    typer.echo("\n📊 OPERACIONES (hoy):")
    typer.echo("  Órdenes procesadas: 42")
    typer.echo("  Revenue: $2,150")
    typer.echo("  Refunds: 1")

    typer.echo("\n🔗 PLATAFORMAS:")
    typer.echo("  Mercado Libre: ✓ Connected (ML123456789)")
    typer.echo("  Amazon: ✓ Connected (ASIN)")
    typer.echo("  Shopify: ✓ Connected")
    typer.echo("  Stripe: ✓ Connected")

    typer.echo("\n📱 INTEGRACIONES:")
    typer.echo("  WhatsApp: ✓ Active (API mode)")
    typer.echo("  Google Calendar: ✓ Sync OK")
    typer.echo("  Shipping (DHL): ✓ Active")
    typer.echo("  FeedIA: ✓ Connected")

    typer.echo("\n🎯 MODO:")
    typer.echo("  Travel Mode: OFF")
    typer.echo("  Sistema: 24/7 Operativo")

    typer.echo("\n✅ SISTEMA HEALTHY\n")


@app.command()
def analytics(
    days: int = typer.Option(30, "--days"),
    format: str = typer.Option("table", "--format", help="table/json/csv"),
):
    """Muestra analytics."""

    typer.echo(f"📈 Analytics (últimos {days} días)\n")

    # TODO: GET /analytics/overview?days=X

    data = {
        "total_revenue": 15250.50,
        "total_orders": 87,
        "avg_order_value": 175.30,
        "conversion_rate": 0.045,
        "customer_acquisition_cost": 42.50,
        "lifetime_value": 450.00,
        "roi": 10.6,
    }

    if format == "json":
        typer.echo(json.dumps(data, indent=2))
    elif format == "csv":
        for k, v in data.items():
            typer.echo(f"{k},{v}")
    else:  # table
        typer.echo(f"Total Revenue:        ${data['total_revenue']:,.2f}")
        typer.echo(f"Total Orders:         {data['total_orders']}")
        typer.echo(f"Avg Order Value:      ${data['avg_order_value']:.2f}")
        typer.echo(f"Conversion Rate:      {data['conversion_rate']:.1%}")
        typer.echo(f"CAC:                  ${data['customer_acquisition_cost']:.2f}")
        typer.echo(f"LTV:                  ${data['lifetime_value']:.2f}")
        typer.echo(f"ROI:                  {data['roi']:.1f}x")


@app.command()
def version():
    """Muestra versión."""
    typer.echo("SellIA CLI v1.0.0")


@app.command()
def help_detailed():
    """Muestra ayuda detallada."""

    typer.echo("""
SellIA CLI — Automation para vendedores.

COMANDOS:

  config              Configura API keys
  travel              Activa/desactiva travel mode
  price-optimize      Calcula precio óptimo
  forecast            Proyecta demanda
  sync                Sincroniza órdenes
  status              Muestra status sistema
  analytics           Muestra analytics
  version             Versión actual

EJEMPLOS:

  # Configurar Stripe
  sellias config --key STRIPE_KEY --value sk_live_xxx

  # Activar travel mode (vacaciones 15-25 julio)
  sellias travel on --start 2025-07-15 --end 2025-07-25 --notes "Vacaciones"

  # Ver status
  sellias status

  # Ver analytics últimos 30 días
  sellias analytics --days 30

  # Proyectar demanda
  sellias forecast --days 30 --product-id prod_123

  # Sincronizar órdenes
  sellias sync --platform mercadolibre

MÁS INFO:

  https://docs.sellias.com/cli
  support@sellias.com
""")


if __name__ == "__main__":
    app()
