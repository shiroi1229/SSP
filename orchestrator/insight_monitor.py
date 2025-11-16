import collections
import json
import os
import argparse
import random
import numpy as np
import datetime # Added datetime import

from orchestrator.context_manager import ContextManager
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.policy_scheduler import PolicyScheduler
from modules.log_manager import log_manager
from modules.anomaly_detector import AnomalyDetector
from modules.predictive_analyzer import PredictiveAnalyzer # Import the new PredictiveAnalyzer
from modules.causal_graph import causal_graph
from modules.causal_verifier import verify_causality
from modules.causal_ingest import ingest_from_history
from modules.context_rollback import rollback_manager
from modules.auto_action_log import log_action
from modules.auto_action_analyzer import compute_action_stats, should_execute

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
        self.anomaly_detector = AnomalyDetector()
        self.predictive_analyzer = PredictiveAnalyzer() # Instantiate PredictiveAnalyzer

    def detect_anomaly(self) -> dict | None:
        """
        Detects anomalies using the AnomalyDetector and predictive model.
        """
        # 1. Update time series buffer and AnomalyDetector with latest metrics from context
        self._update_metrics()

        # Get current metrics for logging
        cpu_percent = self.context_manager.get("short_term.system_health.cpu_percent", default=None)
        memory_percent = self.context_manager.get("short_term.system_health.memory_percent", default=None)
        latency = self.context_manager.get("short_term.system_health.latency", default=None)

        # 2. Predictive Anomaly Detection using PredictiveAnalyzer
        predicted_anomaly_probability = self.predictive_analyzer.predict_anomaly_probability()
        self.context_manager.set("mid_term.predicted_anomaly_probability", predicted_anomaly_probability, reason="Predictive Analyzer output")
        
        PREDICTIVE_ANOMALY_THRESHOLD = 0.7 # Configurable threshold
        action_taken = "none"
        if predicted_anomaly_probability > PREDICTIVE_ANOMALY_THRESHOLD:
            log_manager.warning(f"[PredictiveAnalyzer] High predicted anomaly probability: {predicted_anomaly_probability:.2f}. Triggering preemptive repair.")
            self.policy_scheduler.trigger_preemptive_repair()
            action_taken = "preemptive_repair_triggered"
            # Log the predictive anomaly and action
            self._log_predictive_self_correction(
                pred_prob=predicted_anomaly_probability, 
                action=action_taken,
                metrics={"cpu": cpu_percent, "mem": memory_percent, "latency": latency}
            )
            
            # Return this as an anomaly to potentially trigger auto_fix or other policies
            return {
                "type": "predictive_anomaly",
                "message": f"Predicted anomaly probability {predicted_anomaly_probability:.2f} exceeds threshold {PREDICTIVE_ANOMALY_THRESHOLD}.",
                "predicted_probability": predicted_anomaly_probability,
                "source_module": "predictive_analyzer"
            }
        else:
            # Log the prediction even if no action is taken
            self._log_predictive_self_correction(
                pred_prob=predicted_anomaly_probability,
                action=action_taken,
                metrics={"cpu": cpu_percent, "mem": memory_percent, "latency": latency}
            )


        # 3. Immediate Anomaly Detection using AnomalyDetector
        metrics_to_check = {
            "cpu_percent": self.context_manager.get("short_term.system_health.cpu_percent"),
            "memory_percent": self.context_manager.get("short_term.system_health.memory_percent"),
            "evaluation_score": self.context_manager.get("mid_term.evaluation_score"),
            "impact_score": self.context_manager.get("short_term.impact_score"),
            # Add other critical metrics here as they become available in context
        }

        for metric_name, value in metrics_to_check.items():
            if value is not None:
                anomaly = self.anomaly_detector.detect_anomaly(metric_name, value)
                if anomaly:
                    log_manager.warning(f"[InsightMonitor] Anomaly detected by AnomalyDetector: {anomaly['message']}")
                    return anomaly # Return the first detected anomaly

        # Check for module errors (legacy logic, can be integrated into AnomalyDetector if desired)
        evaluator_feedback = self.context_manager.get("mid_term.evaluation_feedback")
        if isinstance(evaluator_feedback, str) and "error" in evaluator_feedback.lower():
            anomaly_details = {
                "type": "module_error",
                "module": "evaluator",
                "message": f"Evaluator returned an error message: {evaluator_feedback}",
            }
            log_manager.warning(f"[InsightMonitor] Module error detected: {anomaly_details['message']}")
            return anomaly_details

        return None

    def notify_recovery(self, message: dict):
        """Logs a recovery action notice."""
        log_manager.info(f"🩹 [Recovery] {message}")

    def _update_metrics(self):
        """Gathers the latest metrics from the context and adds them to the time series buffer and AnomalyDetector."""
        # Get metrics from context, with defaults if not present
        impact_score = self.context_manager.get("short_term.impact_score", default=None)
        evaluation_score = self.context_manager.get("mid_term.evaluation_score", default=None)
        repair_success_rate = self.context_manager.get("long_term.repair_success_rate", default=None)
        
        # System health metrics from the new /api/system/health endpoint
        cpu_percent = self.context_manager.get("short_term.system_health.cpu_percent", default=None)
        memory_percent = self.context_manager.get("short_term.system_health.memory_percent", default=None)
        latency = self.context_manager.get("short_term.system_health.latency", default=None) # Assuming latency will be available

        self.time_series.add_point("impact_score", impact_score)
        self.time_series.add_point("evaluation_score", evaluation_score)
        self.time_series.add_point("repair_success_rate", repair_success_rate)
        self.time_series.add_point("cpu_percent", cpu_percent)
        self.time_series.add_point("memory_percent", memory_percent)

        # AnomalyDetector also needs to be updated with current metrics
        if cpu_percent is not None:
            self.anomaly_detector.update_metric("cpu_percent", cpu_percent)
        if memory_percent is not None:
            self.anomaly_detector.update_metric("memory_percent", memory_percent)
        if evaluation_score is not None:
            self.anomaly_detector.update_metric("evaluation_score", evaluation_score)
        if impact_score is not None:
            self.anomaly_detector.update_metric("impact_score", impact_score)

        # Feed metrics to PredictiveAnalyzer
        self.predictive_analyzer.update_metrics(cpu_percent, memory_percent, latency)

    def _log_predictive_self_correction(self, pred_prob: float, action: str, result: dict = None, context_id: str = None, metrics: dict = None):
        """
        Logs prediction results and actions to logs/predictive_self_correction.json.
        (R-v1.1 Updated)
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "pred_prob": pred_prob,
            "action": action,
        }
        if result is not None:
            log_entry["result"] = result
        if context_id is not None:
            log_entry["context_id"] = context_id
        if metrics:
            log_entry.update(metrics)

        log_file_path = "logs/predictive_self_correction.json"
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Read existing logs, append new entry, and write back
        logs = []
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    # Handle empty or malformed file
                    content = f.read()
                    if content.strip():
                        logs = json.loads(content)
                    if not isinstance(logs, list):
                        log_manager.warning(f"{log_file_path} is not a list. Re-initializing.")
                        logs = []
            except json.JSONDecodeError:
                log_manager.warning(f"Could not decode JSON from {log_file_path}. Starting new log.")
                logs = []
        
        logs.append(log_entry)
        
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4)
            log_manager.debug(f"Logged predictive self-correction data to {log_file_path}")
        except IOError as e:
            log_manager.error(f"Failed to write predictive self-correction log to {log_file_path}: {e}", exc_info=True)


    def forecast_anomaly(self) -> dict:
        """
        予測型異常検出 (R-v1.1):
        過去のメトリクス履歴から PredictiveAnalyzer により
        異常発生確率を推定し、閾値を超えた場合に予防修復を実行する。
        """
        try:
            # This is a deviation from the class's usual dependency injection for demonstration
            from orchestrator.context_manager import ContextManager
            from modules.auto_fix_executor import AutoFixExecutor
            import time

            context_manager = ContextManager(
                history_path="logs/context_history.json",
                context_filepath="data/test_context.json"
            )
            analyzer = PredictiveAnalyzer()

            # 最新メトリクスを取得
            self._update_metrics() # Ensure analyzer has latest metrics
            pred_prob = analyzer.predict_anomaly_probability()

            # Contextへ記録
            context_manager.set(
                "mid_term.forecast.predicted_anomaly_probability",
                pred_prob,
                reason="Predicted anomaly probability from R-v1.1"
            )

            log_manager.info(f"[Forecast] Predicted anomaly probability: {pred_prob:.3f}")

            # Preventive trigger
            if pred_prob >= 0.7:
                log_manager.warning("[Forecast] Preventive Auto-Fix triggered.")
                auto_fix = AutoFixExecutor()
                result = auto_fix.execute_auto_fix(
                    "preventive_fix",
                    metadata={"pred_prob": pred_prob, "timestamp": time.time()}
                )
                log_manager.info(f"[Forecast] Preventive Auto-Fix Result: {result}")

                context_manager.set(
                    "mid_term.forecast.last_preventive_fix",
                    {"prob": pred_prob, "result": result},
                    reason="Preventive Auto-Fix event record"
                )
                # Log the event
                self._log_predictive_self_correction(pred_prob, "preventive_fix", result=result, context_id="system.forecast.R-v1.1")
                return {"pred_prob": pred_prob, "action": "preventive_fix", "result": result}
            
            # Log the 'none' action case
            self._log_predictive_self_correction(pred_prob, "none", context_id="system.forecast.R-v1.1")
            return {"pred_prob": pred_prob, "action": "none"}

        except Exception as e:
            log_manager.error(f"[InsightMonitor] forecast_anomaly failed: {e}", exc_info=True)
            return {"error": str(e), "action": "failed"}

    def detect_trend(self) -> dict | None:
        """Detects significant trends in historical data."""
        eval_scores = self.time_series.get_series("evaluation_score")
        if len(eval_scores) == self.time_series.window_size:
            avg_score = sum(eval_scores) / len(eval_scores)
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
            cpu = 20 + random.uniform(-5, 5)
            mem = 30 + random.uniform(-5, 5)
            latency = 50 + random.uniform(-10, 10)

            self.context_manager.set("short_term.impact_score", stable_impact, "sim")
            self.context_manager.set("short_term.system_health.cpu_percent", cpu, "sim")
            self.context_manager.set("short_term.system_health.memory_percent", mem, "sim")
            self.context_manager.set("short_term.system_health.latency", latency, "sim")
            self.context_manager.set("mid_term.evaluation_score", 0.8 + random.uniform(-0.1, 0.1), "sim")
            
            # Update metrics and get prediction
            self._update_metrics()
            predicted_prob = self.predictive_analyzer.predict_anomaly_probability()
            self.context_manager.set("mid_term.predicted_anomaly_probability", predicted_prob, reason="Predictive Analyzer output")
            
            # Log simulation step
            self._log_predictive_self_correction(cpu, mem, latency, predicted_prob, "none")
            self.detect_anomaly()

        # Phase 2: Introduce a downward trend
        log_manager.info("Phase 2: Simulating downward trend in impact score and increasing CPU/Memory/Latency.")
        current_impact = 0.1
        current_cpu = 20
        current_mem = 30
        current_latency = 50
        current_eval = 0.8
        for i in range(steps - 30):
            current_impact += random.uniform(0.01, 0.03) # Negative trend
            degradation = 0.1 * (i / (steps - 30)) # Degradation gets worse over time
            cpu = min(95, current_cpu + random.uniform(0.5, 1.5))
            mem = min(95, current_mem + random.uniform(0.5, 1.0))
            latency = min(500, current_latency + random.uniform(1.0, 3.0))

            self.context_manager.set("short_term.impact_score", current_impact + degradation, "sim")
            self.context_manager.set("short_term.system_health.cpu_percent", cpu, "sim")
            self.context_manager.set("short_term.system_health.memory_percent", mem, "sim")
            self.context_manager.set("short_term.system_health.latency", latency, "sim")

            current_eval -= random.uniform(0.01, 0.02)
            self.context_manager.set("mid_term.evaluation_score", max(0.1, current_eval), "sim")

            # Update metrics and get prediction
            self._update_metrics()
            predicted_prob = self.predictive_analyzer.predict_anomaly_probability()
            self.context_manager.set("mid_term.predicted_anomaly_probability", predicted_prob, reason="Predictive Analyzer output")

            # Determine action for logging
            action_taken = "none"
            if predicted_prob > PREDICTIVE_ANOMALY_THRESHOLD: # Use the same threshold as detect_anomaly
                action_taken = "preemptive_repair_triggered"
            
            self._log_predictive_self_correction(cpu, mem, latency, predicted_prob, action_taken)
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

    def compute_causal_integrity(self, sample_size: int = 50) -> dict:
        """Evaluate causal graph consistency by sampling events."""
        graph = causal_graph.build_graph()
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        total_nodes = len(nodes)
        auto_action = None
        if total_nodes == 0:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "sampled": 0,
                "success_ratio": 0.0,
                "missing_parent_events": [],
                "auto_action": auto_action,
            }
        sampled = nodes[-sample_size:]
        failures = []
        for node in sampled:
            result = verify_causality(node["event_id"])
            if not result["success"]:
                failures.append({"event_id": node["event_id"], "missing": result["missing_parents"]})
        success_ratio = 1 - (len(failures) / max(len(sampled), 1))
        if failures:
            action_stats = compute_action_stats(limit=200)
            stats_snapshot = action_stats.get("causal_auto_action", {})
            min_ratio = 0.5
            if not should_execute("causal_auto_action", action_stats, min_ratio=min_ratio):
                auto_action = {
                    "decision": "skipped",
                    "skipped": True,
                    "reason": f"success ratio {stats_snapshot.get('success_ratio', 0.0):.2f} < {min_ratio:.2f}",
                    "stats": stats_snapshot,
                }
            else:
                ingest_result = ingest_from_history(limit=50)
                rollback_result = rollback_manager.rollback(None, reason="auto-causal-repair")
                overall_success = bool(ingest_result.get("success")) and bool(rollback_result.get("success"))
                auto_action = {
                    "decision": "executed",
                    "skipped": False,
                    "ingest": ingest_result,
                    "rollback": rollback_result,
                    "success": overall_success,
                    "stats": stats_snapshot,
                }
                log_action({"type": "causal_auto_action", "ingest": ingest_result, "rollback": rollback_result}, success=overall_success)
        return {
            "total_nodes": total_nodes,
            "total_edges": len(edges),
            "sampled": len(sampled),
            "success_ratio": round(success_ratio, 3),
            "missing_parent_events": failures[:10],
            "auto_action": auto_action,
        }


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
