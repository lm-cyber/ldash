from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TimeEntry(Base):
    __tablename__ = 'time_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    activity_name = Column(String(255), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    entry_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TimeEntry(id={self.id}, user_id={self.user_id}, activity='{self.activity_name}', duration={self.duration_minutes}min, date={self.entry_date})>" 