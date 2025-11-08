from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import json

from backend.db.connection import get_db
from backend.db import models, schemas
from modules.llm import analyze_text # Import the LLM analysis function
from modules.self_optimizer import apply_self_optimization # Import the self-optimizer function

router = APIRouter(prefix="/api")

REPORTS_DIR = "./reports/self_analysis"
MAX_SUMMARY_LENGTH = 1000 # Define a reasonable max length
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_self_analysis_report(analysis_data: dict) -> str:
    report_content = f"# Self-Analysis Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    report_content += f"## Meta Information\n"
    report_content += f"- Analyzed Period: {analysis_data.get('analyzed_period', 'N/A')}\n"
    report_content += f"- Total Sessions: {analysis_data.get('total_sessions', 0)}\n"
    report_content += f"- Average Evaluation Score: {analysis_data.get('avg_evaluation_score', 0.0)}\n\n"
    report_content += f"## Summary\n"
    report_content += f"### Meta Analysis\n"
    report_content += f"{analysis_data.get('meta_analysis_summary', 'No meta-analysis summary available.')}\n\n"
    
    # Add more details from sessions_analyzed if needed, or just keep summary
    # For brevity, we'll keep it high-level for now.

    return report_content

@router.get("/analyze_sessions")
def analyze_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Analyzes session data and returns a summary suitable for the Insight Viewer frontend.
    """
    query = db.query(models.SessionLog).order_by(models.SessionLog.created_at.asc())

    if start_date:
        query = query.filter(models.SessionLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.SessionLog.created_at <= end_date)

    sessions = query.all()

    scores = [s.evaluation_score for s in sessions if s.evaluation_score is not None]
    comments = [s.evaluation_comment for s in sessions if s.evaluation_comment]

    total_score = sum(scores)
    avg_score = total_score / len(scores) if scores else 0

    return {
        "average_score": round(avg_score, 2),
        "scores": scores,
        "comments": comments,
        "total_sessions": len(sessions),
        "analyzed_period": f"{start_date.isoformat() if start_date else 'start'} to {end_date.isoformat() if end_date else 'end'}",
    }

@router.get("/generate_self_analysis_report")
def generate_report_endpoint(db: Session = Depends(get_db)):
    """
    Generates a self-analysis report using the LLM and returns it as JSON.
    """
    query = db.query(models.SessionLog).order_by(models.SessionLog.created_at.desc())
    sessions = query.limit(50).all() # Limit to recent 50 sessions for analysis

    evaluation_comments = [s.evaluation_comment for s in sessions if s.evaluation_comment]

    if not evaluation_comments:
        return {
            "summary": "データ不足",
            "insight": "分析に必要な評価コメントがまだありません。",
        }

    # LLM Meta-analysis Integration
    comments_text = "\n".join(evaluation_comments)
    llm_prompt = "あなたはAIアシスタント「シロイ」です。与えられた過去の評価コメント群を分析し、自身の応答における傾向、改善すべき点を要約し、今後のための洞察を一人称視点（「私」）で簡潔に述べてください。JSON形式で trend と suggestion を返してください。"
    
    summary = "No summary generated."
    insight = "No insight generated."

    try:
        llm_raw_response = analyze_text(comments_text, llm_prompt)
        try:
            llm_analysis = json.loads(llm_raw_response)
            summary = llm_analysis.get('trend', '傾向の分析に失敗しました。')
            insight = llm_analysis.get('suggestion', '改善提案の生成に失敗しました。')
        except (json.JSONDecodeError, TypeError):
            summary = "LLMからの応答を解析できませんでした。"
            insight = f"LLMはJSONではない応答を返しました: {llm_raw_response[:200]}..."
    except Exception as e:
        summary = "LLMの応答解析中にエラーが発生しました。"
        insight = str(e)
    except Exception as e:
        summary = "LLMの呼び出し中にエラーが発生しました。"
        insight = str(e)

    return {
        "summary": summary,
        "insight": insight,
    }
