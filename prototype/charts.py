# DriveSynth prototype - part 7: the charts we use in the presentation
#
#   1. failure_map.png      - where the basic AEB crashes in the cut-in (gap vs scooter speed), dry and wet
#   2. search_compare.png   - random vs guided search, crashes found per 100 runs (needs search.py first)
#   3. basic_vs_improved.png - crash rate of the basic and improved AEB, dry vs wet

import csv
import random

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from aeb import basic_aeb, improved_aeb
from cutin import run_cutin

OUTCOME_NUMBER = {"pass": 0, "near miss": 1, "fail": 2}


def failure_map():
    gaps = [1 + 0.5 * i for i in range(29)]           # 1 .. 15 m
    diffs = [-25 + 1.0 * i for i in range(31)]        # -25 .. +5 km/h
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, rain, title in [(axes[0], 0.0, "dry road"), (axes[1], 1.0, "wet road")]:
        grid = []
        crashes = 0
        for d in diffs:
            row = []
            for g in gaps:
                outcome = run_cutin(40, g, d, 1.0, rain)["outcome"]
                row.append(OUTCOME_NUMBER[outcome])
                crashes += outcome == "fail"
            grid.append(row)
        ax.imshow(grid, origin="lower", aspect="auto", extent=[1, 15, -25, 5],
                  cmap=ListedColormap(["#4caf50", "#ffc107", "#e53935"]), vmin=0, vmax=2)
        ax.set_title(f"{title}: {100 * crashes / (len(gaps) * len(diffs)):.0f}% crash")
        ax.set_xlabel("gap when the scooter cuts in (m)")
    axes[0].set_ylabel("scooter speed minus bus speed (km/h)")
    fig.suptitle("Basic AEB, bus at 40 km/h, scooter moves in at 1 m/s   (green = pass, yellow = near miss, red = crash)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig("failure_map.png", dpi=150)
    print("saved failure_map.png")


def search_compare():
    rows = list(csv.DictReader(open("search_results.csv")))
    random_hits = [int(r["random_crashes"]) for r in rows]
    guided_hits = [int(r["guided_crashes"]) for r in rows]
    avg_r = sum(random_hits) / len(rows)
    avg_g = sum(guided_hits) / len(rows)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["random", "guided (Bayesian opt.)"], [avg_r, avg_g], color=["grey", "tab:blue"])
    for i, hits in enumerate([random_hits, guided_hits]):
        ax.scatter([i] * len(hits), hits, color="black", s=12, zorder=3)   # each repeat as a dot
    ax.set_ylabel("crashes found in 100 runs")
    ax.set_title(f"Cut-in, basic AEB: random {avg_r:.0f} vs guided {avg_g:.0f} (avg of {len(rows)} repeats)")
    fig.tight_layout()
    fig.savefig("search_compare.png", dpi=150)
    print("saved search_compare.png")


def basic_vs_improved(n=400):
    rng = random.Random(1)
    cases = [(rng.uniform(20, 60), rng.uniform(1, 15), rng.uniform(-25, 5), rng.uniform(0.5, 2.5)) for _ in range(n)]
    results = {}
    for rain, label in [(0.0, "dry"), (1.0, "wet")]:
        for name, aeb in [("basic", basic_aeb), ("improved", improved_aeb)]:
            crashes = sum(run_cutin(b, g, d, s, rain, aeb=aeb)["outcome"] == "fail" for b, g, d, s in cases)
            results[(label, name)] = 100 * crashes / n
    fig, ax = plt.subplots(figsize=(6, 4))
    x = [0, 1]
    ax.bar([i - 0.2 for i in x], [results[("dry", "basic")], results[("wet", "basic")]], width=0.4,
           label="basic AEB", color="grey")
    ax.bar([i + 0.2 for i in x], [results[("dry", "improved")], results[("wet", "improved")]], width=0.4,
           label="improved AEB", color="tab:green")
    for i, label in enumerate(["dry", "wet"]):
        ax.text(i - 0.2, results[(label, "basic")] + 0.5, f"{results[(label, 'basic')]:.0f}%", ha="center")
        ax.text(i + 0.2, results[(label, "improved")] + 0.5, f"{results[(label, 'improved')]:.0f}%", ha="center")
    ax.set_ylim(0, max(results.values()) * 1.2)
    ax.set_xticks(x, ["dry road", "wet road"])
    ax.set_ylabel("% of cut-ins that end in a crash")
    ax.set_title(f"Same {n} random cut-ins, basic vs improved AEB")
    ax.legend()
    fig.tight_layout()
    fig.savefig("basic_vs_improved.png", dpi=150)
    print("saved basic_vs_improved.png")
    return results


if __name__ == "__main__":
    failure_map()
    print(basic_vs_improved())
    search_compare()
