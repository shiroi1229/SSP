# path: orchestrator/insight_monitor.py
# version: v2.6

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collections
import json
import os
import argparse
import random
import numpy as np

from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.policy_scheduler import PolicyScheduler
from modules.log_manager import log_manager

class TimeSeriesBuffer:
    """Maintain rolling historical data for anomaly metrics."""
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.metrics = collections.defaultdict(lambda: collections.deque(maxlen=self.window_size))
        log_manager.info(f"[TimeSeriesBuffer] Initialized with window size {self.window_size}")

    def add_point(self, metric_name: str, value: float):
        """Adds a data point to a specified metric's time series."""
        if value is not None:
            self.metrics[metric_name].append(value)
            log_manager.debug(f"[TimeSeriesBuffer] Updated {metric_name}: {list(self.metrics[metric_name])}")

    def get_series(self, metric_name: str) -> list[float]:
        """Returns the entire time series for a given metric."""
        return list(self.metrics[metric_name])

    def to_json(self, path: str):
        """Exports the current time series data to a JSON file."""
        log_manager.info(f"[TimeSeriesBuffer] Exporting time series to {path}")
        # Convert deques to lists for JSON serialization
        export_data = {key: list(series) for key, series in self.metrics.items()}
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
        except IOError as e:
            log_manager.error(f"[TimeSeriesBuffer] Failed to export time series to {path}: {e}", exc_info=True)

class PredictiveRepairModel:
    """Forecasts anomaly probability using simple time-series analysis."""
    def __init__(self):
        self.model_trained = False

    def predict(self, metric_series: list[float]) -> float:
        """
        Predicts the probability of an anomaly based on the trend of a metric series.
        Uses simple exponential smoothing.
        """
        if len(metric_series) < 5: # Need at least a few data points
            return 0.0

        # Simple exponential smoothing (alpha can be tuned)
        alpha = 0.4
        smoothed = [metric_series[0]]
        for i in range(1, len(metric_series)):
            smoothed.append(alpha * metric_series[i] + (1 - alpha) * smoothed[-1])
        
        # Predict the next point
        forecast = alpha * metric_series[-1] + (1 - alpha) * smoothed[-1]

        # Calculate risk: higher negative slope -> higher risk
        # Compare forecast to the recent average
        recent_avg = np.mean(metric_series[-5:])
        
        # Risk is scaled by how much the forecast drops below the recent average
        risk = 0.0
        if forecast < recent_avg:
            risk = min(1.0, (recent_avg - forecast) / (recent_avg + 1e-6)) # Normalize, avoid division by zero
        
        log_manager.debug(f"[PredictiveRepair] Series: {metric_series}, Smoothed: {smoothed}, Forecast: {forecast:.2f}, Risk: {risk:.2f}")
        return risk

    def detect_future_anomaly(self, threshold: float = 0.4) -> bool:
        """Placeholder for a more complex anomaly detection logic."""
        # This method is not directly used in the current integration but is kept for future use.
        return self.predict([]) > threshold

    def train_from_history(self, time_series_path: str):
        """Placeholder for training the model from historical data."""
        log_manager.info(f"[PredictiveRepair] 'Training' from {time_series_path}... (currently a no-op)")
        # In a real scenario, this would load data and fit a model (e.g., ARIMA, LSTM)
        self.model_trained = True


class InsightMonitor:
    """Monitors the context for anomalies, detects trends, and forecasts stability."""

    def __init__(self, context_manager: ContextManager, policy_manager: RecoveryPolicyManager):
        self.context_manager = context_manager
        self.policy_manager = policy_manager
        self.policy_scheduler = PolicyScheduler(self.policy_manager, self.context_manager)
        
        # New v2.6 components
        self.time_series = TimeSeriesBuffer(window_size=50)
        self.predictive_model = PredictiveRepairModel()

        # Legacy deques (can be deprecated if fully replaced by TimeSeriesBuffer)
        self.evaluation_score_history = collections.deque(maxlen=10)
        self.emotion_history = collections.deque(maxlen=10)

    def detect_anomaly(self) -> dict | None:
        """
        Detects anomalies, including predicted future risks.
        """
        # 1. Update time series buffer with latest metrics from context
        self._update_metrics()

        # 2. Predictive Anomaly Detection
        impact_series = self.time_series.get_series("impact_score")
        predicted_risk = self.predictive_model.predict(impact_series)

        if predicted_risk > 0.4: # Configurable threshold
            log_manager.warning(f"[PredictiveRepair] Upcoming anomaly risk detected. Risk level: {predicted_risk:.2f}")
            self.context_manager.set("mid_term.predicted_anomaly_risk", predicted_risk, reason="Forecast")
            self.policy_scheduler.trigger_preemptive_repair()
            # We might still return an anomaly to stop current execution, or just let the preemptive repair run in the background.
            # For now, we log and trigger, but don't return an immediate anomaly.

        # 3. Immediate Anomaly Detection (existing logic)
        # This logic remains important for sudden, non-trend-based failures.
        current_score = self.context_manager.get("mid_term.evaluation_score")
        if current_score is not None:
            self.evaluation_score_history.append(current_score)

        if len(self.evaluation_score_history) >= 2:
            latest_score, previous_score = self.evaluation_score_history[-1], self.evaluation_score_history[-2]
            if (previous_score - latest_score) > 0.3:
                anomaly_details = {
                    "type": "evaluation_score_drop",
                    "message": f"Evaluation score dropped significantly from {previous_score:.2f} to {latest_score:.2f}",
                }
                log_manager.warning(f"[Anomaly Detected] {anomaly_details['message']}")
                return anomaly_details

        evaluator_feedback = self.context_manager.get("mid_term.evaluation_feedback")
        if isinstance(evaluator_feedback, str) and "error" in evaluator_feedback.lower():
            anomaly_details = {
                "type": "module_error",
                "module": "evaluator",
                "message": f"Evaluator returned an error message: {evaluator_feedback}",
            }
            log_manager.warning(f"[Anomaly Detected] {anomaly_details['message']}")
            return anomaly_details

        return None

    def _update_metrics(self):
        """Gathers the latest metrics from the context and adds them to the time series buffer."""
        # Get metrics from context, with defaults if not present
        impact_score = self.context_manager.get("short_term.impact_score", default=None)
        evaluation_score = self.context_manager.get("mid_term.evaluation_score", default=None)
        repair_success_rate = self.context_manager.get("long_term.repair_success_rate", default=None)

        self.time_series.add_point("impact_score", impact_score)
        self.time_series.add_point("evaluation_score", evaluation_score)
        self.time_series.add_point("repair_success_rate", repair_success_rate)

    def detect_trend(self) -> dict | None:
        """Detects significant trends in historical data."""
        # This can be enhanced or replaced by the predictive model's insights
        if len(self.evaluation_score_history) == self.evaluation_score_history.maxlen:
            avg_score = sum(self.evaluation_score_history) / len(self.evaluation_score_history)
            if avg_score < 0.5:
                return {"type": "low_performance_trend", "message": "Consistent low evaluation scores.", "significant_change": True}
        return None

    def run_simulation(self, steps=60):
        """Runs a simulation to test the predictive repair mechanism."""
        log_manager.info("--- Starting Predictive Repair Simulation ---")
        
        # Create dummy context and policy managers for simulation
        if not hasattr(self.context_manager, 'is_simulation'):
             self.context_manager = ContextManager(is_simulation=True)
        if not hasattr(self.policy_manager, 'is_simulation'):
             self.policy_manager = RecoveryPolicyManager(is_simulation=True)
        
        self.policy_scheduler = PolicyScheduler(self.policy_manager, self.context_manager)


        # Phase 1: Stable period
        log_manager.info("Phase 1: Simulating stable performance.")
        for i in range(30):
            stable_impact = 0.1 + random.uniform(-0.05, 0.05)
            self.context_manager.set("short_term.impact_score", stable_impact, "sim")
            self.detect_anomaly()

        # Phase 2: Introduce a downward trend
        log_manager.info("Phase 2: Simulating downward trend in impact score.")
        current_impact = 0.1
        for i in range(steps - 30):
            current_impact += random.uniform(0.01, 0.03) # Negative trend
            degradation = 0.1 * (i / (steps - 30)) # Degradation gets worse over time
            self.context_manager.set("short_term.impact_score", current_impact + degradation, "sim")
            self.detect_anomaly()
            
        # Export final data
        self.time_series.to_json("logs/insight_trends/time_series.json")
        
        # Log final predicted risk
        final_risk_log_path = "logs/insight_trends/predictive_risk_log.json"
        final_risk = self.context_manager.get("mid_term.predicted_anomaly_risk", 0.0)
        os.makedirs(os.path.dirname(final_risk_log_path), exist_ok=True)
        with open(final_risk_log_path, 'w') as f:
            json.dump({"final_predicted_risk": final_risk}, f, indent=4)
        
        log_manager.info(f"--- Simulation Complete. Final predicted risk: {final_risk:.2f} ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run InsightMonitor with optional trend simulation.")
    parser.add_argument("--simulate-trend", action="store_true", help="Run a simulation of a downward trend.")
    args = parser.parse_args()

    # Dummy classes for standalone execution
    class MockContextManager(ContextManager):
        def __init__(self, is_simulation=True):
            super().__init__()
            self._context = {}
            self._context['short_term'] = {}
            self._context['mid_term'] = {}
            self._context['long_term'] = {}
            self.is_simulation = is_simulation
        
        def get(self, key, default=None):
            keys = key.split('.')
            val = self._context
            try:
                for k in keys:
                    val = val[k]
                return val
            except KeyError:
                return default
        
        def set(self, key, value, reason):
            keys = key.split('.')
            d = self._context
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value


    class MockRecoveryPolicyManager(RecoveryPolicyManager):
         def __init__(self, is_simulation=True):
            self.policies = {}
            self.is_simulation = is_simulation
         def apply_policy(self, context_manager, module_name, event_name, metadata=None):
            log_manager.info(f"[SIM] Mock policy application for {module_name}.{event_name}")
            return {"status": "sim_applied", "action_taken": "mock_action"}

    if args.simulate_trend:
        mock_context = MockContextManager()
        mock_policy = MockRecoveryPolicyManager()
        
        monitor = InsightMonitor(mock_context, mock_policy)
        monitor.run_simulation()
    else:
        log_manager.info("InsightMonitor loaded. Use --simulate-trend to run a simulation.")