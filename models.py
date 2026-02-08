from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey, UniqueConstraint
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
    difficulty = Column(String)
    age_group = Column(String)  # ← ДОБАВЛЯЕМ
    score = Column(Integer)
    total = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Обновляем уникальный индекс
    __table_args__ = (
        UniqueConstraint('user_id', 'sdg_id', 'difficulty', 'age_group', 
                       name='uq_user_sdg_diff_age'),
    )

class GameResult(Base):
    __tablename__ = "game_results"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    game_type = Column(String)  # 'waste', 'habits', 'rightwrong', 'story'
    age_group = Column(String)  # 'young', 'teen', 'student'
    difficulty = Column(String, nullable=True)  # Если в играх будет сложность
    score = Column(Integer)  # Общий счет
    max_score = Column(Integer)  # Максимально возможный
    steps_completed = Column(Integer)  # Сколько шагов пройдено
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'game_type', 'age_group', name='uq_user_game_age'),
    )