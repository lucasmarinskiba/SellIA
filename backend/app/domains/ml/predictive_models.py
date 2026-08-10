"""Production ML models using scikit-learn for real data."""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
import pickle
import os

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


class DealClosePredictor:
    """
    Production deal close prediction using RandomForest.
    Trained on historical sales data.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "intent_score",
            "days_in_stage",
            "engagement_score",
            "company_size_score",
            "budget_confirmed",
            "demo_attended",
            "proposal_sent",
            "stage_numeric",
        ]

        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
            logger.info(f"Loaded pre-trained model: {model_path}")
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize with default Random Forest model."""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
        logger.info("Initialized RandomForest model for deal close prediction")

    def train(self, training_data: List[Dict[str, Any]], labels: List[int]):
        """
        Train model on historical deal data.

        Args:
            training_data: List of deal features dicts
            labels: Binary labels (1=closed, 0=lost)
        """
        if not training_data:
            logger.warning("No training data provided")
            return

        X = np.array([self._extract_features(d) for d in training_data])
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        logger.info(
            f"Deal close model trained: train_score={train_score:.3f}, test_score={test_score:.3f}"
        )

    def predict(self, deal_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Predict close probability for a deal.

        Returns:
            (probability, feature_importance_dict)
        """
        if not self.model:
            self._initialize_model()

        features = np.array([self._extract_features(deal_data)])
        probability = self.model.predict_proba(features)[0][1]

        # Feature importance
        importance_dict = {
            name: float(imp)
            for name, imp in zip(
                self.feature_names, self.model.feature_importances_
            )
        }

        return probability, importance_dict

    def _extract_features(self, deal_data: Dict[str, Any]) -> List[float]:
        """Extract feature vector from deal data."""
        stage_map = {
            "qualification": 1,
            "proposal": 2,
            "negotiation": 3,
            "closing": 4,
        }

        return [
            deal_data.get("intent_score", 0.5),
            min(deal_data.get("days_in_stage", 0), 30),  # Cap at 30 days
            deal_data.get("engagement_score", 0.5),
            deal_data.get("company_size_score", 0.5),
            float(deal_data.get("budget_confirmed", False)),
            float(deal_data.get("demo_attended", False)),
            float(deal_data.get("proposal_sent", False)),
            float(stage_map.get(deal_data.get("stage", "qualification"), 1)),
        ]

    def save(self, path: str = None):
        """Save model to disk."""
        path = path or os.path.join(MODEL_DIR, "deal_close_model.pkl")
        joblib.dump(self.model, path)
        logger.info(f"Model saved: {path}")


class ChurnPredictor:
    """Production churn prediction using Gradient Boosting."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = [
            "subscription_months",
            "email_opens_30d",
            "logins_30d",
            "support_tickets_30d",
            "feature_adoption_percent",
            "monthly_active_users",
            "nps_score",
            "data_growth_trend",
        ]

        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
            logger.info(f"Loaded pre-trained model: {model_path}")
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize with default Gradient Boosting model."""
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )
        logger.info("Initialized GradientBoosting model for churn prediction")

    def train(
        self, training_data: List[Dict[str, Any]], labels: List[int]
    ):
        """Train on historical customer data."""
        if not training_data:
            logger.warning("No training data provided")
            return

        X = np.array([self._extract_features(d) for d in training_data])
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        logger.info(
            f"Churn model trained: train_score={train_score:.3f}, test_score={test_score:.3f}"
        )

    def predict(self, customer_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Predict churn probability.

        Returns:
            (probability, risk_signals)
        """
        if not self.model:
            self._initialize_model()

        features = np.array([self._extract_features(customer_data)])
        probability = self.model.predict_proba(features)[0][1]

        # Identify risk signals
        risk_signals = []
        if customer_data.get("email_opens_30d", 0) < 3:
            risk_signals.append("low_email_engagement")
        if customer_data.get("logins_30d", 0) < 7:
            risk_signals.append("declining_logins")
        if customer_data.get("support_tickets_30d", 0) > 10:
            risk_signals.append("high_support_tickets")
        if customer_data.get("nps_score", 50) < 30:
            risk_signals.append("low_nps")
        if customer_data.get("feature_adoption_percent", 50) < 30:
            risk_signals.append("low_adoption")

        return probability, risk_signals

    def _extract_features(self, customer_data: Dict[str, Any]) -> List[float]:
        """Extract feature vector from customer data."""
        return [
            customer_data.get("subscription_months", 0),
            customer_data.get("email_opens_30d", 0),
            customer_data.get("logins_30d", 0),
            customer_data.get("support_tickets_30d", 0),
            customer_data.get("feature_adoption_percent", 50) / 100,
            min(customer_data.get("monthly_active_users", 0) / 50, 1.0),
            (customer_data.get("nps_score", 0) + 100) / 200,  # Normalize -100 to 100
            customer_data.get("data_growth_trend", 0) / 100,  # Monthly growth %
        ]

    def save(self, path: str = None):
        """Save model to disk."""
        path = path or os.path.join(MODEL_DIR, "churn_model.pkl")
        joblib.dump(self.model, path)
        logger.info(f"Model saved: {path}")


class ExpansionScorer:
    """Expansion opportunity scoring using Logistic Regression."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = [
            "tier_utilization",
            "feature_adoption",
            "spending_ratio",
            "tenure_months",
            "revenue_trend",
        ]

        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
            logger.info(f"Loaded pre-trained model: {model_path}")
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize with Logistic Regression."""
        self.model = LogisticRegression(random_state=42)
        logger.info("Initialized LogisticRegression model for expansion scoring")

    def train(self, training_data: List[Dict[str, Any]], labels: List[int]):
        """Train on historical expansion data."""
        if not training_data:
            logger.warning("No training data provided")
            return

        X = np.array([self._extract_features(d) for d in training_data])
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        logger.info(
            f"Expansion model trained: train_score={train_score:.3f}, test_score={test_score:.3f}"
        )

    def predict(self, customer_data: Dict[str, Any]) -> float:
        """Predict expansion probability."""
        if not self.model:
            self._initialize_model()

        features = np.array([self._extract_features(customer_data)])
        probability = self.model.predict_proba(features)[0][1]

        return probability

    def _extract_features(self, customer_data: Dict[str, Any]) -> List[float]:
        """Extract feature vector."""
        return [
            customer_data.get("tier_utilization", 0.5),
            customer_data.get("feature_adoption", 0.5),
            customer_data.get("spending_ratio", 0.5),
            min(customer_data.get("tenure_months", 0) / 24, 1.0),
            customer_data.get("revenue_trend", 0),
        ]

    def save(self, path: str = None):
        """Save model to disk."""
        path = path or os.path.join(MODEL_DIR, "expansion_model.pkl")
        joblib.dump(self.model, path)
        logger.info(f"Model saved: {path}")


# Global model instances
deal_close_model = DealClosePredictor()
churn_model = ChurnPredictor()
expansion_model = ExpansionScorer()
