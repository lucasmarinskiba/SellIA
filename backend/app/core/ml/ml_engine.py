"""ML Engine — Supervised, Unsupervised, Reinforcement Learning for SellIA."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
from enum import Enum

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"


@dataclass
class ModelMetrics:
    """Model evaluation metrics."""

    model_type: ModelType
    train_score: float
    test_score: float
    cv_score: float
    cv_std: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "train_score": float(self.train_score),
            "test_score": float(self.test_score),
            "cv_score": float(self.cv_score),
            "cv_std": float(self.cv_std),
            "precision": float(self.precision) if self.precision else None,
            "recall": float(self.recall) if self.recall else None,
            "f1": float(self.f1) if self.f1 else None,
            "rmse": float(self.rmse) if self.rmse else None,
            "r2": float(self.r2) if self.r2 else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class FeatureEngineer:
    """Extract and transform features from raw data."""

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or []
        self.scaler = StandardScaler()
        self.feature_stats: Dict[str, Dict[str, float]] = {}

    def extract_features(
        self, data: List[Dict[str, Any]], target_column: Optional[str] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Extract and normalize features from raw data."""
        features = []
        targets = None

        for record in data:
            feature_vector = []
            for fname in self.feature_names:
                value = record.get(fname, 0)
                # Handle missing values
                if value is None:
                    value = 0
                feature_vector.append(float(value))
            features.append(feature_vector)

            if target_column and target_column in record:
                if targets is None:
                    targets = []
                targets.append(float(record[target_column]))

        X = np.array(features)
        y = np.array(targets) if targets else None

        # Normalize features
        X_normalized = self.scaler.fit_transform(X)

        # Store statistics
        for i, fname in enumerate(self.feature_names):
            self.feature_stats[fname] = {
                "mean": float(self.scaler.mean_[i]),
                "std": float(self.scaler.scale_[i]),
            }

        logger.info(f"Extracted {len(self.feature_names)} features from {len(data)} records")
        return X_normalized, y

    def add_interaction_features(self, X: np.ndarray, feature_indices: List[Tuple[int, int]]) -> np.ndarray:
        """Add interaction terms between features."""
        interactions = []
        for i, j in feature_indices:
            interaction = X[:, i] * X[:, j]
            interactions.append(interaction)

        if interactions:
            X_interactions = np.column_stack([X] + interactions)
            logger.info(f"Added {len(feature_indices)} interaction features")
            return X_interactions
        return X

    def add_polynomial_features(self, X: np.ndarray, degree: int = 2) -> np.ndarray:
        """Add polynomial features (up to specified degree)."""
        poly_features = [X]
        for d in range(2, degree + 1):
            poly_features.append(np.power(X, d))

        X_poly = np.column_stack(poly_features)
        logger.info(f"Added polynomial features up to degree {degree}")
        return X_poly


class SupervisedLearner:
    """Train and predict on labeled data (regression/classification)."""

    def __init__(self, model_type: ModelType = ModelType.REGRESSION, random_state: int = 42):
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.metrics: Optional[ModelMetrics] = None
        self.feature_names: List[str] = []
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        feature_names: Optional[List[str]] = None,
        hyperparams: Optional[Dict[str, Any]] = None,
    ) -> ModelMetrics:
        """Train supervised model with cross-validation."""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )

        # Initialize model based on type
        if self.model_type == ModelType.REGRESSION:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=self.random_state,
                **(hyperparams or {}),
            )
        else:  # CLASSIFICATION
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=self.random_state,
                **(hyperparams or {}),
            )

        # Train
        self.model.fit(self.X_train, self.y_train)

        # Evaluate
        train_score = self.model.score(self.X_train, self.y_train)
        test_score = self.model.score(self.X_test, self.y_test)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5)

        # Calculate metrics
        y_pred = self.model.predict(self.X_test)

        if self.model_type == ModelType.REGRESSION:
            rmse = float(np.sqrt(mean_squared_error(self.y_test, y_pred)))
            r2 = float(r2_score(self.y_test, y_pred))
            self.metrics = ModelMetrics(
                model_type=self.model_type,
                train_score=train_score,
                test_score=test_score,
                cv_score=cv_scores.mean(),
                cv_std=cv_scores.std(),
                rmse=rmse,
                r2=r2,
            )
        else:  # CLASSIFICATION
            precision = float(precision_score(self.y_test, y_pred, average="weighted"))
            recall = float(recall_score(self.y_test, y_pred, average="weighted"))
            f1 = float(f1_score(self.y_test, y_pred, average="weighted"))
            self.metrics = ModelMetrics(
                model_type=self.model_type,
                train_score=train_score,
                test_score=test_score,
                cv_score=cv_scores.mean(),
                cv_std=cv_scores.std(),
                precision=precision,
                recall=recall,
                f1=f1,
            )

        logger.info(
            f"Trained {self.model_type.value} model. Train: {train_score:.4f}, Test: {test_score:.4f}, CV: {cv_scores.mean():.4f}"
        )
        return self.metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions on new data."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Get prediction probabilities (classification only)."""
        if self.model_type != ModelType.CLASSIFICATION:
            return None
        return self.model.predict_proba(X)

    def feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if self.model is None:
            raise ValueError("Model not trained.")

        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(self.feature_names, importances)}


class UnsupervisedLearner:
    """Cluster and segment data (K-means, etc.)."""

    def __init__(self, n_clusters: int = 3, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = None
        self.labels: Optional[np.ndarray] = None
        self.centers: Optional[np.ndarray] = None
        self.inertia: float = 0.0
        self.silhouette_score: float = 0.0

    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """Fit clustering model."""
        from sklearn.metrics import silhouette_score

        self.model = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)
        self.labels = self.model.fit_predict(X)
        self.centers = self.model.cluster_centers_
        self.inertia = float(self.model.inertia_)
        self.silhouette_score = float(silhouette_score(X, self.labels))

        logger.info(
            f"Fitted KMeans with {self.n_clusters} clusters. Silhouette: {self.silhouette_score:.4f}"
        )

        return {
            "n_clusters": self.n_clusters,
            "inertia": self.inertia,
            "silhouette_score": self.silhouette_score,
            "cluster_sizes": {int(k): int(v) for k, v in zip(*np.unique(self.labels, return_counts=True))},
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Assign new data to clusters."""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return self.model.predict(X)

    def get_cluster_profiles(self, X: np.ndarray, feature_names: List[str]) -> List[Dict[str, Any]]:
        """Get profiles of each cluster."""
        profiles = []
        for cluster_id in range(self.n_clusters):
            mask = self.labels == cluster_id
            cluster_data = X[mask]
            profile = {
                "cluster_id": int(cluster_id),
                "size": int(mask.sum()),
                "center": {
                    name: float(val)
                    for name, val in zip(feature_names, self.centers[cluster_id])
                },
                "statistics": {
                    name: {
                        "mean": float(cluster_data[:, i].mean()),
                        "std": float(cluster_data[:, i].std()),
                        "min": float(cluster_data[:, i].min()),
                        "max": float(cluster_data[:, i].max()),
                    }
                    for i, name in enumerate(feature_names)
                },
            }
            profiles.append(profile)
        return profiles


class ReinforcementLearner:
    """Q-learning based optimization (negotiation strategy, pricing, etc.)."""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95, epsilon: float = 0.1):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table: Dict[Tuple[Any, ...], Dict[str, float]] = {}
        self.episode_rewards: List[float] = []
        self.experience_buffer: List[Tuple[Any, str, float, Any, bool]] = []

    def initialize_state(self, state: Tuple[Any, ...], actions: List[str]) -> None:
        """Initialize Q-values for a state."""
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in actions}

    def choose_action(self, state: Tuple[Any, ...], actions: List[str], training: bool = True) -> str:
        """Choose action using epsilon-greedy strategy."""
        self.initialize_state(state, actions)

        if training and np.random.random() < self.epsilon:
            return np.random.choice(actions)  # Explore
        else:
            q_values = self.q_table[state]
            max_q = max(q_values.values())
            return np.random.choice([a for a, q in q_values.items() if q == max_q])  # Exploit

    def update_q_value(
        self, state: Tuple[Any, ...], action: str, reward: float, next_state: Tuple[Any, ...], actions: List[str]
    ) -> None:
        """Update Q-value using Bellman equation."""
        self.initialize_state(state, actions)
        self.initialize_state(next_state, actions)

        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q

    def learn_from_episode(self, episodes: int, actions: List[str], reward_fn: callable) -> List[float]:
        """Run training episodes and collect rewards."""
        rewards = []
        for episode in range(episodes):
            state = self._reset_episode()
            episode_reward = 0.0

            for _ in range(100):  # Max steps per episode
                action = self.choose_action(state, actions, training=True)
                reward = reward_fn(state, action)
                next_state = self._get_next_state(state, action)
                self.update_q_value(state, action, reward, next_state, actions)
                state = next_state
                episode_reward += reward

            rewards.append(episode_reward)
            self.episode_rewards.append(episode_reward)

            if (episode + 1) % 100 == 0:
                avg_reward = np.mean(rewards[-100:])
                logger.info(f"Episode {episode + 1}: Avg Reward = {avg_reward:.4f}")

        return rewards

    def _reset_episode(self) -> Tuple[Any, ...]:
        """Reset to initial state (override in subclass)."""
        return ()

    def _get_next_state(self, state: Tuple[Any, ...], action: str) -> Tuple[Any, ...]:
        """Transition to next state (override in subclass)."""
        return state

    def get_best_policy(self) -> Dict[Tuple[Any, ...], str]:
        """Extract best policy from Q-table."""
        policy = {}
        for state, q_values in self.q_table.items():
            best_action = max(q_values, key=q_values.get)
            policy[state] = best_action
        return policy


class ModelEvaluator:
    """Cross-validation, versioning, and model comparison."""

    def __init__(self, model_registry: Optional[Dict[str, Any]] = None):
        self.model_registry = model_registry or {}
        self.evaluation_history: List[Dict[str, Any]] = []

    def compare_models(self, models: List[Any], X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, Any]:
        """Compare multiple models using cross-validation."""
        comparison = {}

        for model_name, model in models:
            scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
            comparison[model_name] = {
                "mean_score": float(scores.mean()),
                "std_score": float(scores.std()),
                "scores": [float(s) for s in scores],
            }

        logger.info(f"Model comparison: {comparison}")
        return comparison

    def save_model_version(
        self,
        model_name: str,
        model: Any,
        version: str,
        metrics: ModelMetrics,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save model version with metadata."""
        record = {
            "model_name": model_name,
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics.to_dict(),
            "metadata": metadata or {},
        }
        self.model_registry[f"{model_name}_{version}"] = record
        self.evaluation_history.append(record)

        logger.info(f"Saved model version: {model_name}_{version}")
        return f"{model_name}_{version}"

    def get_model_history(self, model_name: str) -> List[Dict[str, Any]]:
        """Get evaluation history for a model."""
        return [r for r in self.evaluation_history if r["model_name"] == model_name]

    def get_best_model(self, model_name: str, metric: str = "test_score") -> Optional[Dict[str, Any]]:
        """Get best model version by metric."""
        history = self.get_model_history(model_name)
        if not history:
            return None

        best = max(history, key=lambda x: x["metrics"].get(metric, 0))
        return best
