# SellIA Neural Brain - Quick Start Guide

## Installation & Setup

```python
# Import the complete neural brain
from backend.app.core.ml.neural_networks import SelliasNeuralBrain
import numpy as np

# Create instance
brain = SelliasNeuralBrain()
```

## Training the Brain

```python
# Prepare your training data
training_data = {
    "X": X_train,  # Feature matrix (n_samples, n_features)
    "y_sales": y_sales,  # Sales amounts
    "y_churn": y_churn,  # Churn labels (0/1)
    "y_demand": y_demand,  # Demand/revenue
    "y_quality": y_quality,  # Lead quality scores
}

# Train all 47 neural networks
state = brain.train_all_networks(training_data)

# Check status
print(brain.get_brain_status())
```

## Making Predictions

### Sales Prediction
```python
# Predict if a customer will close and how much they'll spend
insight = brain.predict_sales_outcome(customer_data, customer_profile)

# Access results
print(f"Close probability: {insight.predictions['close_probability']:.0%}")
print(f"Deal size estimate: ${insight.predictions['deal_size']:,.0f}")
print(f"Timeline: {insight.predictions['estimated_timeline_days']} days")
print(f"Lead quality: {insight.predictions['lead_quality_score']:.0f}/100")
print(f"\nNext actions: {insight.next_actions}")
```

### Churn Prediction
```python
# Predict if customer will churn
insight = brain.predict_customer_churn(customer_data, customer_profile)

# Access results
print(f"Churn risk: {insight.predictions['churn_probability']:.0%}")
print(f"Days until churn: {insight.predictions['estimated_churn_days']}")
print(f"Retention actions: {insight.recommendations}")
```

### Marketing Optimization
```python
# Get optimal strategy (pricing, channel, budget)
budget = 50000  # $50k marketing budget
insight = brain.optimize_marketing_strategy(market_data, budget)

# Access results
print(f"Recommended price: ${insight.predictions['recommended_price']:.2f}")
print(f"Best channel: {insight.predictions['best_channel']}")
print(f"Expected response rate: {insight.predictions['expected_response_rate']:.0%}")
print(f"Expected revenue: ${insight.predictions['expected_revenue']:,.0f}")
print(f"Expected ROI: {insight.predictions['expected_roi']:.1f}x")
```

### Anomaly Detection
```python
# Find unusual market activity
anomalies = brain.detect_market_anomalies(market_data)

for anomaly in anomalies:
    print(f"Anomaly: {anomaly.headline}")
    print(f"Severity: {anomaly.insights}")
    print(f"Action: {anomaly.next_actions[0]}")
```

## Continuous Learning

```python
# Update with new data as it arrives
new_data = X_new  # New feature samples
new_labels = y_new  # New labels

result = brain.continuous_learning_update(new_data, new_labels)

# Check learning progress
print(f"Update successful: {result['update_success']}")
print(f"Iteration: {result['iteration']}")
print(f"Loss: {result['loss']:.6f}")
```

## System Monitoring

```python
# Get system metrics
metrics = brain.get_system_metrics()

print(f"Total predictions: {metrics['total_predictions']}")
print(f"Model accuracy: {metrics['model_accuracy']:.1%}")
print(f"Networks active: {metrics['networks_active']}/{metrics['total_networks']}")
print(f"Status: {'✓ All systems online' if metrics['networks_active'] == metrics['total_networks'] else '⚠ Incomplete'}")
```

## Individual Network Usage

### Direct Network Access
```python
from backend.app.core.ml.neural_networks import (
    SalesPredictionNetwork,
    DemandForecastingNetwork,
    PricingOptimizationNetwork,
    MarketPatternRecognizer,
)

# Use individual networks
sales_net = SalesPredictionNetwork()
sales_net.fit(X_train, y_close, y_timeline, y_deal)
predictions = sales_net.predict(X_test)

# Get specific insights
for pred in predictions:
    print(f"Close: {pred.will_close}")
    print(f"Probability: {pred.close_probability:.0%}")
    print(f"Timeline: {pred.estimated_timeline_days} days")
    print(f"Deal size: ${pred.deal_size_estimate:,.0f}")
```

### Pattern Recognition
```python
recognizer = MarketPatternRecognizer()
recognizer.fit(X_train)

# Detect patterns in market data
patterns = recognizer.detect_patterns(time_series)

print(f"Market sentiment: {patterns.market_sentiment}")
print(f"Volatility: {patterns.volatility:.2%}")
print(f"Trend strength: {patterns.trend_strength:.2%}")
print(f"Patterns: {[p.description for p in patterns.patterns]}")
```

### Ensemble Predictions
```python
from backend.app.core.ml.neural_networks import EnsemblePredictor

ensemble = EnsemblePredictor()
ensemble.add_model("model1", model1)
ensemble.add_model("model2", model2)
ensemble.add_model("model3", model3)

ensemble.fit(X_train, y_train)

# Get predictions with confidence
preds, votes = ensemble.predict_with_votes(X_test)

for i, vote_list in enumerate(votes):
    print(f"Sample {i}:")
    for vote in vote_list:
        print(f"  {vote.model_name}: {vote.prediction:.2f} (confidence: {vote.confidence:.0%})")
```

## Advanced Features

### Uncertainty Quantification
```python
from backend.app.core.ml.neural_networks import UncertaintyEstimator

estimator = UncertaintyEstimator()
estimator.fit(X_train, y_train, base_model)

# Get predictions with confidence intervals
predictions = estimator.predict_with_uncertainty(X_test)

for pred in predictions:
    print(f"Prediction: {pred.prediction:.2f}")
    print(f"95% CI: [{pred.lower_bound:.2f}, {pred.upper_bound:.2f}]")
    print(f"Uncertainty: ±{pred.std_dev:.2f}")
```

### Feature Importance
```python
from backend.app.core.ml.neural_networks import FeatureImportance

analyzer = FeatureImportanceNetwork()
analyzer.fit(X_train, y_train, feature_names)

importance = analyzer.predict(X_test)[0]
print(f"Top features: {importance.top_features}")
print(f"Key drivers: {importance.key_drivers}")
print(f"Surprising: {importance.surprising_findings}")
```

### Online Learning
```python
from backend.app.core.ml.neural_networks import OnlineLearningEngine

learner = OnlineLearningEngine()
learner.initialize(X_initial, y_initial)

# Learn continuously as new data arrives
for X_batch, y_batch in data_stream:
    update = learner.update(X_batch, y_batch)
    print(f"Epoch {update.epoch}: Loss = {update.loss:.6f}")
```

### Transfer Learning
```python
from backend.app.core.ml.neural_networks import TransferLearningEngine

transfer = TransferLearningEngine()
transfer.train_source_domain(X_source, y_source, "enterprise_sales")

# Transfer to new domain (e.g., SMB sales)
result = transfer.transfer_to_target(X_source, y_source, X_target, y_target)

print(f"Accuracy gain: {result.transfer_accuracy_gain:+.1%}")
print(f"Training time saved: {result.estimated_training_time_saved} hours")
```

## Data Formats

### Input Features (X)
- Type: numpy.ndarray (2D: samples × features)
- Shape: (n_samples, n_features)
- Values: Typically normalized to [-1, 1] or [0, 1]
- Example: (1000, 20) for 1000 customers with 20 features

### Target Variables (y)
- Sales: Float32, range [0, ∞)
- Churn: Int32, values {0, 1}
- Demand: Float32, range [0, ∞)
- Quality: Float32, range [0, 100]

### Customer Profile (dict)
```python
customer_profile = {
    "transaction_frequency": 5,  # transactions per month
    "avg_transaction_value": 10000,  # average deal size
    "purchase_volatility": 0.3,  # price sensitivity
    "engagement_score": 0.8,  # 0-1
}
```

## Output Formats

### Comprehensive Insight
```python
{
    "insight_type": "sales",  # sales, churn, strategy, market
    "headline": "Deal closing probability: 75% (WARM lead)",
    "confidence": 0.85,
    "predictions": {
        "will_close": True,
        "close_probability": 0.75,
        "deal_size": 45000,
        # ... more predictions
    },
    "recommendations": [
        "Use consultative selling approach",
        "Prioritize email channel",
        # ...
    ],
    "risks": [
        "Price sensitive",
        "Long sales cycle",
    ],
    "opportunities": [
        "High-probability deal",
        "Large deal size",
    ],
    "patterns_detected": [
        "Trend pattern in market",
        "High engagement behavior",
    ],
    "next_actions": [
        "Schedule demo within 30 days",
        "Accelerate close",
    ],
    "timestamp": "2025-01-05T10:30:00",
}
```

## Performance Tips

1. **Batch Processing**: Process multiple customers together for efficiency
   ```python
   insights = [brain.predict_sales_outcome(X[i:i+1], profiles[i]) 
               for i in range(0, len(X), 100)]
   ```

2. **Parallel Inference**: Use multiprocessing for large batches
   ```python
   from multiprocessing import Pool
   with Pool(4) as p:
       results = p.map(brain.predict_sales_outcome, customers)
   ```

3. **Caching**: Store predictions for recent customers
   ```python
   prediction_cache = {}
   if customer_id not in prediction_cache:
       prediction_cache[customer_id] = brain.predict_sales_outcome(...)
   ```

4. **Selective Updates**: Only retrain networks with new relevant data
   ```python
   if new_sales_data_available:
       brain.sales_predictor.fit(X_new, y_new)  # Just one network
   ```

## Troubleshooting

### Model Not Trained
```python
# Always train before prediction
if not brain.state.prediction_models_trained:
    brain.train_all_networks(training_data)
```

### Poor Predictions
```python
# Check model accuracy
metrics = brain.get_system_metrics()
if metrics['model_accuracy'] < 0.7:
    # Retrain with more data
    brain.train_all_networks(more_training_data)
```

### Memory Issues
```python
# Process in smaller batches
batch_size = 100
for i in range(0, len(X), batch_size):
    batch_insight = brain.predict_sales_outcome(X[i:i+batch_size])
```

## API Reference Summary

| Method | Purpose | Returns |
|--------|---------|---------|
| `train_all_networks(data)` | Train all 47 networks | BrainState |
| `predict_sales_outcome(X, profile)` | Sales prediction | ComprehensiveInsight |
| `predict_customer_churn(X, profile)` | Churn prediction | ComprehensiveInsight |
| `optimize_marketing_strategy(X, budget)` | Marketing optimization | ComprehensiveInsight |
| `detect_market_anomalies(X)` | Anomaly detection | List[ComprehensiveInsight] |
| `continuous_learning_update(X, y)` | Online learning | Dict |
| `get_brain_status()` | System status | Dict |
| `get_system_metrics()` | Performance metrics | Dict |

## Next Steps

1. **Prepare Data**: Collect historical customer, sales, and market data
2. **Train Brain**: Run `brain.train_all_networks(training_data)`
3. **Validate**: Test predictions on known outcomes
4. **Deploy**: Integrate into sales workflow
5. **Monitor**: Track `get_system_metrics()` regularly
6. **Iterate**: Use `continuous_learning_update()` with new data

## Support & Resources

- Full documentation: See NEURAL_NETWORKS_IMPLEMENTATION.md
- Source code: backend/app/core/ml/neural_networks/
- Example usage patterns above

---

**SellIA's Neural Brain is ready to supercharge your sales predictions and decisions.**
