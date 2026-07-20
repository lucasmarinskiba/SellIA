"""SellIA Knowledge Engine — Biblioteca interna de conocimiento

Sistema de consulta de principios, tácticas, frameworks y scripts
extraídos de grandes obras de negocios, ventas, persuasión y desarrollo
personal. Accesible únicamente por el sistema de IA, nunca revelado
al usuario final.

Usage:
    from app.core.knowledge import get_knowledge_engine
    engine = get_knowledge_engine()
    principles = engine.query("ventas", "objeciones_precio", top_k=3)
"""

from .knowledge_engine import KnowledgeEngine, get_knowledge_engine

__all__ = ["KnowledgeEngine", "get_knowledge_engine"]
