## Evacuation Simulator - User Manual

### Environment

* python 3.12.7

* MacBook OS Sequoia 15.1.1

### Installation Step

* install all required librarys from requirement.txt

* run **EvacuationSimWx.py**

### Simulation Application

* there are 4 different simulation layout attached: 

| File Name                              | Purpose                            | Comments                                   |
| -------------------------------------- | ---------------------------------- | ------------------------------------------ |
| layout_sample1.xlsx                    | Same layout used in original paper | To validate Original paper's data & result |
| Moynihan_Train_Hall_Floor_Plan_V1.xlsx | Penn Station Layout version 1      | testing purpose                            |
| Moynihan_Train_Hall_Floor_Plan_V2.xlsx | Penn Station Layout version 2      | Final version with adjusted layout & exits |
| SimulationScenarioLayout.xlsx          | Sample simulation scenario layout  | To validate the F-D diagram                |

* The major GUI components are very intuitive.  Please let us know if you have any questions.

* To create new Layout file we can follow below rule in excel:

| Cell Type                  | Hex RGB color    |
| -------------------------- | ---------------- |
| LAYOUT_FILE_BORDER         | '000000' #black  |
| LAYOUT_FILE_EMPTY_SPACE    | 'FFC000' #orange |
| LAYOUT_FILE_EXIT           | '00B050' #green  |
| LAYOUT_FILE_OBSTACLE       | '0070C0' #blue   |
| LAYOUT_FILE_EMPTY_CELL     | 'FFFFFF' #white  |
| LAYOUT_FILE_INJECTION_CELL | 'FF0000' #RED    |

* All other color will be treated as empty cell during file loading. 

* All parameters can be configured through the GUI (Left side Panel). we can also modify the **constants.py** to make permenant changes.

* Log file will be saved in same run path. we can adjust the log level by changing logger level in each python source code.

### Known issues & improvements from the C++ code

1. Save animation is not implemented yet
2. current program is working fine in MacBook but might have some issues in Windows env. Haven't tested this in Linux. wxpython might have some flicking issue in other OS.
3. Same speed is currently applied on both Senior and Non-Senior pedestrian
4. The transition probability formular used in pedestrian movement model is following the paper but not following the sample C++ code shared by Thomas since we didn't quite understand the real implementation logic in C++ code. 
5. replace the hardcoded exit definition in C++ code by the Exit Initialization algorithm. 
6. For all inconsistence between the C++ code and the original paper. we modified the logic to follow the paper. 

