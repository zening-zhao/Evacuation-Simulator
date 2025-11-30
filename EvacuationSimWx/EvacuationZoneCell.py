import os
#---------------------------------------------------------------------------
# Define Evacuation Zone Cell
#---------------------------------------------------------------------------

class EvacuationZoneCell():

    def __init__(self, row, column, zone_id, number_of_columns):
        self.row = row                                  # relative row location, need to adjust with min_row to get real cell row
        self.column = column                            # relative column location, need to adjust with min_column to get real cell row
        self.assigned_zone_id = zone_id                 # assigned zone_id
        self.preferred_exit = -1                        # current preferred exit for this zone
        self.number_of_pedestrian = 0                   # store number of pedestrian in this zone
        self.average_speed = 1.2                        # store the average speed of all pedestrain in current zone
        self.potential_dict = {}                        # potential dict, will store potentials with respect to each exit.
                                                        # {exit ID : potential}
        self.temp_potential = 0                         # temp potential for calculation only
        self.temp_distance = 0                          # temp static distance for calculation only
        self.potential_calc_flag = False                # a flag to help calculate the potentials of current zone
        self.distance_calc_flag = False                 # a flag to help calculate the static distance of current zone
        self.static_distance_dict = {}                  # distance dict. will store distances with respect to each exit
                                                        # {exit id : distances}
        self.exit_id_for_current_zone = -1              # indicate if current zone has a direct exit within this zone's area
                                                        ## TODO this is hardcoded. needs to think through a way to expand
        self.number_of_columns = number_of_columns      # this is the width of the layout per zone.
                                                        # based on this information, we can get the index of the entire zone list.
        self.obstacle_zone_flag = False                 # a flag to indicate if current zone is an obstacle zone or not. True = Obstacle zone
                                                        # default to false
        self.temp_exit = -1                             # will be used in Exit choice model when calculate arg min F(s,x) for each exit.


    def __eq__(self, other):
        if isinstance(other, EvacuationZoneCell):
            return self.row == other.row and self.column == other.column and self.assigned_zone_id == other.assigned_zone_id
        return False

    def __hash__(self):
        return hash((self.x,self.y,self.assigned_zone_id))


    def __repr__(self):
        return f"EvaculationZoneCell : assigned_zone_id = {self.assigned_zone_id}, preferred_exit = {self.preferred_exit}, number_of_pedestrian = {self.number_of_pedestrian}, avarage_speed = {self.average_speed}"
