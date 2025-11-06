# path: orchestrator/context_layers.py
# version: v2.4

class BaseContextLayer:
    def __init__(self, history_recorder, layer_name):
        self._data = {}
        self.history_recorder = history_recorder
        self.layer_name = layer_name

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value: any, reason: str):
        old_value = self._data.get(key)
        self._data[key] = value
        if self.history_recorder:
            self.history_recorder.record_change(self.layer_name, key, old_value, value, reason)

    def get_full_layer(self) -> dict:
        return self._data

class LongTermContext(BaseContextLayer):
    def __init__(self, history_recorder):
        super().__init__(history_recorder, 'long_term')

class MidTermContext(BaseContextLayer):
    def __init__(self, history_recorder):
        super().__init__(history_recorder, 'mid_term')

class ShortTermContext(BaseContextLayer):
    def __init__(self, history_recorder):
        super().__init__(history_recorder, 'short_term')