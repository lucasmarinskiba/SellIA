"""Attention Mechanisms for SellIA Brain — Focus on important features & temporal patterns."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
from scipy.special import softmax

logger = logging.getLogger(__name__)


@dataclass
class AttentionWeights:
    """Attention weight distribution."""

    weights: Dict[str, float]  # feature/position -> weight
    top_k: List[Tuple[str, float]]  # top k most important
    entropy: float  # attention entropy (0 = concentrated, 1 = dispersed)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": {k: float(v) for k, v in self.weights.items()},
            "top_k": [(name, float(w)) for name, w in self.top_k],
            "entropy": float(self.entropy),
            "timestamp": self.timestamp.isoformat(),
        }


class FeatureAttention:
    """Determine which features matter most for decision."""

    def __init__(self, n_heads: int = 8):
        self.n_heads = n_heads
        self.attention_scores: Optional[np.ndarray] = None
        self.feature_names: List[str] = []

    def compute_attention(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> AttentionWeights:
        """Compute feature importance using attention."""
        if feature_names:
            self.feature_names = feature_names
        else:
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]

        # Compute correlation with target as attention signal
        correlations = []
        for i in range(X.shape[1]):
            corr = float(np.corrcoef(X[:, i], y)[0, 1])
            correlations.append(abs(corr) if not np.isnan(corr) else 0.0)

        # Apply softmax to convert to weights
        attention_scores = softmax(np.array(correlations))

        weights = {name: float(score) for name, score in zip(self.feature_names, attention_scores)}

        # Compute entropy
        entropy = float(-np.sum(attention_scores * np.log(attention_scores + 1e-10)))

        # Get top-k features
        top_indices = np.argsort(attention_scores)[-3:][::-1]
        top_k = [(self.feature_names[i], float(attention_scores[i])) for i in top_indices]

        result = AttentionWeights(weights=weights, top_k=top_k, entropy=entropy)

        logger.info(f"Feature attention computed. Top features: {[f[0] for f in top_k]}")

        return result

    def apply_attention(self, X: np.ndarray, attention_weights: Dict[str, float]) -> np.ndarray:
        """Apply attention weights to features."""
        X_attended = X.copy()

        for i, name in enumerate(self.feature_names):
            if name in attention_weights:
                X_attended[:, i] *= attention_weights[name]

        return X_attended


class TemporalAttention:
    """Focus on recent data more than old data."""

    def __init__(self, decay_factor: float = 0.95):
        self.decay_factor = decay_factor
        self.attention_weights: Optional[np.ndarray] = None

    def compute_temporal_attention(self, X: np.ndarray) -> AttentionWeights:
        """Compute temporal attention weights."""
        n_timesteps = len(X)

        # Exponential decay: recent data has higher weight
        weights = np.array([self.decay_factor ** (n_timesteps - 1 - i) for i in range(n_timesteps)])
        weights = weights / np.sum(weights)  # Normalize

        # Convert to dict for compatibility
        weight_dict = {f"t_{i}": float(w) for i, w in enumerate(weights)}

        # Compute entropy
        entropy = float(-np.sum(weights * np.log(weights + 1e-10)))

        # Top-k timesteps
        top_indices = np.argsort(weights)[-3:][::-1]
        top_k = [(f"t_{i}", float(weights[i])) for i in top_indices]

        result = AttentionWeights(weights=weight_dict, top_k=top_k, entropy=entropy)

        logger.info(f"Temporal attention computed. Most important: {[f[0] for f in top_k]}")

        return result

    def apply_temporal_attention(self, X: np.ndarray) -> np.ndarray:
        """Apply temporal weights to time series."""
        n_timesteps = len(X)
        weights = np.array([self.decay_factor ** (n_timesteps - 1 - i) for i in range(n_timesteps)])
        weights = weights / np.sum(weights)

        X_attended = X.copy()
        if X.ndim == 2:
            X_attended = X_attended * weights.reshape(-1, 1)
        else:
            X_attended = X_attended * weights

        return X_attended


class SpatialAttention:
    """Focus on local/regional patterns over global."""

    def __init__(self, n_regions: int = 5):
        self.n_regions = n_regions
        self.region_importance: Optional[np.ndarray] = None

    def compute_spatial_attention(self, X: np.ndarray, locality_bias: float = 1.2) -> AttentionWeights:
        """Compute spatial attention weights."""
        n_samples = len(X)
        region_size = max(1, n_samples // self.n_regions)

        # Split into regions
        region_variances = []
        for i in range(self.n_regions):
            start_idx = i * region_size
            end_idx = (i + 1) * region_size if i < self.n_regions - 1 else n_samples

            region_data = X[start_idx:end_idx]
            variance = np.mean(np.var(region_data, axis=0)) if region_data.size > 0 else 0.0
            region_variances.append(variance)

        # Regions with higher variance get more attention
        region_scores = np.array(region_variances) * locality_bias
        region_scores[1:-1] *= locality_bias  # Center regions get boost

        # Softmax
        region_weights = softmax(region_scores)

        weight_dict = {f"region_{i}": float(w) for i, w in enumerate(region_weights)}

        # Compute entropy
        entropy = float(-np.sum(region_weights * np.log(region_weights + 1e-10)))

        # Top-k regions
        top_indices = np.argsort(region_weights)[-2:][::-1]
        top_k = [(f"region_{i}", float(region_weights[i])) for i in top_indices]

        result = AttentionWeights(weights=weight_dict, top_k=top_k, entropy=entropy)

        logger.info(f"Spatial attention computed. Focus regions: {[f[0] for f in top_k]}")

        return result

    def apply_spatial_attention(self, X: np.ndarray, region_weights: np.ndarray) -> np.ndarray:
        """Apply spatial weights."""
        n_samples = len(X)
        region_size = max(1, n_samples // self.n_regions)

        X_attended = X.copy()

        for i in range(self.n_regions):
            start_idx = i * region_size
            end_idx = (i + 1) * region_size if i < self.n_regions - 1 else n_samples

            X_attended[start_idx:end_idx] *= region_weights[i]

        return X_attended


class CrossModalAttention:
    """Combine attention across different modalities (text, images, numbers)."""

    def __init__(self):
        self.modal_importance: Dict[str, float] = {}

    def compute_cross_modal_attention(self, modalities: Dict[str, np.ndarray], target: Optional[np.ndarray] = None) -> AttentionWeights:
        """Compute attention across modalities."""
        modal_scores = {}

        for modal_name, modal_data in modalities.items():
            if modal_data.size == 0:
                modal_scores[modal_name] = 0.0
                continue

            # Compute modal importance based on variance and correlation with target
            variance = np.mean(np.var(modal_data, axis=0)) if modal_data.ndim > 1 else np.var(modal_data)

            if target is not None:
                # Simple correlation-based importance
                if modal_data.ndim == 1:
                    corr = abs(np.corrcoef(modal_data, target)[0, 1])
                else:
                    corr = abs(np.corrcoef(modal_data.flatten(), target)[0, 1])
                corr = 0.0 if np.isnan(corr) else corr
            else:
                corr = 0.5

            modal_scores[modal_name] = float(variance * (1 + corr))

        # Convert to probability distribution
        scores = np.array(list(modal_scores.values()))
        modal_weights = softmax(scores)

        weights = {name: float(w) for name, w in zip(modal_scores.keys(), modal_weights)}
        self.modal_importance = weights

        # Entropy
        entropy = float(-np.sum(modal_weights * np.log(modal_weights + 1e-10)))

        # Top-k modalities
        sorted_modals = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        top_k = sorted_modals[:2] if len(sorted_modals) >= 2 else sorted_modals

        result = AttentionWeights(weights=weights, top_k=top_k, entropy=entropy)

        logger.info(f"Cross-modal attention computed. Weights: {weights}")

        return result

    def apply_cross_modal_attention(self, modalities: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Apply attention weights to each modality."""
        attended_modalities = {}

        for modal_name, modal_data in modalities.items():
            weight = self.modal_importance.get(modal_name, 0.5)
            attended_modalities[modal_name] = modal_data * weight

        return attended_modalities

    def fuse_modalities(self, modalities: Dict[str, np.ndarray], method: str = "concatenate") -> np.ndarray:
        """Fuse multiple modalities into single representation."""
        # Apply attention first
        attended = self.apply_cross_modal_attention(modalities)

        if method == "concatenate":
            # Flatten and concatenate
            flattened = []
            for modal_name in sorted(attended.keys()):
                data = attended[modal_name]
                if data.ndim > 1:
                    flattened.append(data.flatten())
                else:
                    flattened.append(data)
            return np.concatenate(flattened)

        elif method == "weighted_average":
            # Weighted average (for same-shaped modalities)
            total_weight = 0
            weighted_sum = None

            for modal_name, modal_data in attended.items():
                weight = self.modal_importance.get(modal_name, 0.5)
                total_weight += weight

                if weighted_sum is None:
                    weighted_sum = modal_data * weight
                else:
                    weighted_sum += modal_data * weight

            return weighted_sum / total_weight if total_weight > 0 else weighted_sum

        else:  # "attention_gate"
            # Use attention gates to combine
            attended_list = list(attended.values())
            if len(attended_list) == 1:
                return attended_list[0]

            # Stack and compute attention gates
            stacked = np.stack(attended_list)
            gates = softmax(np.sum(stacked, axis=(1, 2)) if stacked.ndim > 2 else np.sum(stacked, axis=1))

            result = None
            for i, gate in enumerate(gates):
                if result is None:
                    result = attended_list[i] * gate
                else:
                    result += attended_list[i] * gate

            return result if result is not None else attended_list[0]
