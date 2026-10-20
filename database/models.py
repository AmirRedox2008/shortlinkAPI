from sqlalchemy import (Integer, Column, DateTime, ForeignKey,   # 👈 Integer اضافه شد
                        String, Text, func)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class savedb(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)      # 👈 BigInteger → Integer
    short_code = Column(String(20), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)

    click_logs = relationship("ClickLog", back_populates="link",
                              cascade="all, delete-orphan")


class ClickLog(Base):
    __tablename__ = "click_logs"

    id = Column(Integer, primary_key=True, index=True)              # 👈 اینم
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"),
                     nullable=False, index=True)                    # 👈 اینم
    clicked_at = Column(DateTime, server_default=func.now(), index=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referer = Column(String(512), nullable=True)

    link = relationship("savedb", back_populates="click_logs")