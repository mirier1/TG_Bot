from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, UniqueConstraint
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
    user_id = Column(BigInteger)
    user_name = Column(String)
    message_id = Column(BigInteger)
    admin_chat_message_id = Column(BigInteger)
    text = Column(Text)
    status = Column(String, default='pending')
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

class QuizResult(Base):
    __tablename__ = "quiz_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    sdg_id = Column(Integer)
    difficulty = Column(String)
    age_group = Column(String) 
    score = Column(Integer)
    total = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
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
    difficulty = Column(String, nullable=True)
    score = Column(Integer)
    max_score = Column(Integer)
    steps_completed = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'game_type', 'age_group', name='uq_user_game_age'),
    )

class AmbassadorApplication(Base):
    __tablename__ = "ambassador_applications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    full_name = Column(String)
    age = Column(Integer)
    institution = Column(String)
    city = Column(String)
    contact = Column(String)
    role = Column(String)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    sdg_id = Column(Integer, nullable=True)
    usefulness = Column(Integer)
    interest = Column(Integer)
    clarity = Column(Integer)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Новая модель для сохранений сюжетной игры
class StorySave(Base):
    __tablename__ = "story_saves"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    save_data = Column(Text)  # JSON с данными сохранения
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_story_save'),
    )