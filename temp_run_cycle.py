# path: temp_run_cycle.py
# version: 1.0.0
# purpose: Manual driver to run a single context evolution cycle.
import traceback
from orchestrator.main import run_context_evolution_cycle

if __name__ == "__main__":
    try:
        result = run_context_evolution_cycle('テスト: 実回答を返して')
        print('RESULT:', result)
    except Exception as exc:
        print('EXCEPTION:', exc)
        traceback.print_exc()
