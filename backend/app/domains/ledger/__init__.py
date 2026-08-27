"""Ledger domain — double-entry general ledger, financial statements,
bank reconciliation and period close.

This is the accounting backbone that the finance autopilot, the
inter-department orchestrator and the ad-budget ROAS engine read from.
Every money movement in the platform (order paid, refund issued, payout
sent, ad spend, subscription charge) is posted here as a balanced journal
entry against a per-business chart of accounts.
"""
