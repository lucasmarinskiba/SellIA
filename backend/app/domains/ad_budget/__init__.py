"""Ad-budget autopilot — autonomous cross-channel ad-spend reallocation.

Closes the loop opened by the ledger: it reads real spend (from the
`ad_spend_*` GL accounts or the ad platform APIs) and real revenue
(orders attributed to each channel), computes ROAS per channel over a
rolling window, and reallocates the daily budget toward the channels
that convert best — inside owner-set guardrails (floors, caps, max
daily shift, kill-ROAS). It can run in recommend-only mode or apply
budget changes automatically via the channel connectors.
"""
