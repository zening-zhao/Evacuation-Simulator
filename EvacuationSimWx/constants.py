import math as math
#---------------------------------------------------------------------------
## DEFINE ALL constants
## TODO: migrate all constants as configuration items and more dynamically configuration
## JSON? XML?
## Each field below will have another flag with _config postfix to indicate if current item
## will be setup in GUI.
## For exmaple:
## LAYOUT_FILE_BORDER              = '000000' #black
## LAYOUT_FILE_BORDER_CONFIG       = False # means current item will *NOT* be showed up in GUI.configuration panel.
##                                     by default, if no _CONFIG value be set here. will not show up in GUI configuration panel.
## LAYOUT_DISPLAY_BORDER           = '000000' #black
## LAYOUT_DISPLAY_BORDER_CONFIG    = True # means current item will be showed up in GUI configuration panel
## introduce another flag to indicate if a certain configuration item needs to be a color picker
## for example:
# LAYOUT_DISPLAY_EXIT                   = 'ffffb2' #'00B050' #green
# LAYOUT_DISPLAY_EXIT_COLORCONFIG       = True # indicate current cell will be a color picker item.
#                                       = default to False. if no _COLOR configuration item
#---------------------------------------------------------------------------

# For input files only
LAYOUT_FILE_BORDER              = '000000' #black
LAYOUT_FILE_EMPTY_SPACE         = 'FFC000' #orange
LAYOUT_FILE_EMPTY_SPACE_NO_PED  = 'FFFF00' #yellow
LAYOUT_FILE_EXIT                = '00B050' #green
LAYOUT_FILE_OBSTACLE            = '0070C0' #blue
LAYOUT_FILE_EMPTY_CELL          = 'FFFFFF' #white
LAYOUT_FILE_INJECTION_CELL      = 'FF0000' #RED


# display related
LAYOUT_DISPLAY_BORDER               = '000000' #black
LAYOUT_DISPLAY_EMPTY_SPACE          = 'FFFBFC' #light rice white
LAYOUT_DISPLAY_EMPTY_SPACE_NO_PED   = 'FFFBFC' #light rice white
LAYOUT_DISPLAY_EXIT                 = 'FFFFB2' #'00B050' #green
LAYOUT_DISPLAY_OBSTACLE             = '9E9AC8' #'0070C0' #blue
LAYOUT_DISPLAY_EMPTY_CELL           = 'F1F505' #'FFFFFF' #white
LAYOUT_SENIOR_COLOR                 = 'E41A1C' #'bae4b3'
LAYOUT_NON_SENIOR_COLOR             = '4DAF4A' # 'df65b0'
LAYOUT_INJECTED_COLOR               = 'ffbd33' # ORANGE -> Only the first step injected cell will be in this color.
LAYOUT_DISPLAY_INJECTION_CELL       = 'FF0000' # RED

# below items will be have a color picker icon
LAYOUT_DISPLAY_BORDER_COLORCONFIG               = True
LAYOUT_DISPLAY_EMPTY_SPACE_COLORCONFIG          = True
LAYOUT_DISPLAY_EMPTY_SPACE_NO_PED_COLORCONFIG   = True
LAYOUT_DISPLAY_EXIT_COLORCONFIG                 = True
LAYOUT_DISPLAY_OBSTACLE_COLORCONFIG             = True
LAYOUT_DISPLAY_EMPTY_CELL_COLORCONFIG           = True
LAYOUT_SENIOR_COLOR_COLORCONFIG                 = True
LAYOUT_NON_SENIOR_COLOR_COLORCONFIG             = True
LAYOUT_DISPLAY_INJECTION_CELL_COLORCONFIG       = True
LAYOUT_INJECTED_COLOR_COLORCONFIG               = True

# # all display related items will be configurable.
# LAYOUT_DISPLAY_BORDER_CONFIG           = True
# LAYOUT_DISPLAY_EMPTY_SPACE_CONFIG      = True
# LAYOUT_DISPLAY_EXIT_CONFIG             = True
# LAYOUT_DISPLAY_OBSTACLE_CONFIG         = True
# LAYOUT_DISPLAY_EMPTY_CELL_CONFIG       = True
# LAYOUT_SENIOR_COLOR_CONFIG             = True
# LAYOUT_NON_SENIOR_COLOR_CONFIG         = True


LAYOUT_NUMBER_BORDER                = 999999
LAYOUT_NUMBER_EMPTY_SPACE           = 0
LAYOUT_NUMBER_EMPTY_SPACE_NO_PED    = 0
LAYOUT_NUMBER_EXIT                  = 100000
LAYOUT_NUMBER_OBSTACLE              = 500000
LAYOUT_NUMBER_EMPTY_CELL            = -1
LAYOUT_NUMBER_INJECTION_CELL        = 200000

# control the real graph displayed in the GUI
LAYOUT_CELL_SIZE                = 6
LAYOUT_CELL_ROUND_RECT_RADIUS   = 0

LAYOUT_CELL_SIZE_CONFIG                 = True
LAYOUT_CELL_ROUND_RECT_RADIUS_CONFIG    = True

LAYOUT_CELL_TYPE_BORDER                 = 'BORDER'
LAYOUT_CELL_TYPE_EMPTY_SPACE            = 'EMPTY_SPACE'
LAYOUT_CELL_TYPE_EMPTY_SPACE_NO_PED     = 'EMPTY_SPACE_NO_PED'
LAYOUT_CELL_TYPE_EXIT                   = 'EXIT'
LAYOUT_CELL_TYPE_OBSTACLE               = 'OBSTACLE'
LAYOUT_CELL_TYPE_EMPTY_CELL             = 'EMPTY_CELL'
LAYOUT_CELL_TYPE_INJECTION_CELL         = 'INJECTION'

# in meters, will be used to calculate the number of evacuation zone
EVACUATION_ZONE_DIMENSION = 10
EVACUATION_ZONE_DIMENSION_CONFIG = True

# cell automata size in meters
# each cell in layout file is representing 0.5m^2
CELL_SIZE = 0.5
CELL_SIZE_CONFIG = True

# pedestrian per square meter(0-4)
PEDESTRIAN_PER_SQUARE_METER = 2
PEDESTRIAN_PER_SQUARE_METER_CONFIG = True

# predefined number of PEDESTRIAN in current scenario
NUMBER_OF_PEDESTRIAN = 5000
NUMBER_OF_PEDESTRIAN_CONFIG = True

#percentage of senior people (0%~100%)
SENIOR_PEDESTRIAN_PERCENTAGE = 0.2
SENIOR_PEDESTRIAN_PERCENTAGE_CONFIG = True

# Horizontal or vertical distance
HORI_VERT_DISTANCE = 1.0
HORI_VERT_DISTANCE_CONFIG = True

DIAGONAL_DISTANCE = math.sqrt(2)
DIAGONAL_DISTANCE_CONFIG = True

#SIMULATION TIME INTERVAL (in seconds)
SIMULATION_TIME_INTERVAL = 0.05
SIMULATION_TIME_INTERVAL_CONFIG = True

# SIMULATION CYCLE (Tau)
SIMULATION_CYCLE = 12
SIMULATION_CYCLE_CONFIG = True

#PEDESTRAIN SPEED m/s
NORMAL_PEDESTRIAN_SPEED = 1.2
NORMAL_PEDESTRIAN_SPEED_CONFIG = True

SENIOR_PEDESTRIAN_SPEED = 0.6
SENIOR_PEDESTRIAN_SPEED_CONFIG = True

# parameter for the exit choice model
EXIT_CHOICE_MODEL_ALPHA_DIAGONAL = math.sqrt(2) - 1
EXIT_CHOICE_MODEL_ALPHA_DIAGONAL_CONFIG = True
EXIT_CHOICE_MODEL_ALPHA_NON_DIAGONAL = 0
EXIT_CHOICE_MODEL_ALPHA_NON_DIAGONAL_CONFIG = True
EXIT_CHOICE_MODEL_BETA = 1
EXIT_CHOICE_MODEL_BETA_CONFIG = True
EXIT_CHOICE_MODEL_GAMMA = 1
EXIT_CHOICE_MODEL_GAMMA_CONFIG = True
EXIT_CHOICE_MODEL_THETA = 10
EXIT_CHOICE_MODEL_THETA_CONFIG = True

# number of exit in current layout
#NUMBER_OF_EXIT = 8

# Parameter for the pedestrain movement model
PEDESTRIAN_MOVEMENT_MODEL_DELTA = 1
PEDESTRIAN_MOVEMENT_MODEL_DELTA_CONFIG = True
PEDESTRIAN_MOVEMENT_MODEL_PHI = 1
PEDESTRIAN_MOVEMENT_MODEL_PHI_CONFIG = True
PEDESTRIAN_MOVEMENT_MODEL_EPSILON = 2
PEDESTRIAN_MOVEMENT_MODEL_EPSILON_CONFIG = True

# DIRECTION
DIRECTION_UP                = 'UP'
DIRECTION_DOWN              = 'DOWN'
DIRECTION_LEFT              = 'LEFT'
DIRECTION_RIGHT             = 'RIGHT'
DIRECTION_UPLEFT            = 'UPLEFT'
DIRECTION_UPRIGHT           = 'UPRIGHT'
DIRECTION_DOWNLEFT          = 'DOWNLEFT'
DIRECTION_DOWNRIGHT         = 'DOWNRIGHT'
DIRECTION_CENTER            = 'CENTER'

# Pedestrian injection related:
NUMBER_OF_PEDESTRIAN_INJECT = 1000
NUMBER_OF_PEDESTRIAN_INJECT_CONFIG = True
INJECTION_RATE = 0.57894                # number of people will be injected into the facility per tick(Second)
INJECTION_RATE_CONFIG = True
INJECTION_UTILIZATION_RATE = 0.5
INJECTION_UTILIZATION_RATE_CONFIG = True    # number of the injection point that will have pedestrian inject to current map.
                                            # assume not all point will have pedestrian get into current map
