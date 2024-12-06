from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class ErrorLog(Base):
    __tablename__ = 'error_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    user_id = Column(String(255), nullable=False) 
    method_name = Column(String(255), nullable=False)
    error_message = Column(String(1000), nullable=False)

    def __repr__(self):
        return f"<ErrorLog(id={self.id}, method_name='{self.method_name}', timestamp='{self.timestamp}')>"
