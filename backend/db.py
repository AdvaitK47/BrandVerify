"""
BrandVerify scan history storage (SQLAlchemy).

Uses DATABASE_URL from settings: SQLite locally by default,
PostgreSQL later by changing DATABASE_URL in .env.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
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
