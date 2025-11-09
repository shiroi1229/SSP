# path: backend/db/models.py
# version: v0.30
from sqlalchemy import Column, Integer, DateTime, Text, Float, JSON, String # String をインポート
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY # Import ARRAY for PostgreSQL specific types

Base = declarative_base()

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(String, primary_key=True, index=True) # Integer から String に変更
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user_input = Column(Text)
    final_output = Column(Text)
    evaluation_score = Column(Float)
    evaluation_comment = Column(Text)
    workflow_trace = Column(JSON) # Store as JSON
    context = Column(Text) # Add context
    generator_prompt = Column(Text) # Add generator_prompt
    generator_response = Column(Text) # Add generator_response
    commit_hash = Column(String(40))
    env_snapshot = Column(Text)
    ai_comment = Column(Text)

    def __repr__(self):
        return f"<SessionLog(id={self.id}, timestamp={self.created_at}, user_input='{self.user_input[:30]}...')>"

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    prompt = Column(Text)
    result = Column(Text)

    def __repr__(self):
        return f"<Sample(id={self.id}, created_at={self.created_at}, prompt='{self.prompt[:30]}...')>"

class DevLog(Base):
    __tablename__ = "dev_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    type = Column(String(32))
    summary = Column(Text)
    file_path = Column(Text)
    tags = Column(JSON) # TEXT[] in PostgreSQL, but JSON in SQLAlchemy for flexibility
    author = Column(String(32))
    commit_hash = Column(String(40)) # SHA1 hash is 40 chars
    env_snapshot = Column(Text)
    execution_trace = Column(JSON)
    ai_comment = Column(Text)

    def __repr__(self):
        return f"<DevLog(id={self.id}, type='{self.type}', summary='{self.summary[:50]}...')>"

class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, index=True, nullable=False)
    codename = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, nullable=False) # "✅" | "🔄" | "⚪"
    description = Column(Text, nullable=False)
    startDate = Column(String) # YYYY-MM-DD
    endDate = Column(String)   # YYYY-MM-DD
    progress = Column(Integer)  # 0-100 percentage
    keyFeatures = Column(ARRAY(String))
    dependencies = Column(ARRAY(String))
    metrics = Column(ARRAY(String))
    owner = Column(String)
    documentationLink = Column(String)
    prLink = Column(String)
    development_details = Column(Text)
    parent_id = Column(Integer, nullable=True) # New column for hierarchical relationships
