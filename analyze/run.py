from dataclasses import dataclass


def normalize_card(card: str) -> str:
    replacements = {
        "Ghostly": "Apparition",
        "Venomology": "Alchemize",
        "Wraith Form v2": "Wraith Form",
        "Gash": "Claw",
    }
    c = card.partition("+")[0]
    return replacements.get(c, c)


def normalize_cards(cards: [str]) -> [str]:
    return [normalize_card(c) for c in cards]


def sum_gold(lst):
    total = 0

    for prev, curr in zip([0] + lst, lst):
        if curr > prev:
            total += curr - prev

    return total


@dataclass
class CardChoice:
    picked: str
    not_picked: [str]
    floor: int

    @classmethod
    def from_dict(cls, d, singing_bowl_floor: int):
        floor = d["floor"]
        picked = normalize_card(d["picked"])
        not_picked = normalize_cards(d["not_picked"])

        if picked != "SKIP" or picked != "Singing Bowl":
            if -1 < singing_bowl_floor <= floor:
                not_picked.append("Singing Bowl")
            else:
                not_picked.append("SKIP")

        return cls(picked=picked, not_picked=not_picked, floor=floor)

    @property
    def is_boss(self):
        return self.floor == 16 or self.floor == 33

    @property
    def act(self):
        if self.floor <= 16:
            return 1
        elif self.floor <= 33:
            return 2
        elif self.floor <= 51:
            return 3
        return 4


@dataclass
class BossRelicChoice:
    picked: str
    not_picked: [str]

    @classmethod
    def from_dict(cls, d):
        return cls(picked=d.get("picked"), not_picked=d["not_picked"])


@dataclass
class DamageTaken:
    damage: int
    enemies: str
    floor: int
    turns: int

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class Campfire:
    key: str
    data: str
    floor: int

    @classmethod
    def from_dict(cls, d):
        return cls(key=d["key"], data=d.get("data"), floor=d["floor"])


@dataclass
class Run:
    victory: bool
    deck: [str]
    relics: [str]
    card_choices: [CardChoice]
    boss_relic_choices: [BossRelicChoice]
    killed_by: str
    damage_takens: [DamageTaken]
    floor: int
    gold: int
    playtime: int
    score: int
    campfires: [Campfire]
    max_hp: int
    removes: [str]
    character: str

    @classmethod
    def from_dict(cls, d):
        relic_obtained = d["relics_obtained"]
        singing_bowl_floor = -1
        for r in relic_obtained:
            floor = r["floor"]
            key = r["key"]
            if key == "Singing Bowl":
                singing_bowl_floor = floor

        return cls(
            victory=d["victory"],
            deck=[c for c in normalize_cards(d["master_deck"]) if c != "AscendersBane"],
            relics=d["relics"],
            card_choices=[
                CardChoice.from_dict(c, singing_bowl_floor) for c in d["card_choices"]
            ],
            boss_relic_choices=[BossRelicChoice.from_dict(c) for c in d["boss_relics"]],
            killed_by=d.get("killed_by"),
            damage_takens=[DamageTaken.from_dict(c) for c in d["damage_taken"]],
            floor=d["floor_reached"],
            gold=sum_gold(d["gold_per_floor"]),
            playtime=d["playtime"],
            score=d["score"],
            campfires=[Campfire.from_dict(c) for c in d["campfire_choices"]],
            max_hp=d["max_hp_per_floor"][-1],
            removes=normalize_cards(d["items_purged"]),
            character=d["character_chosen"],
        )
