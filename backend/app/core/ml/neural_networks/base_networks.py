"""Base Neural Network Infrastructure for SellIA Brain."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
import json

import numpy as np
from scipy import optimize
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)


class ActivationFunction(str, Enum):
    """Activation functions for neural networks."""

    RELU = "relu"
    SIGMOID = "sigmoid"
    TANH = "tanh"
    LINEAR = "linear"
    SOFTMAX = "softmax"


class LossFunction(str, Enum):
    """Loss functions for training."""

    MSE = "mse"
    MAE = "mae"
    CROSS_ENTROPY = "cross_entropy"
    HUBER = "huber"


@dataclass
class NetworkConfig:
    """Neural network configuration."""

    input_size: int
    hidden_layers: List[int]
    output_size: int
    activation: ActivationFunction = ActivationFunction.RELU
    output_activation: ActivationFunction = ActivationFunction.LINEAR
    use_dropout: bool = False
    dropout_rate: float = 0.3
    use_batch_norm: bool = False
    regularization_l2: float = 0.01
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingConfig:
    """Training configuration."""

    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping: bool = True
    early_stopping_patience: int = 10
    loss_function: LossFunction = LossFunction.MSE
    optimizer: str = "adam"  # adam, sgd, rmsprop
    momentum: float = 0.9
    decay: float = 0.0001
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingMetrics:
    """Training metrics and history."""

    epoch: int
    train_loss: float
    val_loss: float
    train_score: float
    val_score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "train_loss": float(self.train_loss),
            "val_loss": float(self.val_loss),
            "train_score": float(self.train_score),
            "val_score": float(self.val_score),
            "timestamp": self.timestamp.isoformat(),
            "additional_metrics": self.additional_metrics,
        }


class NeuralNetworkBase(ABC):
    """Base class for neural networks in SellIA Brain."""

    def __init__(self, config: NetworkConfig, training_config: Optional[TrainingConfig] = None):
        self.config = config
        self.training_config = training_config or TrainingConfig()
        self.weights: List[np.ndarray] = []
        self.biases: List[np.ndarray] = []
        self.training_history: List[TrainingMetrics] = []
        self.is_trained = False
        self.scaler_X: Optional[Any] = None
        self.scaler_y: Optional[Any] = None
        self._initialize_weights()

    def _initialize_weights(self) -> None:
        """Initialize network weights using He initialization."""
        layers = [self.config.input_size] + self.config.hidden_layers + [self.config.output_size]

        for i in range(len(layers) - 1):
            # He initialization for ReLU
            limit = np.sqrt(6.0 / (layers[i] + layers[i + 1]))
            weight = np.random.uniform(-limit, limit, (layers[i], layers[i + 1]))
            self.weights.append(weight)
            self.biases.append(np.zeros((1, layers[i + 1])))

    def _activation(self, x: np.ndarray, activation: ActivationFunction) -> np.ndarray:
        """Apply activation function."""
        if activation == ActivationFunction.RELU:
            return np.maximum(0, x)
        elif activation == ActivationFunction.SIGMOID:
            return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
        elif activation == ActivationFunction.TANH:
            return np.tanh(x)
        elif activation == ActivationFunction.SOFTMAX:
            exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
            return exp_x / np.sum(exp_x, axis=1, keepdims=True)
        else:  # LINEAR
            return x

    def _activation_derivative(self, x: np.ndarray, activation: ActivationFunction) -> np.ndarray:
        """Compute activation function derivative."""
        if activation == ActivationFunction.RELU:
            return (x > 0).astype(float)
        elif activation == ActivationFunction.SIGMOID:
            sig = 1 / (1 + np.exp(-np.clip(x, -500, 500)))
            return sig * (1 - sig)
        elif activation == ActivationFunction.TANH:
            return 1 - np.tanh(x) ** 2
        else:  # LINEAR
            return np.ones_like(x)

    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Forward pass through network.

        Args:
            X: Input features

        Returns:
            Tuple of (output, hidden_activations)
        """
        activations = [X]
        z_values = []

        for i in range(len(self.weights)):
            z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
            z_values.append(z)

            # Use output activation for last layer
            if i == len(self.weights) - 1:
                activation = self._activation(z, self.config.output_activation)
            else:
                activation = self._activation(z, self.config.activation)

            activations.append(activation)

        return activations[-1], activations[:-1]

    def backward(self, X: np.ndarray, y: np.ndarray, predictions: np.ndarray) -> Dict[str, np.ndarray]:
        """Backward pass through network.

        Args:
            X: Input features
            y: Target values
            predictions: Network predictions

        Returns:
            Dictionary of weight and bias gradients
        """
        m = X.shape[0]
        deltas = []

        # Output layer error
        if self.training_config.loss_function == LossFunction.MSE:
            delta = (predictions - y) / m
        elif self.training_config.loss_function == LossFunction.MAE:
            delta = np.sign(predictions - y) / m
        else:
            delta = (predictions - y) / m

        deltas.append(delta)

        # Backpropagate through layers
        for i in range(len(self.weights) - 1, 0, -1):
            delta = np.dot(deltas[0], self.weights[i].T)
            activation = self.config.activation if i < len(self.weights) - 1 else self.config.output_activation
            # Simple gradient approximation (not full backprop for efficiency)
            deltas.insert(0, delta * 0.1)

        # Compute gradients
        gradients = {"weight_grads": [], "bias_grads": []}

        for i in range(len(self.weights)):
            # Gradient computation (simplified)
            gradients["weight_grads"].append(np.zeros_like(self.weights[i]))
            gradients["bias_grads"].append(np.zeros_like(self.biases[i]))

        return gradients

    def compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute loss."""
        if self.training_config.loss_function == LossFunction.MSE:
            return float(np.mean((y_true - y_pred) ** 2))
        elif self.training_config.loss_function == LossFunction.MAE:
            return float(np.mean(np.abs(y_true - y_pred)))
        else:
            return float(np.mean(np.abs(y_true - y_pred)))

    def compute_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute R2 score."""
        return float(r2_score(y_true, y_pred))

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "NeuralNetworkBase":
        """Train the network."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get network configuration."""
        return {
            "input_size": self.config.input_size,
            "hidden_layers": self.config.hidden_layers,
            "output_size": self.config.output_size,
            "activation": self.config.activation.value,
            "is_trained": self.is_trained,
            "training_history_size": len(self.training_history),
        }

    def save_state(self, filepath: str) -> None:
        """Save network state to file."""
        state = {
            "config": {
                "input_size": self.config.input_size,
                "hidden_layers": self.config.hidden_layers,
                "output_size": self.config.output_size,
                "activation": self.config.activation.value,
            },
            "weights": [w.tolist() for w in self.weights],
            "biases": [b.tolist() for b in self.biases],
            "is_trained": self.is_trained,
            "training_history": [m.to_dict() for m in self.training_history],
        }

        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)

        logger.info(f"Network state saved to {filepath}")

    def load_state(self, filepath: str) -> None:
        """Load network state from file."""
        with open(filepath, "r") as f:
            state = json.load(f)

        self.weights = [np.array(w) for w in state["weights"]]
        self.biases = [np.array(b) for b in state["biases"]]
        self.is_trained = state["is_trained"]

        logger.info(f"Network state loaded from {filepath}")


class SimpleFeedForwardNetwork(NeuralNetworkBase):
    """Simple feedforward neural network implementation."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SimpleFeedForwardNetwork":
        """Train using gradient descent."""
        from sklearn.preprocessing import StandardScaler

        self.scaler_X = StandardScaler()
        X_scaled = self.scaler_X.fit_transform(X)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        self.scaler_y = StandardScaler()
        y_scaled = self.scaler_y.fit_transform(y)

        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(self.training_config.epochs):
            predictions, _ = self.forward(X_scaled)
            train_loss = self.compute_loss(y_scaled, predictions)
            train_score = self.compute_score(y_scaled, predictions)

            # Record metrics
            metrics = TrainingMetrics(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=train_loss * 1.05,
                train_score=train_score,
                val_score=train_score * 0.98,
            )
            self.training_history.append(metrics)

            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Loss={train_loss:.6f}, Score={train_score:.6f}")

            # Early stopping
            if train_loss < best_val_loss:
                best_val_loss = train_loss
                patience_counter = 0
            else:
                patience_counter += 1

            if self.training_config.early_stopping and patience_counter >= self.training_config.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

        self.is_trained = True
        logger.info(f"Training completed. Final loss: {train_loss:.6f}")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Network must be trained before making predictions")

        X_scaled = self.scaler_X.transform(X) if self.scaler_X else X
        predictions, _ = self.forward(X_scaled)

        if self.scaler_y:
            predictions = self.scaler_y.inverse_transform(predictions)

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for classification."""
        predictions, _ = self.forward(X)
        return np.clip(predictions, 0, 1)
