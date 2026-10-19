# DriveSynth prototype - part 4: run one scooter cut-in with an AEB and see what happens
#
# Each step (0.05 s): sensor looks -> AEB decides -> bus and scooter move -> check for a crash.
# Result of a run (same as in our idea PDF):
#   fail      = the bus hits the scooter
#   near miss = no crash, but TTC dropped below 1 s
#   pass      = neither

from bus import Bus, BUS_LENGTH, DT
from scooter import Scooter, SCOOTER_LENGTH, START_Y
from sensor import Sensor
from aeb import basic_aeb, in_bus_lane, time_to_collision


def run_cutin(bus_kmh, gap, speed_diff_kmh, sideways_speed, rain, aeb=basic_aeb, show_log=False):
    bus = Bus(bus_kmh, rain)
    scooter = Scooter(bus_kmh, gap, speed_diff_kmh, sideways_speed)
    sensor = Sensor(rain)

    def log(t, text):
        if show_log:
            print(f"t={t:4.2f}s  {text}")

    t = 0.0
    seen = in_lane = warned = braking_logged = False
    smallest_ttc = None
    result = {"outcome": "pass", "crash_speed_kmh": 0.0}

    while t < 10.0:
        info = sensor.look(t, bus, scooter)
        if info and not seen:
            log(t, f"sensor: scooter confirmed, {info['gap']:.1f} m ahead")
            seen = True
        if scooter.is_moving_sideways(t) and scooter.y == START_Y:
            log(t, "scooter starts moving into the bus's lane")
        if info and in_bus_lane(info) and not in_lane:
            log(t, f"scooter is in the bus's lane, {info['gap']:.1f} m ahead")
            in_lane = True

        # what does the AEB want?
        decision = aeb(info)
        if decision == "warning" and not warned and bus.brake_asked_at is None:
            log(t, f"AEB: warning (TTC {time_to_collision(info):.1f} s)")
            warned = True
        if decision == "brake" and bus.brake_asked_at is None:
            log(t, f"AEB: BRAKE (TTC {time_to_collision(info):.1f} s)")
            bus.ask_to_brake(t)

        # keep track of how close it got
        if info and in_bus_lane(info):
            ttc = time_to_collision(info)
            if ttc is not None and (smallest_ttc is None or ttc < smallest_ttc):
                smallest_ttc = ttc

        bus.step(t)
        scooter.step(t)
        if bus.braking > 0 and not braking_logged:
            log(t, "brakes working")
            braking_logged = True

        # crash: scooter overlaps the bus sideways and the gap is gone
        gap_now = scooter.x - bus.x
        if abs(scooter.y) < 1.25 + 0.4 and gap_now <= 0 and scooter.x + SCOOTER_LENGTH > bus.x - BUS_LENGTH:
            result = {"outcome": "fail", "crash_speed_kmh": round(bus.speed * 3.6, 1)}
            log(t, f"CRASH at {bus.speed * 3.6:.0f} km/h")
            break

        # stop the run once it's over: bus has stopped, or the scooter is pulling away
        if bus.stopped() or (gap_now > 30 and scooter.speed >= bus.speed):
            break
        t = round(t + DT, 3)

    if result["outcome"] == "pass" and smallest_ttc is not None and smallest_ttc < 1.0:
        result["outcome"] = "near miss"
    result["smallest_ttc"] = None if smallest_ttc is None else round(smallest_ttc, 2)
    if result["outcome"] != "fail":
        log(t, f"no crash, bus at {bus.speed * 3.6:.0f} km/h, smallest TTC {result['smallest_ttc']} s -> {result['outcome']}")
    return result


if __name__ == "__main__":
    # same cut-in as the sensor test: bus 40 km/h, scooter 15 km/h slower, cuts in 6 m ahead at 1 m/s
    for rain, label in [(0.0, "dry"), (1.0, "wet")]:
        print(f"--- same cut-in, basic AEB, {label} road ---")
        r = run_cutin(40, 6.0, -15, 1.0, rain, show_log=True)
        print(f"result: {r}")
        print()
