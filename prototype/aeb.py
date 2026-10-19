# DriveSynth prototype - part 3: the AEB (the thing we're testing)
#
# Real AEB software isn't public, so this is the usual textbook rule:
#   TTC (time to collision) = gap / closing speed
#   TTC below 2.5 s -> warn the driver
#   TTC below 1.5 s -> full braking
# It only cares about something that is already in the bus's lane and getting closer.
# It only gets what the sensor tells it (see sensor.py), never the real scooter.

WARN_TTC = 2.5    # seconds
BRAKE_TTC = 1.5   # seconds

BUS_HALF_WIDTH = 1.25
SCOOTER_HALF_WIDTH = 0.4


def in_bus_lane(info):
    """Is the scooter overlapping the bus sideways?"""
    return abs(info["y"]) < BUS_HALF_WIDTH + SCOOTER_HALF_WIDTH


def time_to_collision(info):
    """Seconds until we hit it if nothing changes. None if it's not getting closer."""
    if info["closing_speed"] <= 0:
        return None
    return info["gap"] / info["closing_speed"]


def basic_aeb(info):
    """Returns 'none', 'warning' or 'brake'."""
    if info is None or not in_bus_lane(info):
        return "none"
    ttc = time_to_collision(info)
    if ttc is None:
        return "none"
    if ttc < BRAKE_TTC:
        return "brake"
    if ttc < WARN_TTC:
        return "warning"
    return "none"


# ---------------------------------------------------------------------------------------------
# Improved AEB - written after we saw where the basic one fails:
#   1. the basic one ignores the scooter until it's already in the lane. This one also reacts to a
#      scooter moving sideways towards the lane if it will get there before we reach it.
#   2. the basic one brakes at the same TTC on a wet road, but wet brakes need more room.
#      This one starts braking earlier in rain: 1.5 s dry, up to 2.3 s in heavy rain.

def will_enter_lane_in_time(info):
    """Scooter outside the lane but moving towards it: will it be in front of us before we get there?"""
    if info["sideways_speed"] <= 0:
        return False
    distance_to_lane = abs(info["y"]) - (BUS_HALF_WIDTH + SCOOTER_HALF_WIDTH)
    time_to_enter = distance_to_lane / info["sideways_speed"]
    ttc = time_to_collision(info)
    return ttc is not None and time_to_enter < ttc


def improved_aeb(info):
    if info is None:
        return "none"
    if not (in_bus_lane(info) or will_enter_lane_in_time(info)):
        return "none"
    ttc = time_to_collision(info)
    if ttc is None:
        return "none"
    brake_ttc = BRAKE_TTC + 0.8 * info["rain"]
    if ttc < brake_ttc:
        return "brake"
    if ttc < WARN_TTC + 0.8 * info["rain"]:
        return "warning"
    return "none"
