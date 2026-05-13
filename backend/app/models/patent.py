from sqlalchemy import String, Text, Integer, Date, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime

from app.db.base import Base


class Patent(Base):
    __tablename__ = "patents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patent_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    claims: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    ipc_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    cpc_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    inventors: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    applicants: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    publication_date: Mapped[date | None] = mapped_column(Date)
    filing_date: Mapped[date | None] = mapped_column(Date)
    priority_date: Mapped[date | None] = mapped_column(Date)
    legal_status: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(10))
    doc_type: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str | None] = mapped_column(String(50))
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    outgoing_citations: Mapped[list["PatentCitation"]] = relationship(
        back_populates="citing_patent", foreign_keys="PatentCitation.citing_patent_id"
    )
    incoming_citations: Mapped[list["PatentCitation"]] = relationship(
        back_populates="cited_patent", foreign_keys="PatentCitation.cited_patent_id"
    )


class PatentCitation(Base):
    __tablename__ = "patent_citations"
    __table_args__ = (UniqueConstraint("citing_patent_id", "cited_patent_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citing_patent_id: Mapped[int] = mapped_column(Integer, ForeignKey("patents.id"), nullable=False)
    cited_patent_id: Mapped[int] = mapped_column(Integer, ForeignKey("patents.id"), nullable=False)
    citation_type: Mapped[str | None] = mapped_column(String(20))

    citing_patent: Mapped["Patent"] = relationship(
        back_populates="outgoing_citations", foreign_keys=[citing_patent_id]
    )
    cited_patent: Mapped["Patent"] = relationship(
        back_populates="incoming_citations", foreign_keys=[cited_patent_id]
    )


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(100))
    query_type: Mapped[str | None] = mapped_column(String(20))
    query_text: Mapped[str | None] = mapped_column(Text)
    query_params: Mapped[dict | None] = mapped_column(JSONB)
    results_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(100))
    original_name: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(1000))
    file_type: Mapped[str | None] = mapped_column(String(20))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    patent_number: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analyses: Mapped[list["SimilarityAnalysis"]] = relationship(back_populates="upload")


class SimilarityAnalysis(Base):
    __tablename__ = "similarity_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("uploaded_documents.id"))
    target_patent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("patents.id"))
    similarity_score: Mapped[float | None] = mapped_column(Float)
    feature_overlap: Mapped[dict | None] = mapped_column(JSONB)
    ai_analysis: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    upload: Mapped["UploadedDocument"] = relationship(back_populates="analyses")
    target_patent: Mapped["Patent"] = relationship()
