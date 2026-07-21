"""
Sales Playbook: Principios de psicología, ventas, negociación, business intelligence.
Incorpora: Carnegie, Cialdini, Ariely, Poundstone, Spinks, Ries, Rackham, Cardone,
Konrath, Ziglar, Fisher, Voss, Drucker, Ellis, Weinberg.
"""

SALES_PRINCIPLES = {
    "rackham_spin": {
        "titulo": "SPIN Selling: Preguntas que venden",
        "principios": [
            "Situation: entiende contexto, no asumas",
            "Problem: identifica dificultades reales del cliente",
            "Implication: CRÍTICO — desarrolla consecuencias (por qué importa)",
            "Need-Payoff: cliente dice por qué lo necesita (motivación interna)",
            "Evita preguntas abiertas después de problemas — debilitan",
            "Objeción temprana = falta de implicaciones desarrolladas",
        ],
    },
    "cardone_10x": {
        "titulo": "The 10X Rule: Acción masiva + mindset",
        "principios": [
            "Piensa 10x más grande, no 2x",
            "Acción masiva = diferenciador (no solo estrategia)",
            "Objeción = falta de claridad, no 'no' definitivo",
            "Mentalidad de abundancia: hay clientes para todos",
            "Persistencia: reintentos ≠ acoso",
            "Compromiso > talento",
        ],
    },
    "konrath_b2b": {
        "titulo": "Selling to Big Companies: B2B complejos",
        "principios": [
            "Múltiples stakeholders = múltiples objeciones esperadas",
            "Buyer journey largo: construye credibilidad gradualmente",
            "ROI language > feature language",
            "Timing > perfección: a veces el no es 'no ahora'",
            "Persistencia sin ser molesto: toca pero deja respirar",
            "Expertise first, venta second",
        ],
    },
    "ziglar_closing": {
        "titulo": "Secrets of Closing the Sale: Cierre natural",
        "principios": [
            "Cierre es natural si hiciste bien todo antes",
            "Assumptive close: 'cuándo empezamos' vs 'te interesa'",
            "5-7 intentos de cierre esperados, no es rechazo",
            "Objeción = oportunidad para clarificar, no fin",
            "Urgencia real (no fake) cierra conversación",
            "Reflexión: 'si dices yes, qué pasa mañana' (miedo oculto)",
        ],
    },
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

NEGOTIATION_PRINCIPLES = {
    "fisher_getting_to_yes": {
        "titulo": "Getting to Yes: Negociación en los méritos (AVANZADA)",
        "principios": [
            "Separa personas de problemas: ataca problema, no adversario.",
            "Focus en INTERESES, no posiciones: pregunta 'por qué' 7 veces.",
            "BATNA: conoce tu mejor alternativa. Úsala como referencia, no amenaza.",
            "Genera opciones para ganancia MUTUA: crecimiento exponencial, no reparto.",
            "Criterios OBJETIVOS: apela a estándares externos (mercado, industria, ley).",
            "Nunca cedes sin razón: pregunta 'por qué' antes de cualquier cambio.",
            "Intereses múltiples: cada parte tiene varios intereses (no solo precio).",
            "Problema shared: 'cómo resolvemos juntos' vs 'yo vs vos'.",
            "Lluvia de ideas: genera 50+ opciones ANTES de decidir (sin evaluarlas).",
            "Implementación clara: acuerdo es solo el 20%, ejecución es 80%.",
        ],
    },
    "voss_never_split": {
        "titulo": "Never Split the Difference: Empatía táctica + Control",
        "principios": [
            "Tactical empathy: entiende emoción, usa para influencia",
            "Mirroring: repite últimas 3 palabras para validar",
            "Labeling: 'parece que te molesta X' (nomina emoción)",
            "Calibrated questions: 'cómo', 'qué', 'por qué' (no cerradas)",
            "'No' es seguro: activa pensamiento analítico, baja defensas",
            "Anchoring: quien ancla primero generalmente gana",
            "Presión de tiempo = urgencia: úsala, no la ignores",
        ],
    },
    "cialdini_influence_complete": {
        "titulo": "Influence (7 principios): Fundamentos de persuasión",
        "principios": [
            "1. Reciprocidad: si das, te deben. Da valor primero.",
            "2. Commitment & Consistency: pequeño 'sí' → gran 'sí'.",
            "3. Social Proof: 'otros como tú ya lo hicieron'.",
            "4. Authority: credibilidad, expertise, referencias.",
            "5. Liking: similitud, cumplidos, cooperación genuina.",
            "6. Scarcity: lo raro/limitado es más valioso.",
            "7. Unity: identidad compartida > familiaridad superficial.",
        ],
    },
}

OFFER_DESIGN = {
    "hormozi_100m_offers": {
        "titulo": "100M Offers: Framework para ofertas irresistibles",
        "principios": [
            "Offer = (Resultado deseado × Certeza) / (Tiempo + Esfuerzo + Dinero)",
            "10X offer: 10 veces mejor percepción que competencia.",
            "Value stack: agrupa beneficios, hacé parecer más valioso.",
            "Aumentar value: resultado ↑ + certeza ↑ o tiempo ↓ + esfuerzo ↓ + dinero ↓",
            "Guarantees real: garantías reales > sin garantías (reduce riesgo cliente).",
            "Scarcity + urgency: deadline real, stock limitado (VERDADERO).",
            "Social proof: testimonials, números, casos reales.",
            "Pricing psychology: 9-price effect ($997 > $1000), bundling > itemizado.",
            "Distribution matters: medium shapes offer. WhatsApp ≠ email ≠ landing page.",
            "Objections in offer: anticipa qué dirán, resuelve EN la offer.",
            "Test & measure: qué offer convierte, dobla eso.",
        ],
    },
}

COPYWRITING_PRINCIPLES = {
    "halbert_boron": {
        "titulo": "The Boron Letters: Copy es conversación escrita",
        "principios": [
            "Copy = conversación: escribe como hablas, no como máquina.",
            "Hook primero: beneficio principal en primeras 10 palabras.",
            "USP (Unique Selling Proposition): qué te hace diferente > qué haces.",
            "Control de atención: mantén reader engaged todo el tiempo.",
            "Storytelling: historias venden más que hechos/features.",
            "Anticipate objections: responde qué piensan ANTES de que lo digan.",
            "Test & Measure: qué funciona, dobla eso. Qué no, borra.",
            "P.S. y P.P.S.: postscripts generan respuesta (re-hook + urgencia).",
            "Específico > vago: números, detalles, ejemplos reales.",
        ],
    },
    "schwartz_breakthrough": {
        "titulo": "Breakthrough Advertising: Promesa > Pitch",
        "principios": [
            "Primacy of promise: promesa es TODO. Si no vende la promesa, nada.",
            "Levels of awareness: unaware → aware → solution → product → most-aware.",
            "Copy es continuación: extiende lo que el cliente YA piensa.",
            "Emotional triggers: rabia, miedo, deseo, esperanza, curiosidad.",
            "Urgencia real: deadline, escasez, oportunidad limitada (VERDADERA).",
            "Anclaje psicológico: primer precio visto = referencia.",
            "Escalation: desde pregunta (¿has notado?) hasta solución clara.",
            "Specificity: 'reduce presión' vs '37% menos estrés en 14 días'.",
        ],
    },
    "ogilvy_advertising": {
        "titulo": "Ogilvy on Advertising: Datos + Simplicity + Brand",
        "principios": [
            "Headlines: 80% solo lee headline. Hazlo contar.",
            "Clarity > cleverness: claro y específico siempre gana.",
            "Authenticity: honesto, no exageres. La verdad vende más.",
            "Visual + copy: trabajan juntos (en WhatsApp: tone + emoji si aplica).",
            "Research: data real, no intuición. Entiende al customer.",
            "Testing: siempre test. Qué funciona, replicá.",
            "Power of simplicity: simple > complejo. Una idea, una promesa.",
            "Brand building: long-term value > venta de hoy.",
        ],
    },
}

BUSINESS_PRINCIPLES = {
    "drucker_effective": {
        "titulo": "The Effective Executive: Ejecución + Impacto",
        "principios": [
            "Management by Objectives (MBO): claridad de qué importa.",
            "Focus: dónde está el VERDADERO impacto. Elimina ruido.",
            "Decisiones ejecutivas: datos + juicio (no datos solos).",
            "Tiempo = recurso más escaso: protégelo.",
            "Fortalezas > debilidades: contrata/desarrolla fortalezas.",
            "Contribución: pregunta 'qué puedo aportar' (no qué puedo recibir).",
            "Comunicación: claridad + coherencia = resultados.",
        ],
    },
    "ellis_growth_hacking": {
        "titulo": "Hacking Growth: Experimentos data-driven + iteración rápida",
        "principios": [
            "Growth = data-driven experimentation (no intuición).",
            "Cross-functional: product + marketing + engineering juntos.",
            "Ciclos rápidos: prueba → mide → aprende → itera.",
            "Métrica obsession: qué se mide, se mejora (AARRR).",
            "Product-market fit primero, scale después.",
            "Viral loops + referral loops = crecimiento exponencial.",
            "Growth levers: identifica qué mueve la aguja REALMENTE.",
        ],
    },
    "weinberg_traction": {
        "titulo": "Traction: 19 canales de crecimiento (no existe bala de plata)",
        "principios": [
            "19 canales: SEO, SEM, PR, viral, affiliate, partnerships, etc.",
            "No existe 'bala de plata': cada negocio, canal distinto.",
            "Dedica % del tiempo a cada canal, mide ROI.",
            "Concéntrate en 1 que funciona, scale después (no dispersión).",
            "Diferentes etapas = diferentes canales (early vs scale).",
            "Revenue metrics > vanity metrics (usuarios ≠ dinero).",
            "Prueba rápido, abandona rápido (low-cost experiments).",
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
