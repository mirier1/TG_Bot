from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    age_group = Column(String) # 'young', 'teen', 'student'
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)  # ID пользователя задавшего вопрос
    user_name = Column(String)    # Имя пользователя (для удобства)
    message_id = Column(BigInteger)  # ID сообщения с вопросом в чате пользователя
    admin_chat_message_id = Column(BigInteger)  # ID сообщения в админ-чате
    text = Column(Text)  # Текст вопроса
    status = Column(String, default='pending')  # pending/answered/rejected
    answer = Column(Text, nullable=True)  # Ответ админа
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    sdg_id = Column(Integer)
    score = Column(Integer)  # сколько правильных
    total = Column(Integer)  # сколько всего вопросов
    created_at = Column(DateTime, default=datetime.utcnow)