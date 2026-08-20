import sys
import os

# Add the parent directory to sys.path to allow importing 'modules'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.rag_engine import RAGEngine

def test_rag_engine():
    print("--- Testing RAGEngine ---")
    try:
        rag_engine = RAGEngine()
        sample_query = "ナノ博士が火星で眠ってる理由は？"
        context = rag_engine.get_context(sample_query)
        print(f"Query: {sample_query}")
        print(f"Retrieved Context:\n{context}")
    except Exception as e:
        print(f"Error during RAGEngine test: {e}")

if __name__ == "__main__":
    test_rag_engine()
