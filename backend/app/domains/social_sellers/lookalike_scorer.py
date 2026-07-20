"""Lookalike Scorer — funciones puras de scoring (sin DB)."""

import re
from datetime import datetime
from typing import Any, Dict, List


BUYING_INTENT_KEYWORDS = [
    'precio', 'precios', 'cuanto', 'cuesta', 'costo', 'valor',
    'comprar', 'ordenar', 'pedir', 'encargar', 'reservar',
    'descuento', 'oferta', 'promo', 'promocion', 'rebaja',
    'envio', 'envío', 'entrega', 'cuando llega', 'disponible',
    'stock', 'tallas', 'colores', 'variantes', 'medios de pago',
    'mercadopago', 'transferencia', 'tarjeta', 'cuotas',
    'lo quiero', 'me interesa', 'me convence', 'dale',
    'pasame datos', 'como pago', 'factura', 'ticket',
]

PRICE_KEYWORDS = ['precio', 'precios', 'cuanto', 'cuesta', 'costo', 'valor', 'cuánto']


def calculate_similarity_score(lead_data: Dict[str, Any], ideal_profile: Dict[str, Any]) -> int:
    """Puntaje 0-100 de qué tan similar es un lead al perfil ideal.

    Factores:
    - Platform match (10 pts)
    - Engagement level (20 pts)
    - Message intent (20 pts)
    - Response speed (15 pts)
    - Demographic similarity (15 pts)
    - Behavior patterns (20 pts)
    """
    score = 0

    # 1. Platform match (10 pts)
    platform_score = match_platform_preference(
        lead_data.get('platform', ''),
        ideal_profile.get('preferred_platforms', [])
    )
    score += int(platform_score * 10)

    # 2. Engagement level (20 pts)
    engagement = lead_data.get('engagement', {})
    msg_count = engagement.get('total_messages', 0)
    inbound_ratio = engagement.get('inbound_ratio', 0.0)
    if msg_count >= 10:
        score += 10
    elif msg_count >= 5:
        score += 5
    elif msg_count >= 2:
        score += 2
    if inbound_ratio >= 0.8:
        score += 10
    elif inbound_ratio >= 0.5:
        score += 5

    # 3. Message intent (20 pts)
    intent = lead_data.get('intent', {})
    buying_keywords = intent.get('buying_keywords', 0)
    price_mentioned = intent.get('price_mentioned', False)
    score += min(15, buying_keywords * 3)
    if price_mentioned:
        score += 5

    # 4. Response speed (15 pts)
    behavior = lead_data.get('behavior', {})
    response_time_avg = behavior.get('response_time_avg_seconds')
    if response_time_avg is not None:
        if response_time_avg <= 300:  # <= 5 min
            score += 15
        elif response_time_avg <= 900:  # <= 15 min
            score += 10
        elif response_time_avg <= 3600:  # <= 1 hr
            score += 5

    # 5. Demographic similarity (15 pts)
    demo = lead_data.get('demographic', {})
    has_email = bool(demo.get('email'))
    has_phone = bool(demo.get('phone'))
    has_name = bool(demo.get('name'))
    if has_email:
        score += 5
    if has_phone:
        score += 5
    if has_name:
        score += 5

    # 6. Behavior patterns (20 pts)
    if behavior:
        question_count = behavior.get('question_count', 0)
        emoji_usage = behavior.get('emoji_usage_rate', 0.0)
        msg_length_avg = behavior.get('message_length_avg', 0)
        if question_count >= 3:
            score += 8
        elif question_count >= 1:
            score += 4
        if emoji_usage >= 0.1:
            score += 6
        elif emoji_usage > 0:
            score += 3
        if msg_length_avg >= 20:
            score += 6
        elif msg_length_avg >= 10:
            score += 3

    return max(0, min(100, score))


def extract_behavioral_features(conversation_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extrae features comportamentales de una lista de mensajes.

    Returns:
        - response_time_avg_seconds
        - question_count
        - price_mention_count
        - emoji_usage_rate
        - message_length_avg
    """
    if not conversation_messages:
        return {
            'response_time_avg_seconds': None,
            'question_count': 0,
            'price_mention_count': 0,
            'emoji_usage_rate': 0.0,
            'message_length_avg': 0.0,
        }

    inbound_msgs = [
        m for m in conversation_messages
        if m.get('direction') == 'inbound'
    ]

    # Response time avg: tiempo entre outbound y siguiente inbound
    response_times = []
    sorted_msgs = sorted(
        conversation_messages,
        key=lambda x: x.get('created_at') or datetime.min,
    )
    for i, msg in enumerate(sorted_msgs):
        if msg.get('direction') == 'outbound' and i + 1 < len(sorted_msgs):
            next_msg = sorted_msgs[i + 1]
            if next_msg.get('direction') == 'inbound':
                t1 = msg.get('created_at')
                t2 = next_msg.get('created_at')
                if isinstance(t1, datetime) and isinstance(t2, datetime):
                    diff = (t2 - t1).total_seconds()
                    if 0 < diff < 86400:  # max 1 día
                        response_times.append(diff)

    response_time_avg = (
        sum(response_times) / len(response_times)
        if response_times else None
    )

    # Question count
    question_count = sum(
        1 for m in inbound_msgs
        if '?' in (m.get('content') or '')
    )

    # Price mentions
    price_mention_count = sum(
        1 for m in inbound_msgs
        if any(kw in (m.get('content') or '').lower() for kw in PRICE_KEYWORDS)
    )

    # Emoji usage
    emoji_pattern = re.compile(
        '['
        '\\U0001F600-\\U0001F64F'
        '\\U0001F300-\\U0001F5FF'
        '\\U0001F680-\\U0001F6FF'
        '\\U0001F1E0-\\U0001F1FF'
        '\\U00002702-\\U000027B0'
        '\\U000024C2-\\U0001F251'
        ']+',
        flags=re.UNICODE,
    )
    emoji_count = sum(
        len(emoji_pattern.findall(m.get('content') or ''))
        for m in inbound_msgs
    )
    total_inbound_chars = sum(
        len(m.get('content', '')) for m in inbound_msgs
    )
    emoji_usage_rate = emoji_count / max(1, total_inbound_chars)

    # Message length avg
    total_chars = sum(
        len(m.get('content', '') or '') for m in inbound_msgs
    )
    message_length_avg = total_chars / max(1, len(inbound_msgs))

    return {
        'response_time_avg_seconds': response_time_avg,
        'question_count': question_count,
        'price_mention_count': price_mention_count,
        'emoji_usage_rate': round(emoji_usage_rate, 4),
        'message_length_avg': round(message_length_avg, 2),
    }


def match_platform_preference(lead_platform: str, ideal_platforms: List[str]) -> float:
    """Devuelve 1.0 si la plataforma está en las preferidas, 0.5 si es similar, 0.0 si no."""
    lead = (lead_platform or '').lower().strip()
    ideals = [p.lower().strip() for p in (ideal_platforms or [])]
    if not lead or not ideals:
        return 0.0
    if lead in ideals:
        return 1.0

    similar = {
        'instagram': ['messenger', 'facebook', 'threads'],
        'tiktok': ['instagram', 'twitter'],
        'whatsapp': ['messenger', 'telegram'],
        'facebook': ['instagram', 'messenger', 'threads'],
        'twitter': ['threads', 'tiktok'],
        'threads': ['instagram', 'twitter'],
        'messenger': ['facebook', 'instagram', 'whatsapp'],
        'telegram': ['whatsapp'],
    }
    for sim in similar.get(lead, []):
        if sim in ideals:
            return 0.5
    return 0.0
