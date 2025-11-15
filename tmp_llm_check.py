from orchestrator.context_manager import ContextManager
from modules.generator import generate_response

ctx = ContextManager()
ctx.set('short_term.prompt', '軌道エレベータ修復の進捗を教えて。')
ctx.set('short_term.rag_context', '最新報告ではシパス計画フェーズ3。')
ctx.set('mid_term.chat_history', [])

generate_response(ctx)
print(ctx.get('mid_term.generated_output')[:400])
