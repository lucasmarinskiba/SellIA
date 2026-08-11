from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json


class ReportFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class DashboardWidget:
    id: str
    type: str
    title: str
    metric: str
    config: dict


@dataclass
class Dashboard:
    id: str
    user_id: str
    name: str
    widgets: list[DashboardWidget]
    is_default: bool
    created_at: datetime


@dataclass
class ScheduledReport:
    id: str
    user_id: str
    name: str
    query: str
    schedule: ScheduleFrequency
    recipients: list[str]
    format: ReportFormat
    is_active: bool


class AnalyticsReportingManager:
    """Manage dashboards, reports, and BI exports."""

    def __init__(self):
        self.dashboards: dict[str, Dashboard] = {}
        self.reports: dict[str, ScheduledReport] = {}
        self.exports: dict[str, dict] = {}
        self.metrics: dict[str, dict] = {}

    def create_dashboard(
        self,
        user_id: str,
        name: str,
        widgets: list[dict],
        is_default: bool = False,
        description: Optional[str] = None,
    ) -> Dashboard:
        """Create custom dashboard."""
        dashboard_id = str(uuid.uuid4())
        dashboard = Dashboard(
            id=dashboard_id,
            user_id=user_id,
            name=name,
            widgets=[DashboardWidget(**w) for w in widgets],
            is_default=is_default,
            created_at=datetime.utcnow(),
        )
        self.dashboards[dashboard_id] = dashboard
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)

    def list_dashboards(self, user_id: str) -> list[Dashboard]:
        """List dashboards for user."""
        return [d for d in self.dashboards.values() if d.user_id == user_id]

    def create_scheduled_report(
        self,
        user_id: str,
        name: str,
        query: str,
        schedule: ScheduleFrequency,
        recipients: list[str],
        format: ReportFormat = ReportFormat.CSV,
    ) -> ScheduledReport:
        """Create scheduled report."""
        report_id = str(uuid.uuid4())
        report = ScheduledReport(
            id=report_id,
            user_id=user_id,
            name=name,
            query=query,
            schedule=schedule,
            recipients=recipients,
            format=format,
            is_active=True,
        )
        self.reports[report_id] = report
        return report

    def execute_report(self, report_id: str) -> dict:
        """Execute scheduled report."""
        if report_id not in self.reports:
            return {'success': False, 'error': 'Report not found'}

        report = self.reports[report_id]

        try:
            # Placeholder: actual query execution
            rows = self._execute_query(report.query)

            file_url = f"https://storage.example.com/reports/{report_id}.{report.format}"

            return {
                'success': True,
                'file_url': file_url,
                'row_count': len(rows),
                'format': report.format,
                'recipients': report.recipients,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def export_data(
        self,
        user_id: str,
        entity_type: str,
        format: ReportFormat = ReportFormat.CSV,
        filters: Optional[dict] = None,
    ) -> dict:
        """Export data as CSV/Excel/JSON."""
        export_id = str(uuid.uuid4())

        try:
            # Placeholder: actual data export
            rows = self._get_entity_data(entity_type, filters)

            file_url = f"https://storage.example.com/exports/{export_id}.{format}"

            self.exports[export_id] = {
                'user_id': user_id,
                'entity_type': entity_type,
                'format': format,
                'file_url': file_url,
                'row_count': len(rows),
                'created_at': datetime.utcnow().isoformat(),
            }

            return {
                'success': True,
                'export_id': export_id,
                'file_url': file_url,
                'row_count': len(rows),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_realtime_metrics(self, user_id: str) -> dict:
        """Get real-time metrics dashboard."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'total_calls_today': 42,
                'avg_call_duration': 145,
                'deals_closed_today': 3,
                'revenue_today': 45000,
                'active_calls': 2,
                'sentiment_avg': 0.82,
            },
        }

    def track_metric(self, user_id: str, metric_name: str, value: Any) -> bool:
        """Track custom metric."""
        try:
            key = f"{user_id}:{metric_name}"
            self.metrics[key] = {
                'value': value,
                'timestamp': datetime.utcnow().isoformat(),
            }
            return True
        except Exception:
            return False

    def get_metric_history(
        self,
        user_id: str,
        metric_name: str,
        days: int = 30,
    ) -> list[dict]:
        """Get metric history."""
        # Placeholder: actual history retrieval
        return [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat(),
                'value': 100 + (i * 5),
            }
            for i in range(days)
        ]

    def _execute_query(self, query: str) -> list[dict]:
        """Execute report query (placeholder)."""
        return []

    def _get_entity_data(self, entity_type: str, filters: Optional[dict]) -> list[dict]:
        """Get entity data for export (placeholder)."""
        return []


# Singleton instance
analytics_manager = AnalyticsReportingManager()
