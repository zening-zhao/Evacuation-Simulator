
# 9/29
## Questions:

1. when load new layout, can we still apply the same evacuation zone rule as the 10m X 10m square layout? like the size of evacuation zone?

2. we have irregular shape in the new layout, will this affect the evacuation zone assignment?

3. how does the square layout's exit been choose at very beginning? are they predefined or also have some algorithm? what if in the new layout, one exit can be shared by 2 evacuation zone?

4. why the ped_congestion been calculated by divide 9 but not 8?

   ```python
   			cmap[i][j].spa_around = spa_around;//周围障碍物和行人数量
   			cmap[i][j].ped_congestion = double(spa_around) / double(9);
   ```

5. 

## Progress
1. re write the skeleton in Python.
2. can  load different layout map file
3. pedestrians are still pre defined. needs to go through or understanding the rule to inject into this scenario
4. working to final E2E cycles now. most of the algorithm logics are completed.
5. updated penn station layout is done. 
6. setup Github for this project.
7. 

# 10/8:
## Questions:
1. how to define the people injection algorithm?
   a. for each escalator, will inject predefined number of people into this evacuation facility
   b. people will based on same speed? or faster speed? also define senior and non-senior speed?
   c. the all other algorithm stays same? any modification or adjustment might need to reconsider?
   d. any other design aspect need to be considered in this scenario?

## Progress:
1. working on existing simple scenario in parallel with the Penn station scenario. a couple of code refactoring work needs to be done to solve the hardcode issue in current C++ code. such as the layout design, exit predefine, etc. to modify current C++ code with loading Penn station layout is almost impossible since current code all layout elements are hardcoded. you cannot add complex layout with just modifying current code. 
2. also trying to make the code generic so all later modification and parameter adjustment can be done easily through configuration
3. fixing some integration issues in pedestrian movement model now.
4. working with Zening together to understand the full code structure and underlying logic.
5. Zening is working with teacher in school to register the ISEF. 

## next step:
1. start to focus on the paper structure, each chapter's main idea and required work.
2. any potential change of current simulation engine. including layout adjustment, algorithm tweak?
3. continue code work and understand all required algorithm thoroughly


# 10/10
## the Transition Probability algorithm is not very clear in updatemap function. 
   1. why using p = arr[2]/10000? and how does it can achieve randomly update the pedestrian in this facility?
   2. why check if (p >= 0 && p < np)//上 and then if (p >= np && p < (np + nep))//右上 till 
   if (p >= (np + nep + ep + sep + sp + swp + wp) && p < (np + nep + ep + sep + sp + swp + wp + nwp))//左上
   how does this connect to chose the smaller potential with larger probability?

## we will go to Penn station again to count the people get into the station.
   1. how to start the modeling of a real world scenario?
   2. what aspect we needs to consider?
   3. some general question about how to start to modeling?


# 10/12 
   1. in the paper: Each pedestrian can move from a lattice site to the next adjacent lattice site in horizontal or vertical directions,
   only if this adjacent lattice site is not occupied by an obstacle or another pedestrian. If all adjacent cells are occupied, the
   pedestrian stays still. but in the code, it seems allow the pedestrian to move diagonal? line 2293 ~ 2269

   3. in below case:
      ![alt text](image.png)
      will this cell consider can exit this facility?



# 10/29
## Wx Version
   1. GUI in general works fine in Windows.
   2. windows version needs to work on below improvement
      a. screen flickering, might need to use MemoryDC to write screen on a bitmap
      b. threading control not good. stop/pause/resume needs to fix the functionality and status bar updates.
      c. need to refactor the configuration dict to use reflection to get the string so this way will not have the string passed as a parameter to get the configuration item
      d. color picker? to improve the usability
      e. occactionally exit the application will cause python crash?
      f. move the apply/reset/re-paint button to a better position?
   4. Mac version needs to work on below improve (also inherit the changes from windows side)
      a. screen is not automatically refresh?
   5. 

## QT version
   1. inherit all changes from Wx version.
   2. performance turning? in general it is slower than Wx version? needs to figure out why. 

## general requirements:
   1. pedestrian injection.
   2. senior/non-senior speed control?
   3. other type of pedestian customize?
   4. continue the simulation for multiple times?
   5. historical track visulization?
   6. other data collection? 

<<<<<<< HEAD
# 11/2:
## Progress
   1. updated the layout to reflect the real map.
   2. exit count for 5 minutes at bottom right exit, not very crowded, can multiply by some factor here
   3. Escalator injection 6:20 220 ppl
   4. Top right exit 62 pedestrians exit the station 57 pedestrians enter the station in 5:30
   5. saved one video into Baidu shared drive.
## questions:
   1. need to implment the pedestrian injecetion model. theoretically how many people should we inject based on the data we collected? Our assumtion is that each platform has a train with 220 passangers. 

   ### We have 2 floorfields, one is the floorfield for the exit, other is density floorfield, people want to seek to go to space that is less crowded than the current space. The probability transition exit O_ij, D_ij. With each floorflied, we have one weight, phi, we decrease phi but increase the value of delta, see what happens from there

   2. which parameter we need to adjust for the sensitivity testing?
   
   
   
   3. Is there any method we can implement so that pedestrians can walk around each other so they can exit quicker? i will show you example during running

   ###  We have 2 floorfields, one is the floorfield for the exit, other is density floorfield, people want to seek to go to space that is less crowded than the current space. The probability transition exit O_ij, D_ij. With each floorflied, we have one weight, phi, we decrease phi but increase the value of delta, see what happens from there

   4. need a 500 words executive summary for register the ISEF compeitiion. how to start this? 

   first paragraph: real world problem
   second paragraph: summarizing scienfic question
   third paragraph: how can current community solve this problem
   4th paragraph: to describe my method, how do we deal with dynamic input, how to we guive pedestrians guidance. 
=======
# 11/6 
## LLM questions to generate the framework.
i want to recap the previous multiple thread example with pyside6 GUI. 1. a gui with menu, toolbar, status bar and splitter window. left side window is the formlayout with mutilple configuration items with label and text field. right side windows is scrollable canvas will show the complex graph with big datastructure and complex calculation behind it. 2. the toolbar will have a couple of buttons to control the calculation. start, pause/resume, stop and reset. 3. the status bar will show 4 different fields, includes current calculation ticker, current running status, current progress of the complex calculation and time elapased. 4. the calculation will be driven by a ticker. apscheduler will be used to create background thread and do the real calculation work. the ticker time is controllable and within each ticker, the scheduled calculation has to completed and finished update the canvas on right side window. there are also special calculation route in every 12 ticker. using ticker % 12 == 0 to control.  5. the main GUI should not be blocked by the background thread & ticker thread (daemon one). user can start, pause/resume, full stop or reset the calculation. 6. need to make sure the canvas repaint finished before ticker increase for next cycle of calculation. 7. performance wise needs to make the repaint concentrated in as less as possible places
>>>>>>> fd65fda4021ca2a5f35c742552da0d75aa218808
