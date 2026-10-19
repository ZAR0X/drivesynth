# DriveSynth prototype - part 2a: the scooter that cuts in
#
# Road layout (top view, traffic moves to the right, left-hand traffic like India):
#
#   y = +1.75  ------------------------------------  kerb side edge of the bus's lane
#   y =  0          [=====BUS=====]>                  centre of the bus's lane
#   y = -1.75  - - - - - - - - - - - - - - - - - - -  lane line
#   y = -2.3                         [scoo]>          scooter starts here, in the next lane
#
# x = distance along the road (m), y = sideways position (m).
# The scooter does not react to the bus. It just follows its script:
#   ride straight for 0.5 s, then move sideways into the bus's lane until it reaches the lane centre.

DT = 0.05
SCOOTER_LENGTH = 2.0
SCOOTER_WIDTH = 0.8
START_Y = -2.3          # just across the lane line, in the next lane
CUT_IN_STARTS_AT = 0.5  # seconds


def kmh_to_ms(kmh):
    return kmh / 3.6


class Scooter:
    def __init__(self, bus_speed_kmh, gap, speed_diff_kmh, sideways_speed):
        """
        gap            - metres between the bus front and the scooter's back when the scooter starts cutting in
        speed_diff_kmh - scooter speed minus bus speed (negative = scooter is slower, which is the dangerous case)
        sideways_speed - how fast it moves into the lane, m/s
        """
        self.speed = kmh_to_ms(bus_speed_kmh + speed_diff_kmh)
        self.sideways_speed = sideways_speed
        self.y = START_Y
        # the bus front starts at x = 0; place the scooter so the gap is right at t = CUT_IN_STARTS_AT
        bus_speed = kmh_to_ms(bus_speed_kmh)
        self.x = gap - (self.speed - bus_speed) * CUT_IN_STARTS_AT   # x of the scooter's back end

    def step(self, t):
        self.x += self.speed * DT
        if t >= CUT_IN_STARTS_AT and self.y < 0.0:
            self.y = min(0.0, self.y + self.sideways_speed * DT)

    def is_moving_sideways(self, t):
        return t >= CUT_IN_STARTS_AT and self.y < 0.0
