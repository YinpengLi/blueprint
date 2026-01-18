from sqlalchemy import Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Message(Base):
    __tablename__ = "message"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chat_session.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(Text)
    idx: Mapped[int] = mapped_column(Integer)
    content_text: Mapped[str] = mapped_column(Text)
    content_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat = relationship("ChatSession", back_populates="messages")
