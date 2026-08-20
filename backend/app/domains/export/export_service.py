"""Export & BI service — data export, scheduled reports, warehouse sync."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.export.export_models import (
    DataExport, ScheduledReport, DataWarehouseSync, BIDashboardConfig, ExportMetrics,
    ExportFormat, ExportType, ReportFrequency
)

logger = logging.getLogger(__name__)


class ExportBIService:
    """Manage data exports, reports, BI dashboards."""

    @staticmethod
    def create_export(
        business_id: UUID,
        export_name: str,
        export_type: str,
        export_format: str = ExportFormat.CSV,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        filters: Optional[Dict] = None,
        requested_by: str = None,
        db: Session = None
    ) -> dict:
        """Request data export."""
        if not db:
            raise ValueError("Database session required")

        export = DataExport(
            business_id=business_id,
            export_name=export_name,
            export_type=export_type,
            export_format=export_format,
            date_start=date_start,
            date_end=date_end,
            filters=filters or {},
            requested_by=requested_by,
            status="pending"
        )

        db.add(export)
        db.commit()
        db.refresh(export)

        logger.info(f"Export requested: {export_name} ({export_type}) - {export_format}")

        return {
            "export_id": str(export.id),
            "export_name": export_name,
            "export_type": export_type,
            "format": export_format,
            "status": "pending",
            "requested_at": export.requested_at.isoformat()
        }

    @staticmethod
    def complete_export(
        export_id: UUID,
        file_url: str,
        file_size_bytes: int,
        row_count: int,
        db: Session = None
    ) -> dict:
        """Mark export as complete."""
        if not db:
            raise ValueError("Database session required")

        export = db.query(DataExport).filter(DataExport.id == export_id).first()
        if not export:
            raise ValueError(f"Export {export_id} not found")

        export.status = "completed"
        export.file_url = file_url
        export.file_size_bytes = file_size_bytes
        export.row_count = row_count
        export.completed_at = datetime.now(timezone.utc)
        export.expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # 7-day retention

        db.commit()

        logger.info(f"Export completed: {export_id} - {row_count} rows, {file_size_bytes} bytes")

        return {
            "export_id": str(export.id),
            "status": "completed",
            "file_url": file_url,
            "row_count": row_count,
            "expires_at": export.expires_at.isoformat()
        }

    @staticmethod
    def create_scheduled_report(
        business_id: UUID,
        report_name: str,
        report_type: str,
        frequency: str,
        schedule_time: str = "06:00",
        recipients: List[str] = None,
        db: Session = None
    ) -> dict:
        """Create scheduled report."""
        if not db:
            raise ValueError("Database session required")

        # Calculate next send time
        now = datetime.now(timezone.utc)
        next_send = None

        if frequency == ReportFrequency.DAILY:
            hour, minute = map(int, schedule_time.split(":"))
            next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_send <= now:
                next_send += timedelta(days=1)

        elif frequency == ReportFrequency.WEEKLY:
            next_send = now + timedelta(days=7)

        elif frequency == ReportFrequency.MONTHLY:
            next_send = now + timedelta(days=30)

        report = ScheduledReport(
            business_id=business_id,
            report_name=report_name,
            report_type=report_type,
            frequency=frequency,
            schedule_time=schedule_time,
            recipients=recipients or [],
            next_send_at=next_send
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(f"Scheduled report created: {report_name} - {frequency}")

        return {
            "report_id": str(report.id),
            "report_name": report_name,
            "frequency": frequency,
            "next_send_at": report.next_send_at.isoformat() if report.next_send_at else None,
            "recipients": recipients or []
        }

    @staticmethod
    def setup_warehouse_sync(
        business_id: UUID,
        warehouse_type: str,
        warehouse_name: str,
        connection_string: str,
        tables_to_sync: List[str] = None,
        db: Session = None
    ) -> dict:
        """Configure data warehouse integration."""
        if not db:
            raise ValueError("Database session required")

        # Encrypt connection string (placeholder - use real encryption in production)
        encrypted_conn = f"encrypted_{connection_string[:10]}..."

        sync = db.query(DataWarehouseSync).filter(
            DataWarehouseSync.business_id == business_id
        ).first()

        if sync:
            sync.warehouse_type = warehouse_type
            sync.warehouse_name = warehouse_name
            sync.connection_string_encrypted = encrypted_conn
            sync.tables_synced = tables_to_sync or []
            sync.connection_status = "testing"
        else:
            sync = DataWarehouseSync(
                business_id=business_id,
                warehouse_type=warehouse_type,
                warehouse_name=warehouse_name,
                connection_string_encrypted=encrypted_conn,
                tables_synced=tables_to_sync or [],
                connection_status="testing"
            )
            db.add(sync)

        db.commit()
        db.refresh(sync)

        logger.info(f"Warehouse sync configured: {warehouse_type} - {warehouse_name}")

        return {
            "sync_id": str(sync.id),
            "warehouse_type": warehouse_type,
            "warehouse_name": warehouse_name,
            "connection_status": "testing",
            "tables_synced": tables_to_sync or []
        }

    @staticmethod
    def complete_warehouse_sync(
        sync_id: UUID,
        rows_synced: int,
        db: Session = None
    ) -> dict:
        """Mark warehouse sync complete."""
        if not db:
            raise ValueError("Database session required")

        sync = db.query(DataWarehouseSync).filter(DataWarehouseSync.id == sync_id).first()
        if not sync:
            raise ValueError(f"Sync {sync_id} not found")

        sync.connection_status = "connected"
        sync.last_sync_at = datetime.now(timezone.utc)
        sync.next_sync_at = datetime.now(timezone.utc) + timedelta(hours=sync.sync_interval_hours)
        sync.rows_synced_total += rows_synced

        db.commit()

        logger.info(f"Warehouse sync completed: {rows_synced} rows synced")

        return {
            "sync_id": str(sync.id),
            "connection_status": "connected",
            "rows_synced": rows_synced,
            "next_sync_at": sync.next_sync_at.isoformat()
        }

    @staticmethod
    def create_bi_dashboard(
        business_id: UUID,
        dashboard_name: str,
        dashboard_type: str,
        charts: List[Dict] = None,
        db: Session = None
    ) -> dict:
        """Create BI dashboard."""
        if not db:
            raise ValueError("Database session required")

        dashboard = BIDashboardConfig(
            business_id=business_id,
            dashboard_name=dashboard_name,
            dashboard_type=dashboard_type,
            charts=charts or []
        )

        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)

        logger.info(f"BI dashboard created: {dashboard_name}")

        return {
            "dashboard_id": str(dashboard.id),
            "dashboard_name": dashboard_name,
            "dashboard_type": dashboard_type,
            "chart_count": len(charts or [])
        }

    @staticmethod
    def get_export_status(
        export_id: UUID,
        db: Session = None
    ) -> dict:
        """Get export status."""
        if not db:
            raise ValueError("Database session required")

        export = db.query(DataExport).filter(DataExport.id == export_id).first()
        if not export:
            raise ValueError(f"Export {export_id} not found")

        return {
            "export_id": str(export.id),
            "export_name": export.export_name,
            "export_type": export.export_type,
            "status": export.status,
            "file_url": export.file_url,
            "row_count": export.row_count,
            "file_size_bytes": export.file_size_bytes,
            "requested_at": export.requested_at.isoformat(),
            "completed_at": export.completed_at.isoformat() if export.completed_at else None,
            "expires_at": export.expires_at.isoformat() if export.expires_at else None
        }

    @staticmethod
    def get_export_metrics(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Get export & BI metrics."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        # Count exports
        exports = db.query(DataExport).filter(
            DataExport.business_id == business_id,
            DataExport.requested_at >= date_start,
            DataExport.requested_at < date_end
        ).all()

        if not exports:
            return {"metrics_available": False}

        successful = len([e for e in exports if e.status == "completed"])
        failed = len([e for e in exports if e.status == "failed"])
        total_rows = sum(e.row_count for e in exports)
        total_bytes = sum(e.file_size_bytes for e in exports)

        # Count by format
        format_counts = {}
        for export in exports:
            fmt = export.export_format
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

        # Scheduled reports
        reports_sent = db.query(ScheduledReport).filter(
            ScheduledReport.business_id == business_id,
            ScheduledReport.last_sent_at >= date_start,
            ScheduledReport.last_sent_at < date_end
        ).count()

        # Dashboard views
        dashboards = db.query(BIDashboardConfig).filter(
            BIDashboardConfig.business_id == business_id
        ).all()

        dashboard_views = sum(d.view_count for d in dashboards)

        metrics = ExportMetrics(
            business_id=business_id,
            date=date,
            total_exports_requested=len(exports),
            successful_exports=successful,
            failed_exports=failed,
            total_rows_exported=total_rows,
            total_bytes_exported=total_bytes,
            csv_exports=format_counts.get(ExportFormat.CSV, 0),
            excel_exports=format_counts.get(ExportFormat.EXCEL, 0),
            json_exports=format_counts.get(ExportFormat.JSON, 0),
            parquet_exports=format_counts.get(ExportFormat.PARQUET, 0),
            scheduled_reports_sent=reports_sent,
            dashboard_views=dashboard_views
        )

        db.add(metrics)
        db.commit()

        logger.info(f"Export metrics recorded: {business_id} - {len(exports)} exports")

        return {
            "metrics_recorded": True,
            "date": date,
            "exports": {
                "total_requested": len(exports),
                "successful": successful,
                "failed": failed
            },
            "data_volume": {
                "total_rows": total_rows,
                "total_bytes": total_bytes
            },
            "formats": format_counts,
            "reports": {
                "scheduled_sent": reports_sent
            },
            "bi": {
                "dashboard_views": dashboard_views
            }
        }
