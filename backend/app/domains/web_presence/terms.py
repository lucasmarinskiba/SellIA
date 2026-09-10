"""What a page actually talks about, counted from the page itself.

This is NOT keyword research: it says nothing about how many people search a
term or how hard it is to rank for it -- those need a paid API (see
docs/INTEGRACIONES.md) and are never guessed here.

What it does answer is the question a seller can act on today: given the words
really on your page, and where they sit (title, H1, headings, body), what is
this page about in a crawler's eyes? A store convinced it sells "zapatillas de
running" whose page never says those words outside the title has a real,
fixable problem, and it is visible without any external service.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any, Iterable

#: Weight per position. A term in the title is a claim about the whole page;
#: the same term buried in the body is just prose.
WEIGHT_TITLE = 5
WEIGHT_H1 = 4
WEIGHT_DESCRIPTION = 3
WEIGHT_SUBHEADING = 2
WEIGHT_BODY = 1

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# Spanish + English function words. A stopword list is a blunt instrument, but
# the alternative -- reporting "de", "the" and "para" as a page's main topics --
# is worse. Kept short and obvious rather than exhaustive.
STOPWORDS: set[str] = {
    # español
    "a", "al", "algo", "algun", "alguna", "algunas", "alguno", "algunos", "ante", "antes",
    "aqui", "asi", "aun", "aunque", "bien", "cada", "casi", "como", "con", "contra", "cual",
    "cuales", "cuando", "cuanto", "de", "del", "desde", "donde", "dos", "el", "ella", "ellas",
    "ellos", "en", "entre", "era", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta",
    "estan", "estar", "estas", "este", "esto", "estos", "estoy", "fue", "fueron", "ha", "hace",
    "hacer", "hacia", "han", "hasta", "hay", "la", "las", "le", "les", "lo", "los", "mas", "me",
    "mi", "mientras", "mucho", "muy", "nada", "ni", "no", "nos", "nosotros", "nuestra",
    "nuestro", "o", "os", "otra", "otras", "otro", "otros", "para", "pero", "poco", "por",
    "porque", "que", "quien", "se", "sea", "segun", "ser", "si", "sin", "sobre", "solo", "son",
    "su", "sus", "tambien", "tan", "tanto", "te", "tiene", "tienen", "todo", "todos", "tu",
    "tus", "un", "una", "uno", "unos", "usted", "va", "vos", "y", "ya", "yo",
    # english
    "a", "about", "all", "an", "and", "any", "are", "as", "at", "be", "been", "but", "by",
    "can", "do", "does", "for", "from", "get", "has", "have", "how", "i", "if", "in", "is",
    "it", "its", "more", "my", "no", "not", "of", "on", "one", "or", "our", "out", "so",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "to",
    "up", "use", "was", "we", "were", "what", "when", "which", "who", "will", "with", "you",
    "your",
    # ruido habitual de e-commerce que no describe el negocio
    "aqui", "click", "clic", "envio", "gratis", "home", "inicio", "mas", "menu", "pagina",
    "productos", "ver",
    # saludos y muletillas de título: aparecen en el <title> de medio internet y
    # dispararían el chequeo "el título promete algo que la página no dice" sin
    # describir ningún tema real.
    "welcome", "bienvenido", "bienvenida", "bienvenidos", "official", "oficial", "web",
    "sitio", "site",
}


def _normalize(word: str) -> str:
    """Fold accents for counting so 'café' and 'cafe' are the same term. The
    original casing/accents are irrelevant once we are counting topics."""
    lowered = word.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(c) != "Mn"
    )


def _tokens(text: str) -> list[str]:
    return [
        norm for norm in (_normalize(w) for w in _WORD_RE.findall(text or ""))
        if len(norm) > 2 and norm not in STOPWORDS
    ]


def _bigrams(tokens: list[str]) -> list[str]:
    return [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]


def extract(
    *,
    title: str | None,
    description: str | None,
    h1: Iterable[str],
    subheadings: Iterable[str],
    body_text: str,
    limit: int = 12,
) -> dict[str, Any]:
    """Weighted term profile of one page, plus the consistency checks that fall
    out of it for free."""
    scores: Counter[str] = Counter()
    body_tokens = _tokens(body_text)

    def add(text: str, weight: int) -> None:
        toks = _tokens(text)
        for token in toks:
            scores[token] += weight
        for gram in _bigrams(toks):
            scores[gram] += weight

    add(title or "", WEIGHT_TITLE)
    add(description or "", WEIGHT_DESCRIPTION)
    for heading in h1:
        add(heading, WEIGHT_H1)
    for heading in subheadings:
        add(heading, WEIGHT_SUBHEADING)
    for token in body_tokens:
        scores[token] += WEIGHT_BODY
    for gram in _bigrams(body_tokens):
        scores[gram] += WEIGHT_BODY

    body_set = set(body_tokens)
    title_tokens = _tokens(title or "")

    # A term promised in the title but absent from the body is the single most
    # common self-inflicted SEO problem in a small store's page.
    promised_not_delivered = [t for t in title_tokens if t not in body_set]

    top = [
        {"term": term, "score": score, "in_title": term in title_tokens,
         "in_body": term.split(" ")[0] in body_set}
        for term, score in scores.most_common(limit)
    ]

    return {
        "top_terms": top,
        "title_terms": title_tokens,
        "promised_not_delivered": promised_not_delivered,
        "distinct_terms": len(scores),
        "body_tokens": len(body_tokens),
    }
