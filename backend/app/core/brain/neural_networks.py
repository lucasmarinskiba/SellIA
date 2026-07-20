"""Neural Networks & Reasoning Pathways.

Redes de decisión que conectan agentes + tools + contexto.

Implementa:
  - Bayesian Networks (inferencia de probabilidades)
  - Decision Trees (lógica de decisión)
  - Causal Inference (qué causa qué)
  - Reinforcement Learning (optimización de políticas)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
import json
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────
# BAYESIAN NETWORKS
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class ConditionalProbabilityTable:
    """Tabla de probabilidad condicional: P(node | parents)."""
    node_name: str
    parent_names: List[str] = field(default_factory=list)
    probabilities: Dict[Tuple[Any, ...], Dict[str, float]] = field(
        default_factory=dict
    )

    def get_probability(self, parent_values: Tuple[Any, ...],
                       node_value: str) -> float:
        """Obtiene P(node=node_value | parents=parent_values)."""
        key = parent_values if parent_values else ()
        return self.probabilities.get(key, {}).get(node_value, 0.5)

    def set_probability(self, parent_values: Tuple[Any, ...],
                       node_value: str, prob: float) -> None:
        """Establece probabilidad."""
        key = parent_values if parent_values else ()
        if key not in self.probabilities:
            self.probabilities[key] = {}
        self.probabilities[key][node_value] = prob


@dataclass
class BayesianNode:
    """Nodo en red Bayesiana."""
    name: str
    possible_values: List[str]
    cpt: ConditionalProbabilityTable
    parents: List[BayesianNode] = field(default_factory=list)
    children: List[BayesianNode] = field(default_factory=list)

    def add_parent(self, parent: BayesianNode) -> None:
        if parent not in self.parents:
            self.parents.append(parent)
            parent.children.append(self)

    def add_child(self, child: BayesianNode) -> None:
        if child not in self.children:
            self.children.append(child)
            child.parents.append(self)


class BayesianNetwork:
    """Red Bayesiana para inferencia probabilística."""

    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, BayesianNode] = {}
        self.evidence: Dict[str, str] = {}
        self.posterior: Dict[str, Dict[str, float]] = {}

    def add_node(self, node: BayesianNode) -> None:
        """Agrega nodo a la red."""
        self.nodes[node.name] = node

    def add_edge(self, parent_name: str, child_name: str) -> None:
        """Agrega relación causal parent → child."""
        if parent_name in self.nodes and child_name in self.nodes:
            self.nodes[child_name].add_parent(self.nodes[parent_name])

    def set_evidence(self, node_name: str, value: str) -> None:
        """Establece evidencia observada."""
        if node_name in self.nodes:
            self.evidence[node_name] = value

    def infer(self, target_node: str) -> Dict[str, float]:
        """Inferencia: P(target | evidence) usando variable elimination."""
        if target_node not in self.nodes:
            return {}

        posteriors = self._variable_elimination(target_node)
        self.posterior[target_node] = posteriors
        return posteriors

    def _variable_elimination(self, target: str) -> Dict[str, float]:
        """Variable elimination algorithm."""
        # Simplified: usa forward-backward
        node = self.nodes[target]
        probs = {}
        for value in node.possible_values:
            prob = self._compute_probability(target, value)
            probs[value] = prob

        # Normalizar
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        return probs

    def _compute_probability(self, node_name: str, value: str) -> float:
        """Computa P(node=value | evidence)."""
        if node_name in self.evidence:
            return 1.0 if self.evidence[node_name] == value else 0.0

        node = self.nodes[node_name]
        if not node.parents:
            # Nodo raíz: usa prior
            return 0.5

        # Itersa sobre combinaciones de parent values
        parent_names = [p.name for p in node.parents]
        parent_values_combinations = self._get_parent_value_combinations(
            [self.nodes[pn] for pn in parent_names]
        )

        prob = 0.0
        for combo in parent_values_combinations:
            parent_evidence_compatible = all(
                self.evidence.get(pn, combo[i]) == combo[i]
                for i, pn in enumerate(parent_names)
            )
            if parent_evidence_compatible:
                cond_prob = node.cpt.get_probability(combo, value)
                parent_joint_prob = self._compute_parent_joint_prob(combo, parent_names)
                prob += cond_prob * parent_joint_prob

        return prob

    def _get_parent_value_combinations(self,
                                       parents: List[BayesianNode]) -> List[Tuple[str, ...]]:
        """Genera todas las combinaciones de valores de parents."""
        if not parents:
            return [()]
        first_parent = parents[0]
        rest_combos = self._get_parent_value_combinations(parents[1:])
        result = []
        for value in first_parent.possible_values:
            for combo in rest_combos:
                result.append((value,) + combo)
        return result

    def _compute_parent_joint_prob(self, parent_values: Tuple[str, ...],
                                   parent_names: List[str]) -> float:
        """Computa P(parent1=v1, parent2=v2, ...) recursivamente."""
        if not parent_names:
            return 1.0
        parent_name = parent_names[0]
        parent_value = parent_values[0]
        parent_prob = self.infer(parent_name).get(parent_value, 0.5)
        rest_prob = self._compute_parent_joint_prob(parent_values[1:], parent_names[1:])
        return parent_prob * rest_prob


# ─────────────────────────────────────────────────────────────────────────
# CAUSAL INFERENCE
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class CausalEdge:
    """Relación causal: X → Y (direccionada)."""
    source: str
    target: str
    strength: float = 0.7  # 0–1, confianza
    mechanism: str = ""    # Cómo causa X a Y?
    conditions: List[str] = field(default_factory=list)  # Cuándo aplica?


class CausalGraph:
    """Grafo causal: identifica relaciones causa-efecto."""

    def __init__(self, name: str):
        self.name = name
        self.edges: Dict[str, List[CausalEdge]] = {}
        self.nodes: set[str] = set()

    def add_edge(self, edge: CausalEdge) -> None:
        """Agrega relación causal."""
        self.nodes.add(edge.source)
        self.nodes.add(edge.target)
        if edge.source not in self.edges:
            self.edges[edge.source] = []
        self.edges[edge.source].append(edge)

    def get_causes(self, effect: str) -> List[CausalEdge]:
        """¿Qué causa 'effect'?"""
        causes = []
        for source, edges in self.edges.items():
            for edge in edges:
                if edge.target == effect:
                    causes.append(edge)
        return causes

    def get_effects(self, cause: str) -> List[CausalEdge]:
        """¿Qué causa 'cause'?"""
        return self.edges.get(cause, [])

    def counterfactual_inference(self, intervention: Dict[str, Any],
                                 target: str) -> Dict[str, Any]:
        """Inferencia contrafáctica: ¿Qué pasaría si hacemos X?"""
        # If we set 'source' to value, what happens to target?
        result = {}
        for source, value in intervention.items():
            effects = self._trace_effects(source, value, target, depth=3)
            result[source] = effects
        return result

    def _trace_effects(self, source: str, value: Any, target: str,
                      depth: int) -> Dict[str, Any]:
        """Traza efectos de intervención."""
        if depth == 0 or source not in self.edges:
            return {}

        traced = {}
        for edge in self.edges.get(source, []):
            if edge.target == target:
                traced[edge.target] = {
                    "strength": edge.strength,
                    "mechanism": edge.mechanism,
                }
            else:
                # Recursive: sigue el camino
                sub_effects = self._trace_effects(edge.target, value, target, depth - 1)
                if sub_effects:
                    traced[edge.target] = sub_effects

        return traced


# ─────────────────────────────────────────────────────────────────────────
# REINFORCEMENT LEARNING
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class State:
    """Estado: vector de features."""
    features: Dict[str, float]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def distance_to(self, other: State) -> float:
        """Distancia Euclidiana a otro estado."""
        diff = sum((self.features.get(k, 0) - other.features.get(k, 0)) ** 2
                   for k in set(self.features.keys()) | set(other.features.keys()))
        return diff ** 0.5


@dataclass
class Action:
    """Acción: cambio en el estado."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    """Transición: state → action → next_state + reward."""
    state: State
    action: Action
    next_state: State
    reward: float
    terminal: bool = False


class ReinforcementLearner:
    """Learner Q-learning para optimización de políticas."""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9,
                 exploration_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.transitions: List[Transition] = []

    def record_transition(self, transition: Transition) -> None:
        """Registra transición para aprender."""
        self.transitions.append(transition)

    def update_q_value(self, state_key: str, action_name: str,
                      reward: float, next_state_value: float) -> float:
        """Q-learning update: Q(s,a) ← Q(s,a) + α(r + γ max_a' Q(s',a') - Q(s,a))."""
        if state_key not in self.q_table:
            self.q_table[state_key] = {}

        old_q = self.q_table[state_key].get(action_name, 0.0)
        td_error = reward + self.discount_factor * next_state_value - old_q
        new_q = old_q + self.learning_rate * td_error

        self.q_table[state_key][action_name] = new_q
        return new_q

    def get_best_action(self, state_key: str) -> str:
        """Greedy: escoge mejor acción conocida."""
        if state_key not in self.q_table:
            return "explore"
        return max(self.q_table[state_key].items(), key=lambda x: x[1])[0]

    def get_policy(self, state_key: str) -> Dict[str, float]:
        """Retorna política π(a|s)."""
        if state_key not in self.q_table:
            return {}
        q_values = self.q_table[state_key]
        max_q = max(q_values.values()) if q_values else 0
        policy = {}
        for action, q_value in q_values.items():
            # Softmax
            policy[action] = (q_value - (max_q - 1)) if q_values else 1.0 / len(q_values)
        return policy

    def learn_from_episodes(self) -> None:
        """Aprende de transiciones registradas."""
        for transition in self.transitions:
            state_key = json.dumps(transition.state.features, sort_keys=True)
            next_state_key = json.dumps(transition.next_state.features, sort_keys=True)
            next_best_q = max(
                self.q_table.get(next_state_key, {}).values(),
                default=0.0
            )
            self.update_q_value(
                state_key, transition.action.name,
                transition.reward, next_best_q
            )


# ─────────────────────────────────────────────────────────────────────────
# NEURAL PATHWAY IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────────


class SalesClosurePathway:
    """Pathway neural: lead → closure probability usando Bayesian inference."""

    def __init__(self):
        self.network = BayesianNetwork("sales_closure")
        self._build_network()

    def _build_network(self) -> None:
        """Construye red Bayesiana para predecir cierre."""
        # Nodos
        deal_value_node = BayesianNode(
            "deal_value",
            ["high", "medium", "low"],
            ConditionalProbabilityTable("deal_value", []),
        )
        deal_value_node.cpt.set_probability((), "high", 0.3)
        deal_value_node.cpt.set_probability((), "medium", 0.4)
        deal_value_node.cpt.set_probability((), "low", 0.3)

        buyer_authority_node = BayesianNode(
            "buyer_authority",
            ["high", "medium", "low"],
            ConditionalProbabilityTable("buyer_authority", []),
        )
        buyer_authority_node.cpt.set_probability((), "high", 0.4)
        buyer_authority_node.cpt.set_probability((), "medium", 0.35)
        buyer_authority_node.cpt.set_probability((), "low", 0.25)

        close_probability = BayesianNode(
            "closure_probability",
            ["high", "medium", "low"],
            ConditionalProbabilityTable(
                "closure_probability",
                ["deal_value", "buyer_authority"]
            ),
        )
        # P(closure | deal, authority)
        close_probability.cpt.set_probability(("high", "high"), "high", 0.9)
        close_probability.cpt.set_probability(("high", "medium"), "high", 0.7)
        close_probability.cpt.set_probability(("medium", "high"), "high", 0.75)
        close_probability.cpt.set_probability(("low", "high"), "high", 0.5)
        close_probability.cpt.set_probability(("low", "low"), "high", 0.1)

        self.network.add_node(deal_value_node)
        self.network.add_node(buyer_authority_node)
        self.network.add_node(close_probability)
        self.network.add_edge("deal_value", "closure_probability")
        self.network.add_edge("buyer_authority", "closure_probability")

    def predict_closure(self, deal_value: str, buyer_authority: str) -> Dict[str, float]:
        """Predice probabilidad de cierre."""
        self.network.set_evidence("deal_value", deal_value)
        self.network.set_evidence("buyer_authority", buyer_authority)
        return self.network.infer("closure_probability")


class ChurnPreventionPathway:
    """Pathway: detecta churn risk + recomienda intervención."""

    def __init__(self):
        self.causal_graph = CausalGraph("churn_prevention")
        self._build_causal_graph()

    def _build_causal_graph(self) -> None:
        """Construye grafo causal."""
        # Causas de churn
        self.causal_graph.add_edge(CausalEdge(
            "inactivity",
            "churn",
            strength=0.8,
            mechanism="No se ve valor si no usa"
        ))
        self.causal_graph.add_edge(CausalEdge(
            "support_tickets_unresolved",
            "churn",
            strength=0.7,
            mechanism="Frustración por falta de soporte"
        ))
        self.causal_graph.add_edge(CausalEdge(
            "competitor_offer",
            "churn",
            strength=0.6,
            mechanism="Atractivo de alternativa"
        ))
        self.causal_graph.add_edge(CausalEdge(
            "product_upgrade",
            "retention",
            strength=0.75,
            mechanism="Más valor = más sticky"
        ))
        self.causal_graph.add_edge(CausalEdge(
            "qbr_conducted",
            "retention",
            strength=0.8,
            mechanism="Alineamiento + revisión de ROI"
        ))

    def predict_churn_and_intervene(self, indicators: Dict[str, bool]) -> Dict[str, Any]:
        """Predice churn + recomienda intervención."""
        churn_causes = []
        if indicators.get("inactivity"):
            churn_causes.append("inactivity")
        if indicators.get("support_unresolved"):
            churn_causes.append("support_tickets_unresolved")

        interventions = self.causal_graph.counterfactual_inference(
            {"support_tickets_unresolved": False, "qbr_conducted": True},
            "churn"
        )
        return {
            "churn_causes": churn_causes,
            "recommended_interventions": interventions,
        }


class RevenueOptimizationPathway:
    """Pathway RL: optimiza pricing + upsell strategy."""

    def __init__(self):
        self.learner = ReinforcementLearner(learning_rate=0.15)

    def optimize_pricing(self, current_state: State, possible_actions: List[Action]) -> Action:
        """Escoge mejor action para maximizar revenue."""
        state_key = json.dumps(current_state.features, sort_keys=True)
        policy = self.learner.get_policy(state_key)

        if policy:
            best_action_name = max(policy.items(), key=lambda x: x[1])[0]
            return Action(best_action_name)
        else:
            # Explorar
            return possible_actions[0] if possible_actions else Action("hold_price")

    def learn_from_pricing_experiment(self, transitions: List[Transition]) -> None:
        """Aprende de experimentos de pricing."""
        for t in transitions:
            self.learner.record_transition(t)
        self.learner.learn_from_episodes()


# ─────────────────────────────────────────────────────────────────────────
# NEURAL NETWORK REGISTRY
# ─────────────────────────────────────────────────────────────────────────


class NeuralPathwayRegistry:
    """Registry de pathways neurales."""

    def __init__(self):
        self.pathways: Dict[str, Any] = {
            "sales_closure": SalesClosurePathway(),
            "churn_prevention": ChurnPreventionPathway(),
            "revenue_optimization": RevenueOptimizationPathway(),
        }

    def get_pathway(self, pathway_name: str) -> Any:
        """Obtiene pathway por nombre."""
        return self.pathways.get(pathway_name)

    def infer(self, pathway_name: str, **inputs) -> Dict[str, Any]:
        """Ejecuta inferencia en pathway."""
        pathway = self.get_pathway(pathway_name)
        if not pathway:
            return {"error": "pathway not found"}

        # Delegation by pathway type
        if pathway_name == "sales_closure":
            return pathway.predict_closure(
                inputs.get("deal_value", "medium"),
                inputs.get("buyer_authority", "medium")
            )
        elif pathway_name == "churn_prevention":
            return pathway.predict_churn_and_intervene(inputs)
        elif pathway_name == "revenue_optimization":
            return {"optimization": "TODO"}

        return {}


# Export
__all__ = [
    "ConditionalProbabilityTable", "BayesianNode", "BayesianNetwork",
    "CausalEdge", "CausalGraph",
    "State", "Action", "Transition", "ReinforcementLearner",
    "SalesClosurePathway", "ChurnPreventionPathway",
    "RevenueOptimizationPathway",
    "NeuralPathwayRegistry",
]
