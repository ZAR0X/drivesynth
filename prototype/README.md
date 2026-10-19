# DriveSynth prototype

Small 2D simulator we're writing for K-Impact 2026. The idea: put a bus with emergency braking (AEB) into
Indian-style traffic situations and find the settings where the AEB doesn't stop in time.

Work in progress. Done so far: the bus and its brakes, the scooter that cuts in, a simple sensor, a
basic AEB, a script that runs one cut-in from start to finish, and a simple 2D viewer.

## Run

Needs Python 3. The viewer also needs matplotlib (and ffmpeg if you want to save videos).

```
cd prototype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python bus.py      # braking test, dry vs wet
.venv/bin/python sensor.py   # scooter cuts in, nobody brakes
.venv/bin/python cutin.py    # scooter cuts in, basic AEB, dry vs wet
.venv/bin/python view.py     # watch it from above, log prints in the terminal
```

## What's done so far

**bus.py**: the bus. Drives straight, can brake, can't steer.

- brakes kick in 0.3 s after the AEB asks (air brakes on buses are slow)
- max braking is 6.5 m/s² on a dry road and 3.5 m/s² on a wet one (rain goes from 0 to 1, we just
  interpolate in between)
- every 0.05 s: `speed = speed - braking * 0.05`, then `position = position + speed * 0.05`

Sanity check against the usual stopping distance formula `d = v * 0.3 + v² / (2a)`:

| bus at 40 km/h | our sim | formula |
|---|---|---|
| dry | 12.6 m | 12.8 m |
| wet | 20.7 m | 21.0 m |

Close enough. The small gap is because we move in 0.05 s steps instead of continuously.

**scooter.py**: the scooter that cuts in. It starts in the next lane (y = -2.3 m), rides straight for
0.5 s, then moves sideways into the bus's lane until it's in the middle. It doesn't react to the bus.
You set three things:

- `gap`: metres between the bus front and the scooter's back when it starts cutting in
- `speed_diff_kmh`: scooter speed minus bus speed (negative = slower, that's the dangerous one)
- `sideways_speed`: how fast it moves across, m/s

**sensor.py**: what the bus knows about the scooter. We don't simulate a real radar/camera, just two
limits they have:

- range: 100 m, down to 60 m in heavy rain (`100 * (1 - 0.4 * rain)`)
- confirm time: the scooter has to be seen for 0.3 s before the AEB trusts it, up to 0.6 s in
  heavy rain (`0.3 * (1 + rain)`)

The sensor gives the AEB the gap, the scooter's sideways position, how fast the gap is closing and how
fast the scooter is moving sideways. The values are exact, no noise. A real sensor isn't that clean.

Example run of `sensor.py` (bus 40 km/h, scooter 15 km/h slower, cuts in 6 m ahead at 1 m/s):

```
t=0.30s  sensor: scooter confirmed, 6.8 m ahead
t=0.50s  scooter starts moving into the bus's lane
t=1.20s  scooter is now in front of the bus, gap 3.1 m
t=1.95s  CRASH at 40 km/h (no AEB in this test)
```

Checked by hand: closing speed is 15 km/h = 4.2 m/s, so a 6 m gap is gone in 6 / 4.2 = 1.44 s after
the cut-in starts at 0.5 s, so a crash at about 1.95 s.

"In front of the bus" means the scooter overlaps the bus sideways: `|y| < 1.25 + 0.4` (half bus
width + half scooter width).

Bug we hit: adding 0.05 s again and again gives 0.49999 instead of 0.5, so things that should start at
0.5 s started one step late. We round the clock to 3 decimals now.

**aeb.py**: the basic AEB. Real AEB code from bus makers isn't public, so we wrote the usual textbook
rule (time to collision with staged braking, same idea as the MathWorks AEB example):

```
TTC = gap / closing speed
TTC < 2.5 s  -> warning
TTC < 1.5 s  -> full braking
```

It only reacts to the scooter once it's in the bus's lane and getting closer. Once it asks for brakes
the bus keeps braking until it stops (a real AEB would let go earlier; good enough for now).

**cutin.py**: runs one cut-in. Every 0.05 s: sensor looks, AEB decides, bus and scooter move, check
for a crash. Outcome is the same as in our idea PDF: `fail` = crash, `near miss` = no crash but TTC
went below 1 s, `pass` = neither.

Same cut-in as before (bus 40 km/h, scooter 15 km/h slower, cuts in 6 m ahead at 1 m/s):

```
--- dry road ---
t=1.20s  scooter is in the bus's lane, 3.1 m ahead
t=1.20s  AEB: BRAKE (TTC 0.7 s)
t=1.50s  brakes working
t=3.20s  no crash, bus at 0 km/h, smallest TTC 0.41 s -> near miss

--- wet road ---
t=1.20s  scooter is in the bus's lane, 3.1 m ahead
t=1.20s  AEB: BRAKE (TTC 0.7 s)
t=1.50s  brakes working
t=2.10s  CRASH at 32 km/h
```

Why: when the brakes start working there's 1.85 m left and the gap is closing at 4.2 m/s. To get rid
of that closing speed you need `4.2² / (2 * braking)` metres. Dry (6.5 m/s²): 1.34 m, it fits. Wet
(3.5 m/s²): 2.5 m, it doesn't.

Note the AEB never got to warn here. The scooter was only "in the lane" when TTC was already 0.7 s,
so it went straight to braking. With a 15 m gap it warns at 1.60 s, brakes at 2.60 s and stops fine.

First version of the log printed "AEB: warning" after it had already braked (TTC goes back up while
the bus slows down). Fixed: once it's braking we don't log warnings anymore.

**view.py**: watch one cut-in from above. Plain matplotlib window, camera follows the bus, and the
same log lines get printed in the terminal when the playback reaches them.

```
.venv/bin/python view.py                          # same cut-in as above, dry
.venv/bin/python view.py --rain 1                 # wet
.venv/bin/python view.py --gap 15 --slow 0.25     # bigger gap, quarter speed
.venv/bin/python view.py --rain 1 --save wet.mp4  # save a video instead
```

Colours: bus blue = watching, yellow = warning, purple = brake asked but the air brakes aren't working
yet (that 0.3 s), red = braking. Cyan outline on the scooter = the sensor has confirmed it.

The bus was orange during the "brake asked" bit at first, same as the scooter, which was confusing.
Changed it to purple.

**aeb.py, improved_aeb**: a second AEB version, only so the tester has two things to compare. We're
not building an AEB; a company would plug in its own. It changes two things the basic one got wrong:

- it also reacts to a scooter moving sideways towards the lane, if it'll get there before the bus does
- in rain it brakes earlier: TTC 1.5 s dry, up to 2.3 s in heavy rain (the sensor passes on the rain
  level, like the rain sensor that runs the wipers)

**search.py**: the main idea of the project. 5 knobs for the cut-in (bus speed 20-60 km/h, gap 1-15 m,
scooter speed -25..+5 km/h vs the bus, sideways speed 0.5-2.5 m/s, rain 0-1). We pick 100 settings two
ways and count crashes:

- random: 100 random settings
- guided: `gp_minimize` from scikit-optimize (Bayesian optimisation). It looks at the runs so far and
  tests next where it expects the smallest safety margin. Safety margin = smallest TTC if no crash, or
  minus (crash speed / 10) if it crashed.

Each done 5 times with different random starts (`search_results.csv`), takes about 4 minutes:

```
repeat 1: random found 21 crashes, guided found 89 crashes (out of 100 runs)
repeat 2: random found 23 crashes, guided found 87 crashes (out of 100 runs)
repeat 3: random found 20 crashes, guided found 84 crashes (out of 100 runs)
repeat 4: random found 22 crashes, guided found 89 crashes (out of 100 runs)
repeat 5: random found 21 crashes, guided found 90 crashes (out of 100 runs)
average: random 21, guided 88 crashes per 100 runs
```

Catch: the guided search heads straight for the worst corner (tiny gaps, much slower scooter), so lots
of its crashes are ones no brake could have stopped. It's great at finding failures, but the count
alone overstates it a bit.

**charts.py**: makes the three charts we use in the presentation:

- `failure_map.png`: basic AEB, bus 40 km/h, gap vs scooter speed. Red = crash, yellow = near miss,
  green = fine. 23% of the grid crashes on a dry road, 29% on a wet one.
- `search_compare.png`: random vs guided, crashes per 100 runs (bars = average, dots = each repeat).
- `basic_vs_improved.png`: the same 400 random cut-ins with both AEBs. Basic 17% crash dry / 23% wet,
  improved 7% / 14%.

Demo videos: `view.py ... --save out/name.mp4`. `out/` isn't in git.

## Numbers we assumed

The 0.3 s delay and the 6.5 / 3.5 m/s² values are typical figures for a city bus on dry/wet asphalt,
not measured on a real bus. Change them at the top of `bus.py` if you have better numbers.
