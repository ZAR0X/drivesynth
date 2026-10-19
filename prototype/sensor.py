# DriveSynth prototype - part 2b: what the bus can "see"
#
# Real AEB uses a radar and a camera. We don't simulate those. We only copy two of their limits:
#   1. range  - it can only see so far ahead, and less far in rain
#   2. delay  - a new object has to be seen for a short while before the AEB trusts it
#               (the camera software needs a few frames to be sure it's really a scooter)
# Everything the AEB knows comes from here. The AEB never looks at the scooter directly.

DT = 0.05
RANGE_DRY = 100.0     # metres
CONFIRM_TIME = 0.3    # seconds the scooter must be seen before the AEB trusts it (dry, daylight)


class Sensor:
    def __init__(self, rain=0.0):
        self.range = RANGE_DRY * (1 - 0.4 * rain)       # heavy rain: 60 m
        self.confirm_time = CONFIRM_TIME * (1 + rain)   # heavy rain: 0.6 s
        self.first_seen = None

    def look(self, t, bus, scooter):
        """Returns what the AEB is told about the scooter, or None if it doesn't know about it yet."""
        gap = scooter.x - bus.x
        visible = 0 < gap < self.range
        if not visible:
            self.first_seen = None
            return None
        if self.first_seen is None:
            self.first_seen = t
        if t - self.first_seen < self.confirm_time:
            return None   # seen, but not trusted yet
        return {
            "gap": gap,                                   # metres from bus front to scooter back
            "y": scooter.y,                               # sideways position of the scooter
            "closing_speed": bus.speed - scooter.speed,   # how fast the gap shrinks (m/s)
            "sideways_speed": scooter.sideways_speed if scooter.is_moving_sideways(t) else 0.0,
        }


# ---------------------------------------------------------------------------------------------
# Test: bus + scooter + sensor, no AEB yet. Does the bus hit the scooter if nobody brakes?

if __name__ == "__main__":
    from bus import Bus, BUS_LENGTH, BUS_WIDTH
    from scooter import Scooter, SCOOTER_LENGTH, SCOOTER_WIDTH

    bus_kmh, gap, diff, side, rain = 40, 6.0, -15, 1.0, 0.0
    print(f"bus {bus_kmh} km/h, scooter {abs(diff)} km/h slower, cuts in {gap:.0f} m ahead "
          f"at {side} m/s sideways, rain {rain}")
    bus = Bus(bus_kmh, rain)
    scooter = Scooter(bus_kmh, gap, diff, side)
    sensor = Sensor(rain)

    t = 0.0
    told = False
    entered = False
    while t < 5.0:
        info = sensor.look(t, bus, scooter)
        if info and not told:
            print(f"t={t:4.2f}s  sensor: scooter confirmed, {info['gap']:.1f} m ahead")
            told = True
        if scooter.is_moving_sideways(t) and abs(scooter.y - (-2.3)) < 1e-9:
            print(f"t={t:4.2f}s  scooter starts moving into the bus's lane")
        in_path = abs(scooter.y) < BUS_WIDTH / 2 + SCOOTER_WIDTH / 2
        if in_path and not entered:
            print(f"t={t:4.2f}s  scooter is now in front of the bus, gap {scooter.x - bus.x:.1f} m")
            entered = True
        gap_now = scooter.x - bus.x
        if in_path and gap_now <= 0 and scooter.x + SCOOTER_LENGTH > bus.x - BUS_LENGTH:
            print(f"t={t:4.2f}s  CRASH at {bus.speed * 3.6:.0f} km/h (no AEB in this test)")
            break
        bus.step(t)
        scooter.step(t)
        t = round(t + 0.05, 3)   # round so 0.05 + 0.05 + ... lands exactly on 0.5, 1.0, ...
    else:
        print("no crash")
