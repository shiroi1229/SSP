import os
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db.models import RoadmapItem
from modules.config_manager import load_environment

def update_v1_0_status():
    # Load environment variables
    config = load_environment()

    # Construct the database URL using loaded config
    DATABASE_URL = (
        f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@"
        f"{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DB']}"
    )

    # Create the SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

    # Create a SessionLocal class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        # Find the v1.0 roadmap item
        item = db.query(RoadmapItem).filter(RoadmapItem.version == "v1.0").first()

        if not item:
            print("v1.0 roadmap item not found.")
            return

        # Update the status, progress, and keyFeatures
        item.status = "🔄"  # In progress
        item.progress = 50  # Based on the manual assessment
        new_key_features = [
            "backend/api/analyze_sessions.py — 自己分析の中核。過去セッションを走査し、平均スコア・感情傾向・トピック頻度を算出。",
            "backend/api/analyze_sessions.py — レポート生成。分析結果をMarkdown形式に変換。",
            "backend/api/analyze_sessions.py — 評価データをtimestamp順に並べ、スコア分布を算出。",
            "backend/api/analyze_sessions.py — session_logから感情値・応答文・評価スコアを統合抽出。",
            "backend/api/analyze_sessions.py — GET /api/analyze_sessionsエンドポイントでレポートをJSON出力。",
            "Not Implemented — 可視化UI。感情バランス、回答品質推移を表示。"
        ]
        item.keyFeatures = new_key_features

        # Commit the changes
        db.commit()
        print("Successfully updated v1.0 status, progress, and keyFeatures in the database.")

    except Exception as e:
        db.rollback()
        print(f"Error updating v1.0: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_v1_0_status()
