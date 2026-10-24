"""
BrandVerify scan history storage (SQLAlchemy).

Uses DATABASE_URL from settings: SQLite locally by default,
PostgreSQL later by changing DATABASE_URL in .env.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from backend.config import settings

_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ScanRecord(Base):
    __tablename__ = "scans"

    scan_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    brand_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    overall_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    compliance_score: Mapped[int] = mapped_column(Integer)
    scanned_at: Mapped[datetime] = mapped_column(DateTime)
    result_json: Mapped[str] = mapped_column(Text)


def init_db() -> None:
    """Create the tables if they do not exist yet."""
    Base.metadata.create_all(engine)


def save_scan(result: Any) -> None:
    """Save one ScanResult (a pydantic model). Saving the same scan_id updates it."""
    with SessionLocal() as session:
        session.merge(
            ScanRecord(
                scan_id=result.scan_id,
                brand_id=result.brand_id,
                title=result.title,
                content_type=result.content_type,
                overall_status=result.overall_status,
                compliance_score=result.compliance_score,
                scanned_at=result.scanned_at,
                result_json=result.model_dump_json(),
            )
        )
        session.commit()


def list_scans(brand_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Return short summaries of recent scans, newest first."""
    stmt = select(ScanRecord).order_by(ScanRecord.scanned_at.desc()).limit(limit)
    if brand_id:
        stmt = stmt.where(ScanRecord.brand_id == brand_id)

    with SessionLocal() as session:
        rows = session.scalars(stmt).all()
        return [
            {
                "scan_id": r.scan_id,
                "brand_id": r.brand_id,
                "title": r.title,
                "content_type": r.content_type,
                "overall_status": r.overall_status,
                "compliance_score": r.compliance_score,
                "scanned_at": r.scanned_at.isoformat(),
            }
            for r in rows
        ]


def get_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    """Return the full saved result of one scan, or None if not found."""
    with SessionLocal() as session:
        record = session.get(ScanRecord, scan_id)
        return json.loads(record.result_json) if record else None


class AuditRecord(Base):
    """One human decision on a scan. Rows are only ever added, never changed."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String(64), index=True)
    brand_id: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(32))
    reviewer: Mapped[str] = mapped_column(String(100))
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overrode_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class AuditLogError(RuntimeError):
    """Raised on any attempt to change or delete an audit log entry."""


@event.listens_for(AuditRecord, "before_update")
def _audit_rows_cannot_be_updated(mapper, connection, target):
    raise AuditLogError("Audit log entries cannot be changed.")


@event.listens_for(AuditRecord, "before_delete")
def _audit_rows_cannot_be_deleted(mapper, connection, target):
    raise AuditLogError("Audit log entries cannot be deleted.")


def _audit_to_dict(record: AuditRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "scan_id": record.scan_id,
        "brand_id": record.brand_id,
        "action": record.action,
        "reviewer": record.reviewer,
        "comment": record.comment,
        "overrode_critical": bool(record.overrode_critical),
        "created_at": record.created_at,
    }


def add_audit_entry(
    scan_id: str,
    brand_id: str,
    action: str,
    reviewer: str,
    comment: Optional[str],
    overrode_critical: bool,
) -> Dict[str, Any]:
    """Append one decision to the audit log and return it."""
    with SessionLocal() as session:
        record = AuditRecord(
            scan_id=scan_id,
            brand_id=brand_id,
            action=action,
            reviewer=reviewer,
            comment=comment,
            overrode_critical=overrode_critical,
            created_at=datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        return _audit_to_dict(record)


def list_audit(scan_id: str) -> List[Dict[str, Any]]:
    """Every decision on one scan, oldest first."""
    stmt = (
        select(AuditRecord)
        .where(AuditRecord.scan_id == scan_id)
        .order_by(AuditRecord.id)
    )
    with SessionLocal() as session:
        return [_audit_to_dict(r) for r in session.scalars(stmt).all()]


def review_statuses(scan_ids: List[str]) -> Dict[str, str]:
    """Latest decision per scan ('approved' or 'rejected').
    Scans with no decision yet are left out of the result."""
    if not scan_ids:
        return {}
    stmt = (
        select(AuditRecord)
        .where(AuditRecord.scan_id.in_(scan_ids))
        .order_by(AuditRecord.id)
    )
    latest: Dict[str, str] = {}
    with SessionLocal() as session:
        for record in session.scalars(stmt).all():
            latest[record.scan_id] = record.action
    return latest
