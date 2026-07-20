"""
ML Trainer

Entrena modelos simples con scikit-learn basados en datos recolectados.
Modelos: intent classifier, response quality predictor, lead scorer.
"""

import os
import pickle
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.feedback.models import MLTrainingData
from app.core.logger import get_logger

logger = get_logger(__name__)

MODELS_DIR = "data/ml_models"
os.makedirs(MODELS_DIR, exist_ok=True)


class SimpleIntentClassifier:
    """Clasificador de intenciones basado en TF-IDF + LogisticRegression."""

    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.version = "0.0.0"
        self.accuracy = 0.0

    def train(self, texts: list, labels: list) -> float:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split

            if len(texts) < 10:
                logger.warning("Not enough data to train intent classifier")
                return 0.0

            X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

            self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X_train_vec = self.vectorizer.fit_transform(X_train)
            X_test_vec = self.vectorizer.transform(X_test)

            self.classifier = LogisticRegression(max_iter=1000, class_weight="balanced")
            self.classifier.fit(X_train_vec, y_train)

            self.accuracy = self.classifier.score(X_test_vec, y_test)
            self.version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            logger.info(f"Trained intent classifier v{self.version} with accuracy {self.accuracy:.3f}")
            return self.accuracy
        except Exception as e:
            logger.error(f"Failed to train intent classifier: {e}")
            return 0.0

    def predict(self, text: str) -> Optional[str]:
        if not self.vectorizer or not self.classifier:
            return None
        vec = self.vectorizer.transform([text])
        return self.classifier.predict(vec)[0]

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "classifier": self.classifier, "version": self.version, "accuracy": self.accuracy}, f)

    def load(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.classifier = data["classifier"]
            self.version = data.get("version", "unknown")
            self.accuracy = data.get("accuracy", 0.0)
            return True
        except Exception:
            return False


async def train_all_models(db: AsyncSession) -> Dict[str, float]:
    """Entrena todos los modelos ML con datos recolectados."""
    results = {}

    # 1. Intent Classifier
    try:
        result = await db.execute(
            select(MLTrainingData).where(MLTrainingData.data_type == "intent_accuracy")
        )
        samples = result.scalars().all()

        if len(samples) >= 10:
            texts = [s.features.get("message_content", "") for s in samples]
            labels = [s.label or "unknown" for s in samples]

            model = SimpleIntentClassifier()
            accuracy = model.train(texts, labels)

            if accuracy > 0:
                model.save(f"{MODELS_DIR}/intent_classifier.pkl")
                results["intent_classifier"] = accuracy

                # Update model version in DB
                for s in samples:
                    s.model_version = model.version
                await db.commit()
    except Exception as e:
        logger.error(f"Intent classifier training failed: {e}")

    # 2. Response Quality Predictor (placeholder for future)
    # 3. Lead Scorer (placeholder for future)

    logger.info(f"ML training completed: {results}")
    return results


async def get_model_status() -> Dict[str, Any]:
    """Obtiene el estado de los modelos entrenados."""
    status = {}
    for model_name in ["intent_classifier", "response_quality", "lead_scorer"]:
        path = f"{MODELS_DIR}/{model_name}.pkl"
        if os.path.exists(path):
            import os.path
            mtime = os.path.getmtime(path)
            status[model_name] = {
                "exists": True,
                "last_trained": datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
            }
        else:
            status[model_name] = {"exists": False}
    return status
