# DriveSynth

Team Brand New Day, KPIT K-Impact 2026 (Simulation).

We test emergency braking (AEB) on a bus in Indian-style traffic situations, in a small 2D simulator,
and use a search to find the settings where it fails. Right now it covers one situation: a scooter
cutting in front of the bus.

Code, how to run it and our notes are in [prototype/](prototype/README.md).

Full documentation (rebuilt on every push, with the latest charts and numbers): https://zar0x.github.io/drivesynth/

```
cd prototype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python view.py --rain 1
.venv/bin/python gui.py      # sliders, buttons and the log in one window
```
