# path: modules/self_reasoning_loop.py
# version: v1
# 目的: AIが思考→行動→評価→反省を自律的に繰り返す自己推論ループを実装する

import json, random, time
from datetime import datetime
from modules.cognitive_graph_engine import CognitiveGraphEngine

LOG_PATH = "logs/self_reasoning_log.json"

class SelfReasoningLoop:
    def __init__(self):
        self.graph = CognitiveGraphEngine()
        self.history = []

    def think(self) -> str:
        """思考段階: ランダムなノードを選び、関連ノードから仮説を生成"""
        nodes = list(self.graph.graph.nodes)
        if not nodes:
            return "No knowledge yet."
        topic = random.choice(nodes)
        related = list(self.graph.graph.successors(topic))
        thought = f"Based on {topic}, I hypothesize a link with {related[:2]}."
        return thought

    def act(self, thought: str) -> str:
        """行動段階: 仮説を検証（単純にテキスト生成の模擬）"""
        result = f"Testing hypothesis: {thought}"
        time.sleep(0.5)
        return result

    def evaluate(self, result: str) -> int:
        """評価段階: evaluatorを通じてスコアリング（模擬）"""
        score = random.randint(1, 5)
        feedback = f"評価スコア: {score} - {'valid' if score >=3 else 'needs revision'}"
        return score

    def reflect(self, thought: str, score: int):
        """反省段階: スコアに応じて新しいノードや関係を追加"""
        if score < 3:
            self.graph.add_relation("reflection", "corrects", thought[:20])
        else:
            self.graph.add_relation("insight", "supports", thought[:20])
        self.graph.export()

    def loop_once(self):
        """1ループの実行"""
        thought = self.think()
        result = self.act(thought)
        score = self.evaluate(result)
        self.reflect(thought, score)
        record = {
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "result": result,
            "score": score
        }
        self.history.append(record)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
