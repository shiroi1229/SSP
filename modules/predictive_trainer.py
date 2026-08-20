# path: modules/predictive_trainer.py
# version: R-v1.1
"""
Trains and evaluates the Predictive Self-Correction model (LSTM).
Re-trains periodically using historical logs and replaces the model if it improves.
"""

import json
import os
import numpy as np
import torch
from sklearn.metrics import f1_score, accuracy_score
from datetime import datetime
from modules.log_manager import log_manager
from modules.predictive_analyzer import PredictiveAnalyzer, LSTMAnomalyPredictor

LOG_PATH = "logs/predictive_self_correction.json"
MODEL_PATH = "models/predictive_lstm.pt" # Use the same path as the analyzer
MODEL_DIR = os.path.dirname(MODEL_PATH)
os.makedirs(MODEL_DIR, exist_ok=True)

class PredictiveTrainer:
    def __init__(self):
        self.model_path = MODEL_PATH
        # Use the same model parameters as the analyzer for consistency
        self.analyzer_params = {
            "lstm_input_size": 3,
            "lstm_hidden_size": 50,
            "lstm_num_layers": 1,
            "lstm_output_size": 1
        }

    def load_log_data(self, max_samples=1000):
        """
        Load historical forecast logs and create training data.
        It filters for logs that contain the necessary metric data.
        """
        if not os.path.exists(LOG_PATH):
            log_manager.warning(f"[Trainer] Log file not found at {LOG_PATH}")
            return None, None

        X, y = [], []
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            log_manager.error(f"[Trainer] Could not read or parse log file: {LOG_PATH}")
            return None, None

        for entry in logs:
            # We need logs that have both metrics and a clear action
            if 'metrics' in entry and 'action' in entry:
                metrics = entry.get('metrics', {})
                cpu = metrics.get('cpu')
                mem = metrics.get('mem')
                latency = metrics.get('latency')

                if all(v is not None for v in [cpu, mem, latency]):
                    # Feature: [cpu, mem, latency]
                    features = [cpu, mem, latency]
                    # Label: 1 if a corrective action was triggered, 0 otherwise
                    label = 1 if entry['action'] in ["preemptive_repair_triggered", "preventive_fix"] else 0
                    
                    X.append(features)
                    y.append(label)

        if len(X) == 0:
            log_manager.warning("[Trainer] No suitable training data found in logs.")
            return None, None

        log_manager.info(f"[Trainer] Loaded {len(X)} data points for training.")
        return np.array(X[-max_samples:]), np.array(y[-max_samples:])

    def train_new_model(self, X_train, y_train):
        """Trains a new LSTM model instance."""
        if X_train is None or len(X_train) < 20:
            log_manager.warning("[Trainer] Insufficient data for retraining.")
            return None, None

        # Reshape for LSTM: (batch_size, seq_len, input_size)
        # We treat each entry as a sequence of length 1 for simplicity here.
        # A more advanced implementation would create sequences from the time-series data.
        X_tensor = torch.tensor(X_train, dtype=torch.float32).unsqueeze(1)
        y_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)

        model = LSTMAnomalyPredictor(**self.analyzer_params)
        model.train()
        
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        log_manager.info("[Trainer] Starting model training...")
        for epoch in range(50): # Increased epochs for better training on small data
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            if (epoch + 1) % 10 == 0:
                log_manager.debug(f"[Trainer] Epoch [{epoch+1}/50], Loss: {loss.item():.4f}")

        # Save the newly trained model to a temporary candidate path
        candidate_path = os.path.join(MODEL_DIR, f"predictive_model_candidate_{datetime.now().strftime('%Y%m%d%H%M%S')}.pt")
        torch.save(model.state_dict(), candidate_path)
        log_manager.info(f"[Trainer] Trained new candidate model and saved to: {candidate_path}")
        
        model.eval()
        return candidate_path, model

    def evaluate_and_replace(self):
        """
        Trains a new model, compares its F1 score with the current model,
        and replaces the current model if the new one performs better.
        """
        X_test, y_test = self.load_log_data()
        if X_test is None:
            return {"status": "aborted", "reason": "Insufficient data"}

        training_result = self.train_new_model(X_test, y_test)
        if not training_result:
            return {"status": "aborted", "reason": "Training failed"}
        
        candidate_path, new_model = training_result
        X_tensor = torch.tensor(X_test, dtype=torch.float32).unsqueeze(1)

        # --- Evaluate New Model ---
        with torch.no_grad():
            preds_new_raw = new_model(X_tensor)
        preds_new = (preds_new_raw.numpy() > 0.5).astype(int)
        score_new = f1_score(y_test, preds_new, zero_division=0)
        accuracy_new = accuracy_score(y_test, preds_new)
        log_manager.info(f"[Trainer] New model evaluation: F1 Score={score_new:.4f}, Accuracy={accuracy_new:.4f}")

        # --- Evaluate Old Model ---
        try:
            analyzer_old = PredictiveAnalyzer(model_path=self.model_path)
            # The analyzer loads the model on init. We access it directly.
            old_model = analyzer_old.lstm_model
            old_model.eval()
            with torch.no_grad():
                preds_old_raw = old_model(X_tensor)
            preds_old = (preds_old_raw.numpy() > 0.5).astype(int)
            score_old = f1_score(y_test, preds_old, zero_division=0)
            accuracy_old = accuracy_score(y_test, preds_old)
            log_manager.info(f"[Trainer] Old model evaluation: F1 Score={score_old:.4f}, Accuracy={accuracy_old:.4f}")
        except FileNotFoundError:
            log_manager.warning("[Trainer] No old model found to compare against. The new model will be adopted by default.")
            score_old = -1.0 # Ensure new model is adopted

        # --- Compare and Replace ---
        if score_new > score_old:
            log_manager.info(f"[Trainer] New model is superior. Replacing old model. New F1={score_new:.4f}, Old F1={score_old:.4f}")
            try:
                os.replace(candidate_path, self.model_path)
                return {"status": "replaced", "score_new": score_new, "score_old": score_old}
            except Exception as e:
                log_manager.error(f"[Trainer] Failed to replace model file: {e}", exc_info=True)
                # Clean up candidate file if replacement fails
                if os.path.exists(candidate_path):
                    os.remove(candidate_path)
                return {"status": "error", "reason": "File replacement failed"}
        else:
            log_manager.info(f"[Trainer] New model is not superior. Discarding candidate. New F1={score_new:.4f}, Old F1={score_old:.4f}")
            if os.path.exists(candidate_path):
                os.remove(candidate_path)
            return {"status": "kept_old", "score_new": score_new, "score_old": score_old}

if __name__ == '__main__':
    # For direct testing of the trainer
    trainer = PredictiveTrainer()
    result = trainer.evaluate_and_replace()
    print(f"Training cycle finished. Result: {result}")
