import os
#---------------------------------------------------------------------------
# Define celluar automata
#---------------------------------------------------------------------------

class CelluarAutomata():

    def __init__(self, row, column, zone, zone_x, zone_y):
        self.x = row                    # relative row location, need to adjust with min_row to get real cell row
        self.y = column                 # relative column location, need to adjust with min_column to get real cell row
        self.zone_x = zone_x            # evacuation zone x coordination (index to identify the zone ID? not sure this is required)
        self.zone_y = zone_y            # evacuation zone y coordination (index to identify the zone ID? not sure this is required)
        self.is_outside = False         # flag indicator: True -> outside False -> inside
        self.current_zone = zone        # current evacuation zone ID
        self.current_exit = -1          # current choosed exit
        self.velocity_mode = 1          # 1 => normal speed. 2. half-speed
        self.obey_mode = 0              # 0 => not obey the evacuationrule, 1 => obey the evacuation rule
        self.occupied = False           # default to False. False means empty and True means occupied
        self.last_speed = 0.0           # default 0.0. avarage speed of this pedestrian
        self.last_exit = -1             # default -1. exit chosen by this cell in last stage
        self.last_step_count = 0        # default 0. how many steps this cell has moved at the moment of last stage
        self.current_step_count = 0     # default 0. how many steps this cell has moved from now.
        self.move_history = []          # store all index (row, column) of current Automata for each movement.
        self.automata_index = -1        # store current entire automata array's index, for look up purpose.
        self.just_injected_flag = False # flag to indicator current cell just get injected. only for newly injected cells.
                                        # will change color after one tick.

    def __eq__(self, other):
        if isinstance(other, CelluarAutomata):
            return self.x == other.x and \
                    self.y == other.y and \
                    self.zone_x == other.zone_x and \
                    self.zone_y == other.zone_y and \
                    self.current_zone == other.current_zone and \
                    self.current_exit == other.current_exit
        return False

    def __hash__(self):
        return hash((self.x, self.y, self.zone_x, self.zone_y))


    def __repr__(self):
        return f"CelluarAutomata : x = {self.x}, y = {self.y}, occupied = {self.occupied}, is_outside = {self.is_outside}, current_zone = {self.current_zone}, current_exit = {self.current_exit}"
