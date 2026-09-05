"""Document model — manages all documents in the acquisition workflow."""

import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, TimestampMixin
from app.models.enums import DocumentStatus, DocumentType


class Document(TimestampMixin, AuditMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    parcel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("land_parcels.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, comment="Supabase Storage URL")
    file_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DocumentStatus.UPLOADED, index=True,
    )
    # AI-extracted fields from OCR/document intelligence
    extracted_fields: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="AI-extracted key-value pairs from document"
    )
    # AI validation result comparing extracted vs system data
    validation_result: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Field-by-field validation result from AI"
    )
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Document '{self.title}' type={self.document_type.value}>"
