"""Export & BI API — data export, reports, dashboards."""

from uuid import UUID
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.export.export_service import ExportBIService

router = APIRouter(prefix="/api/v1", tags=["export-bi"])


class CreateExportRequest(BaseModel):
    export_name: str
    export_type: str  # customers, orders, transactions, journeys, segments, etc
    export_format: str = "csv"  # csv, excel, json, parquet
    date_start: Optional[str] = None  # YYYY-MM-DD
    date_end: Optional[str] = None
    filters: Optional[Dict] = None
    requested_by: Optional[str] = None


class CreateScheduledReportRequest(BaseModel):
    report_name: str
    report_type: str
    frequency: str  # daily, weekly, monthly, quarterly
    schedule_time: str = "06:00"  # HH:MM
    recipients: Optional[List[str]] = None


class SetupWarehouseSyncRequest(BaseModel):
    warehouse_type: str  # bigquery, snowflake, redshift, databricks
    warehouse_name: str
    connection_string: str
    tables_to_sync: Optional[List[str]] = None


class CreateBIDashboardRequest(BaseModel):
    dashboard_name: str
    dashboard_type: str
    charts: Optional[List[Dict]] = None


@router.post("/businesses/{business_id}/exports")
def create_export(
    business_id: UUID,
    request: CreateExportRequest,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Get export & BI metrics."""
    return ExportBIService.get_export_metrics(
        business_id=business_id,
        date=date,
        db=db
    )
