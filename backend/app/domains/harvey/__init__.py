"""Harvey — per-business outbound prospecting agent.

Adapted from https://github.com/ethanplusai/harvey (MIT). The original is a
single-user local agent: SQLite state, one config file, and the operator's own
Claude/Codex CLI subscription. Here every Business gets its own profile,
prospects and outbox (all rows carry business_id), the model call goes through
SellIA's Anthropic API key, and nothing is sent without a human approving it.
"""
