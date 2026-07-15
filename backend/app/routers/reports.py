import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.dependencies import DbSession, FinanceOrAdminUser
from app.emailing import email_layout, send_email
from app.models import (
    CustodyAssignment,
    CustodyExpense,
    Donation,
    DonationStatus,
    DonationType,
    Donor,
    GeneratedReport,
    GeneratedReportStatus,
    ReportFormat,
    ReportType,
    ScheduledReport,
)
from app.schemas import (
    ReportGenerate,
    ScheduledReportCreate,
    ScheduledReportOut,
    ScheduledReportUpdate,
)
from app.services import custody_balance

router = APIRouter(prefix="/reports", tags=["Reports"])
scheduled_router = APIRouter(prefix="/scheduled-reports", tags=["Scheduled Reports"])


def donation_rows(
    db: DbSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    donation_type_id: int | None = None,
    donor_id: int | None = None,
) -> list[dict]:
    query = (
        db.query(Donation)
        .join(Donor)
        .join(DonationType)
        .filter(Donation.status == DonationStatus.confirmed)
    )
    if start_date:
        query = query.filter(Donation.donation_date >= start_date)
    if end_date:
        query = query.filter(Donation.donation_date <= end_date)
    if donation_type_id:
        query = query.filter(Donation.donation_type_id == donation_type_id)
    if donor_id:
        query = query.filter(Donation.donor_id == donor_id)
    return [
        {
            "id": item.id,
            "date": item.donation_date,
            "donor": f"{item.donor.first_name} {item.donor.last_name}",
            "donation_type": item.donation_type.type_name,
            "amount": item.amount,
            "currency": item.currency,
            "payment_method": item.payment_method or "",
            "receipt_number": item.receipt_number or "",
        }
        for item in query.order_by(Donation.donation_date.desc()).all()
    ]


def donor_rows(
    db: DbSession, start_date: datetime | None = None, end_date: datetime | None = None
) -> list[dict]:
    donation_join_conditions = [
        Donation.donor_id == Donor.id,
        Donation.status == DonationStatus.confirmed,
    ]
    if start_date:
        donation_join_conditions.append(Donation.donation_date >= start_date)
    if end_date:
        donation_join_conditions.append(Donation.donation_date <= end_date)
    rows = (
        db.query(
            Donor.id,
            Donor.first_name,
            Donor.last_name,
            func.coalesce(func.sum(Donation.amount), 0).label("total_donated"),
            func.max(Donation.donation_date).label("last_donation_at"),
        )
        .outerjoin(
            Donation,
            and_(*donation_join_conditions),
        )
        .filter(Donor.is_deleted.is_(False))
        .group_by(Donor.id, Donor.first_name, Donor.last_name)
        .order_by(Donor.last_name, Donor.first_name)
        .all()
    )
    return [
        {
            "id": row.id,
            "donor": f"{row.first_name} {row.last_name}",
            "total_donated": row.total_donated,
            "last_donation_at": row.last_donation_at or "",
        }
        for row in rows
    ]


def custody_rows(
    db: DbSession, start_date: datetime | None = None, end_date: datetime | None = None
) -> list[dict]:
    query = db.query(CustodyAssignment)
    if start_date:
        query = query.filter(CustodyAssignment.assigned_at >= start_date)
    if end_date:
        query = query.filter(CustodyAssignment.assigned_at <= end_date)
    assignments = query.order_by(CustodyAssignment.assigned_at.desc()).all()
    return [
        {
            "id": assignment.id,
            "user_id": assignment.user_id,
            "assigned_at": assignment.assigned_at,
            "amount": assignment.amount,
            "status": assignment.status.value,
            "available_balance": custody_balance(db, assignment.id),
        }
        for assignment in assignments
    ]


def rows_for_report(db: DbSession, payload: ReportGenerate) -> list[dict]:
    if payload.report_type == ReportType.donations:
        return donation_rows(
            db,
            payload.start_date,
            payload.end_date,
            payload.donation_type_id,
            payload.donor_id,
        )
    if payload.report_type == ReportType.donors:
        return donor_rows(db, payload.start_date, payload.end_date)
    return custody_rows(db, payload.start_date, payload.end_date)


def write_csv(report_id: int, report_type: ReportType, rows: list[dict]) -> Path:
    report_dir = Path(get_settings().report_storage_path)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{report_type.value}-{report_id}.csv"
    fieldnames = list(rows[0].keys()) if rows else ["message"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow({"message": "No data for the selected filters"})
    return path


def create_generated_report(
    db: Session,
    payload: ReportGenerate,
    generated_by_user_id: int | None,
    scheduled_report_id: int | None = None,
) -> GeneratedReport:
    if payload.format != ReportFormat.csv:
        raise ValueError("Only CSV exports are currently supported")
    record = GeneratedReport(
        scheduled_report_id=scheduled_report_id,
        report_type=payload.report_type,
        format=payload.format,
        generated_by_user_id=generated_by_user_id,
        status=GeneratedReportStatus.pending,
    )
    db.add(record)
    db.flush()
    path = write_csv(record.id, payload.report_type, rows_for_report(db, payload))
    record.file_path = str(path.resolve())
    record.status = GeneratedReportStatus.completed
    return record


def next_run_for(frequency: str, from_time: datetime | None = None) -> datetime:
    current_time = from_time or datetime.now(timezone.utc)
    intervals = {
        "weekly": timedelta(days=7),
        "monthly": timedelta(days=30),
        "yearly": timedelta(days=365),
        "custom": timedelta(days=1),
    }
    return current_time + intervals[frequency]


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def report_payload_for_schedule(scheduled_report: ScheduledReport) -> ReportGenerate:
    filters = scheduled_report.filters_json or {}
    now = datetime.now(timezone.utc)
    if filters.get("start_date") and filters.get("end_date"):
        start_date = parse_datetime(filters["start_date"])
        end_date = parse_datetime(filters["end_date"])
    else:
        window_days = {
            "last_7_days": 7,
            "last_30_days": 30,
            "last_365_days": 365,
        }.get(filters.get("window"), 30)
        start_date = now - timedelta(days=window_days)
        end_date = now
    return ReportGenerate(
        report_type=scheduled_report.report_type,
        format=scheduled_report.format,
        start_date=start_date,
        end_date=end_date,
        donation_type_id=filters.get("donation_type_id"),
        donor_id=filters.get("donor_id"),
    )


def email_generated_report(record: GeneratedReport, recipients: list[str]) -> None:
    settings = get_settings()
    if not record.file_path:
        raise RuntimeError("Generated report has no file to attach")

    report_path = Path(record.file_path)
    report_name = record.report_type.value.replace("_", " ").title()
    generated_at = record.generated_at.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    send_email(
        recipients=recipients,
        subject=f"{settings.app_name} | {report_name} report",
        text=(
            f"Your {report_name.lower()} is ready.\n\n"
            f"It was generated on {generated_at} and is attached as a CSV file."
        ),
        html=email_layout(
            heading=f"Your {report_name.lower()} is ready",
            eyebrow="Scheduled report",
            preview_text=f"Your {report_name.lower()} is ready to download.",
            body=(
                "<p>Your scheduled report has been generated and is ready for review.</p>"
                "<p>The CSV file is attached to this email so you can access it securely from your device.</p>"
            ),
            details=[
                ("Report", report_name),
                ("Generated", generated_at),
                ("Attachment", report_path.name),
            ],
        ),
        attachments=[
            (report_path.name, report_path.read_bytes(), "text", "csv"),
        ],
    )


def run_scheduled_report(db: Session, scheduled_report: ScheduledReport) -> GeneratedReport:
    record = create_generated_report(
        db,
        report_payload_for_schedule(scheduled_report),
        generated_by_user_id=scheduled_report.created_by_user_id,
        scheduled_report_id=scheduled_report.id,
    )
    try:
        email_generated_report(record, scheduled_report.recipients_json)
    except Exception as error:
        record.status = GeneratedReportStatus.failed
        record.error_message = str(error)
    return record


def process_due_scheduled_reports() -> None:
    """Run due reports from the in-process scheduler.

    This is intentionally single-instance for local Docker Compose. Move this
    work to a dedicated worker before running multiple backend replicas.
    """
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        scheduled_reports = db.scalars(
            select(ScheduledReport).where(
                ScheduledReport.is_active.is_(True),
                ScheduledReport.next_run_at.is_not(None),
                ScheduledReport.next_run_at <= now,
            )
        ).all()
        for scheduled_report in scheduled_reports:
            run_scheduled_report(db, scheduled_report)
            scheduled_report.last_run_at = now
            scheduled_report.next_run_at = next_run_for(
                scheduled_report.frequency, now
            )
        db.commit()


@router.get("/donations", response_model=list[dict])
def donation_report_data(
    _: FinanceOrAdminUser,
    db: DbSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    donation_type_id: int | None = None,
    donor_id: int | None = None,
) -> list[dict]:
    return donation_rows(db, start_date, end_date, donation_type_id, donor_id)


@router.get("/donors", response_model=list[dict])
def donor_report_data(
    _: FinanceOrAdminUser,
    db: DbSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    return donor_rows(db, start_date, end_date)


@router.get("/custody", response_model=list[dict])
def custody_report_data(
    _: FinanceOrAdminUser,
    db: DbSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    return custody_rows(db, start_date, end_date)


@router.post("/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerate, current_user: FinanceOrAdminUser, db: DbSession
) -> dict:
    try:
        record = create_generated_report(
            db, payload, generated_by_user_id=current_user.id
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    db.commit()
    return {
        "id": record.id,
        "report_type": record.report_type,
        "format": record.format,
        "generated_at": record.generated_at,
        "download_url": f"/api/v1/reports/generated/{record.id}/download",
    }


@router.get("/generated", response_model=list[dict])
def list_generated_reports(
    _: FinanceOrAdminUser, db: DbSession
) -> list[dict]:
    records = db.query(GeneratedReport).order_by(GeneratedReport.generated_at.desc()).all()
    return [
        {
            "id": record.id,
            "report_type": record.report_type,
            "format": record.format,
            "status": record.status,
            "generated_at": record.generated_at,
            "download_url": f"/api/v1/reports/generated/{record.id}/download",
        }
        for record in records
    ]


@router.get("/generated/{report_id}/download")
def download_generated_report(
    report_id: int, _: FinanceOrAdminUser, db: DbSession
) -> FileResponse:
    record = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    if not record or not record.file_path:
        raise HTTPException(status_code=404, detail="Generated report not found")
    path = Path(record.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Generated report file is no longer available")
    return FileResponse(path, media_type="text/csv", filename=path.name)


@scheduled_router.get("", response_model=list[ScheduledReportOut])
def list_scheduled_reports(
    _: FinanceOrAdminUser, db: DbSession
) -> list[ScheduledReport]:
    return db.query(ScheduledReport).order_by(ScheduledReport.created_at.desc()).all()


@scheduled_router.post("", response_model=ScheduledReportOut, status_code=status.HTTP_201_CREATED)
def create_scheduled_report(
    payload: ScheduledReportCreate, current_user: FinanceOrAdminUser, db: DbSession
) -> ScheduledReport:
    item = ScheduledReport(
        **payload.model_dump(exclude={"recipients_json"}),
        recipients_json=[str(email) for email in payload.recipients_json],
        next_run_at=next_run_for(payload.frequency),
        created_by_user_id=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@scheduled_router.patch("/{report_id}", response_model=ScheduledReportOut)
def update_scheduled_report(
    report_id: int,
    payload: ScheduledReportUpdate,
    _: FinanceOrAdminUser,
    db: DbSession,
) -> ScheduledReport:
    item = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    values = payload.model_dump(exclude_unset=True)
    if "recipients_json" in values and values["recipients_json"] is not None:
        values["recipients_json"] = [str(email) for email in values["recipients_json"]]
    for field, value in values.items():
        setattr(item, field, value)
    if item.is_active:
        item.next_run_at = next_run_for(item.frequency)
    db.commit()
    db.refresh(item)
    return item


@scheduled_router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def disable_scheduled_report(
    report_id: int, _: FinanceOrAdminUser, db: DbSession
) -> None:
    item = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    item.is_active = False
    db.commit()


@scheduled_router.post("/{report_id}/run", response_model=dict)
def run_scheduled_report_now(
    report_id: int, _: FinanceOrAdminUser, db: DbSession
) -> dict:
    item = db.query(ScheduledReport).filter(ScheduledReport.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    try:
        record = run_scheduled_report(db, item)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    item.last_run_at = datetime.now(timezone.utc)
    item.next_run_at = next_run_for(item.frequency, item.last_run_at)
    db.commit()
    return {
        "id": record.id,
        "status": record.status,
        "error_message": record.error_message,
        "download_url": f"/api/v1/reports/generated/{record.id}/download",
    }
