import uuid
from sqlalchemy import Text, String, Integer, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class ChatSession(Base):
    __tablename__ = "chat_session"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    root_id: Mapped[uuid.UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, index=True)

    title: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text, index=True)
    captured_at: Mapped[str] = mapped_column(Text)

    project: Mapped[str | None] = mapped_column(String(200), nullable=True)
    area: Mapped[str | None] = mapped_column(String(200), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    storage_raw_path: Mapped[str] = mapped_column(Text, default="")
    storage_note_path: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(Text, default="")

    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="chat", cascade="all, delete-orphan")
    files = relationship("FileAsset", back_populates="chat", cascade="all, delete-orphan")
