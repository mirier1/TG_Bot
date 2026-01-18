from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    age_group = Column(String) # 'young', 'teen', 'student'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
