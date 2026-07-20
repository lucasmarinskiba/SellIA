"""
Brain ↔ Computer Use Coordinator.

Brain decide. Computer Use ejecuta.
Loop infinito: Analyze → Decide → Execute → Monitor → Learn → Repeat.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class BrainComputerUseCoordinator:
    """Orquesta Brain + Computer Use en loop infinito."""

    def __init__(self, brain_engine, computer_use_agent):
        """
        brain_engine: Super Seller Engine (problem detector, strategy generator, etc)
        computer_use_agent: BrowserAgent (ejecuta automations en navegador)
        """
        self.brain = brain_engine
        self.computer_use = computer_use_agent
        self.execution_history: List[Dict[str, Any]] = []
        self.learning_log: List[Dict[str, Any]] = []

    async def run_sales_cycle(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ciclo de venta automático end-to-end.

        1. Brain: Analiza producto + mercado
        2. Brain: Genera estrategia
        3. Brain: Detecta problemas
        4. Brain: Selecciona acciones óptimas
        5. Computer Use: Ejecuta (vía navegador)
        6. Computer Use: Monitorea resultados
        7. Brain: Analiza resultados → aprender
        8. Loop: Optimiza siguientes acciones
        """

        logger.info(f"Starting sales cycle for product: {product.get('name')}")

        # ========== FASE 1: BRAIN ANALYSIS ==========
        logger.info("PHASE 1: Brain analyzes market + product")

        # Análisis mercado
        market_analysis = await self.brain.analyze_market(product)
        logger.info(f"Market: {market_analysis.get('demand_level')} demand, {market_analysis.get('competition_level')} competition")

        # Genera estrategia
        strategy = await self.brain.generate_strategy(product, market_analysis)
        logger.info(f"Strategy: {strategy.get('segment')} segment, channels: {strategy.get('recommended_channels')}")

        # Detecta problemas
        problems = await self.brain.detect_problems(product, market_analysis)
        logger.info(f"Problems detected: {len(problems)} issues")

        # Selecciona acciones óptimas
        actions = await self.brain.select_optimal_actions(strategy, problems)
        logger.info(f"Actions to execute: {len(actions)} total")

        # ========== FASE 2: COMPUTER USE EXECUTION ==========
        logger.info("PHASE 2: Computer Use executes actions")

        execution_results = []
        for i, action in enumerate(actions):
            logger.info(f"Executing action {i+1}/{len(actions)}: {action.get('type')}")

            # Brain decide: qué acción específica (con parámetros)
            # Computer Use ejecuta en navegador
            result = await self._execute_brain_action(action, product)
            execution_results.append(result)

            # Log for learning
            self.execution_history.append({
                "action": action,
                "result": result,
                "timestamp": self._current_timestamp(),
            })

        # ========== FASE 3: MONITORING + FEEDBACK ==========
        logger.info("PHASE 3: Monitor results + feedback to brain")

        monitoring_data = await self._monitor_execution(execution_results)
        logger.info(f"Monitoring: {monitoring_data.get('success_rate')}% success rate")

        # ========== FASE 4: LEARNING LOOP ==========
        logger.info("PHASE 4: Brain learns + optimizes")

        learning_feedback = await self.brain.analyze_execution_results(
            actions=actions,
            results=execution_results,
            monitoring=monitoring_data
        )

        self.learning_log.append({
            "cycle": len(self.learning_log) + 1,
            "product": product.get("name"),
            "actions": len(actions),
            "success_rate": monitoring_data.get("success_rate"),
            "learnings": learning_feedback.get("learnings"),
            "next_improvements": learning_feedback.get("next_improvements"),
        })

        logger.info(f"Learning: {learning_feedback.get('summary')}")

        return {
            "status": "completed",
            "product": product.get("name"),
            "market_analysis": market_analysis,
            "strategy": strategy,
            "problems_detected": len(problems),
            "actions_executed": len(execution_results),
            "success_rate": monitoring_data.get("success_rate"),
            "learning_feedback": learning_feedback,
        }

    async def _execute_brain_action(self, brain_action: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta acción ordenada por Brain vía Computer Use.

        Brain decide → Computer Use ejecuta.
        """

        action_type = brain_action.get("type")
        action_params = brain_action.get("params", {})

        logger.info(f"Executing brain action: {action_type}")

        try:
            if action_type == "list_on_platform":
                # Brain decide: "list on MercadoLibre"
                # Computer Use: ejecuta script
                platform = action_params.get("platform")
                script = self.computer_use.get_script(f"{platform}_create_listing", product)
                result = await self.computer_use.run_automation_script(script)

            elif action_type == "create_ads_campaign":
                # Brain decide: "create Meta Ads campaign"
                # Computer Use: ejecuta
                platform = action_params.get("platform")
                campaign_config = action_params.get("config", {})
                script = self.computer_use.get_script(f"{platform}_create_campaign", campaign_config)
                result = await self.computer_use.run_automation_script(script)

            elif action_type == "schedule_social_post":
                # Brain decide: "schedule Instagram post at 3pm"
                # Computer Use: ejecuta
                platform = action_params.get("platform")
                post_config = action_params.get("config", {})
                script = self.computer_use.get_script(f"{platform}_schedule_post", post_config)
                result = await self.computer_use.run_automation_script(script)

            elif action_type == "dynamic_price_update":
                # Brain decide: "update price to $X.XX based on demand"
                # Computer Use: ejecuta
                price = action_params.get("new_price")
                platform = action_params.get("platform")
                script = self.computer_use.get_script(f"{platform}_update_price", {"price": price})
                result = await self.computer_use.run_automation_script(script)

            elif action_type == "extract_competitor_data":
                # Brain decide: "analyze competitors"
                # Computer Use: extrae datos vía navegador
                competitors = action_params.get("competitor_urls", [])
                data = []
                for url in competitors:
                    script = [
                        {"type": "navigate", "params": {"url": url}},
                        {"type": "extract_data", "params": {"selector": ".price", "attribute": "innerText"}},
                        {"type": "extract_data", "params": {"selector": ".rating", "attribute": "innerText"}},
                    ]
                    competitor_data = await self.computer_use.run_automation_script(script)
                    data.append(competitor_data)
                result = {"status": "success", "competitor_data": data}

            else:
                result = {"status": "error", "message": f"Unknown action type: {action_type}"}

            return result

        except Exception as e:
            logger.error(f"Error executing action {action_type}: {str(e)}")
            return {"status": "error", "action": action_type, "error": str(e)}

    async def _monitor_execution(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Monitorea resultados ejecución.

        Computer Use reporta qué pasó. Brain lo analiza.
        """

        total = len(results)
        successes = sum(1 for r in results if r.get("status") == "success")
        success_rate = (successes / total * 100) if total > 0 else 0

        # Extrae datos importantes para feedback
        monitoring = {
            "total_actions": total,
            "successful": successes,
            "failed": total - successes,
            "success_rate": success_rate,
            "results": results,
        }

        logger.info(f"Monitoring: {successes}/{total} actions successful ({success_rate}%)")

        return monitoring

    def _current_timestamp(self) -> str:
        """Timestamp actual."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    async def run_continuous_optimization(self, account_id: str, interval_hours: int = 6):
        """
        Loop infinito: cada N horas, Brain analiza + optimiza.

        Continuous improvement.
        """

        logger.info(f"Starting continuous optimization loop (every {interval_hours}h)")

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"Optimization iteration {iteration}")

            try:
                # Brain: analiza performance actual
                performance = await self.brain.analyze_performance(account_id)

                # Brain: identifica oportunidades mejora
                improvements = await self.brain.identify_improvements(performance)

                # Brain: selecciona acciones próximas
                next_actions = await self.brain.select_actions(improvements)

                logger.info(f"Iteration {iteration}: {len(next_actions)} improvements identified")

                # Computer Use: ejecuta mejoras
                for action in next_actions:
                    await self._execute_brain_action(action, {})

                # Learning: guardar en log
                self.learning_log.append({
                    "iteration": iteration,
                    "improvements": len(next_actions),
                    "timestamp": self._current_timestamp(),
                })

            except Exception as e:
                logger.error(f"Error in optimization iteration {iteration}: {str(e)}")

            # Esperar próxima iteración
            await asyncio.sleep(interval_hours * 3600)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Retorna resumen de learnings acumulados."""

        return {
            "total_cycles": len(self.learning_log),
            "total_actions": len(self.execution_history),
            "avg_success_rate": (
                sum(l.get("success_rate", 0) for l in self.learning_log) / len(self.learning_log)
                if self.learning_log else 0
            ),
            "learning_log": self.learning_log[-10:],  # Últimas 10 iteraciones
        }
