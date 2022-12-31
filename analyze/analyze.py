import itertools
import json
import math
import os
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from run import Run

sns.set_theme()

markdown_args = {"index": False, "tablefmt": "github"}


def save_fig(plot, path: Path):
    fig = plot.get_figure()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.clf()
    plt.cla()
    plt.close()


def flatten(lst):
    return [item for sublist in lst for item in sublist]


def join_markdown_tables(a, b):
    a, b = a.splitlines(), b.splitlines()
    c = [
        a[0] + "     " + b[0],
        a[1] + "-----" + b[1],
    ]

    for aa, bb in itertools.zip_longest(a[2:], b[2:], fillvalue="|   |   |"):
        c.append(aa + "     " + bb)
    return "\n".join(c)


def dual_tables(df):
    df1 = df[: math.ceil(len(df) / 2)]
    df2 = df[math.ceil(len(df) / 2) :]
    return join_markdown_tables(
        df1.to_markdown(**markdown_args), df2.to_markdown(**markdown_args)
    )


class Stats:
    @classmethod
    def from_dir(cls, directory: str):
        runs = []
        for root, _, files in os.walk(directory):
            for file in files:
                data = json.loads(Path(root, file).read_text())
                run = Run.from_dict(data)
                runs.append(run)
        return cls(runs)

    def __init__(self, runs: [Run]):
        self.runs = runs
        self.general_stats = GeneralStats(runs)

        self.kill_count = pd.DataFrame.from_records(
            list(Counter(r.killed_by for r in self.runs if r.killed_by).items()),
            columns=["Killed by", "Count"],
        ).sort_values(by="Count", ascending=False)

        _f = Counter(r.floor for r in self.runs)
        self.floors = pd.DataFrame.from_records(
            [(i, _f[i]) for i in range(1, 58)],
            columns=["Floor", "Count"],
        ).sort_values(by="Floor")

        self.gold = pd.DataFrame({"Gold": [run.gold for run in self.runs]})

        self.card_removed = pd.DataFrame.from_records(
            list(Counter(flatten(run.removes for run in self.runs)).items()),
            columns=["Card", "Count"],
        ).sort_values(by="Count", ascending=False)

        self.damage_taken = pd.DataFrame.from_records(
            flatten(
                [[(d.enemies, d.damage) for d in r.damage_takens] for r in self.runs]
            ),
            columns=["Enemy", "Damage Taken"],
        ).sort_values(by="Damage Taken", ascending=False)

        self.card_picks = self._card_picks()

        self.card_wins = pd.DataFrame.from_records(
            flatten(
                [[(card, run.victory) for card in set(run.deck)] for run in self.runs]
            ),
            columns=["Card", "Win"],
        )

        self.boss_relics = self._boss_relics()
        self.relic_wins = pd.DataFrame.from_records(
            flatten(
                [[(relic, run.victory) for relic in run.relics] for run in self.runs]
            ),
            columns=["Relic", "Win"],
        )

    def _card_picks(self):
        data = []
        for run in self.runs:
            for choice in run.card_choices:
                picked = choice.picked
                not_picked = choice.not_picked
                floor = choice.floor
                data.append((picked, floor, True, choice.act, choice.is_boss))
                for skip in not_picked:
                    data.append((skip, floor, False, choice.act, choice.is_boss))
        return pd.DataFrame.from_records(
            data, columns=["Card", "Floor", "Picked", "Act", "Boss"]
        )

    def _boss_relics(self):
        data = []
        for run in self.runs:
            for i, boss in enumerate(run.boss_relic_choices):
                act = i + 1
                picked = boss.picked
                if picked:
                    data.append((picked, act, True, run.victory))
                for skipped in boss.not_picked:
                    data.append((skipped, act, False, run.victory))
        return pd.DataFrame.from_records(
            data, columns=["Relic", "Act", "Picked", "Win"]
        )

    def export(self, out_dir: Path, title: str):
        md = []

        out_dir.mkdir(parents=True, exist_ok=True)

        with open(out_dir / "general.json", "w+") as f:
            json.dump(self.general_stats.to_dict(), f)

        self.kill_count.to_csv(out_dir / "killed_by.csv", index=False)
        self.floors.to_csv(out_dir / "floor.csv", index=False)
        self.gold.to_csv(out_dir / "gold.csv", index=False)
        self.card_removed.to_csv(out_dir / "card_removed.csv", index=False)
        self.damage_taken.to_csv(out_dir / "damage_taken.csv", index=False)
        self.card_picks.to_csv(out_dir / "card_picks.csv", index=False)
        self.card_wins.to_csv(out_dir / "card_wins.csv", index=False)
        self.relic_wins.to_csv(out_dir / "relic_wins.csv", index=False)
        self.boss_relics.to_csv(out_dir / "boss_relics.csv", index=False)

        self._top_20_killed_count(out_dir)
        self._top_20_avg_damage_taken(out_dir)
        self._floors_reached(out_dir)
        self._gold_distribution(out_dir)

        top_10_card_removed = self.card_removed.head(10).to_markdown(**markdown_args)

        top_10_damage_taken = (
            self.damage_taken[self.damage_taken["Enemy"] != "The Heart"]
            .head(10)
            .to_markdown(**markdown_args)
        )

        top_80_card_winrate = dual_tables(
            self.card_wins.groupby(by="Card")
            .mean()
            .reset_index()
            .sort_values(by="Win", ascending=False)
            .rename(columns={"Win": "Win rate"})
            .round(2)
            .head(80)
        )

        _relic_winrates = (
            self.relic_wins.groupby(by="Relic")
            .mean()
            .reset_index()
            .sort_values(by="Win", ascending=False)
            .rename(columns={"Win": "Win rate"})
            .round(2)
        )
        top_40_relic_winrates = dual_tables(_relic_winrates.head(40))
        bottom_40_relic_winrates = dual_tables(_relic_winrates.tail(40))

        act1_boss_relic_pick_rate = dual_tables(
            self.boss_relics[self.boss_relics["Act"] == 1][["Relic", "Picked"]]
            .groupby(by="Relic")
            .mean()
            .reset_index()
            .sort_values(by="Picked", ascending=False)
            .rename(columns={"Picked": "Pick rate"})
            .round(2)
        )

        act1_boss_relic_win_rate = dual_tables(
            self.boss_relics[
                (self.boss_relics["Act"] == 1) & (self.boss_relics["Picked"])
            ][["Relic", "Win"]]
            .groupby(by="Relic")
            .mean()
            .reset_index()
            .sort_values(by="Win", ascending=False)
            .rename(columns={"Win": "Win rate"})
            .round(2)
        )

        act2_boss_relic_pick_rate = dual_tables(
            self.boss_relics[self.boss_relics["Act"] == 2][["Relic", "Picked"]]
            .groupby(by="Relic")
            .mean()
            .reset_index()
            .sort_values(by="Picked", ascending=False)
            .rename(columns={"Picked": "Pick rate"})
            .round(2)
        )

        act2_boss_relic_win_rate = dual_tables(
            self.boss_relics[
                (self.boss_relics["Act"] == 2) & (self.boss_relics["Picked"])
            ][["Relic", "Win"]]
            .groupby(by="Relic")
            .mean()
            .reset_index()
            .sort_values(by="Win", ascending=False)
            .rename(columns={"Win": "Win rate"})
            .round(2)
        )

        act1_card_pick_rate = dual_tables(
            self.card_picks[
                (self.card_picks["Act"] == 1) & (self.card_picks["Boss"] == False)
            ][["Card", "Picked"]]
            .groupby(by="Card")
            .mean()
            .reset_index()
            .sort_values(by="Picked", ascending=False)
            .rename(columns={"Picked": "Pick rate"})
            .round(2)
        )
        after_act1_card_pick_rate = dual_tables(
            self.card_picks[
                (self.card_picks["Act"] > 1) & (self.card_picks["Boss"] == False)
            ][["Card", "Picked"]]
            .groupby(by="Card")
            .mean()
            .reset_index()
            .sort_values(by="Picked", ascending=False)
            .rename(columns={"Picked": "Pick rate"})
            .round(2)
        )

        if title:
            md.append(f"# {title}")

        md.append("## General stats")
        md.append(self.general_stats.to_markdown())
        md.append("\n![Top 20 killed count](./top_20_killed_count.png)")
        md.append("\n![Top 20 avg damage taken](./top_20_avg_damage_taken.png)")
        md.append("\n![Floors reached](./floors_reached.png)")
        md.append("\n![Gold distribution](./gold_distribution.png)")

        md.append("\n### Top 10 damage taken fights (excluding heart)")
        md.append(top_10_damage_taken)
        md.append("\n")

        md.append("## Card stats")
        md.append("### Top 10 card removed count")
        md.append(top_10_card_removed)
        md.append("\n")
        md.append("### Top 80 card win rate (exclude duplicate)")
        md.append(top_80_card_winrate)
        md.append("\n")
        md.append("### Card pick rate act 1 (exclude boss)")
        md.append(act1_card_pick_rate)
        md.append("\n")
        md.append("### Card pick rate after act 1 (exclude boss)")
        md.append(after_act1_card_pick_rate)
        md.append("\n")

        md.append("## Relic stats")
        md.append("### Top relic win rate")
        md.append(top_40_relic_winrates)
        md.append("\n")
        md.append("### Bottom relic win rate")
        md.append(bottom_40_relic_winrates)
        md.append("\n")
        md.append("### Act 1 boss relic pick rate")
        md.append(act1_boss_relic_pick_rate)
        md.append("\n")
        md.append("### Act 1 boss relic win rate")
        md.append(act1_boss_relic_win_rate)
        md.append("\n")
        md.append("### Act 2 boss relic pick rate")
        md.append(act2_boss_relic_pick_rate)
        md.append("\n")
        md.append("### Act 2 boss relic win rate")
        md.append(act2_boss_relic_win_rate)
        md.append("\n")

        with open(out_dir / "README.md", "w+") as f:
            f.write("\n".join(md))

    def _top_20_killed_count(self, out_dir: Path):
        plot = sns.barplot(
            data=self.kill_count.sort_values(by="Count", ascending=False).head(20),
            x="Killed by",
            y="Count",
        )
        plt.xticks(rotation=90)
        plt.title("Top 20 killed count")
        save_fig(plot, out_dir / "top_20_killed_count.png")

    def _top_20_avg_damage_taken(self, out_dir: Path):
        data = (
            self.damage_taken.groupby(by="Enemy")
            .mean()
            .reset_index()
            .sort_values(by="Damage Taken", ascending=False)
            .head(20)
        )

        plot = sns.barplot(
            data=data,
            x="Enemy",
            y="Damage Taken",
        )

        plt.xticks(rotation=90)
        plt.title("Top 20 avg damage taken")
        save_fig(plot, out_dir / "top_20_avg_damage_taken.png")

    def _floors_reached(self, out_dir: Path):
        plot = sns.barplot(
            data=self.floors,
            x="Floor",
            y="Count",
        )
        plt.title("Floors reached")
        plt.xticks(rotation=90)
        plt.tick_params(axis="x", which="major", labelsize=7)
        save_fig(plot, out_dir / "floors_reached.png")

    def _gold_distribution(self, out_dir: Path):
        data = self.gold
        max_gold = data.max()[0]
        plot = sns.histplot(
            data=data, x="Gold", bins=[100 * i for i in range(1, max_gold // 100 + 2)]
        )
        plt.title("Gold distribution")
        save_fig(plot, out_dir / "gold_distribution.png")


class GeneralStats:
    def __init__(self, runs: [Run]):
        self.total_games_played = len(runs)
        self.win_rate = len([r for r in runs if r.victory]) / self.total_games_played
        self.avg_playtime = sum(r.playtime for r in runs) / self.total_games_played / 60
        self.avg_floor = sum(r.floor for r in runs) / self.total_games_played
        self.max_score = max(r.score for r in runs)
        self.avg_times_rest = (
            sum(sum(1 for c in r.campfires if c.key == "REST") for r in runs)
            / self.total_games_played
        )
        self.avg_times_upgrade = (
            sum(sum(1 for c in r.campfires if c.key == "SMITH") for r in runs)
            / self.total_games_played
        )

        self.max_hp_over_80 = len([r for r in runs if r.max_hp >= 80])
        self.max_hp_under_40 = len([r for r in runs if r.max_hp <= 40])

    def to_dict(self):
        return {
            "total_games_played": self.total_games_played,
            "win_rate": self.win_rate,
            "avg_playtime_mins": self.avg_playtime,
            "avg_floor": self.avg_floor,
            "max_score": self.max_score,
            "avg_times_rest": self.avg_times_rest,
            "avg_times_upgrade": self.avg_times_upgrade,
            "max_hp_over_80": self.max_hp_over_80,
            "max_hp_under_40": self.max_hp_under_40,
        }

    def to_markdown(self):
        return f"""\
- Total games played: {self.total_games_played}
- Win rate (%): {round(100 * self.win_rate, 2)}
- Avg playtime (mins): {round(self.avg_playtime, 2)}
- Avg floor reached: {round(self.avg_floor, 2)}
- Max score: {self.max_score}
- Times rest: {round(self.avg_times_rest, 2)}
- Times smith: {round(self.avg_times_upgrade, 2)}
- Max hp >= 80: {self.max_hp_over_80}
- Max hp <= 40: {self.max_hp_under_40}"""


def main():
    parser = ArgumentParser(description="Analyze Slay the Spire run history data")
    parser.add_argument("directory", help="directory containing the run history files")
    parser.add_argument(
        "output_directory", help="directory to output the data analysis"
    )
    parser.add_argument("--report-title", help="add a title to the report produced")
    args = parser.parse_args()

    stats = Stats.from_dir(args.directory)
    stats.export(Path(args.output_directory), args.report_title)


if __name__ == "__main__":
    main()
