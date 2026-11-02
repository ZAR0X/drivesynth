# Run it

Needs Python 3. Saving videos also needs `ffmpeg`.

```bash
git clone https://github.com/ZAR0X/drivesynth.git
cd drivesynth/prototype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Commands

| Command | What you get | Time |
|---|---|---|
| `.venv/bin/python bus.py` | braking test, dry vs wet, compared with the formula | instant |
| `.venv/bin/python sensor.py` | scooter cuts in, nobody brakes | instant |
| `.venv/bin/python cutin.py` | same cut-in with the basic AEB, dry and wet | instant |
| `.venv/bin/python gui.py` | one window: sliders + AEB choice, Run cut-in plays it, other buttons run the scripts below; log on the right | instant |
| `.venv/bin/python view.py --rain 1` | window with the 2D top view, log in the terminal | ~5 s |
| `.venv/bin/python view.py --rain 1 --aeb improved` | same, with the second AEB version | ~5 s |
| `.venv/bin/python view.py --rain 1 --save out/wet.mp4` | saves a video instead (log drawn under the road) | ~10 s |
| `.venv/bin/python search.py` | random vs guided search, 5 repeats, writes `search_results.csv` | ~4 min |
| `.venv/bin/python charts.py` | the three charts + `results.json` (run `search.py` first) | ~30 s |

### view.py options

```
--speed 40      bus speed, km/h
--gap 6         gap when the scooter starts cutting in, m
--diff -15      scooter speed minus bus speed, km/h
--side 1.0      scooter sideways speed, m/s
--rain 0        0 = dry, 1 = heavy rain
--slow 0.5      playback speed, 1 = real time
--aeb basic     or "improved"
--save out.mp4  save a video instead of opening a window
```

## Building these docs locally

```bash
pip install -r docs/requirements.txt
cp prototype/*.png docs/img/
mkdocs serve
```

Then open <http://127.0.0.1:8000>. On GitHub this happens automatically on every push (see
`.github/workflows/docs.yml`).

## How the docs stay up to date

You don't edit the docs to describe code changes. They're generated from the code on every push:

| You do this in the code | What changes on the site |
|---|---|
| add or change a function, with a one-line docstring | it appears on that file's page under **Reference** |
| add a new `.py` file in `prototype/` | it gets its own Reference page |
| add a new scenario family: a file with a `FAMILY = {...}` block (name, description, run function, settings with min/max) | it appears on **Scenario families**; copy the block in `cutin.py` |
| change code that affects results | `search.py` and `charts.py` re-run, so charts and numbers update |
| commit | it shows up in the **Change log** under "Unreleased" |

## Releasing a version

The site has a version picker. Every push to `main` updates the `dev` version. To publish a release:

```bash
git tag v0.2.0
git push origin v0.2.0
```

That builds the docs as `v0.2.0` and points `latest` at it. Older versions stay readable from the picker.
