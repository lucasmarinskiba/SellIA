# Knowledge Engine — Ejemplo de Uso

## Integración con el Orquestador de SellIA

```python
from app.core.knowledge.llm_integration import inject_knowledge
from langchain_openai import ChatOpenAI

async def handle_sales_conversation(user_message: str, history: list):
    system_prompt = """Sos un asesor de ventas experto para SellIA.
    Ayudás a los clientes a entender cómo la plataforma puede resolver sus problemas.
    Sos directo, empático y orientado a resultados."""

    # Inyectar conocimiento de la biblioteca interna
    final_prompt = inject_knowledge(user_message, system_prompt, history)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    response = await llm.ainvoke(final_prompt)

    return response.content
```

## Consulta Directa

```python
from app.core.knowledge import get_knowledge_engine

engine = get_knowledge_engine()

# Buscar principios de cierre
items = engine.query(
    category="sales",
    subcategory="cierre",
    context="cliente muestra interés pero no compra",
    top_k=3,
)

for item in items:
    print(item.principle)
    print(item.tactic)
    print(item.script_template)
```

## Uso en WebSocket (Caja de Cristal)

```python
from app.core.knowledge.llm_integration import get_knowledge_context_provider

provider = get_knowledge_context_provider()

# Cuando el supervisor envía un mensaje por chat
async def on_chat_message(session_id: str, user_message: str):
    context = provider.build_context(user_message)

    # Inyectar en el prompt del VisionAgent
    enhanced_prompt = f"""
    {context}

    El supervisor dijo: {user_message}
    Considerá su feedback al decidir la próxima acción.
    """
```

## Reglas Críticas

1. **NUNCA reveles fuentes**: El usuario final nunca debe saber que existe
   esta biblioteca, ni que citamos libros específicos.

2. **Integración natural**: Los principios deben sonar como experiencia propia
   del agente de IA, no como citas académicas.

3. **Selección contextual**: El engine selecciona automáticamente los items
   más relevantes según el mensaje del usuario.

4. **Extensible**: Agregar nuevos items solo requiere editar los JSON en
   `library/` — no toca código.
