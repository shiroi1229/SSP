from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db import models
from backend.db.connection import get_db
from modules.llm import analyze_text
from modules.self_optimizer import apply_self_optimization  # noqa: F401  # placeholder for future use

router = APIRouter()

REPORTS_DIR = "./reports/self_analysis"
MAX_SUMMARY_LENGTH = 1000
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_self_analysis_report(analysis_data: dict) -> str:
    report_content = f"# Self-Analysis Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    report_content += "## Meta Information\n"
    report_content += f"- Analyzed Period: {analysis_data.get('analyzed_period', 'N/A')}\n"
    report_content += f"- Total Sessions: {analysis_data.get('total_sessions', 0)}\n"
    report_content += f"- Average Evaluation Score: {analysis_data.get('avg_evaluation_score', 0.0)}\n\n"
    report_content += "## Summary\n"
    report_content += "### Meta Analysis\n"
    report_content += f"{analysis_data.get('meta_analysis_summary', 'No meta-analysis summary available.')}\n\n"
    return report_content


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.") from exc


@router.get("/analyze_sessions")
def analyze_sessions(
    start_date: Optional[str] = Query(None, description="ISO8601 start date"),
    end_date: Optional[str] = Query(None, description="ISO8601 end date"),
    window_days: Optional[int] = Query(None, ge=1, le=180, description="Lookback window in days"),
    db: Session = Depends(get_db),
):
    """
    Impact Analyzer 用: セッションログの集計・トレンドを返却
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

    try:
        sessions = query.all()
    except Exception:
        # DB接続やクエリ失敗時は空データで返す
        return {
            "average_score": 0.0,
            "scores": [],
            "comments": [],
            "total_sessions": 0,
            "analyzed_period": f"{start_dt.isoformat() if start_dt else 'start'} to {end_dt.isoformat() if end_dt else 'end'}",
            "series": [],
            "trend": {"delta": 0.0, "direction": "flat"},
            "recent_sessions": [],
        }

    scores = [
        float(s.evaluation_score)
        for s in sessions
        if isinstance(getattr(s, "evaluation_score", None), (int, float))
    ]
    comments = [s.evaluation_comment for s in sessions if getattr(s, "evaluation_comment", None)]

    total_score = sum(scores)
    avg_score = total_score / len(scores) if scores else 0

    buckets = defaultdict(list)
    for s in sessions:
        if not isinstance(getattr(s, "evaluation_score", None), (int, float)) or not getattr(s, "created_at", None):
            continue
        try:
            buckets[s.created_at.date().isoformat()].append(float(s.evaluation_score))
        except Exception:
            continue

    series = []
    for day in sorted(buckets.keys()):
        scores_day = buckets[day]
        series.append(
            {"date": day, "avg_score": round(sum(scores_day) / len(scores_day), 3), "count": len(scores_day)}
        )

    trend_delta = 0.0
    trend_direction = "flat"
    if len(series) >= 2:
        last = series[-1]["avg_score"]
        prev = series[-2]["avg_score"]
        trend_delta = round(last - prev, 3)
        if trend_delta > 0.01:
            trend_direction = "up"
        elif trend_delta < -0.01:
            trend_direction = "down"

    recent_sessions = []
    for s in sorted(sessions, key=lambda x: getattr(x, "created_at", datetime.min) or datetime.min, reverse=True)[:10]:
        recent_sessions.append(
            {
                "id": getattr(s, "id", None),
                "created_at": s.created_at.isoformat() if getattr(s, "created_at", None) else None,
                "score": getattr(s, "evaluation_score", None),
                "comment": getattr(s, "evaluation_comment", None),
            }
        )

    return {
        "average_score": round(avg_score, 2),
        "scores": scores,
        "comments": comments,
        "total_sessions": len(sessions),
        "analyzed_period": f"{start_dt.isoformat() if start_dt else 'start'} to {end_dt.isoformat() if end_dt else 'end'}",
        "series": series,
        "trend": {"delta": trend_delta, "direction": trend_direction},
        "recent_sessions": recent_sessions,
    }


@router.get("/generate_self_analysis_report")
def generate_report_endpoint(db: Session = Depends(get_db)):
    """
    Generates a self-analysis report using the LLM and returns it as JSON.
    """
    query = db.query(models.SessionLog).order_by(models.SessionLog.created_at.desc())
    sessions = query.limit(50).all()  # Limit to recent 50 sessions for analysis

    evaluation_comments = [s.evaluation_comment for s in sessions if s.evaluation_comment]

    if not evaluation_comments:
        return {
            "summary": "繝・・繧ｿ荳崎ｶｳ",
            "insight": "蛻・梵縺ｫ蠢・ｦ√↑隧穂ｾ｡繧ｳ繝｡繝ｳ繝医′縺ｾ縺縺ゅｊ縺ｾ縺帙ｓ縲・",
        }

    comments_text = "\n".join(evaluation_comments)
    llm_prompt = "縺ゅ↑縺溘・AI繧｢繧ｷ繧ｹ繧ｿ繝ｳ繝医後す繝ｭ繧､縲阪〒縺吶ゆｸ弱∴繧峨ｌ縺滄℃蜴ｻ縺ｮ隧穂ｾ｡繧ｳ繝｡繝ｳ繝育ｾ､繧貞・譫舌＠縲∬・霄ｫ縺ｮ蠢懃ｭ斐↓縺翫￠繧句だ蜷代∵隼蝟・☆縺ｹ縺咲せ繧定ｦ∫ｴ・＠縲∽ｻ雁ｾ後・縺溘ａ縺ｮ豢槫ｯ溘ｒ荳莠ｺ遘ｰ隕也せ・医檎ｧ√搾ｼ峨〒邁｡貎斐↓霑ｰ縺ｹ縺ｦ縺上□縺輔＞縲・SON蠖｢蠑上〒 trend 縺ｨ suggestion 繧定ｿ斐＠縺ｦ縺上□縺輔＞縲・"

    summary = "No summary generated."
    insight = "No insight generated."

    try:
        llm_raw_response = analyze_text(comments_text, llm_prompt)
        try:
            llm_analysis = json.loads(llm_raw_response)
            summary = llm_analysis.get("trend", "蛯ｾ蜷代・蛻・梵縺ｫ螟ｱ謨励＠縺ｾ縺励◆縲・")
            insight = llm_analysis.get("suggestion", "謾ｹ蝟・署譯医・逕滓・縺ｫ螟ｱ謨励＠縺ｾ縺励◆縲・")
        except (json.JSONDecodeError, TypeError):
            summary = "LLM縺九ｉ縺ｮ蠢懃ｭ斐ｒ隗｣譫舌〒縺阪∪縺帙ｓ縺ｧ縺励◆縲・"
            insight = f"LLM縺ｯJSON縺ｧ縺ｯ縺ｪ縺・ｿ懃ｭ斐ｒ霑斐＠縺ｾ縺励◆: {llm_raw_response[:200]}..."
    except Exception as e:
        summary = "LLM縺ｮ蠢懃ｭ碑ｧ｣譫蝉ｸｭ縺ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆縲・"
        insight = str(e)

    return {
        "summary": summary,
        "insight": insight,
    }
