import os

class LayoutCell():
    def __init__ (self, row, column, value, color, cell_type):
        self.row = row                                  # current row index
        self.column = column                            # current column index
        self.value = value                              # current cell value assigned (per constants.py)
        self.color = color                              # hex color code for current cell
        self.type = cell_type                           # current cell type, border/obstacle/exit/ etc
        self.assigned_evacuation_zone = -1              # integer value for current assigned evacuation zone.
                                                        # evacuation zone is equaly destributed based on the evacuation area size.
                                                        # start from top left to bottom right
                                                        #   -----------------------------------------
                                                        #   |   0   |   1   |   2   |   3   |   4   |
                                                        #   -----------------------------------------
                                                        #   |   5   |   6   |   7   |   8   |   9   |
                                                        #   -----------------------------------------
                                                        #   |   10  |   11  |   12  |   13  |   14  |
                                                        #   -----------------------------------------
                                                        #   |   15  |   16  |   17  |   18  |   19  |
                                                        #   -----------------------------------------
                                                        #   |   20  |   21  |   22  |   23  |   24  |
                                                        #   -----------------------------------------
        self.preferred_exit = -1                        # current exit assigned for this cell (same for all same cells in same zone)
        self.static_potential = {}                      # potential of current cell with respect of each exit.
                                                        # -1 = border/obstacle 0= exit, store positive float
                                                        # Here is a dict to store the pair of {exit ID : potential}
        self.static_potential_calc_flag = False         # indicate whether current cell has the potential calcualtion completed or not.
        self.temp_potential = -1.0                      # temp value during calculation
        self.ped_congestion = 0.0                       # pedestrain congestion value. defined by spa_around/9.
        self.occupied_space_around = 0                  # how many cell/lattice are occupied around current cell/lattice.
                                                        # we consider occupied for both by people or another obstacle.
        self.automataIndex = -1                         # only when this cell is occupied, then then rnd_value (used as index) will be
                                                        # saved here. we can use this to quickly idenfity the position in AutomataList
        self.adjacent_to_exit = False                   # default to False. indicate if current cell is right adjacent to an exit.
                                                        # this will be used to start the static potential calculation.
        self.exit_index = -1                            # store current exit's Index if current cell is an exit type cell
                                                        # TODO: this should associated with the exit identification algorithm
                                                        # if a cell is not an exit type, then this field will be default to -1.
                                                        # if a cell is exit type
                                                        #   get all non-obstacle/non border cell's preferred_exit
                                                        #   this preferred exit ID will be used to index the exit.
                                                        #   assumption: the exit will not cross 2 sub area. we only will get one value from
                                                        #   the adjacent cell's preferred exit.
        self.assigned_to_exit_flag = False              # a flag use to indicate if current cell has been visited when assigned to belongs to a specific exit.
                                                        # only used for type = EXIT_CELL cell. default to False.
        self.injection_index = -1                       # store current injection's index if current cell is an injection cell type cell.
        self.adjacent_to_injection = False              # default to False. indicate if current cell is right adjacent to an injection cell.
        self.assigned_to_injection_flag = False         # a flag use to indicate if current cell has been visited when assigned to belongs to a specific injection point.
        self.empty_index = -1                           # for empty spaces only. will store each individual empty spaces' index.
                                                        # should be same as the automataIndex if this cell is occupied. otherwise just for
                                                        # index purpose.

    def AssignEvacuationZone(self):
        pass

    def __eq__(self, other):
        if isinstance(other, LayoutCell):
            return self.row == other.row and self.column == other.column and self.type == other.type
        return False

    def __hash__(self):
        return hash((self.row, self.column, self.type))


    def __repr__(self):
        return f"LayoutCell : row = {self.row}, column = {self.column}, type = {self.type}, automataIndex = {self.automataIndex} , ped_congestion = {self.ped_congestion}, preferred_exit = {self.preferred_exit}"

