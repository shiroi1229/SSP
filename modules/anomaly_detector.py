# path: modules/anomaly_detector.py
# version: R-v1.0

import numpy as np
import collections
from modules.log_manager import log_manager

class AnomalyDetector:
    """
    Detects anomalies in real-time metric series using Z-Score and EWMA.
    """
    def __init__(self, window_size: int = 100, ewma_alpha: float = 0.2):
        self.window_size = window_size
        self.ewma_alpha = ewma_alpha
        self.metric_history = collections.defaultdict(lambda: collections.deque(maxlen=window_size))
        self.ewma_values = collections.defaultdict(float)
        self.consecutive_anomalies = collections.defaultdict(int)

    def update_metric(self, metric_name: str, value: float):
        """
        Updates the history and EWMA for a given metric.
        """
        self.metric_history[metric_name].append(value)
        
        if metric_name not in self.ewma_values or len(self.metric_history[metric_name]) == 1:
            self.ewma_values[metric_name] = value
        else:
            self.ewma_values[metric_name] = (self.ewma_alpha * value) + \
                                             ((1 - self.ewma_alpha) * self.ewma_values[metric_name])

    def detect_anomaly(self, metric_name: str, current_value: float, z_score_threshold: float = 3.0, consecutive_threshold: int = 3) -> dict:
        """
        Detects anomalies for a specific metric using Z-Score and EWMA.
        Returns a dictionary with anomaly details if detected, otherwise None.
        """
        self.update_metric(metric_name, current_value)

        history = list(self.metric_history[metric_name])
        if len(history) < 2: # Need at least 2 data points for std dev
            return None

        mean = self.ewma_values[metric_name] # Use EWMA as the dynamic mean
        std_dev = np.std(history)

        if std_dev == 0: # Avoid division by zero if all values are the same
            return None

        z_score = (current_value - mean) / std_dev

        is_anomaly = abs(z_score) > z_score_threshold

        if is_anomaly:
            self.consecutive_anomalies[metric_name] += 1
            log_manager.warning(f"[AnomalyDetector] Anomaly detected for {metric_name}: value={current_value:.2f}, Z-score={z_score:.2f}, Consecutive={self.consecutive_anomalies[metric_name]}")
            if self.consecutive_anomalies[metric_name] >= consecutive_threshold:
                self.consecutive_anomalies[metric_name] = 0 # Reset after triggering
                return {
                    "metric": metric_name,
                    "value": current_value,
                    "z_score": z_score,
                    "mean": mean,
                    "std_dev": std_dev,
                    "message": f"High anomaly detected for {metric_name} (Z-score: {z_score:.2f}) over {consecutive_threshold} cycles.",
                    "type": "metric_anomaly"
                }
        else:
            self.consecutive_anomalies[metric_name] = 0 # Reset if not anomalous

        return None
