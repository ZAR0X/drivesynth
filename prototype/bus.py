# DriveSynth prototype - part 1: the bus and its brakes
#
# The bus only drives straight ahead. It can brake, but it cannot steer.
# Two things make a bus different from a car when braking:
#   1. air brakes take about 0.3 s to start working after the AEB asks for them
#   2. on a wet road the tyres grip less, so the bus cannot brake as hard

DT = 0.05            # time step in seconds (we update everything 20 times per second)
BRAKE_DELAY = 0.3    # seconds between "AEB says brake" and the brakes actually working
DRY_BRAKING = 6.5    # strongest braking on a dry road, in m/s^2
WET_BRAKING = 3.5    # strongest braking on a fully wet road, in m/s^2

BUS_LENGTH = 12.0    # metres
BUS_WIDTH = 2.5      # metres


def kmh_to_ms(kmh):
    return kmh / 3.6


def ms_to_kmh(ms):
    return ms * 3.6


def max_braking(rain):
    """Strongest braking possible. rain = 0 (dry) ... 1 (heavy rain). Simple straight line between dry and wet."""
    return DRY_BRAKING - (DRY_BRAKING - WET_BRAKING) * rain


class Bus:
    def __init__(self, speed_kmh, rain=0.0):
        self.x = 0.0                      # position of the bus front along the road (m)
        self.speed = kmh_to_ms(speed_kmh) # m/s
        self.rain = rain
        self.brake_asked_at = None        # time when the AEB first asked to brake
        self.braking = 0.0                # current braking in m/s^2

    def ask_to_brake(self, t):
        """Called by the AEB. Only the first request matters - after that the bus keeps braking."""
        if self.brake_asked_at is None:
            self.brake_asked_at = t

    def step(self, t):
        """Move the bus forward by one time step."""
        if self.brake_asked_at is not None and t >= self.brake_asked_at + BRAKE_DELAY:
            self.braking = max_braking(self.rain)
        self.speed = max(0.0, self.speed - self.braking * DT)
        self.x += self.speed * DT

    def stopped(self):
        return self.speed == 0.0


def stopping_distance_formula(speed_kmh, rain):
    """Distance = (distance covered during the brake delay) + (distance while braking) = v*delay + v^2 / (2*a)"""
    v = kmh_to_ms(speed_kmh)
    a = max_braking(rain)
    return v * BRAKE_DELAY + v * v / (2 * a)


if __name__ == "__main__":
    # Test: bus at 40 km/h, AEB asks to brake at t = 0. How far until it stops? Dry road vs wet road.
    for rain, label in [(0.0, "dry"), (1.0, "wet")]:
        print(f"--- bus at 40 km/h, {label} road ---")
        bus = Bus(speed_kmh=40, rain=rain)
        bus.ask_to_brake(0.0)
        t = 0.0
        print(f"t={t:4.2f}s  AEB asks to brake")
        brakes_on_printed = False
        while not bus.stopped():
            bus.step(t)
            if bus.braking > 0 and not brakes_on_printed:
                print(f"t={t:4.2f}s  brakes working, bus at {ms_to_kmh(bus.speed):.0f} km/h, moved {bus.x:.1f} m")
                brakes_on_printed = True
            t = round(t + DT, 3)
        print(f"t={t:4.2f}s  stopped after {bus.x:.1f} m")
        print(f"          formula says {stopping_distance_formula(40, rain):.1f} m")
        print()
