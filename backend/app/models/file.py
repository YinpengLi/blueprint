from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class FileAsset(Base):
    __tablename__ = "file_asset"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[str | None] = mapped_column(ForeignKey("chat_session.id", ondelete="SET NULL"), index=True, nullable=True)
    filename: Mapped[str] = mapped_column(Text)
    mime: Mapped[str] = mapped_column(Text, default="application/octet-stream")
    storage_path: Mapped[str] = mapped_column(Text, default="")
    sha256: Mapped[str] = mapped_column(Text, default="")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat = relationship("ChatSession", back_populates="files")
