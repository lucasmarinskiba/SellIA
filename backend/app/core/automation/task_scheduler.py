"""
Task Scheduler — CUÁNDO ejecutar cada tarea.

Soporta:
- Cron expressions (recurring)
- One-time scheduling
- Event-triggered scheduling
- Smart timing (avoid peak hours, optimize for conversions)

Built-in schedules:
- Post products: 9am, 2pm, 6pm (3 times daily)
- Respond to inquiries: every 30 min (real-time)
- Send email campaigns: 10am, 3pm, 7pm (3 times daily)
- Check inventory: hourly sync
- Monitor performance: every 2 hours
- Weekly report: Monday 8am
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from croniter import croniter
import asyncio

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Programa tareas: cuándo ejecutar qué."""

    def __init__(self):
        self.tasks: Dict[str, Any] = {}  # task_id → Task
        self.task_list: List[Any] = []
        self.lock = asyncio.Lock()

    async def add_task(self, task: Any) -> None:
        """Registra tarea (recurrente o one-time)."""
        async with self.lock:
            self.tasks[task.id] = task
            self.task_list.append(task)

            # Calcular next_run
            if task.schedule == "once":
                # Ya tiene next_run
                pass
            elif task.enabled:
                task.next_run = self._calculate_next_run(task.schedule)

            logger.info(f"Task added: {task.name} (id: {task.id})")

    async def get_tasks_for_now(self) -> List[Any]:
        """Obtiene tasks que deben ejecutarse ahora."""
        now = datetime.utcnow()
        tasks_due = []

        async with self.lock:
            for task in self.task_list:
                if not task.enabled:
                    continue

                if task.next_run and task.next_run <= now:
                    tasks_due.append(task)

                    # Schedule next run if recurring
                    if task.schedule != "once":
                        task.next_run = self._calculate_next_run(task.schedule)
                    else:
                        task.enabled = False  # One-time tasks are disabled after execution

        logger.debug(f"Tasks due now: {len(tasks_due)}")
        return tasks_due

    async def disable_task(self, task_id: str) -> None:
        """Deshabilita tarea."""
        async with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
                logger.info(f"Task disabled: {task_id}")

    async def enable_task(self, task_id: str) -> None:
        """Habilita tarea."""
        async with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
                logger.info(f"Task enabled: {task_id}")

    async def list_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas."""
        async with self.lock:
            return [
                {
                    "id": task.id,
                    "name": task.name,
                    "enabled": task.enabled,
                    "schedule": task.schedule,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                }
                for task in self.task_list
            ]

    async def update_task_schedule(self, task_id: str, new_schedule: str) -> bool:
        """Actualiza schedule de una tarea."""
        async with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            task.schedule = new_schedule
            task.next_run = self._calculate_next_run(new_schedule)
            logger.info(f"Task schedule updated: {task_id} → {new_schedule}")
            return True

    @staticmethod
    def _calculate_next_run(schedule: str) -> Optional[datetime]:
        """Calcula próxima ejecución basado en cron expression."""
        try:
            # Validar y obtener próxima ejecución
            cron = croniter(schedule, datetime.utcnow())
            next_run = cron.get_next(datetime)
            return next_run
        except Exception as e:
            logger.error(f"Invalid cron expression '{schedule}': {str(e)}")
            return None

    async def record_execution(self, task_id: str) -> None:
        """Registra que una tarea fue ejecutada."""
        async with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].last_run = datetime.utcnow()


# Built-in task definitions
def get_default_tasks() -> List[Dict[str, Any]]:
    """Retorna tareas por defecto (recetas automáticas)."""
    return [
        # ========== VENTAS ==========
        {
            "name": "Post productos (mañana)",
            "schedule": "0 9 * * *",  # 9am diario
            "enabled": True,
            "description": "Publica 5 productos nuevos",
        },
        {
            "name": "Post productos (tarde)",
            "schedule": "0 14 * * *",  # 2pm diario
            "enabled": True,
            "description": "Publica 3 productos al mediodía",
        },
        {
            "name": "Post productos (noche)",
            "schedule": "0 18 * * *",  # 6pm diario
            "enabled": True,
            "description": "Publica 2 productos al atardecer",
        },

        # ========== INQUIRIES ==========
        {
            "name": "Responder inquiries",
            "schedule": "*/30 * * * *",  # Cada 30 min
            "enabled": True,
            "description": "Responde automáticamente a preguntas de clientes",
        },

        # ========== EMAILS ==========
        {
            "name": "Enviar campañas (mañana)",
            "schedule": "0 10 * * *",  # 10am diario
            "enabled": True,
            "description": "Envía emails de bienvenida",
        },
        {
            "name": "Enviar campañas (tarde)",
            "schedule": "0 15 * * *",  # 3pm diario
            "enabled": True,
            "description": "Envía emails de oferta especial",
        },
        {
            "name": "Enviar campañas (noche)",
            "schedule": "0 19 * * *",  # 7pm diario
            "enabled": True,
            "description": "Envía emails de seguimiento",
        },

        # ========== INVENTORY ==========
        {
            "name": "Sincronizar inventario",
            "schedule": "0 * * * *",  # Cada hora
            "enabled": True,
            "description": "Sincroniza stock entre plataformas",
        },

        # ========== ANALYTICS ==========
        {
            "name": "Monitorear performance",
            "schedule": "0 */2 * * *",  # Cada 2 horas
            "enabled": True,
            "description": "Extrae métricas de plataformas",
        },

        # ========== REPORTS ==========
        {
            "name": "Reporte semanal",
            "schedule": "0 8 * * MON",  # Monday 8am
            "enabled": True,
            "description": "Genera reporte de ventas semanal",
        },

        # ========== INFLUENCER ==========
        {
            "name": "Rastrear influencers",
            "schedule": "0 */6 * * *",  # Cada 6 horas
            "enabled": True,
            "description": "Calcula comisiones de influencers",
        },

        # ========== REVIEWS ==========
        {
            "name": "Analizar reviews",
            "schedule": "0 12 * * *",  # Mediodía
            "enabled": True,
            "description": "Análisis de sentimiento de reviews",
        },
    ]


class SmartScheduler:
    """Scheduler inteligente que adapta timing basado en performance."""

    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}

    async def record_performance(
        self,
        task_name: str,
        execution_time: float,
        success: bool,
        engagement_metric: Optional[float] = None,
    ) -> None:
        """Registra performance de tarea para optimizar timing."""
        if task_name not in self.performance_history:
            self.performance_history[task_name] = []

        self.performance_history[task_name].append({
            "timestamp": datetime.utcnow(),
            "execution_time": execution_time,
            "success": success,
            "engagement": engagement_metric,
        })

        # Keep only last 100 records per task
        if len(self.performance_history[task_name]) > 100:
            self.performance_history[task_name] = self.performance_history[task_name][-100:]

        # Analyze and potentially adjust schedule
        await self._analyze_and_adjust(task_name)

    async def _analyze_and_adjust(self, task_name: str) -> None:
        """Analiza y ajusta schedule si es necesario."""
        history = self.performance_history.get(task_name, [])
        if len(history) < 10:
            return  # Need more data

        # Simple heuristic: if last 5 runs had low engagement, shift timing
        recent = history[-5:]
        avg_engagement = sum(r.get("engagement", 0) for r in recent) / len(recent)

        if avg_engagement < 0.3:  # Low engagement threshold
            logger.warning(
                f"Task '{task_name}' has low engagement ({avg_engagement:.2f}). "
                "Consider adjusting schedule."
            )

    async def get_optimal_schedule(self, task_name: str) -> str:
        """Retorna schedule óptimo basado en histórico."""
        history = self.performance_history.get(task_name, [])
        if not history:
            return "0 9 * * *"  # Default

        # Find time slot with best performance
        times_by_hour: Dict[int, List[float]] = {}
        for record in history:
            hour = record["timestamp"].hour
            engagement = record.get("engagement", 0)
            if hour not in times_by_hour:
                times_by_hour[hour] = []
            times_by_hour[hour].append(engagement)

        if not times_by_hour:
            return "0 9 * * *"  # Default

        # Find best hour
        best_hour = max(
            times_by_hour.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
        )[0]

        return f"0 {best_hour} * * *"
