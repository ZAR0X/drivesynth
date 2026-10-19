# DriveSynth prototype

Small 2D simulator we're writing for K-Impact 2026. The idea: put a bus with emergency braking (AEB) into
Indian-style traffic situations and find the settings where the AEB doesn't stop in time.

Work in progress. Done so far: the bus and its brakes, the scooter that cuts in, a simple sensor, a
basic AEB, and a script that runs one cut-in from start to finish.

## Run

Needs Python 3 (no extra packages yet).

```
cd prototype
python3 bus.py      # braking test, dry vs wet
python3 sensor.py   # scooter cuts in, nobody brakes
python3 cutin.py    # scooter cuts in, basic AEB, dry vs wet
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

## Numbers we assumed

The 0.3 s delay and the 6.5 / 3.5 m/s² values are typical figures for a city bus on dry/wet asphalt,
not measured on a real bus. Change them at the top of `bus.py` if you have better numbers.
