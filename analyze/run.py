from dataclasses import dataclass


@dataclass
class CardChoice:
    picked: str
    not_picked: [str]
    floor: int

    @classmethod
    def from_dict(cls, d):
        return cls(picked=d["picked"], not_picked=d["not_picked"], floor=d["floor"])


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

    @classmethod
    def from_dict(cls, d):
        return cls(
            victory=d["victory"],
            deck=d["master_deck"],
            relics=d["relics"],
            card_choices=[CardChoice.from_dict(c) for c in d["card_choices"]],
            boss_relic_choices=[BossRelicChoice.from_dict(c) for c in d["boss_relics"]],
            killed_by=d.get("killed_by"),
            damage_takens=[DamageTaken.from_dict(c) for c in d["damage_taken"]],
            floor=d["floor_reached"],
            gold=sum_gold(d["gold_per_floor"]),
            playtime=d["playtime"],
            score=d["score"],
            campfires=[Campfire.from_dict(c) for c in d["campfire_choices"]],
            max_hp=d["max_hp_per_floor"][-1],
        )


def sum_gold(lst):
    total = 0

    for prev, curr in zip([0] + lst, lst):
        if curr > prev:
            total += curr - prev

    return total
