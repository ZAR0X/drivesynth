# DriveSynth prototype - part 5: watch a cut-in from above
#
# Plays one run slowly in a window and prints the log in the terminal as it goes.
#   python view.py                         same cut-in as before, dry road
#   python view.py --rain 1                wet road
#   python view.py --gap 15 --slow 0.25    bigger gap, quarter speed
#   python view.py --rain 1 --save wet.mp4 save a video instead of opening a window

import argparse

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Rectangle

from bus import BUS_LENGTH, BUS_WIDTH, DT
from cutin import run_cutin
from scooter import SCOOTER_LENGTH, SCOOTER_WIDTH

BUS_COLOURS = {"watching": "tab:blue", "warning": "gold", "brake asked": "mediumpurple", "braking": "red"}

parser = argparse.ArgumentParser()
parser.add_argument("--speed", type=float, default=40, help="bus speed, km/h")
parser.add_argument("--gap", type=float, default=6, help="gap when the scooter starts cutting in, m")
parser.add_argument("--diff", type=float, default=-15, help="scooter speed minus bus speed, km/h")
parser.add_argument("--side", type=float, default=1.0, help="scooter sideways speed, m/s")
parser.add_argument("--rain", type=float, default=0.0, help="0 = dry, 1 = heavy rain")
parser.add_argument("--slow", type=float, default=0.5, help="playback speed, 1 = real time")
parser.add_argument("--save", help="save to this .mp4 file instead of showing a window")
args = parser.parse_args()

run = run_cutin(args.speed, args.gap, args.diff, args.side, args.rain, record=True)
frames = run["frames"]
events = run["events"]
frames = frames + [frames[-1]] * int(1.5 / DT)   # hold the last picture for a moment

print(f"bus {args.speed:.0f} km/h, scooter {args.diff:+.0f} km/h, gap {args.gap} m, "
      f"sideways {args.side} m/s, rain {args.rain}")

fig, ax = plt.subplots(figsize=(10, 2.8))
fig.subplots_adjust(left=0.02, right=0.98, top=0.85, bottom=0.05)
printed = set()


def draw(i):
    f = frames[i]
    ax.clear()
    left, right = f["bus_x"] - 16, f["bus_x"] + 30      # camera follows the bus
    ax.set_xlim(left, right)
    ax.set_ylim(-6.8, 2.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # road: bus lane (y -1.75..1.75) and the lane next to it (y -5.25..-1.75)
    ax.add_patch(Rectangle((left, -5.25), right - left, 7.0, color="0.35"))
    ax.plot([left, right], [1.75, 1.75], color="white", lw=2)
    ax.plot([left, right], [-5.25, -5.25], color="white", lw=2)
    ax.plot([left, right], [-1.75, -1.75], color="white", lw=1.5, ls=(0, (6, 6)))

    bus_colour = BUS_COLOURS[f["aeb"]]
    ax.add_patch(Rectangle((f["bus_x"] - BUS_LENGTH, -BUS_WIDTH / 2), BUS_LENGTH, BUS_WIDTH,
                           facecolor=bus_colour, edgecolor="black"))
    ax.text(f["bus_x"] - BUS_LENGTH / 2, 0, "BUS", ha="center", va="center", fontsize=9)

    ax.add_patch(Rectangle((f["scooter_x"], f["scooter_y"] - SCOOTER_WIDTH / 2), SCOOTER_LENGTH, SCOOTER_WIDTH,
                           facecolor="tab:orange", edgecolor="cyan" if f["seen"] else "black", lw=2))
    ax.text(f["scooter_x"] + SCOOTER_LENGTH / 2, f["scooter_y"] - 0.9, "scooter", ha="center", va="top",
            fontsize=8, color="white")
    ax.text(left, -6.0, "bus: blue = watching, yellow = warning, purple = brake asked (air brakes not working yet), red = braking   "
                        "cyan outline = sensor has seen the scooter", fontsize=8, va="top", color="0.3")

    title = f"t = {f['t']:.2f} s     bus {f['bus_kmh']:.0f} km/h     AEB: {f['aeb']}"
    if i >= len(run["frames"]) - 1:
        if run["outcome"] == "fail":
            title += f"     CRASH at {run['crash_speed_kmh']:.0f} km/h"
        else:
            title += f"     no crash ({run['outcome']})"
    ax.set_title(title, loc="left", fontsize=10, family="monospace")

    # print log lines in the terminal when the playback reaches them
    for k, (et, text) in enumerate(events):
        if et <= f["t"] + 1e-9 and k not in printed:
            print(f"t={et:4.2f}s  {text}")
            printed.add(k)


anim = FuncAnimation(fig, draw, frames=len(frames), interval=DT * 1000 / args.slow, repeat=False)
if args.save:
    anim.save(args.save, writer=FFMpegWriter(fps=round(1 / DT * args.slow)))
    print(f"saved {args.save}")
else:
    plt.show()
