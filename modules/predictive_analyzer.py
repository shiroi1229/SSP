# path: modules/predictive_analyzer.py
# version: R-v1.1

import collections
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import os
import json
from modules.log_manager import log_manager

# Define the LSTM model
class LSTMAnomalyPredictor(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(LSTMAnomalyPredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :]) # Get output from the last time step
        out = self.sigmoid(out)
        return out

class PredictiveAnalyzer:
    """
    Analyzes time-series system metrics to predict anomaly probabilities
    using a hybrid EWMA + LSTM model.
    """
    def __init__(self, model_path: str = "models/predictive_lstm.pt", 
                 window_size: int = 60, ewma_alpha: float = 0.3,
                 lstm_input_size: int = 3, lstm_hidden_size: int = 50, 
                 lstm_num_layers: int = 1, lstm_output_size: int = 1):
        
        self.model_path = model_path
        self.window_size = window_size
        self.ewma_alpha = ewma_alpha
        
        # Ring buffers for metrics: cpu, mem, latency
        self.metrics_history = {
            "cpu": collections.deque(maxlen=window_size),
            "mem": collections.deque(maxlen=window_size),
            "latency": collections.deque(maxlen=window_size)
        }
        self.ewma_values = {"cpu": 0.0, "mem": 0.0, "latency": 0.0
        }

        self.lstm_model = LSTMAnomalyPredictor(lstm_input_size, lstm_hidden_size, lstm_num_layers, lstm_output_size)
        self.load_model() # Load pre-trained model if available
        self.lstm_model.eval() # Set to evaluation mode by default

        log_manager.info("[PredictiveAnalyzer] Initialized.")

    def update_metrics(self, cpu: float, mem: float, latency: float):
        """
        Accumulates recent metrics into ring buffers and updates EWMA.
        """
        current_metrics = {"cpu": cpu, "mem": mem, "latency": latency}
        for metric_name, value in current_metrics.items():
            if value is not None:
                self.metrics_history[metric_name].append(value)
                
                # Update EWMA
                if len(self.metrics_history[metric_name]) == 1:
                    self.ewma_values[metric_name] = value
                else:
                    self.ewma_values[metric_name] = (self.ewma_alpha * value) + \
                                                     ((1 - self.ewma_alpha) * self.ewma_values[metric_name])
            else:
                log_manager.warning(f"[PredictiveAnalyzer] Received None for metric {metric_name}. Skipping update.")

    def compute_ewma_score(self) -> float:
        """
        Calculates a combined EWMA score representing short-term risk.
        This is a simplified combination; can be made more sophisticated.
        """
        # Ensure we have enough data for meaningful EWMA
        if any(len(q) < 1 for q in self.metrics_history.values()):
            return 0.0 # Not enough data

        # Simple average of EWMA values for now
        combined_ewma = np.mean(list(self.ewma_values.values()))
        
        # Normalize or scale combined_ewma to a 0-1 range if necessary
        # For now, assuming EWMA values are somewhat indicative of risk directly
        return min(1.0, max(0.0, combined_ewma / 100.0)) # Assuming metrics are % based, scale to 0-1

    def predict_lstm(self) -> float:
        """
        Predicts the next anomaly probability using the LSTM model.
        Returns 0.0 if not enough historical data.
        """
        # Ensure enough data for LSTM input (window_size)
        if any(len(q) < self.window_size for q in self.metrics_history.values()):
            return 0.0 # Not enough data for a full sequence

        # Prepare data for LSTM: (batch_size, seq_len, input_size)
        # input_size = 3 for cpu, mem, latency
        lstm_input_data = []
        for i in range(self.window_size):
            # Assuming metrics_history deques are aligned by index for the same timestamp
            # This might need more robust timestamp-based alignment in a real system
            cpu_val = self.metrics_history["cpu"][i] if i < len(self.metrics_history["cpu"]) else 0.0
            mem_val = self.metrics_history["mem"][i] if i < len(self.metrics_history["mem"]) else 0.0
            latency_val = self.metrics_history["latency"][i] if i < len(self.metrics_history["latency"]) else 0.0
            lstm_input_data.append([cpu_val, mem_val, latency_val])
        
        # Convert to tensor and add batch dimension
        input_tensor = torch.tensor(lstm_input_data, dtype=torch.float32).unsqueeze(0) # Add batch_size=1

        with torch.no_grad():
            prediction = self.lstm_model(input_tensor)
        
        return prediction.item() # Get the scalar probability

    def predict_anomaly_probability(self) -> float:
        """
        Integrates EWMA and LSTM predictions to return a final risk probability.
        Hybrid inference: EWMA score * 0.3 + LSTM probability * 0.7
        """
        ewma_risk = self.compute_ewma_score()
        lstm_prob = self.predict_lstm()

        # Ensure EWMA and LSTM have enough data to contribute meaningfully
        if any(len(q) < 5 for q in self.metrics_history.values()): # Arbitrary threshold for EWMA to be stable
            final_risk = lstm_prob # Rely more on LSTM if EWMA is unstable
        elif any(len(q) < self.window_size for q in self.metrics_history.values()): # Not enough for full LSTM sequence
            final_risk = ewma_risk # Rely more on EWMA if LSTM is unstable
        else:
            final_risk = (ewma_risk * 0.3) + (lstm_prob * 0.7)
        
        return min(1.0, max(0.0, final_risk)) # Ensure probability is within [0, 1]

    def train_predictive_model(self, log_path: str, epochs: int = 10, learning_rate: float = 0.001):
        """
        Retrains the LSTM model from past logs.
        log_path: Path to a JSON file containing historical metric data and anomaly labels.
        """
        log_manager.info(f"[PredictiveAnalyzer] Starting LSTM model training from {log_path}...")
        self.lstm_model.train() # Set to training mode

        # Placeholder for data loading and preprocessing
        # In a real scenario, this would load logs/predictive_self_correction.json
        # and prepare sequences (X) and labels (y) for training.
        # For now, generate dummy data.
        X_train = torch.randn(100, self.window_size, 3) # 100 samples, 60 timesteps, 3 features
        y_train = torch.randint(0, 2, (100, 1)).float() # 100 labels (0 or 1)

        criterion = nn.BCEWithLogitsLoss() # Binary Cross-Entropy with Logits
        optimizer = optim.Adam(self.lstm_model.parameters(), lr=learning_rate)

        for epoch in range(epochs):
            outputs = self.lstm_model(X_train)
            loss = criterion(outputs, y_train)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            log_manager.debug(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
        
        log_manager.info("[PredictiveAnalyzer] LSTM model training complete.")
        self.lstm_model.eval() # Set back to evaluation mode
        self.save_model()

    def save_model(self):
        """Saves the trained LSTM model to self.model_path."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.lstm_model.state_dict(), self.model_path)
        log_manager.info(f"[PredictiveAnalyzer] LSTM model saved to {self.model_path}")

    def load_model(self):
        """Loads the LSTM model from self.model_path."""
        if os.path.exists(self.model_path):
            try:
                self.lstm_model.load_state_dict(torch.load(self.model_path))
                log_manager.info(f"[PredictiveAnalyzer] LSTM model loaded from {self.model_path}")
            except Exception as e:
                log_manager.error(f"[PredictiveAnalyzer] Error loading LSTM model from {self.model_path}: {e}. Initializing new model.", exc_info=True)
        else:
            log_manager.info(f"[PredictiveAnalyzer] No pre-trained model found at {self.model_path}. Initializing new model.")
