# DriveSynth prototype - simple GUI
#
# One window: the 2D road on the left, the log on the right, controls at the bottom.
#   - sliders + AEB choice, then "Run cut-in" plays that run in the window
#   - the other buttons run our scripts (bus.py, sensor.py, cutin.py, search.py, charts.py) and stream
#     their output into the log
# Built with matplotlib's own widgets, so it needs nothing beyond requirements.txt.
#   .venv/bin/python gui.py

"""Simple GUI: pick the settings, run a cut-in or one of our scripts, and read the log on the side."""

import os
import queue
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, Slider

from aeb import basic_aeb, improved_aeb
from bus import DT
from cutin import FAMILY, run_cutin
from view import draw_scene

HERE = Path(__file__).parent
LOG_LINES = 32

log = deque(maxlen=200)
incoming = queue.Queue()      # lines from scripts running in the background
state = {"frames": None, "i": 0, "run": None, "events": None, "shown": 0, "busy": False}

fig = plt.figure(figsize=(14, 8))
fig.canvas.manager.set_window_title("DriveSynth")
ax_road = fig.add_axes([0.02, 0.50, 0.62, 0.44])
ax_log = fig.add_axes([0.66, 0.30, 0.33, 0.66])
ax_log.axis("off")
log_text = ax_log.text(0, 1, "", va="top", family="monospace", fontsize=8, transform=ax_log.transAxes)
ax_log.set_title("log", loc="left", fontsize=10)
ax_road.axis("off")
ax_road.set_title("pick settings below, then Run cut-in", loc="left", fontsize=10, family="monospace")

# sliders come from the FAMILY block, so ranges match the search
defaults = {"bus_kmh": 40, "gap": 6, "speed_diff_kmh": -15, "sideways_speed": 1.0, "rain": 0.0}
short = {"bus_kmh": "bus speed (km/h)", "gap": "cut-in gap (m)", "speed_diff_kmh": "scooter vs bus (km/h)",
         "sideways_speed": "sideways speed (m/s)", "rain": "rain (0 dry, 1 heavy)"}
sliders = {}
for k, s in enumerate(FAMILY["settings"]):
    ax = fig.add_axes([0.17, 0.40 - k * 0.055, 0.40, 0.03])
    sliders[s["name"]] = Slider(ax, short.get(s["name"], s["label"]), s["min"], s["max"], valinit=defaults[s["name"]])

aeb_choice = RadioButtons(fig.add_axes([0.02, 0.05, 0.10, 0.10]), ["basic AEB", "improved AEB"])


def write(line):
    log.append(line)
    log_text.set_text("\n".join(list(log)[-LOG_LINES:]))


def run_cutin_clicked(_):
    v = {name: sl.val for name, sl in sliders.items()}
    aeb = improved_aeb if aeb_choice.value_selected == "improved AEB" else basic_aeb
    r = run_cutin(v["bus_kmh"], v["gap"], v["speed_diff_kmh"], v["sideways_speed"], v["rain"], aeb=aeb, record=True)
    write("")
    write(f"--- cut-in, {aeb_choice.value_selected}: bus {v['bus_kmh']:.0f} km/h, gap {v['gap']:.1f} m,")
    write(f"    scooter {v['speed_diff_kmh']:+.0f} km/h, sideways {v['sideways_speed']:.1f} m/s, rain {v['rain']:.1f}")
    state.update(frames=r["frames"] + [r["frames"][-1]] * 20, i=0, run=r, events=r["events"], shown=0)


def run_script(name, *args):
    """Run one of our scripts in the background and stream its output into the log."""
    if state["busy"]:
        write("(wait, a script is still running)")
        return

    def worker():
        state["busy"] = True
        incoming.put(f"--- running {name} {' '.join(args)}")
        p = subprocess.Popen([sys.executable, "-u", name, *args], cwd=HERE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, env=dict(os.environ, MPLBACKEND="Agg"))
        for line in p.stdout:
            if "Warning" not in line:          # skip sklearn/skopt warnings
                incoming.put(line.rstrip())
        p.wait()
        incoming.put(f"--- {name} finished")
        state["busy"] = False

    threading.Thread(target=worker, daemon=True).start()


def tick():
    """Runs every 50 ms in the GUI thread: plays the cut-in and moves script output into the log."""
    changed = False
    while not incoming.empty():
        write(incoming.get())
        changed = True
    frames = state["frames"]
    if frames and state["i"] < len(frames):
        i = state["i"]
        f, r = frames[i], state["run"]
        title = f"t = {f['t']:.2f} s   bus {f['bus_kmh']:.0f} km/h   AEB: {f['aeb']}"
        if i >= len(r["frames"]) - 1:
            title += f"   CRASH at {r['crash_speed_kmh']:.0f} km/h" if r["outcome"] == "fail" else f"   no crash ({r['outcome']})"
        draw_scene(ax_road, f, title)
        events = state["events"]
        while state["shown"] < len(events) and events[state["shown"]][0] <= f["t"] + 1e-9:
            et, text = events[state["shown"]]
            write(f"t={et:4.2f}s  {text}")
            state["shown"] += 1
        state["i"] += 1
        changed = True
    if changed:
        fig.canvas.draw_idle()


buttons = []
for k, (label, action) in enumerate([
        ("Run cut-in", run_cutin_clicked),
        ("Braking test", lambda _: run_script("bus.py")),
        ("No-AEB test", lambda _: run_script("sensor.py")),
        ("Dry vs wet", lambda _: run_script("cutin.py")),
        ("Search 4 min", lambda _: run_script("search.py")),
        ("Make charts", lambda _: run_script("charts.py")),
        ("Clear log", lambda _: (log.clear(), write("")))]):
    b = Button(fig.add_axes([0.66 + (k % 4) * 0.083, 0.19 - (k // 4) * 0.07, 0.078, 0.05]), label)
    b.on_clicked(action)
    buttons.append(b)                         # keep a reference, or the button stops working

write("DriveSynth: set the sliders and click Run cut-in.")
write("The other buttons run our scripts; their output appears here.")
timer = fig.canvas.new_timer(interval=int(DT * 1000))
timer.add_callback(tick)
timer.start()
plt.show()
