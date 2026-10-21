"""Ensemble Networks for SellIA Brain — Model combination, uncertainty, boosting."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.ensemble import (
    BaggingClassifier,
    BaggingRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    VotingClassifier,
    VotingRegressor,
)

from app.core.clock import utc_now

logger = logging.getLogger(__name__)


@dataclass
class EnsembleVote:
    """Vote from ensemble member."""

    model_name: str
    prediction: float
    confidence: float
    weight: float
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "prediction": float(self.prediction),
            "confidence": float(self.confidence),
            "weight": float(self.weight),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class UncertaintyEstimate:
    """Uncertainty in prediction."""

    prediction: float
    lower_bound: float
    upper_bound: float
    std_dev: float
    confidence_interval_width: float
    prediction_variance: float
    epistemic_uncertainty: float  # Model uncertainty
    aleatoric_uncertainty: float  # Data uncertainty
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": float(self.prediction),
            "lower_bound": float(self.lower_bound),
            "upper_bound": float(self.upper_bound),
            "std_dev": float(self.std_dev),
            "confidence_interval_width": float(self.confidence_interval_width),
            "prediction_variance": float(self.prediction_variance),
            "epistemic_uncertainty": float(self.epistemic_uncertainty),
            "aleatoric_uncertainty": float(self.aleatoric_uncertainty),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ModelSelectionResult:
    """Model selection result."""

    best_model: str
    selection_reason: str
    top_models: list[tuple[str, float]]  # (model_name, score)
    performance_scores: dict[str, float]  # model -> score
    recommended_ensemble: list[str]
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_model": self.best_model,
            "selection_reason": self.selection_reason,
            "top_models": [(name, float(score)) for name, score in self.top_models],
            "performance_scores": {
                k: float(v) for k, v in self.performance_scores.items()
            },
            "recommended_ensemble": self.recommended_ensemble,
            "timestamp": self.timestamp.isoformat(),
        }


class EnsemblePredictor:
    """Combine predictions from multiple models."""

    def __init__(self, voting_method: str = "soft", n_estimators: int = 5):
        self.voting_method = voting_method
        self.n_estimators = n_estimators
        self.models: dict[str, BaseEstimator] = {}
        self.model_weights: dict[str, float] = {}
        self.voting_regressor: VotingRegressor | None = None
        self.voting_classifier: VotingClassifier | None = None
        self.is_trained = False

    def add_model(
        self, name: str, model: BaseEstimator, weight: float = 1.0
    ) -> "EnsemblePredictor":
        """Add model to ensemble."""
        self.models[name] = model
        self.model_weights[name] = weight
        logger.info(f"Model '{name}' added to ensemble with weight {weight}")
        return self

    def fit(
        self, X: np.ndarray, y: np.ndarray, task: str = "regression"
    ) -> "EnsemblePredictor":
        """Fit all ensemble models."""
        if not self.models:
            raise ValueError("No models added to ensemble")

        # Prepare estimator list with weights
        estimators = [(name, model) for name, model in self.models.items()]

        if task == "regression":
            weights = [self.model_weights.get(name, 1.0) for name, _ in estimators]
            self.voting_regressor = VotingRegressor(
                estimators=estimators, weights=weights
            )
            self.voting_regressor.fit(X, y)
        else:
            weights = [self.model_weights.get(name, 1.0) for name, _ in estimators]
            self.voting_classifier = VotingClassifier(
                estimators=estimators, weights=weights
            )
            self.voting_classifier.fit(X, y)

        self.is_trained = True
        logger.info("Ensemble fitted successfully")
        return self

    def predict(self, X: np.ndarray, task: str = "regression") -> np.ndarray:
        """Make ensemble predictions."""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained first")

        if task == "regression":
            return self.voting_regressor.predict(X)
        else:
            return self.voting_classifier.predict(X)

    def predict_with_votes(
        self, X: np.ndarray, task: str = "regression"
    ) -> tuple[np.ndarray, list[list[EnsembleVote]]]:
        """Get predictions with individual model votes."""
        if not self.models:
            raise ValueError("No models in ensemble")

        all_votes = []

        for i in range(len(X)):
            sample = X[i : i + 1]
            votes = []

            for name, model in self.models.items():
                try:
                    if task == "regression":
                        pred = float(model.predict(sample)[0])
                        confidence = 0.85
                    else:
                        pred_proba = model.predict_proba(sample)[0]
                        pred = float(np.argmax(pred_proba))
                        confidence = float(np.max(pred_proba))

                    weight = self.model_weights.get(name, 1.0)

                    vote = EnsembleVote(
                        model_name=name,
                        prediction=pred,
                        confidence=confidence,
                        weight=weight,
                    )
                    votes.append(vote)
                except Exception as e:
                    logger.warning(f"Model {name} failed: {e}", exc_info=True)

            all_votes.append(votes)

        # Get ensemble predictions
        ensemble_preds = self.predict(X, task=task)

        return ensemble_preds, all_votes

    def get_model_performance(self, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """Evaluate individual models."""
        from sklearn.metrics import accuracy_score, r2_score

        performance = {}

        for name, model in self.models.items():
            try:
                preds = model.predict(X)

                if isinstance(y[0], (int, np.integer)):
                    score = accuracy_score(y, preds)
                else:
                    score = r2_score(y, preds)

                performance[name] = float(score)
            except Exception as e:
                logger.warning(f"Could not evaluate {name}: {e}", exc_info=True)
                performance[name] = 0.0

        return performance


class UncertaintyEstimator:
    """Estimate prediction uncertainty."""

    def __init__(self, n_bootstrap: int = 10):
        self.n_bootstrap = n_bootstrap
        self.base_model: BaseEstimator | None = None
        self.bootstrap_models: list[BaseEstimator] = []

    def fit(
        self, X: np.ndarray, y: np.ndarray, base_model: BaseEstimator
    ) -> "UncertaintyEstimator":
        """Fit uncertainty estimator using bootstrap."""
        from sklearn.utils import resample

        self.base_model = base_model
        n_samples = len(X)

        # Fit bootstrap models
        for i in range(self.n_bootstrap):
            X_boot, y_boot = resample(X, y, n_samples=n_samples, random_state=i)

            model = type(base_model)(**base_model.get_params())
            model.fit(X_boot, y_boot)
            self.bootstrap_models.append(model)

        logger.info(f"Fitted {self.n_bootstrap} bootstrap models")
        return self

    def predict_with_uncertainty(self, X: np.ndarray) -> list[UncertaintyEstimate]:
        """Predict with uncertainty estimates."""
        if not self.bootstrap_models:
            raise ValueError("Models must be fitted first")

        predictions = []

        for i in range(len(X)):
            sample = X[i : i + 1]

            # Get predictions from all bootstrap models
            boot_preds = [model.predict(sample)[0] for model in self.bootstrap_models]

            mean_pred = np.mean(boot_preds)
            std_pred = np.std(boot_preds)
            variance = np.var(boot_preds)

            # Confidence interval
            z_score = 1.96  # 95% CI
            ci_lower = mean_pred - z_score * std_pred
            ci_upper = mean_pred + z_score * std_pred

            # Uncertainty breakdown
            epistemic = std_pred  # Model uncertainty
            aleatoric = std_pred * 0.3  # Data uncertainty (approximation)

            estimate = UncertaintyEstimate(
                prediction=float(mean_pred),
                lower_bound=float(ci_lower),
                upper_bound=float(ci_upper),
                std_dev=float(std_pred),
                confidence_interval_width=float(ci_upper - ci_lower),
                prediction_variance=float(variance),
                epistemic_uncertainty=float(epistemic),
                aleatoric_uncertainty=float(aleatoric),
            )
            predictions.append(estimate)

        return predictions


class ModelSelector:
    """Select best model for given task."""

    def __init__(self):
        self.model_scores: dict[str, float] = {}
        self.candidate_models: dict[str, BaseEstimator] = {}

    def evaluate_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        models: dict[str, BaseEstimator],
        task: str = "regression",
    ) -> ModelSelectionResult:
        """Evaluate and rank models."""
        from sklearn.model_selection import cross_val_score

        self.candidate_models = models

        for name, model in models.items():
            try:
                scores = cross_val_score(
                    model,
                    X,
                    y,
                    cv=5,
                    scoring="r2" if task == "regression" else "accuracy",
                )
                self.model_scores[name] = float(np.mean(scores))
            except Exception as e:
                logger.warning(f"Error evaluating {name}: {e}", exc_info=True)
                self.model_scores[name] = 0.0

        # Rank models
        ranked = sorted(self.model_scores.items(), key=lambda x: x[1], reverse=True)
        best_model = ranked[0][0]

        # Determine if ensemble is better
        ensemble_candidates = [name for name, score in ranked[:3]]

        selection_reason = f"Model '{best_model}' shows best cross-validation performance ({self.model_scores[best_model]:.4f})"

        if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.05:
            selection_reason += ". Consider ensemble with top performers."

        result = ModelSelectionResult(
            best_model=best_model,
            selection_reason=selection_reason,
            top_models=ranked[:3],
            performance_scores=self.model_scores,
            recommended_ensemble=ensemble_candidates,
        )

        return result


class BoostingEngine:
    """Gradient boosting for improved predictions."""

    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.regressor: GradientBoostingRegressor | None = None
        self.classifier: GradientBoostingClassifier | None = None
        self.is_trained = False

    def fit(
        self, X: np.ndarray, y: np.ndarray, task: str = "regression"
    ) -> "BoostingEngine":
        """Train boosting model."""
        if task == "regression":
            self.regressor = GradientBoostingRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                random_state=42,
            )
            self.regressor.fit(X, y)
        else:
            self.classifier = GradientBoostingClassifier(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                random_state=42,
            )
            self.classifier.fit(X, y)

        self.is_trained = True
        logger.info(f"Boosting model trained with {self.n_estimators} estimators")
        return self

    def predict(self, X: np.ndarray, task: str = "regression") -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if task == "regression":
            return self.regressor.predict(X)
        else:
            return self.classifier.predict(X)

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from boosting model."""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        model = self.regressor if self.regressor else self.classifier
        importances = model.feature_importances_

        return {f"feature_{i}": float(imp) for i, imp in enumerate(importances)}


class BaggingEngine:
    """Bootstrap aggregating for variance reduction."""

    def __init__(
        self, n_estimators: int = 10, base_estimator: BaseEstimator | None = None
    ):
        self.n_estimators = n_estimators
        self.base_estimator = base_estimator
        self.regressor: BaggingRegressor | None = None
        self.classifier: BaggingClassifier | None = None
        self.is_trained = False

    def fit(
        self, X: np.ndarray, y: np.ndarray, task: str = "regression"
    ) -> "BaggingEngine":
        """Train bagging model."""
        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

        base_est = self.base_estimator or (
            DecisionTreeRegressor()
            if task == "regression"
            else DecisionTreeClassifier()
        )

        if task == "regression":
            self.regressor = BaggingRegressor(
                estimator=base_est, n_estimators=self.n_estimators, random_state=42
            )
            self.regressor.fit(X, y)
        else:
            self.classifier = BaggingClassifier(
                estimator=base_est, n_estimators=self.n_estimators, random_state=42
            )
            self.classifier.fit(X, y)

        self.is_trained = True
        logger.info(f"Bagging model trained with {self.n_estimators} estimators")
        return self

    def predict(self, X: np.ndarray, task: str = "regression") -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if task == "regression":
            return self.regressor.predict(X)
        else:
            return self.classifier.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get class probabilities."""
        if not self.is_trained or not self.classifier:
            raise ValueError("Classifier must be trained first")

        return self.classifier.predict_proba(X)

    def get_out_of_bag_score(self) -> float:
        """Get out-of-bag score."""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        model = self.regressor if self.regressor else self.classifier
        return float(model.oob_score_)
