"""
Static list of every card the bank tracks. Mirrors the four categories from
clash.ninja/cards: Elixir (19), Dark Elixir (13), Builder Base (11), Super
Troop (17), 60 cards total. Everything downstream (progress math,
autocomplete, image grids) derives from this list, so a new Supercell troop
only needs an entry here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    key: str
    name: str
    category: str


CATEGORIES = ["Elixir", "Dark Elixir", "Builder Base", "Super Troop"]

CATEGORY_EMOJI = {
    "Elixir": "🟣",
    "Dark Elixir": "⚫",
    "Builder Base": "🟠",
    "Super Troop": "🔴",
}

_RAW_TROOPS = {
    "Elixir": [
        "Barbarian", "Archer", "Giant", "Goblin", "Wall Breaker", "Balloon",
        "Wizard", "Healer", "Dragon", "PEKKA", "Baby Dragon", "Miner",
        "Electro Dragon", "Yeti", "Dragon Rider", "Electro Titan",
        "Root Rider", "Thrower", "Meteor Golem",
    ],
    "Dark Elixir": [
        "Minion", "Hog Rider", "Valkyrie", "Golem", "Witch", "Lava Hound",
        "Bowler", "Ice Golem", "Headhunter", "Apprentice Warden", "Druid",
        "Furnace", "Rubble Witch",
    ],
    "Builder Base": [
        "Raged Barbarian", "Sneaky Archer", "Boxer Giant", "Beta Minion",
        "Bomber", "BB Baby Dragon", "Cannon Cart", "Night Witch",
        "Drop Ship", "Power PEKKA", "Hog Glider",
    ],
    "Super Troop": [
        "Super Barbarian", "Super Archer", "Super Giant", "Sneaky Goblin",
        "Super Wall Breaker", "Rocket Balloon", "Super Wizard", "Super Dragon",
        "Inferno Dragon", "Super Miner", "Super Yeti", "Super Minion",
        "Super Hog Rider", "Super Valkyrie", "Super Witch", "Ice Hound",
        "Super Bowler",
    ],
}


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


CARDS: list[Card] = [
    Card(key=_slug(name), name=name, category=category)
    for category, names in _RAW_TROOPS.items()
    for name in names
]

CARD_BY_KEY: dict[str, Card] = {card.key: card for card in CARDS}

CATEGORY_TOTALS: dict[str, int] = {
    category: sum(1 for card in CARDS if card.category == category) for category in CATEGORIES
}

TOTAL_CARDS = len(CARDS)


def cards_in(category: str) -> list[Card]:
    return [card for card in CARDS if card.category == category]


def search_cards(query: str, limit: int = 25) -> list[Card]:
    needle = query.lower().strip()
    if not needle:
        return CARDS[:limit]
    starts_with = [card for card in CARDS if card.name.lower().startswith(needle)]
    contains = [card for card in CARDS if needle in card.name.lower() and card not in starts_with]
    return (starts_with + contains)[:limit]
