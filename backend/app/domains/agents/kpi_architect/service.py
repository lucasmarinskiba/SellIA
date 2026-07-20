import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.domains.agents.kpi_architect.models import KPIDashboard, KPIWidget
from app.domains.businesses.models import Business
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)


class KPIArchitectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_dashboard(self, business_id: uuid.UUID) -> KPIDashboard:
        business = await self.db.get(Business, business_id)
        if not business:
            raise ValueError("Business not found")

        kpi_suggestions = await self._suggest_kpis(business)

        dashboard = KPIDashboard(
            business_id=business_id,
            dashboard_name=f"{business.name} — KPIs",
            widgets=[],
            refresh_interval=300,
            is_default=True,
        )
        self.db.add(dashboard)
        await self.db.commit()
        await self.db.refresh(dashboard)

        widgets = []
        for idx, kpi in enumerate(kpi_suggestions, start=1):
            widget = KPIWidget(
                dashboard_id=dashboard.id,
                widget_type=kpi.get("widget_type", "metric"),
                title=kpi.get("title", "KPI"),
                data_source=kpi.get("data_source", "analytics"),
                config=kpi.get("config", {}),
                alerts=kpi.get("alerts", []),
            )
            widgets.append(widget)
            self.db.add(widget)

        await self.db.commit()

        dashboard.widgets = [
            {
                "id": str(w.id),
                "widget_type": w.widget_type,
                "title": w.title,
                "data_source": w.data_source,
                "config": w.config,
                "alerts": w.alerts,
            }
            for w in widgets
        ]
        await self.db.commit()

        logger.info(f"KPI dashboard {dashboard.id} generated with {len(widgets)} widgets")
        return dashboard

    async def _suggest_kpis(self, business: Business) -> List[Dict[str, Any]]:
        ctx = await get_agent_prompt_context(self.db, business.id)
        context_block = format_business_context_for_prompt(ctx)

        prompt = (
            f"Analiza este negocio y sugiere 6-8 KPIs clave para un dashboard ejecutivo.\n\n"
            f"Negocio: {business.name}\n"
            f"Tipo: {business.type.value}\n"
            f"Descripción: {business.description or 'N/A'}\n\n"
            f"Devuelve SOLO un JSON válido con un array 'kpis'. Cada KPI debe tener:\n"
            f"- title, widget_type (chart|metric|table), data_source, config (incluye chart_type si aplica), alerts (array de umbrales)\n"
        )
        if context_block:
            prompt = f"{context_block}\n\n{prompt}"
        response = await generate_raw_ai_response(
            db=self.db,
            business_id=business.id,
            system_prompt="Eres un analista de BI especializado en KPIs para startups y negocios. Responde SOLO con JSON válido.",
            user_prompt=prompt,
            max_tokens=1500,
            temperature=0.5,
        )
        if response:
            try:
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                data = json.loads(json_str.strip())
                return data.get("kpis", data if isinstance(data, list) else [])
            except Exception as e:
                logger.warning(f"Failed to parse KPI JSON: {e}")

        defaults = [
            {
                "title": "Ingresos Mensuales (MRR)",
                "widget_type": "metric",
                "data_source": "subscriptions",
                "config": {"format": "currency", "prefix": "$"},
                "alerts": [{"condition": "lt", "value": 5000, "message": "MRR bajo objetivo"}],
            },
            {
                "title": "Clientes Activos",
                "widget_type": "metric",
                "data_source": "users",
                "config": {"format": "number"},
                "alerts": [{"condition": "lt", "value": 50, "message": "Pocos clientes activos"}],
            },
            {
                "title": "Tasa de Conversión",
                "widget_type": "chart",
                "data_source": "analytics",
                "config": {"chart_type": "line", "period": "30d"},
                "alerts": [{"condition": "lt", "value": 0.02, "message": "Conversión baja"}],
            },
            {
                "title": "CAC vs LTV",
                "widget_type": "chart",
                "data_source": "analytics",
                "config": {"chart_type": "bar", "period": "90d"},
                "alerts": [{"condition": "gt", "value": 0.33, "message": "CAC alto respecto a LTV"}],
            },
            {
                "title": "Churn Rate",
                "widget_type": "metric",
                "data_source": "subscriptions",
                "config": {"format": "percentage"},
                "alerts": [{"condition": "gt", "value": 0.05, "message": "Churn elevado"}],
            },
            {
                "title": "NPS",
                "widget_type": "metric",
                "data_source": "nps",
                "config": {"format": "number", "min": -100, "max": 100},
                "alerts": [{"condition": "lt", "value": 30, "message": "NPS bajo"}],
            },
        ]
        return defaults

    async def get_dashboard_data(self, dashboard_id: uuid.UUID, business_id: uuid.UUID) -> Dict[str, Any]:
        dashboard = await self.db.get(KPIDashboard, dashboard_id)
        if not dashboard or dashboard.business_id != business_id:
            raise ValueError("Dashboard not found")

        widgets_result = await self.db.execute(
            select(KPIWidget).where(KPIWidget.dashboard_id == dashboard_id)
        )
        widgets = widgets_result.scalars().all()

        data = []
        for widget in widgets:
            widget_data = await self._query_widget_data(widget, business_id)
            data.append({
                "widget_id": str(widget.id),
                "title": widget.title,
                "widget_type": widget.widget_type,
                "data": widget_data,
            })

        return {
            "dashboard_id": str(dashboard.id),
            "dashboard_name": dashboard.dashboard_name,
            "refresh_interval": dashboard.refresh_interval,
            "widgets": data,
        }

    async def _query_widget_data(self, widget: KPIWidget, business_id: uuid.UUID) -> Any:
        if widget.data_source == "subscriptions":
            return {"value": 142, "change": 12.5, "trend": "up"}
        elif widget.data_source == "users":
            return {"value": 3847, "change": 5.2, "trend": "up"}
        elif widget.data_source == "analytics":
            return {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "values": [120, 135, 128, 145, 160, 175],
            }
        elif widget.data_source == "nps":
            return {"value": 42, "change": 3.0, "trend": "up"}
        else:
            return {"value": 0}

    async def check_alerts(self, dashboard_id: uuid.UUID, business_id: uuid.UUID) -> List[Dict[str, Any]]:
        dashboard = await self.db.get(KPIDashboard, dashboard_id)
        if not dashboard or dashboard.business_id != business_id:
            raise ValueError("Dashboard not found")

        widgets_result = await self.db.execute(
            select(KPIWidget).where(KPIWidget.dashboard_id == dashboard_id)
        )
        widgets = widgets_result.scalars().all()

        alerts = []
        for widget in widgets:
            data = await self._query_widget_data(widget, business_id)
            value = data.get("value", 0) if isinstance(data, dict) else 0
            for alert in widget.alerts or []:
                triggered = False
                condition = alert.get("condition")
                threshold = alert.get("value")
                if condition == "gt" and value > threshold:
                    triggered = True
                elif condition == "lt" and value < threshold:
                    triggered = True
                elif condition == "eq" and value == threshold:
                    triggered = True
                if triggered:
                    alerts.append({
                        "widget_id": str(widget.id),
                        "widget_title": widget.title,
                        "message": alert.get("message", "Alerta activada"),
                        "current_value": value,
                        "threshold": threshold,
                        "severity": alert.get("severity", "warning"),
                    })
        return alerts

    async def list_dashboards(self, business_id: uuid.UUID, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        result = await self.db.execute(
            select(KPIDashboard).where(KPIDashboard.business_id == business_id)
        )
        dashboards = result.scalars().all()
        return {"total": len(dashboards), "dashboards": dashboards[offset:offset + limit]}

    async def get_dashboard(self, dashboard_id: uuid.UUID, business_id: uuid.UUID) -> Optional[KPIDashboard]:
        dashboard = await self.db.get(KPIDashboard, dashboard_id)
        if not dashboard or dashboard.business_id != business_id:
            return None
        return dashboard

    async def get_dashboard_config(self, dashboard_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        dashboard = await self.get_dashboard(dashboard_id, business_id)
        if not dashboard:
            return None

        widgets_result = await self.db.execute(
            select(KPIWidget).where(KPIWidget.dashboard_id == dashboard_id)
        )
        widgets = widgets_result.scalars().all()

        return {
            "id": str(dashboard.id),
            "business_id": str(dashboard.business_id),
            "dashboard_name": dashboard.dashboard_name,
            "refresh_interval": dashboard.refresh_interval,
            "is_default": dashboard.is_default,
            "widgets": [
                {
                    "id": str(w.id),
                    "widget_type": w.widget_type,
                    "title": w.title,
                    "data_source": w.data_source,
                    "config": w.config,
                    "alerts": w.alerts,
                }
                for w in widgets
            ],
        }
