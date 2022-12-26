import os
import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path
import sys
from run import Run
import plotly.express as px

import json


def main(directory):
    runs = []
    for root, _, files in os.walk(directory):
        for file in files:
            data = json.loads(Path(root, file).read_text())
            run = Run.from_dict(data)
            runs.append(run)

    total_games_played = len(runs)
    win_rate = len([r for r in runs if r.victory]) / total_games_played
    avg_playtime = sum(r.playtime for r in runs) / total_games_played / 60
    avg_floor = sum(r.floor for r in runs) / total_games_played
    max_score = max(r.score for r in runs)
    avg_times_rest = (
            sum(sum(1 for c in r.campfires if c.key == "REST") for r in runs)
            / total_games_played
    )
    avg_times_upgrade = (
            sum(sum(1 for c in r.campfires if c.key == "SMITH") for r in runs)
            / total_games_played
    )
    kill_count = Counter()
    for run in runs:
        if run.killed_by:
            kill_count[run.killed_by] += 1

    damage_taken = defaultdict(list)
    average_damage_taken = Counter()

    for run in runs:
        for damage in run.damage_takens:
            damage_taken[damage.enemies].append(damage.damage)

    for e, d in damage_taken.items():
        average_damage_taken[e] = sum(d) / len(d)

    print(
        f"""\
    Total games played: {total_games_played}
    Win rate (%): {round(win_rate * 100, 2)}
    Average playtime (min): {round(avg_playtime, 2)} 
    Average floor reached: {round(avg_floor, 2)}
    Max score: {max_score}
    Average times rest: {round(avg_times_rest, 2)}
    Average times upgrade: {round(avg_times_upgrade, 2)}
    """
    )

    top_20_killed_count = px.bar(x=[kill[0] for kill in kill_count.most_common(20)],
                                 y=[kill[1] for kill in kill_count.most_common(20)])
    top_20_killed_count.write_html('top_20_killed_count.html', auto_open=True)

    top_20_damage_taken = px.bar(x=[dmg[0] for dmg in average_damage_taken.most_common(20)],
                                 y=[dmg[1] for dmg in average_damage_taken.most_common(20)])
    top_20_damage_taken.write_html('top_20_damage_taken.html', auto_open=True)

    floors = Counter()
    for run in runs:
        floors[run.floor] += 1

    floors_reached = px.bar(x=[i for i in range(58)], y=[floors[i] for i in range(58)])
    floors_reached.write_html('floors_reached.html', auto_open=True)

    df = pd.array([run.gold for run in runs])
    df = pd.cut(df, [100 * i for i in range(24)])
    counts = df.value_counts()
    gold_distribution = px.bar(x=[a.right for a in counts.axes[0].to_list()], y=counts.values)
    gold_distribution.write_html('gold_distribution.html', auto_open=True)


if __name__ == "__main__":
    _, d = sys.argv
    # d = "../runs"
    main(d)
