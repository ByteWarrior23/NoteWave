import datetime
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config import settings

logger = logging.getLogger("notewave.database")

Base = declarative_base()

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)
    title = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default="Indexed")
    error_message = Column(Text, nullable=True)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.filename,
            "filename": self.filename,
            "size": self.file_size_bytes,
            "page_count": self.page_count,
            "chunks": self.chunk_count,
            "title": self.title or self.filename,
            "status": self.status,
            "date": self.upload_time.strftime("%Y-%m-%d %H:%M") if self.upload_time else "Uploaded",
            "mastery": 85,
        }

class ParentChunkRecord(Base):
    """Stores full parent section context for child-chunk expansion."""
    __tablename__ = "parent_chunks"

    parent_id = Column(String(128), primary_key=True, index=True)
    document_id = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, default=1)
    section_heading = Column(String(255), nullable=True)
    content_type = Column(String(50), nullable=False, default="prose")
    text = Column(Text, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_id": self.parent_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "page_number": self.page_number,
            "section_heading": self.section_heading or "General",
            "content_type": self.content_type,
            "text": self.text,
        }

class QueryLogRecord(Base):
    __tablename__ = "query_logs"

    id = Column(String(64), primary_key=True)
    query_text = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    filename_filter = Column(String(255), nullable=True)
    retrieval_ms = Column(Float, nullable=True)
    rerank_ms = Column(Float, nullable=True)
    llm_ms = Column(Float, nullable=True)
    total_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Relational database initialized.")

@contextmanager
def get_db_session():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_document_by_hash(file_hash: str) -> Optional[DocumentRecord]:
    with get_db_session() as session:
        return session.query(DocumentRecord).filter(DocumentRecord.file_hash == file_hash).first()

def get_document_by_filename(filename: str) -> Optional[DocumentRecord]:
    with get_db_session() as session:
        return session.query(DocumentRecord).filter(DocumentRecord.filename == filename).first()

def list_all_documents() -> List[Dict[str, Any]]:
    with get_db_session() as session:
        records = session.query(DocumentRecord).order_by(DocumentRecord.upload_time.desc()).all()
        return [r.to_dict() for r in records]

def upsert_document_record(
    filename: str,
    file_hash: str,
    file_size_bytes: int,
    page_count: int,
    chunk_count: int,
    title: Optional[str] = None,
    status: str = "Indexed",
    error_message: Optional[str] = None,
) -> DocumentRecord:
    with get_db_session() as session:
        record = session.query(DocumentRecord).filter(
            (DocumentRecord.file_hash == file_hash) | (DocumentRecord.filename == filename)
        ).first()
        if record:
            record.filename = filename
            record.file_hash = file_hash
            record.file_size_bytes = file_size_bytes
            record.page_count = page_count
            record.chunk_count = chunk_count
            record.title = title or filename
            record.status = status
            record.error_message = error_message
            record.upload_time = datetime.datetime.utcnow()
        else:
            record = DocumentRecord(
                filename=filename,
                file_hash=file_hash,
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                chunk_count=chunk_count,
                title=title or filename,
                status=status,
                error_message=error_message,
            )
            session.add(record)
        session.flush()
        return record

def delete_document_record(filename: str) -> bool:
    with get_db_session() as session:
        record = session.query(DocumentRecord).filter(DocumentRecord.filename == filename).first()
        if record:
            session.delete(record)
            # Also delete parent chunks
            session.query(ParentChunkRecord).filter(ParentChunkRecord.filename == filename).delete()
            return True
        return False

def save_parent_chunks(parents: List[Dict[str, Any]]):
    """Saves parent section texts for child-to-parent context expansion."""
    if not parents:
        return
    with get_db_session() as session:
        for p in parents:
            existing = session.query(ParentChunkRecord).filter(ParentChunkRecord.parent_id == p["parent_id"]).first()
            if existing:
                existing.text = p["text"]
                existing.section_heading = p.get("section_heading")
                existing.page_number = p.get("page_number", 1)
            else:
                session.add(ParentChunkRecord(
                    parent_id=p["parent_id"],
                    document_id=p["document_id"],
                    filename=p["filename"],
                    page_number=p.get("page_number", 1),
                    section_heading=p.get("section_heading"),
                    content_type=p.get("content_type", "prose"),
                    text=p["text"],
                ))

def get_parent_chunks_by_ids(parent_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetches parent records mapped by parent_id."""
    if not parent_ids:
        return {}
    with get_db_session() as session:
        records = session.query(ParentChunkRecord).filter(ParentChunkRecord.parent_id.in_(parent_ids)).all()
        return {r.parent_id: r.to_dict() for r in records}

def log_query(
    query_id: str,
    query_text: str,
    rewritten_query: Optional[str],
    filename_filter: Optional[str],
    retrieval_ms: float,
    rerank_ms: float,
    llm_ms: float,
    total_ms: float,
):
    try:
        with get_db_session() as session:
            session.add(QueryLogRecord(
                id=query_id,
                query_text=query_text[:1000],
                rewritten_query=(rewritten_query or "")[:1000],
                filename_filter=filename_filter,
                retrieval_ms=retrieval_ms,
                rerank_ms=rerank_ms,
                llm_ms=llm_ms,
                total_ms=total_ms,
            ))
    except Exception as e:
        logger.warning(f"Could not record query log: {e}")
