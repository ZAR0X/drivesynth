# DriveSynth prototype - part 6: random search vs guided search
#
# We have 5 knobs for the cut-in. Trying every combination is too many runs, so we compare two ways of
# picking 100 settings to test:
#   random - 100 random settings
#   guided - Bayesian optimisation (gp_minimize from scikit-optimize). It looks at the runs so far,
#            guesses where the safety margin will be smallest, and tests there next.
# Then we count how many of the 100 runs ended in a crash.

import random
import sys

from skopt import gp_minimize

from aeb import basic_aeb
from cutin import run_cutin

KNOBS = [
    (20.0, 60.0),   # bus speed, km/h
    (1.0, 15.0),    # gap when the scooter starts cutting in, m
    (-25.0, 5.0),   # scooter speed minus bus speed, km/h
    (0.5, 2.5),     # scooter sideways speed, m/s
    (0.0, 1.0),     # rain, 0 = dry, 1 = heavy
]
RUNS = 100
REPEATS = 5


def safety_margin(knobs, aeb=basic_aeb):
    """Smaller = more dangerous. Crash gives a negative number (worse crash = more negative)."""
    bus_kmh, gap, diff, side, rain = knobs
    r = run_cutin(bus_kmh, gap, diff, side, rain, aeb=aeb)
    if r["outcome"] == "fail":
        return -r["crash_speed_kmh"] / 10
    return min(r["smallest_ttc"] if r["smallest_ttc"] is not None else 5.0, 5.0)


def random_search(seed, aeb=basic_aeb):
    rng = random.Random(seed)
    margins = []
    for _ in range(RUNS):
        knobs = [rng.uniform(lo, hi) for lo, hi in KNOBS]
        margins.append(safety_margin(knobs, aeb))
    return margins


def guided_search(seed, aeb=basic_aeb):
    result = gp_minimize(lambda k: safety_margin(k, aeb), KNOBS, n_calls=RUNS, n_initial_points=10,
                         random_state=seed)
    return list(result.func_vals)


def count_crashes(margins):
    return sum(1 for m in margins if m < 0)


if __name__ == "__main__":
    rows = []
    for seed in range(REPEATS):
        r = count_crashes(random_search(seed))
        g = count_crashes(guided_search(seed))
        rows.append((seed, r, g))
        print(f"repeat {seed + 1}: random found {r} crashes, guided found {g} crashes (out of {RUNS} runs)")
        sys.stdout.flush()
    avg_r = sum(r for _, r, _ in rows) / REPEATS
    avg_g = sum(g for _, _, g in rows) / REPEATS
    print(f"average: random {avg_r:.0f}, guided {avg_g:.0f} crashes per {RUNS} runs")
    with open("search_results.csv", "w") as f:
        f.write("repeat,random_crashes,guided_crashes\n")
        for seed, r, g in rows:
            f.write(f"{seed + 1},{r},{g}\n")
