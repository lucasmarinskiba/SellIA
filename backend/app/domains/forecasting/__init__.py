"""Demand forecasting.

A proper multi-series forecasting pipeline:

    load  ->  feature-engineer  ->  backtest (rolling origin)  ->  select /
    weight models  ->  refit on full history  ->  produce an H-step-ahead
    probabilistic forecast  ->  persist  ->  serve + track accuracy

Models are an ensemble of a statistical family (seasonal-naive, Theta,
Holt-Winters ETS, optional SARIMA) and a gradient-boosted machine-learning
model on lag/calendar/price/ad-spend features, with Croston/SBA for
intermittent series. Per series, the ensemble weights come from a
rolling-origin backtest (weight ∝ softmax(−MASE)).

Optional heavy backends (statsmodels, lightgbm, holidays) are imported
defensively — absent, the pipeline falls back to pure-numpy / scikit-learn
implementations: lower accuracy, same contract.

Consumers: inventory reorder planning, the finance cash-flow forecast,
the ad-budget autopilot, and the inter-department orchestrator.
"""
