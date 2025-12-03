# RAG Evaluation Dataset

This directory stores representative query/answer pairs for offline RAG evaluation.

- `qa_pairs.jsonl`: JSON Lines file where each entry contains a realistic user query, a canonical answer, tags, and supporting contexts used as ground truth.
- `retrieved_contexts` and `model_answer` fields provide a baseline snapshot so evaluation scripts can run even without live RAG connectivity.
- Tags are thematic (e.g., `rag`, `frontend`, `operations`) to help slice results.
