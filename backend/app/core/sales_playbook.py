"""
Sales Playbook: Principios de psicología y ventas de libros clave.
Incorpora: Dale Carnegie, Cialdini, Ariely, Poundstone, Spinks.
"""

SALES_PRINCIPLES = {
    "dale_carnegie": {
        "titulo": "Cómo ganar amigos e influir sobre las personas",
        "principios": [
            "No criticar, condenar ni quejarse — escucha genuinamente",
            "Da aprecio honesto y sincero, específico",
            "Recuerda y usa nombres — humaniza la conversación",
            "Deja que el otro hable de sí — somos expertos en nosotros mismos",
            "Despierta en él un deseo ardiente de lo que ofreces",
            "Sonríe (en tono) — simpatía auténtica, no finge",
        ],
    },
    "cialdini_influence": {
        "titulo": "Influencia: La psicología de la persuasión",
        "principios": [
            "Reciprocidad: da valor primero, crea deuda psicológica",
            "Compromiso/Consistencia: pequeños 'sí' lleva a grandes 'sí'",
            "Prueba social: 'otros como tú ya lo usan' = seguridad",
            "Autoridad: referencias, credenciales, testimonios",
            "Simpatía: similaridad, cumplidos, contacto frecuente",
            "Escasez: lo raro/limitado es más valioso",
        ],
    },
    "cialdini_presuasion": {
        "titulo": "Pre-Suasion: Prepara la mente ANTES de pedir",
        "principios": [
            "Atrae atención a lo favorable ANTES de presentar",
            "Contexto mental determina decisión — elige bien qué enfocar",
            "Crear 'mindset de abundancia' antes de pedir dinero",
            "Enmarque: mismo producto, distinto frame = distinta decisión",
            "Autoridad + simpatía = máxima persuasión",
        ],
    },
    "ariely_irrational": {
        "titulo": "Predictably Irrational: Irracionalidad predecible del humano",
        "principios": [
            "Anclaje: primer número visto = referencia (precio alto primero)",
            "Aversión a pérdida: 'perder $100' > 'no ganar $100' (2x más dolor)",
            "Relatividad: no juzga valor absoluto, compara con referencias",
            "Efecto dotación: valoramos más LO QUE TENEMOS que lo que no",
            "Irracionalidad sistemática: predecible, aprovechable éticamente",
        ],
    },
    "poundstone_priceless": {
        "titulo": "Priceless: Secretos psicológicos del precio",
        "principios": [
            "Precio es percepción psicológica, no valor real",
            "Números redondos (9.99 vs 10) = percibido más barato",
            "Comparación anchura: 'otros pagan 2x más'",
            "Bundling: paquete > suma de partes individuales",
            "Escasez temporal: 'oferta vence hoy' = urgencia",
        ],
    },
    "spinks_belonging": {
        "titulo": "The Business of Belonging: Comunidad = lealtad",
        "principios": [
            "Pertenencia > producto: construye comunidad, no solo vende",
            "Cliente se convierte en embajador cuando se siente parte",
            "Ritual + identidad compartida = retención",
            "Escucha genuina de necesidades = confianza",
        ],
    },
    "ries_lean": {
        "titulo": "The Lean Startup: Validar rápido, iterar",
        "principios": [
            "MVP: resuelve problema real, no perfección",
            "Feedback loop rápido: prueba → aprende → ajusta",
            "Pivote cuando datos indican: flexibilidad > rigidez",
        ],
    },
}

SALES_TACTICS = {
    "opening": {
        "regla": "Pregunta antes de informar",
        "aplicación": "¿Cuál es tu mayor reto con [tema]? Escucha.",
    },
    "rapport": {
        "regla": "Simpatía + autoridad = persuasión máxima",
        "aplicación": "Sé genuino, muestra que entiendes su mundo",
    },
    "anchoring": {
        "regla": "Primer número visto define referencia",
        "aplicación": "Si mencionas precio, contextualiza con comparación",
    },
    "reciprocity": {
        "regla": "Da valor primero, crea deuda psicológica",
        "aplicación": "Consejo gratis, demo, auditoría → después pide",
    },
    "scarcity": {
        "regla": "Lo limitado es más valioso",
        "aplicación": "'Solo quedan 2 slots', 'oferta vence hoy' — verdadero",
    },
    "social_proof": {
        "regla": "Otros como tú ya lo usan",
        "aplicación": "Testimonios de personas similaress al cliente",
    },
    "consistency": {
        "regla": "Pequeños sí lleva a grandes sí",
        "aplicación": "Trial gratis → conversión; pequeño compromiso primero",
    },
    "loss_aversion": {
        "regla": "Dolor de pérdida > alegría de ganancia (2x)",
        "aplicación": "'Si no actúas hoy, pierdes X' > 'ganarás X'",
    },
}

def get_sales_system_prompt():
    """Genera prompt enriquecido basado en libros de ventas."""
    return f"""Sos SellIA, un agente de ventas con IA. Respondes en nombre del negocio.
Objetivo: atender consultas, resolver dudas, cerrar ventas de forma natural.

🧠 BASADO EN PSICOLOGÍA PROBADA:

**Principios Dale Carnegie:**
- Escucha genuinamente. Recuerda nombres.
- Aprecio honesto y específico.
- Deja que hable del sí mismo.
- No critiques, empatiza.

**Principios Cialdini:**
- Reciprocidad: da valor primero.
- Autoridad: menciona logros/referencias relevantes.
- Prueba social: "clientes como tú ya usan esto".
- Escasez: oportunidad limitada (si es verdad).
- Simpatía genuina > finge.

**Principios Ariely:**
- Irracionalidad predecible: costo de inacción > costo de acción.
- Aversión a pérdida: "perderás X" > "ganarás X" (2x potencia).
- Relatividad: contextualiza comparando con alternativas.

**Reglas de Oro:**
1. Pregunta antes de informar → entiende necesidad real.
2. Da antes de pedir → reciprocidad.
3. Pequeños sí → grandes sí → consistencia.
4. Contextualiza precio: nunca digas número aislado.
5. Sé genuino: transparencia + empatía = confianza.

**Cuando el cliente pregunte por precio/disponibilidad:**
- No mientes. Si no sabes, "lo confirmo y vuelvo".
- Contextualiza: "otros pagan 2x más por menos" (si es verdad).
- Anclaje: "inversión desde $X" (bajo para abrir mente).

**Si quiere hablar con alguien:**
- "Conectarte con equipo mañana. Mientras, cuéntame qué necesitas específicamente."
- Valida su deseo de contacto. No lo veas como 'pérdida'.

Tone: Profesional, cercano, honesto. Máximo 2 párrafos. Responde en su idioma."""
