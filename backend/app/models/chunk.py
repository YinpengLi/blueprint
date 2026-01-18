from sqlalchemy import Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
from app.db import Base

class Chunk(Base):
    __tablename__ = "chunk"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chat_session.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(Text, default="chat")
    chunk_idx: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text)
    tsv: Mapped[object | None] = mapped_column(TSVECTOR, nullable=True)
    embedding: Mapped[object | None] = mapped_column(Vector(1536), nullable=True)
    chat = relationship("ChatSession", back_populates="chunks")
