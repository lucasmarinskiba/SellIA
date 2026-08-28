"""Fase H: Multi-Agent Orchestrator Tests"""

import pytest

from app.domains.fomo.ai_orchestrator_agent import (
    AIOrchestratorAgent,
    AgentCatalog,
    ContextRouter,
    ConflictResolver,
    UnifiedDashboard,
)


class TestAgentCatalog:
    def test_lists_all_seven_agents(self):
        agents = AgentCatalog.list_agents()
        assert len(agents) == 7

    def test_all_fases_represented(self):
        agents = AgentCatalog.list_agents()
        fases = {a["fase"] for a in agents}
        assert fases == {"A", "B", "C", "D", "E", "F", "G"}

    def test_get_agent_found(self):
        agent = AgentCatalog.get_agent("churn_prevention")
        assert agent is not None
        assert agent["fase"] == "G"

    def test_get_agent_not_found(self):
        assert AgentCatalog.get_agent("nonexistent") is None

    def test_every_agent_has_required_fields(self):
        for agent in AgentCatalog.list_agents():
            assert "id" in agent
            assert "fase" in agent
            assert "name" in agent
            assert "purpose" in agent
            assert "module" in agent


class TestContextRouter:
    def test_route_known_event(self):
        result = ContextRouter.route_event("cart_abandoned")
        assert result["known_event"] is True
        assert "timing" in result["agents_to_invoke"]
        assert "copywriter" in result["agents_to_invoke"]

    def test_route_unknown_event(self):
        result = ContextRouter.route_event("something_made_up")
        assert result["known_event"] is False
        assert result["agents_to_invoke"] == []

    def test_route_preserves_order(self):
        result = ContextRouter.route_event("customer_at_risk")
        assert result["agents_to_invoke"][0] == "churn_prevention"

    def test_route_includes_execution_plan_with_reasons(self):
        result = ContextRouter.route_event("stock_low")
        assert "execution_plan" in result
        for step in result["execution_plan"]:
            assert "agent" in step
            assert "reason" in step

    def test_route_carries_context(self):
        result = ContextRouter.route_event("purchase_completed", context={"order_id": "123"})
        assert result["context"]["order_id"] == "123"

    def test_all_referenced_agents_exist_in_catalog(self):
        catalog_ids = {a["id"] for a in AgentCatalog.list_agents()}
        for event, steps in ContextRouter.EVENT_AGENT_MAP.items():
            for step in steps:
                assert step["agent"] in catalog_ids, f"{step['agent']} referenced by {event} not in catalog"

    def test_list_known_events(self):
        events = ContextRouter.list_known_events()
        assert "daily_tick" in events
        assert "cart_abandoned" in events
        assert len(events) >= 8


class TestConflictResolver:
    def test_empty_proposals(self):
        result = ConflictResolver.resolve([])
        assert result["winners"] == []
        assert result["deferred"] == []

    def test_single_proposal_wins_no_conflict(self):
        proposals = [{"agent": "copywriter", "channel": "email"}]
        result = ConflictResolver.resolve(proposals)
        assert len(result["winners"]) == 1
        assert len(result["deferred"]) == 0

    def test_churn_prevention_outranks_general_campaign(self):
        proposals = [
            {"agent": "autonomous_campaign", "channel": "email"},
            {"agent": "churn_prevention", "channel": "sms"},
        ]
        result = ConflictResolver.resolve(proposals, max_per_day=1)
        assert result["winners"][0]["agent"] == "churn_prevention"
        assert len(result["deferred"]) == 1
        assert result["deferred"][0]["agent"] == "autonomous_campaign"

    def test_same_priority_tiebreak_by_urgency(self):
        proposals = [
            {"agent": "competitor_monitor", "channel": "email", "urgency": 0.4},
            {"agent": "autonomous_campaign", "channel": "email", "urgency": 0.9},
        ]
        result = ConflictResolver.resolve(proposals, max_per_day=1)
        assert result["winners"][0]["agent"] == "autonomous_campaign"

    def test_max_per_day_allows_multiple_winners(self):
        proposals = [
            {"agent": "churn_prevention", "channel": "sms"},
            {"agent": "autonomous_campaign", "channel": "email"},
            {"agent": "copywriter", "channel": "email"},
        ]
        result = ConflictResolver.resolve(proposals, max_per_day=2)
        assert len(result["winners"]) == 2
        assert len(result["deferred"]) == 1

    def test_deferred_has_reason_and_suggestion(self):
        proposals = [
            {"agent": "churn_prevention", "channel": "sms"},
            {"agent": "copywriter", "channel": "email"},
        ]
        result = ConflictResolver.resolve(proposals, max_per_day=1)
        deferred = result["deferred"][0]
        assert "reason" in deferred
        assert deferred["suggested_defer_to_days"] == 1

    def test_unknown_agent_gets_lowest_priority(self):
        proposals = [
            {"agent": "totally_unknown_agent", "channel": "email"},
            {"agent": "copywriter", "channel": "email"},
        ]
        result = ConflictResolver.resolve(proposals, max_per_day=1)
        assert result["winners"][0]["agent"] == "copywriter"

    def test_resolve_batch(self):
        proposals_by_customer = {
            "c1": [
                {"agent": "churn_prevention", "channel": "sms"},
                {"agent": "copywriter", "channel": "email"},
            ],
            "c2": [{"agent": "copywriter", "channel": "email"}],
        }
        result = ConflictResolver.resolve_batch(proposals_by_customer, max_per_day=1)
        assert result["total_customers"] == 2
        assert result["total_deferred"] == 1
        assert result["results"]["c1"]["winners"][0]["agent"] == "churn_prevention"


class TestUnifiedDashboard:
    def test_empty_decisions(self):
        result = UnifiedDashboard.build_dashboard([])
        assert result["total_decisions"] == 0

    def test_groups_by_agent_and_action(self):
        decisions = [
            {"agent": "copywriter", "action": "generated_copy", "timestamp": "2026-08-27T10:00:00Z"},
            {"agent": "copywriter", "action": "generated_copy", "timestamp": "2026-08-28T10:00:00Z"},
            {"agent": "churn_prevention", "action": "triggered_winback", "timestamp": "2026-08-28T09:00:00Z"},
        ]
        result = UnifiedDashboard.build_dashboard(decisions)
        assert result["decisions_by_agent"]["copywriter"] == 2
        assert result["decisions_by_agent"]["churn_prevention"] == 1
        assert result["decisions_by_action"]["generated_copy"] == 2

    def test_most_recent_sorted_descending(self):
        decisions = [
            {"agent": "a", "action": "x", "timestamp": "2026-08-25T10:00:00Z"},
            {"agent": "b", "action": "y", "timestamp": "2026-08-28T10:00:00Z"},
        ]
        result = UnifiedDashboard.build_dashboard(decisions)
        assert result["most_recent"][0]["timestamp"] == "2026-08-28T10:00:00Z"

    def test_most_recent_capped_at_ten(self):
        decisions = [
            {"agent": "a", "action": "x", "timestamp": f"2026-08-{i:02d}T10:00:00Z"}
            for i in range(1, 16)
        ]
        result = UnifiedDashboard.build_dashboard(decisions)
        assert len(result["most_recent"]) == 10

    def test_includes_conflict_summary_when_provided(self):
        conflict_results = {"total_deferred": 3}
        result = UnifiedDashboard.build_dashboard([], conflict_results)
        assert result["conflicts"]["total_deferred"] == 3

    def test_no_conflicts_key_when_not_provided(self):
        result = UnifiedDashboard.build_dashboard([])
        assert "conflicts" not in result


class TestAIOrchestratorAgent:
    def test_get_agent_catalog(self):
        agents = AIOrchestratorAgent.get_agent_catalog()
        assert len(agents) == 7

    def test_route_event(self):
        result = AIOrchestratorAgent.route_event("daily_tick")
        assert result["known_event"] is True

    def test_list_known_events(self):
        events = AIOrchestratorAgent.list_known_events()
        assert len(events) > 0

    def test_resolve_conflicts(self):
        proposals = [{"agent": "churn_prevention"}, {"agent": "copywriter"}]
        result = AIOrchestratorAgent.resolve_conflicts(proposals)
        assert result["winners"][0]["agent"] == "churn_prevention"

    def test_resolve_conflicts_batch(self):
        batch = {"c1": [{"agent": "copywriter"}]}
        result = AIOrchestratorAgent.resolve_conflicts_batch(batch)
        assert result["total_customers"] == 1

    def test_build_dashboard(self):
        decisions = [{"agent": "copywriter", "action": "x", "timestamp": "2026-08-28T10:00:00Z"}]
        result = AIOrchestratorAgent.build_dashboard(decisions)
        assert result["total_decisions"] == 1

    def test_handle_event_with_conflict_check_known_event(self):
        result = AIOrchestratorAgent.handle_event_with_conflict_check(
            "cart_abandoned", customer_id="cust1"
        )
        assert result["known_event"] is True
        assert result["customer_id"] == "cust1"
        assert result["conflict_check"] is not None
        assert len(result["conflict_check"]["winners"]) == 1  # max_per_day=1 default

    def test_handle_event_with_conflict_check_unknown_event(self):
        result = AIOrchestratorAgent.handle_event_with_conflict_check(
            "made_up_event", customer_id="cust1"
        )
        assert result["known_event"] is False
        assert result["conflict_check"] is None

    def test_handle_event_respects_existing_proposals(self):
        existing = [{"agent": "churn_prevention", "channel": "sms"}]
        result = AIOrchestratorAgent.handle_event_with_conflict_check(
            "new_visitor", customer_id="cust1", existing_proposals_today=existing, max_per_day=1
        )
        # churn_prevention (existing, priority 1) should still win over
        # segmentation/copywriter (priority 4/5) triggered by new_visitor
        assert result["conflict_check"]["winners"][0]["agent"] == "churn_prevention"
        assert len(result["conflict_check"]["deferred"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
