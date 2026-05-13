"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patent_number", sa.String(50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("claims", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ipc_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("cpc_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("inventors", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("applicants", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("priority_date", sa.Date(), nullable=True),
        sa.Column("legal_status", sa.String(50), nullable=True),
        sa.Column("country", sa.String(10), nullable=True),
        sa.Column("doc_type", sa.String(20), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patent_number"),
    )
    op.create_index("ix_patents_patent_number", "patents", ["patent_number"])

    op.create_table(
        "patent_citations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("citing_patent_id", sa.Integer(), nullable=False),
        sa.Column("cited_patent_id", sa.Integer(), nullable=False),
        sa.Column("citation_type", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["citing_patent_id"], ["patents.id"]),
        sa.ForeignKeyConstraint(["cited_patent_id"], ["patents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("citing_patent_id", "cited_patent_id"),
    )

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("query_type", sa.String(20), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=True),
        sa.Column("query_params", postgresql.JSONB(), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("original_name", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_type", sa.String(20), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("patent_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "similarity_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("upload_id", sa.Integer(), nullable=True),
        sa.Column("target_patent_id", sa.Integer(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("feature_overlap", postgresql.JSONB(), nullable=True),
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["upload_id"], ["uploaded_documents.id"]),
        sa.ForeignKeyConstraint(["target_patent_id"], ["patents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("similarity_analyses")
    op.drop_table("uploaded_documents")
    op.drop_table("search_history")
    op.drop_table("patent_citations")
    op.drop_table("patents")
