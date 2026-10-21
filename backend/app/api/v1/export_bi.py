"""Export & BI API — data export, reports, dashboards."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.export.export_service import ExportBIService

router = APIRouter(prefix="/api/v1", tags=["export-bi"])


class CreateExportRequest(BaseModel):
    export_name: str
    export_type: str  # customers, orders, transactions, journeys, segments, etc
    export_format: str = "csv"  # csv, excel, json, parquet
    date_start: str | None = None  # YYYY-MM-DD
    date_end: str | None = None
    filters: dict | None = None
    requested_by: str | None = None


class CreateScheduledReportRequest(BaseModel):
    report_name: str
    report_type: str
    frequency: str  # daily, weekly, monthly, quarterly
    schedule_time: str = "06:00"  # HH:MM
    recipients: list[str] | None = None


class SetupWarehouseSyncRequest(BaseModel):
    warehouse_type: str  # bigquery, snowflake, redshift, databricks
    warehouse_name: str
    connection_string: str
    tables_to_sync: list[str] | None = None


class CreateBIDashboardRequest(BaseModel):
    dashboard_name: str
    dashboard_type: str
    charts: list[dict] | None = None


@router.post("/businesses/{business_id}/exports")
def create_export(
    business_id: UUID,
    request: CreateExportRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Request data export."""
    return ExportBIService.create_export(
        business_id=business_id,
        export_name=request.export_name,
        export_type=request.export_type,
        export_format=request.export_format,
        date_start=request.date_start,
        date_end=request.date_end,
        filters=request.filters,
        requested_by=request.requested_by,
        db=db
    )


@router.get("/exports/{export_id}")
def get_export_status(
    export_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Get export status."""
    return ExportBIService.get_export_status(
        export_id=export_id,
        db=db
    )


@router.post("/businesses/{business_id}/scheduled-reports")
def create_scheduled_report(
    business_id: UUID,
    request: CreateScheduledReportRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Create scheduled report."""
    return ExportBIService.create_scheduled_report(
        business_id=business_id,
        report_name=request.report_name,
        report_type=request.report_type,
        frequency=request.frequency,
        schedule_time=request.schedule_time,
        recipients=request.recipients,
        db=db
    )


@router.post("/businesses/{business_id}/warehouse-sync")
def setup_warehouse_sync(
    business_id: UUID,
    request: SetupWarehouseSyncRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Configure data warehouse integration."""
    return ExportBIService.setup_warehouse_sync(
        business_id=business_id,
        warehouse_type=request.warehouse_type,
        warehouse_name=request.warehouse_name,
        connection_string=request.connection_string,
        tables_to_sync=request.tables_to_sync,
        db=db
    )


@router.post("/businesses/{business_id}/bi-dashboards")
def create_bi_dashboard(
    business_id: UUID,
    request: CreateBIDashboardRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Create BI dashboard."""
    return ExportBIService.create_bi_dashboard(
        business_id=business_id,
        dashboard_name=request.dashboard_name,
        dashboard_type=request.dashboard_type,
        charts=request.charts,
        db=db
    )


@router.get("/businesses/{business_id}/export-metrics")
def get_export_metrics(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
):
    """Get export & BI metrics."""
    return ExportBIService.get_export_metrics(
        business_id=business_id,
        date=date,
        db=db
    )
