"""Seasonal campaign suggestions: when a season falls and a draft to start from.

Read-only. Nothing here sends anything, and nothing here promises an offer: the drafts invite a reply, and the
business adds its own offer if it has one. Holiday dates for Argentina are fixed or rule-based; school and winter
holiday dates vary by province, so they are marked approximate.
"""

from dataclasses import dataclass
from datetime import date, timedelta

# Seasons that apply to every country, and seasons that only have a calendar for Argentina.
GLOBAL_SEASONS = ("christmas", "easter")
ARGENTINA_SEASONS = ("mothers_day", "fathers_day", "winter_holidays", "summer_holidays")
PUBLIC_WINDOW = timedelta(days=14)


def easter_sunday(year: int) -> date:
    """Gregorian Easter (anonymous algorithm, Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The n-th given weekday of a month (Monday = 0, Sunday = 6)."""
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


@dataclass(frozen=True)
class Season:
    key: str
    start: date
    end: date
    approximate: bool
    note: str | None


def _occurrence(key: str, year: int) -> Season:
    if key == "christmas":
        return Season(key, date(year, 12, 1), date(year, 12, 24), False, None)
    if key == "easter":
        sunday = easter_sunday(year)
        return Season(key, sunday - PUBLIC_WINDOW, sunday, False, None)
    if key == "mothers_day":
        sunday = nth_weekday(year, 10, 6, 3)
        return Season(key, sunday - PUBLIC_WINDOW, sunday, False, None)
    if key == "fathers_day":
        sunday = nth_weekday(year, 6, 6, 3)
        return Season(key, sunday - PUBLIC_WINDOW, sunday, False, None)
    if key == "winter_holidays":
        return Season(key, date(year, 7, 1), date(year, 7, 31), True,
                      "Las vacaciones de invierno varían por provincia: confirmá las fechas antes de enviar.")
    if key == "summer_holidays":
        return Season(key, date(year, 1, 1), date(year, 2, 28), True,
                      "Las vacaciones de verano varían por provincia: confirmá las fechas antes de enviar.")
    raise KeyError(key)


def seasons_for(country: str, year: int) -> list[str]:
    """Season keys that have a calendar for this country."""
    keys = list(GLOBAL_SEASONS)
    if country == "AR":
        keys += list(ARGENTINA_SEASONS)
    return keys


def next_occurrences(country: str, today: date) -> list[tuple[Season, bool]]:
    """For each season of the country, the next occurrence whose window has not ended, and whether it is open now."""
    result: list[tuple[Season, bool]] = []
    for key in seasons_for(country, today.year):
        for year in (today.year, today.year + 1):
            season = _occurrence(key, year)
            if season.end >= today:
                result.append((season, season.start <= today <= season.end))
                break
    return sorted(result, key=lambda item: item[0].start)


# Draft per season and language: (subject, season name, body). {negocio} is the business name, filled when shown.
DRAFTS: dict[str, dict[str, tuple[str, str, str]]] = {
    "christmas": {
        "es": ("Feliz Navidad de parte de {negocio}", "Feliz Navidad", "Se acercan las fiestas y queremos agradecerte por acompañarnos este año. Si buscás un regalo o algo para vos, escribinos y te ayudamos a elegir."),
        "en": ("Happy holidays from {negocio}", "Happy holidays", "The holidays are coming and we want to thank you for being with us this year. If you're looking for a gift or something for yourself, write to us and we'll help you choose."),
    },
    "easter": {
        "es": ("Feliz Pascua de parte de {negocio}", "Feliz Pascua", "Se acerca Pascua y queremos desearte un muy buen fin de semana. Si planeás algo especial, escribinos y te asesoramos."),
        "en": ("Happy Easter from {negocio}", "Happy Easter", "Easter is coming and we wish you a wonderful long weekend. If you're planning something special, write to us and we'll advise you."),
    },
    "mothers_day": {
        "es": ("Por el Día de la Madre", "Día de la Madre", "Este fin de semana es el Día de la Madre. Si buscás un regalo especial, escribinos y te ayudamos a elegirlo."),
        "en": ("For Mother's Day", "Mother's Day", "This weekend is Mother's Day. If you're looking for a special gift, write to us and we'll help you choose one."),
    },
    "fathers_day": {
        "es": ("Por el Día del Padre", "Día del Padre", "Este fin de semana es el Día del Padre. Si buscás un regalo especial, escribinos y te ayudamos a elegirlo."),
        "en": ("For Father's Day", "Father's Day", "This weekend is Father's Day. If you're looking for a special gift, write to us and we'll help you choose one."),
    },
    "winter_holidays": {
        "es": ("Vacaciones de invierno", "Vacaciones de invierno", "Se vienen las vacaciones de invierno. Si planeás pasar tiempo en familia o con amigos, escribinos y te contamos lo que tenemos para vos."),
        "en": ("Winter holidays are coming", "Winter holidays", "Winter holidays are coming. If you're planning time with family or friends, write to us and we'll tell you what we have for you."),
    },
    "summer_holidays": {
        "es": ("Vacaciones de verano", "Vacaciones de verano", "Se acercan las vacaciones de verano. Si planeás viajar o pasar tiempo al aire libre, escribinos y te contamos lo que tenemos para vos."),
        "en": ("Summer holidays are here", "Summer holidays", "Summer holidays are coming. If you're planning to travel or spend time outdoors, write to us and we'll tell you what we have for you."),
    },
}
