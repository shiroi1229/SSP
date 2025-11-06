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

router = APIRouter()

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
    module: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyzes session data based on specified criteria.
    If `start_date` and `end_date` are both None, all available sessions will be analyzed.
    """
    query = db.query(models.SessionLog)

    if start_date:
        query = query.filter(models.SessionLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.SessionLog.created_at <= end_date)
    if module:
        # TODO: For improved accuracy, consider adding a dedicated 'module_name' field to SessionLog
        # and filtering on that. Currently, it filters on workflow_trace which might be less precise.
        query = query.filter(models.SessionLog.workflow_trace.contains(module))

    sessions = query.all()
    # TODO: For very large datasets, consider implementing pagination (e.g., using limit and offset)
    # to avoid high memory load from query.all().

    total_sessions = len(sessions)
    total_score = 0
    scored_sessions = 0
    
    evaluation_comments = []
    for session in sessions:
        if session.evaluation_score is not None:
            total_score += session.evaluation_score
            scored_sessions += 1
        if session.evaluation_comment:
            evaluation_comments.append(session.evaluation_comment)

    avg_score = total_score / scored_sessions if scored_sessions > 0 else 0

    # LLM Meta-analysis Integration
    meta_analysis_summary = "Based on the current data, the system shows consistent performance in session handling. Further analysis by a large language model would identify specific trends in evaluation comments and workflow traces to suggest improvements."
    if evaluation_comments:
        comments_text = "\n".join(evaluation_comments)
        llm_prompt = "過去の評価コメントの傾向を要約し、改善提案を出して"
        try:
            llm_raw_response = analyze_text(comments_text, llm_prompt)
            try:
                llm_analysis = json.loads(llm_raw_response)
                meta_analysis_summary = f"LLM Analysis:\n  Trend: {llm_analysis.get('trend', 'N/A')}\n  Suggestion: {llm_analysis.get('suggestion', 'N/A')}"
            except json.JSONDecodeError:
                meta_analysis_summary = f"LLM returned non-JSON response. Raw: {llm_raw_response[:200]}..."
            except Exception as e:
                meta_analysis_summary = f"LLM analysis failed: {e}. Default summary used."
        except Exception as e:
            meta_analysis_summary = f"LLM analysis failed during analyze_text: {e}. Default summary used."
    
    # TODO: Future Improvement: Add a "confidence" score to meta_analysis_summary so that Collective Optimizer
    # can use weighted averaging for further evolution.
    # TODO: Future Improvement: Add a retry routine for cases where LLM output is non-JSON for increased stability.
    # Truncate meta_analysis_summary if it's too long
    MAX_SUMMARY_LENGTH = 1000 # Define a reasonable max length
    if len(meta_analysis_summary) > MAX_SUMMARY_LENGTH:
        meta_analysis_summary = meta_analysis_summary[:MAX_SUMMARY_LENGTH - 3] + "..."

    return {
        "message": "Session analysis complete",
        "analyzed_period": f"{start_date.isoformat()} to {end_date.isoformat()}" if start_date and end_date else "all available data",
        "total_sessions": total_sessions,
        "avg_evaluation_score": round(avg_score, 2),
        "meta_analysis_summary": meta_analysis_summary,
        "sessions_analyzed": [
            {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "user_input": session.user_input,
                "evaluation_score": session.evaluation_score,
                "evaluation_comment": session.evaluation_comment,
                "workflow_trace": session.workflow_trace # This might be large, consider truncating for summary
            } for session in sessions
        ]
    }

@router.get("/generate_self_analysis_report")
def generate_report_endpoint(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    module: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Generates a self-analysis report and saves it as a Markdown file.
    """
    analysis_results = analyze_sessions(start_date, end_date, module, db)
    report_content = generate_self_analysis_report(analysis_results)
    
    report_filename = os.path.join(REPORTS_DIR, f"self_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    # Call the self-optimizer after generating the report
    optimization_result = apply_self_optimization(report_filename)

    return {"message": "Self-analysis report generated and saved", "filename": report_filename, "params_updated": optimization_result.get("params", {})}
