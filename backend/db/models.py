# path: backend/db/models.py
# version: v0.30
# purpose: アプリ全体で用いるDBモデル定義（副作用なし、スキーマのみ）
from sqlalchemy import Column, Integer, DateTime, Text, Float, JSON, String, Boolean # String をインポート
from sqlalchemy.orm import declarative_base
from datetime import datetime, UTC
from sqlalchemy.dialects.postgresql import ARRAY # Import ARRAY for PostgreSQL specific types

Base = declarative_base()

class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(String, primary_key=True, index=True) # Integer から String に変更
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
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
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    log_persist_failed = Column(Integer, default=0)
    regeneration_attempts = Column(Integer, default=0)
    regeneration_success = Column(Boolean, default=False)
    error_tag = Column(String, nullable=True)
    impact_level = Column(String, nullable=True)

    def __repr__(self):
        return f"<SessionLog(id={self.id}, timestamp={self.created_at}, user_input='{self.user_input[:30]}...')>"

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    prompt = Column(Text)
    result = Column(Text)

    def __repr__(self):
        return f"<Sample(id={self.id}, created_at={self.created_at}, prompt='{self.prompt[:30]}...')>"

class DevLog(Base):
    __tablename__ = "dev_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
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
    interaction_notes = Column(Text)  # シロイとのやり取りなどの自由記述欄
    parent_id = Column(Integer, nullable=True) # New column for hierarchical relationships


class AwarenessSnapshot(Base):
    __tablename__ = "awareness_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    backend_state = Column(JSON)
    frontend_state = Column(JSON)
    robustness_state = Column(JSON)
    awareness_summary = Column(Text)
    context_vector = Column(JSON)


class InternalDialogue(Base):
    __tablename__ = "internal_dialogues"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    participants = Column(JSON)  # e.g., ["創造","理性","感情","意志"]
    transcript = Column(JSON)    # list of {"speaker": str, "message": str}
    insights = Column(Text)
    source_snapshot_id = Column(Integer, nullable=True)
    meta = Column(JSON)


class Chronicle(Base):
    __tablename__ = "chronicles"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    event_date_str = Column(String, nullable=False, index=True) # e.g., "王国暦 105年", "古代魔法時代"
    event_year = Column(Integer, nullable=True, index=True) # For sorting and filtering
    
    title = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    
    tags = Column(JSON, nullable=True) # e.g., {"characters": ["英雄A"], "locations": ["王都"]}
    category = Column(String, nullable=True, index=True) # e.g., "戦争", "政治", "文化"

    def __repr__(self):
        return f"<Chronicle(id={self.id}, event_date_str='{self.event_date_str}', title='{self.title[:30]}...')>"
