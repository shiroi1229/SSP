from __future__ import annotations

from datetime import datetime, timedelta
import json
import os
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.session_summary import build_session_summary
from backend.db import models
from backend.db.connection import get_db
from modules.llm import analyze_text
from modules.self_optimizer import apply_self_optimization  # noqa: F401  # placeholder for future use

router = APIRouter()

REPORTS_DIR = "./reports/self_analysis"
MAX_SUMMARY_LENGTH = 1000
os.makedirs(REPORTS_DIR, exist_ok=True)


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.") from exc


def _classify_emotion(score: float) -> str:
    if score >= 4.0:
        return "positive"
    if score >= 3.0:
        return "neutral"
    return "negative"


def generate_self_analysis_report(analysis_data: Dict[str, Any]) -> str:
    """
    Build a Markdown self-analysis report with sections:
    Summary / Emotion Trends / Performance / Improvement Plan.
    """
    report_content = f"# Self-Analysis Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"

    report_content += "## Summary\n"
    report_content += f"- Analyzed Period: {analysis_data.get('analyzed_period', 'N/A')}\n"
    report_content += f"- Total Sessions: {analysis_data.get('total_sessions', 0)}\n"
    report_content += f"- Average Evaluation Score: {analysis_data.get('avg_evaluation_score', 0.0):.2f}\n\n"

    report_content += "## Emotion Trends\n"
    emotion_stats = analysis_data.get("emotion_summary") or {}
    if emotion_stats:
        for label, value in emotion_stats.items():
            report_content += f"- {label}: {value} sessions\n"
    else:
        report_content += "- No emotion trend data available.\n"
    report_content += "\n"

    report_content += "## Performance\n"
    trend = analysis_data.get("trend") or {}
    delta = trend.get("delta")
    direction = trend.get("direction", "flat")
    report_content += f"- Trend: {direction} (Δ={delta})\n"
    report_content += f"- Series points: {len(analysis_data.get('series', []))}\n\n"

    report_content += "## Improvement Plan\n"
    avg_score = analysis_data.get("avg_evaluation_score", 0.0)
    if avg_score < 3.0:
        plan = "Focus on clarity and grounding; increase regeneration attempts for low-scoring sessions."
    elif avg_score < 4.5:
        plan = "Maintain current style but watch for drift; review sessions with sharp drops in score."
    else:
        plan = "Performance is strong; capture best sessions as exemplars and gradually tighten parameters."
    report_content += f"- Plan: {plan}\n"

    meta_summary = analysis_data.get("meta_analysis_summary")
    if meta_summary:
        report_content += f"\n### Meta Analysis Notes\n{meta_summary}\n"

    return report_content


@router.get("/analyze_sessions")
def analyze_sessions(
    start_date: Optional[str] = Query(None, description="ISO8601 start date"),
    end_date: Optional[str] = Query(None, description="ISO8601 end date"),
    window_days: Optional[int] = Query(None, ge=1, le=180, description="Lookback window in days"),
    db: Session = Depends(get_db),
):
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    if window_days and not end_dt:
        end_dt = datetime.utcnow()
    if window_days and not start_dt and end_dt:
        start_dt = end_dt - timedelta(days=window_days)

    query = db.query(models.SessionLog).order_by(models.SessionLog.created_at.asc())

    if start_dt:
        query = query.filter(models.SessionLog.created_at >= start_dt)
    if end_dt:
        query = query.filter(models.SessionLog.created_at <= end_dt)

    try:
        sessions: List[models.SessionLog] = query.all()
    except Exception:
        analyzed_period = f"{start_dt.isoformat() if start_dt else 'start'} to {end_dt.isoformat() if end_dt else 'end'}"
        return {
            "average_score": 0.0,
            "scores": [],
            "comments": [],
            "total_sessions": 0,
            "analyzed_period": analyzed_period,
            "series": [],
            "trend": {"delta": 0.0, "direction": "flat"},
            "recent_sessions": [],
            "emotion_summary": {},
        }

    scores: List[float] = [
        float(s.evaluation_score)
        for s in sessions
        if isinstance(getattr(s, "evaluation_score", None), (int, float))
    ]
    comments = [s.evaluation_comment for s in sessions if getattr(s, "evaluation_comment", None)]

    summary = build_session_summary(sessions)

    emotion_summary = {"positive": 0, "neutral": 0, "negative": 0}
    for score in scores:
        emotion_summary[_classify_emotion(score)] += 1

    recent_sessions: List[Dict[str, Any]] = []
    for s in sorted(
        sessions, key=lambda x: getattr(x, "created_at", datetime.min) or datetime.min, reverse=True
    )[:10]:
        recent_sessions.append(
            {
                "id": getattr(s, "id", None),
                "created_at": s.created_at.isoformat() if getattr(s, "created_at", None) else None,
                "score": getattr(s, "evaluation_score", None),
                "comment": getattr(s, "evaluation_comment", None),
            }
        )

    analyzed_period = f"{start_dt.isoformat() if start_dt else 'start'} to {end_dt.isoformat() if end_dt else 'end'}"

    return {
        "average_score": summary["average_score"],
        "scores": scores,
        "comments": comments,
        "total_sessions": summary["total_sessions"],
        "analyzed_period": analyzed_period,
        "series": summary["series"],
        "trend": summary["trend"],
        "recent_sessions": recent_sessions,
        "emotion_summary": emotion_summary,
    }


@router.get("/generate_self_analysis_report")
def generate_report_endpoint(
    start_date: Optional[str] = Query(None, description="ISO8601 start date"),
    end_date: Optional[str] = Query(None, description="ISO8601 end date"),
    window_days: Optional[int] = Query(7, ge=1, le=180, description="Lookback window in days"),
    db: Session = Depends(get_db),
):
    """
    Generates a self-analysis report and persists it under /reports/self_analysis
    in both Markdown and HTML formats.
    """
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    if window_days and not end_dt:
        end_dt = datetime.utcnow()
    if window_days and not start_dt and end_dt:
        start_dt = end_dt - timedelta(days=window_days)

    query = db.query(models.SessionLog).order_by(models.SessionLog.created_at.asc())
    if start_dt:
        query = query.filter(models.SessionLog.created_at >= start_dt)
    if end_dt:
        query = query.filter(models.SessionLog.created_at <= end_dt)

    sessions: List[models.SessionLog] = query.all()
    if not sessions:
        return {
            "summary": "No sessions available for analysis.",
            "insight": "Try again after more conversations have been logged.",
        }

    summary = build_session_summary(sessions)
    scores: List[float] = [
        float(s.evaluation_score)
        for s in sessions
        if isinstance(getattr(s, "evaluation_score", None), (int, float))
    ]
    emotion_summary = {"positive": 0, "neutral": 0, "negative": 0}
    for score in scores:
        emotion_summary[_classify_emotion(score)] += 1

    analyzed_period = f"{start_dt.isoformat() if start_dt else 'start'} to {end_dt.isoformat() if end_dt else 'end'}"
    analysis_data: Dict[str, Any] = {
        "analyzed_period": analyzed_period,
        "total_sessions": summary["total_sessions"],
        "avg_evaluation_score": summary["average_score"],
        "trend": summary["trend"],
        "series": summary["series"],
        "emotion_summary": emotion_summary,
    }

    evaluation_comments = [s.evaluation_comment for s in sessions if s.evaluation_comment]
    insight = "No evaluation comments available for meta-analysis."
    if evaluation_comments:
        comments_text = "\n".join(evaluation_comments)[:MAX_SUMMARY_LENGTH]
        llm_prompt = (
            "Analyze the following evaluation comments from the perspective of trend and suggestions. "
            "Return JSON with keys 'trend' and 'suggestion'."
        )
        try:
            llm_raw_response = analyze_text(comments_text, llm_prompt)
            try:
                llm_analysis = json.loads(llm_raw_response)
                analysis_data["meta_analysis_summary"] = llm_analysis.get("trend")
                insight = llm_analysis.get("suggestion", insight)
            except (json.JSONDecodeError, TypeError):
                insight = llm_raw_response[:MAX_SUMMARY_LENGTH]
        except Exception as exc:  # pragma: no cover
            insight = str(exc)

    markdown_report = generate_self_analysis_report(analysis_data)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(REPORTS_DIR, f"self_analysis_{timestamp_str}.md")
    html_path = os.path.join(REPORTS_DIR, f"self_analysis_{timestamp_str}.html")

    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_report)

    html_content = (
        "<html><head><meta charset='utf-8'><title>Self-Analysis Report</title></head>"
        "<body><pre>"
        + markdown_report
        + "</pre></body></html>"
    )
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

    return {
        "summary": markdown_report[:MAX_SUMMARY_LENGTH],
        "insight": insight,
        "report_markdown_path": md_path,
        "report_html_path": html_path,
        "analysis": analysis_data,
    }

