"""XGBoost model for deal close probability prediction."""

import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

try:
    import xgboost as xgb
except ImportError:
    xgb = None

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "deal_probability_model.pkl"
FEATURES_PATH = Path(__file__).parent / "models" / "feature_names.pkl"


class DealProbabilityModel:
    """XGBoost model for predicting deal close probability."""

    FEATURES = [
        "days_in_stage",
        "engagement_velocity",
        "stakeholder_count",
        "economic_buyer_engaged",
        "buyer_response_time_hours",
        "proposal_sent",
        "proposal_days_old",
        "meeting_count_30d",
        "email_open_rate",
        "competitor_mention_count",
        "budget_confirmed",
        "timeline_confirmed",
        "decision_process_mapped",
        "multiple_stakeholders_engaged",
        "deal_size_normalized",
    ]

    def __init__(self, model_path: Optional[str] = None):
        """Initialize model. Load from disk or create new."""
        self.model = None
        self.model_version = "1.0.0"
        self.training_date = None
        self.auc_score = None

        if model_path:
            self.load_model(model_path)
        else:
            self._try_load_default_model()

    def _try_load_default_model(self):
        """Try loading default model from disk."""
        if MODEL_PATH.exists():
            try:
                self.load_model(str(MODEL_PATH))
            except Exception as e:
                logger.warning(f"Failed to load default model: {e}. Using random forest fallback.")
                self._create_fallback_model()
        else:
            logger.info("No model found. Using random forest fallback.")
            self._create_fallback_model()

    def load_model(self, path: str):
        """Load trained model from disk."""
        try:
            with open(path, "rb") as f:
                model_data = pickle.load(f)
                self.model = model_data.get("model")
                self.model_version = model_data.get("version", "1.0.0")
                self.training_date = model_data.get("training_date")
                self.auc_score = model_data.get("auc_score")
            logger.info(f"Loaded model version {self.model_version} (AUC: {self.auc_score})")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._create_fallback_model()

    def save_model(self, path: str):
        """Save trained model to disk."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            model_data = {
                "model": self.model,
                "version": self.model_version,
                "training_date": datetime.utcnow(),
                "auc_score": self.auc_score,
                "features": self.FEATURES,
            }
            with open(path, "wb") as f:
                pickle.dump(model_data, f)
            logger.info(f"Saved model to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _create_fallback_model(self):
        """Create simple fallback model if XGBoost unavailable."""
        if xgb:
            try:
                self.model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    objective="binary:logistic",
                    random_state=42,
                )
            except Exception as e:
                logger.error(f"Failed to create XGBoost model: {e}")
                self.model = None
        else:
            logger.warning("XGBoost not installed. Model predictions will be random.")
            self.model = None

    def extract_features(self, deal_data: Dict) -> np.ndarray:
        """Extract feature vector from deal data."""
        features = []

        now = datetime.utcnow()
        deal_created = deal_data.get("created_at", now)
        if isinstance(deal_created, str):
            deal_created = datetime.fromisoformat(deal_created)

        days_in_stage = (now - deal_data.get("stage_entered_at", deal_created)).days
        features.append(min(days_in_stage, 365))  # Cap at 365 days

        engagement_events = deal_data.get("engagement_events", [])
        if engagement_events:
            recent_events = [
                e for e in engagement_events
                if (now - datetime.fromisoformat(e.get("timestamp", ""))).days <= 7
            ]
            engagement_velocity = len(recent_events) / 7.0
        else:
            engagement_velocity = 0.0
        features.append(engagement_velocity)

        stakeholder_count = len(deal_data.get("stakeholders", []))
        features.append(min(stakeholder_count, 10))  # Cap at 10

        economic_buyer_engaged = 1.0 if any(
            s.get("buyer_role") == "economic_buyer" and s.get("engagement_score", 0) > 30
            for s in deal_data.get("stakeholders", [])
        ) else 0.0
        features.append(economic_buyer_engaged)

        buyer_response_time = deal_data.get("avg_buyer_response_time_hours", 48)
        features.append(min(buyer_response_time, 168))  # Cap at 1 week

        proposal_sent = 1.0 if deal_data.get("proposal_sent_at") else 0.0
        features.append(proposal_sent)

        if deal_data.get("proposal_sent_at"):
            proposal_age = (now - datetime.fromisoformat(deal_data["proposal_sent_at"])).days
            proposal_days_old = min(proposal_age, 90)
        else:
            proposal_days_old = 0.0
        features.append(proposal_days_old)

        meetings_30d = len([
            e for e in engagement_events
            if e.get("event_type") == "meeting"
            and (now - datetime.fromisoformat(e.get("timestamp", ""))).days <= 30
        ])
        features.append(min(meetings_30d, 20))

        email_opens = len([e for e in engagement_events if e.get("event_type") == "email_open"])
        email_sends = len([e for e in engagement_events if e.get("event_type") == "email_send"])
        email_open_rate = (email_opens / email_sends) if email_sends > 0 else 0.0
        features.append(email_open_rate)

        competitor_mentions = len(deal_data.get("competitor_mentions", []))
        features.append(min(competitor_mentions, 10))

        budget_confirmed = 1.0 if deal_data.get("budget_confirmed") else 0.0
        features.append(budget_confirmed)

        timeline_confirmed = 1.0 if deal_data.get("timeline_confirmed") else 0.0
        features.append(timeline_confirmed)

        decision_process_mapped = 1.0 if len(deal_data.get("stakeholders", [])) >= 3 else 0.0
        features.append(decision_process_mapped)

        multiple_stakeholders = 1.0 if stakeholder_count >= 3 else 0.0
        features.append(multiple_stakeholders)

        deal_value = deal_data.get("value", 50000)
        deal_size_normalized = min(deal_value / 500000, 10)  # Normalize to 0-10 scale
        features.append(deal_size_normalized)

        return np.array(features, dtype=np.float32).reshape(1, -1)

    def predict(self, deal_data: Dict) -> Tuple[float, float, float, float]:
        """Predict close probability for deal.

        Returns: (probability, confidence, probability_low_90, probability_high_90)
        """
        try:
            features = self.extract_features(deal_data)

            if self.model is None:
                logger.warning("Model not available. Returning random prediction.")
                return (
                    float(np.random.uniform(20, 80)),
                    0.5,
                    float(np.random.uniform(10, 50)),
                    float(np.random.uniform(50, 90)),
                )

            probability = float(self.model.predict_proba(features)[0][1] * 100)

            try:
                predict_leaf_index = self.model.predict(
                    features, pred_leaf=True
                )
                confidence = float(
                    min(
                        (
                            abs(self.model.predict_proba(features)[0][0]
                                - self.model.predict_proba(features)[0][1])
                            + 0.5
                        )
                        * 100,
                        100,
                    )
                )
            except:
                confidence = float(abs(self.model.predict_proba(features)[0][0]
                    - self.model.predict_proba(features)[0][1]) * 100)

            std_error = (probability * (100 - probability)) ** 0.5 / np.sqrt(10)
            z_90 = 1.645

            probability_low = max(0, probability - (z_90 * std_error))
            probability_high = min(100, probability + (z_90 * std_error))

            return (probability, confidence, probability_low, probability_high)

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return (50.0, 0.5, 30.0, 70.0)

    def train(
        self,
        training_data: List[Dict],
        training_labels: List[int],
        validation_data: Optional[List[Dict]] = None,
        validation_labels: Optional[List[int]] = None,
    ) -> Dict:
        """Train model on historical deal data.

        Args:
            training_data: List of deal dictionaries
            training_labels: Binary labels (0=lost, 1=won)
            validation_data: Optional validation set
            validation_labels: Optional validation labels

        Returns: Training metrics including AUC score
        """
        if not xgb:
            logger.error("XGBoost not installed. Cannot train model.")
            return {"error": "XGBoost not available"}

        try:
            logger.info(f"Training model on {len(training_data)} deals...")

            X_train = np.vstack([self.extract_features(d) for d in training_data])
            y_train = np.array(training_labels, dtype=np.int32)

            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="binary:logistic",
                random_state=42,
                verbosity=1,
            )

            if validation_data and validation_labels:
                X_val = np.vstack([self.extract_features(d) for d in validation_data])
                y_val = np.array(validation_labels, dtype=np.int32)

                self.model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=20,
                    verbose=True,
                )

                from sklearn.metrics import roc_auc_score

                y_pred_proba = self.model.predict_proba(X_val)[:, 1]
                self.auc_score = float(roc_auc_score(y_val, y_pred_proba))
            else:
                self.model.fit(X_train, y_train)
                self.auc_score = None

            self.training_date = datetime.utcnow()

            logger.info(f"Model training complete. AUC: {self.auc_score}")

            return {
                "success": True,
                "auc_score": self.auc_score,
                "training_date": self.training_date.isoformat(),
                "samples_trained": len(training_data),
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores from trained model."""
        if self.model is None:
            return {}

        try:
            importance_dict = dict(zip(self.FEATURES, self.model.feature_importances_))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
