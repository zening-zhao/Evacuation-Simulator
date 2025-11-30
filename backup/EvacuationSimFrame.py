import wx.lib.sized_controls as sized_ctrls
import wx
import time
import threading
import os
import numpy as np
import matplotlib as matplotlib
import logging
import LayoutBuilder as LayoutBuilder
import datetime as datetime
import constants
from wx.lib.scrolledpanel import ScrolledPanel
from ThemeColorConverter import ThemeColorConverter
from pathlib import Path
from matplotlib.ticker import MultipleLocator, FuncFormatter
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib import pyplot
from logger_config import setup_logger
import datetime
from concurrent import futures
from apscheduler.schedulers.background import BackgroundScheduler,BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

matplotlib.use("WXAgg")

# Custom logging filter to suppress specific messages
class SkipFilter(logging.Filter):
    def filter(self, record):
        return "skipped: maximum number of running instances reached" not in record.getMessage()

setup_logger()
logger = logging.getLogger(__name__)
logger.addFilter(SkipFilter())
logger.setLevel(logging.INFO)
# logging.getLogger('apscheduler.scheduler').propagate = False

# Get the logger for APScheduler
apscheduler_logger = logging.getLogger('apscheduler')

# Set the log level to WARNING or higher to suppress INFO and DEBUG messages
apscheduler_logger.setLevel(logging.ERROR) 
#---------------------------------------------------------------------------
##  GUI related compoment
#---------------------------------------------------------------------------

BUFFERED = True
GLOBAL_COUNTER = 0
ALL_PEDESTRIANS_OUT = False

class EvacuationSimFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame .__init__(self, None, -1, title, size=(800, 600)) ## Initial size
        # TODO: add a icon for simulator
        #self.SetIcon(wx.Icon('./icons/wxwin.ico', wx.BITMAP_TYPE_ICO))
        self.sp = None
        self.layout_panel = None
        self.configuration_panel = None
        self.menubar = None
        self.frame_statusbar = None
        self.frame_toolbar = None
        self.buffer = None
        self.myLayoutBuilder = None
        self.scheduler = None

        #Setup widgets     
        self.InitializeComponents()
        
        #setup buffer for the DC
        if BUFFERED:
            self.buffer = None
            self.InitBuffer()
            
    #---------------------------------------------------------------------------
    ##  intiliazed all widgets
    #---------------------------------------------------------------------------
    def InitializeComponents(self):
        self.sp = wx.SplitterWindow(self)
        
        ## Left side panel
        self.configuration_panel = sized_ctrls.SizedPanel(self.sp, style=wx.SUNKEN_BORDER)
        self.configuration_panel.SetSizerType("form")
        self.configuration_panel.SetBackgroundColour(wx.Colour(*ThemeColorConverter.hex_to_rgb(constants.LAYOUT_DISPLAY_EMPTY_SPACE)))

        # Create the Controls.
        # Each time through the loop creates one row in
        # the dialogs layout ("form" is a two column grid).
        # TODO: when read the configuration file, each variable/parameter will be setup here.

        for ctrl in ("Number of Pedestrian", "CPU Ticks", "Cell Size",
                    "Evacuation Zone Dimension", "# of People per square meter"):
            lbltext = "%s :" % ctrl.title()
            lbl = wx.StaticText(self.configuration_panel, label=lbltext)
            lbl.SetForegroundColour((255,0,0)) # set text color
            lbl.SetSizerProps(valign="center")
            txt = wx.TextCtrl(self.configuration_panel, name=ctrl)
            txt.SetForegroundColour(wx.RED)
            txt.SetSizerProps(expand=True)

        ## right side panel
        self.layout_panel = ScrolledPanel(self.sp, style=wx.SUNKEN_BORDER)
        self.layout_panel.Bind(wx.EVT_SCROLLWIN, self.on_scroll)
        self.layout_panel.SetBackgroundColour(wx.Colour(*ThemeColorConverter.hex_to_rgb(constants.LAYOUT_DISPLAY_EMPTY_SPACE)))
        self.layout_panel.Bind(wx.EVT_PAINT, self.on_paint)
        # self.layout_panel.Bind(wx.EVT_SIZE, self.on_size)
        self.layout_panel.Show(True)

        ## Insert into the split vertical panels
        self.sp.SplitVertically(self.configuration_panel, self.layout_panel, 300) # Split the window left and right.
        self.sp.SetMinimumPaneSize(1)         # Minimum size of subwindow.
        
        ## Menu bar
        self.menubar = wx.MenuBar()
        file = wx.Menu()
        item = file.Append(wx.ID_ANY, "Load Floor Layout File", "Load floor layout from excel/csv file")
        self.Bind(wx.EVT_MENU, self.on_menu_file_loadLayout, item)
        item = file.Append(wx.ID_ANY, "Save Animation", "Save Current simulation to animation file")
        self.Bind(wx.EVT_MENU, self.on_menu_file_saveAnimation, item)
        item = file.Append(wx.ID_ANY, "Exit", "Exit the Simulator")
        self.Bind(wx.EVT_MENU, self.on_menu_file_exit, item)

        operation = wx.Menu()
        item = operation.Append(wx.ID_ANY, "Start Simulation", "Start Simulation")
        item.Enable(False) # Default to disable
        self.Bind(wx.EVT_MENU, self.on_menu_operation_startsimulation, item)
        item = operation.Append(wx.ID_ANY, "Pause/Resume Simluation", "Pause/Resume Simluation")
        item.Enable(False) # Default to disable
        self.Bind(wx.EVT_MENU, self.on_menu_operation_pause_resume_simuation, item)
        item = operation.Append(wx.ID_ANY, "Stop Simuation", "Stop Simuation")
        item.Enable(False) # Default to disable
        self.Bind(wx.EVT_MENU, self.on_menu_operation_stopsimulation, item)
        
        help = wx.Menu()
        item = help.Append(wx.ID_ANY, "About", "About")
        self.Bind(wx.EVT_MENU, self.on_menu_help_about, item)
        
        self.menubar.Append(file, '&File')
        self.menubar.Append(operation, '&Operation')
        self.menubar.Append(help, '&Help')
        
        self.SetMenuBar(self.menubar)
        
        ## Status Bar
        self.frame_statusbar = wx.StatusBar(self, style = wx.SB_FLAT)
        self.frame_statusbar.SetFieldsCount(2)
        self.frame_statusbar.SetStatusWidths([-1, 200])
        # TODO : Status bar will update current run time, cpu tick etc.
        self.frame_statusbar.SetStatusText("Time Elapsed : " + "00:00:00 (s)", 1)
        self.SetStatusBar(self.frame_statusbar)

        ## Toolbax bar
        self.frame_toolbar = wx.ToolBar(self)
        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Load Layout", 
                                     wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, 
                                    (32,32)),wx.NullBitmap, wx.ITEM_NORMAL,"Load Layout","")
        self.Bind(wx.EVT_TOOL,self.on_menu_file_loadLayout, id = tool.GetId())
        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Save Animation", 
                                     wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, 
                                    (32,32)),wx.NullBitmap, wx.ITEM_NORMAL,"Save Animation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_file_saveAnimation, id = tool.GetId())
        self.frame_toolbar.AddSeparator()
        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Start Simulation", 
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","start_simulation.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Start Simulation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_startsimulation, id = tool.GetId())
        tool.Enable(False) # disable the start button, only will be enabled after we load the layout.

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Resume/Pause Simulation", 
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","pause_simulation.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Resume/Pause Simulation","")
        
        self.Bind(wx.EVT_TOOL,self.on_toolbar_pause_resume_simuation, id = tool.GetId())
        tool.Enable(False) #default to disable stop/pause simulation button

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Stop Simulation", 
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","stop_simulation.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Stop Simulation","")
        
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_stopsimulation, id = tool.GetId())        
        tool.Enable(False) #default to disable stop/pause simulation button

        self.SetToolBar(self.frame_toolbar)
        self.frame_toolbar.Realize()
    
        # Handle program exit issue
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    #---------------------------------------------------------------------------
    ##  use buffered DC to draw the screen to prevent flicking
    #---------------------------------------------------------------------------
    def InitBuffer(self):
        size = self.layout_panel.GetClientSize()
        self.buffer = wx.Bitmap(*size)
        dc = wx.BufferedDC(wx.ClientDC(self.layout_panel), self.buffer)
        dc.SetBackground(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(constants.LAYOUT_DISPLAY_EMPTY_SPACE))))
        dc.Clear()
    
    
    #---------------------------------------------------------------------------
    ##  event handle function when load file
    #---------------------------------------------------------------------------       
    def on_menu_file_loadLayout(self, event):
        frame = wx.Frame(None, -1, 'Load Layout')
        frame.SetSize(0,0,200,50)

        with wx.FileDialog(self, "Open xlsx file", wildcard="xlsx files (*.xlsx)|*.xlsx",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            filepath = fileDialog.GetPath()
            try:
                #now we have the file path
                self.myLayoutBuilder = LayoutBuilder.LayoutBuilder(filepath, self.layout_panel)

                # read the layout file
                self.myLayoutBuilder.load_layout_file()

                # we have the real layout size. will adjust the buffer size so we have enough space to show the graph
                self.AdjustBuffer(self.myLayoutBuilder.max_column - self.myLayoutBuilder.min_column, 
                                self.myLayoutBuilder.max_row - self.myLayoutBuilder.min_row)

                # draw the lay out on scorlled panel & initialize the number of pedestrians
                self.myLayoutBuilder.construct_layoutMap(self.get_current_bufferedDC())
            except IOError:
                wx.LogError("Cannot open file '%s'." % filepath)

        # enable the start simulation button.
        self.frame_toolbar.GetToolByPos(3).Enable(True)
        self.frame_toolbar.Realize()
        # Enable the Start button from menu
        self.menubar.Menus[1][0].MenuItems[0].Enable(True)


    #---------------------------------------------------------------------------
    ##  buggy one. when load a big file, the predefined screen size doesn't fit 
    ##  the entire layout. use an ugly way to manually adjusted the buffered DC.
    ##  still couldn't resolve when scrollbar move, the DC doesn't refresh properly issue
    ## TODO: Fix this.
    #---------------------------------------------------------------------------  
    def AdjustBuffer(self, width, height):
        adjustedWidth = width * constants.LAYOUT_CELL_SIZE + 400 # give extra pixel buffer
        adjustedHeight = height * constants.LAYOUT_CELL_SIZE + 200 # give extra pixel buffer
        new_size = wx.Size(adjustedWidth, adjustedHeight) # the full frame size
        # set the entire frame to new size
        self.SetSize(new_size)
        self.layout_panel.SetupScrolling()
        self.Layout()
        self.Center()

        # only use the layout panel size to initial the buffer.
        layout_panel_size = self.layout_panel.GetClientSize()

        if self.buffer is None:
            self.buffer = wx.Bitmap(*layout_panel_size)
        else: # we already have a buffer here
            if self.buffer.GetSize().Width < layout_panel_size.Width or self.buffer.GetSize().Height < layout_panel_size.Height:
                max_size = wx.Size(max(self.buffer.GetSize().Width, layout_panel_size.Width),
                                max(self.buffer.GetSize().Height, layout_panel_size.Height))
                #copy current buffer into the new buffer
                # TODO: need to find a way to copy smaller buffer into a big buffer area. right now just create a bigger buffer area.
                # new_buffer = wx.Bitmap(*max_size)
                # self.buffer = new_buffer
                # new_buffer.CopyFromBuffer(self.buffer.ConvertToImage().GetDataBuffer())
                self.buffer = wx.Bitmap(*max_size)
        dc = wx.BufferedDC(wx.ClientDC(self.layout_panel), self.buffer)
        dc.SetBackground(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(constants.LAYOUT_DISPLAY_EMPTY_SPACE))))
        dc.Clear()

    #---------------------------------------------------------------------------
    ##  when we need a DC to draw on any widget out side of on_paint event.
    ##  get a buffered DC or a client DC
    #--------------------------------------------------------------------------- 
    def get_current_bufferedDC(self):
        if self.buffer is None:
            self.InitBuffer()
        if BUFFERED:
            dc = wx.BufferedDC(wx.ClientDC(self.layout_panel), self.buffer)
        else:
            dc = wx.ClientDC(self.layout_panel)
        return dc

    #---------------------------------------------------------------------------
    ##  below are event handler functions have not been implemented.
    #--------------------------------------------------------------------------- 

    def on_menu_file_saveAnimation(self, event):
        logger.info("Event handler for 'on_menu_file_saveAnimation' not implemented yet")
        event.Skip()

    def on_menu_file_exit(self, event):
        self.Destroy()
        wx.Exit()  # Exit the application

    def on_menu_operation_pause_resume_simuation(self, event):
        logger.info("Event handler for 'on_menu_operation_pause_resume_simuation' not implemented yet")
        event.Skip()
        
    def on_toolbar_pause_resume_simuation(self, event):
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.next_run_time is not None: # means current job is not paused
                job.pause()
                logger.info(f"Current Simulation Job Paused at Ticker : {GLOBAL_COUNTER}")
            else:
                job.resume()
                logger.info(f"Current Simulation Job Resumed at Ticker : {GLOBAL_COUNTER}")

        ## TODO: for the pause/resume
        ## 1. change the icon to correct bitmap?
        ## 2. add another status bar item to indicate the status?
        ## 3. maybe also capture the keyboard input (like space to pause/resume the operation.)

    def on_menu_operation_stopsimulation(self, event):
        logger.info("Event handler for 'on_menu_operation_stopsimulation' not implemented yet")
        event.Skip()

    def on_menu_help_about(self, event):
        logger.info("Event handler for 'on_menu_help_about' not implemented yet")
        # event.Skip()
        # self.myLayoutBuilder.printOutLayout()

    #---------------------------------------------------------------------------
    ## TODO: how to resolve the screen not refresh properly issue?
    #--------------------------------------------------------------------------- 
    def on_scroll(self, event):
        logger.info("In Event handler for 'on_scroll' ")
        event.Skip()

    #---------------------------------------------------------------------------
    ## when closed the wx frame. needs to destory the entire instance
    #--------------------------------------------------------------------------- 
    def on_close(self, event):
        logger.info(f"Current Simulation Main Thread will be terminated...")
        self.Destroy()
        wx.Exit()  # Exit the application

    #---------------------------------------------------------------------------
    ## on_paint. will automatically draw the buffered content on screen.
    ## don't need to be called explicity but underlying will just draw the screen
    ## based on the buffer
    #--------------------------------------------------------------------------- 
    def on_paint(self, event):
        logger.info(f"In Event handler for 'on_paint'. Current Client Size: {self.layout_panel.GetClientSize()}")
        if self.buffer is None:
            self.InitBuffer()
            logger.info(self.buffer)
        if BUFFERED:
            dc = wx.BufferedPaintDC(self.layout_panel, self.buffer)
        else:
            dc = wx.PaintDC(self.layout_panel)
        dc.SetBackground(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(constants.LAYOUT_DISPLAY_EMPTY_SPACE))))

    #---------------------------------------------------------------------------
    ## start simulation event handler (click the button or from the drop down menu)
    #--------------------------------------------------------------------------- 
    def on_menu_operation_startsimulation(self, event):
        logger.info('Start the simulation...')
        ## Start the simulation
 
        ## Precondition:
 
        ## 1. initialize S : (subareas)  -> already done during construct the layout map. 
        ##      current_assigned_evacuation_zone has been assigned for each empty cell
        ##      all empty spaces within one subarea will have same predefined evacuation zone .
 
        ## 2. initialize E : (Exit) -> already done during constuct the layout map.
        ##      each cell will have prefered exit id. NUmber of exit and preferred exit id are both hardcoded
 
        ## 3. initialize n(i,j). -> this denotes the total number of neighboring lattice sites of lattice site (i, j)
        ##      also completed during construct the map. 2 dimension area of layout cell have all neighbouring information
 
        ## 4. initialize l(i,j). -> calculate the feasible distance for each cell
        ##      call calculate Static Potential Matrix function as below. 
 
        if self.myLayoutBuilder is not None:
            # # based on initialized pedestrian in current facility, calculate the potential
            # # and assign the preferred Exit.
            # # in this case, the hardcoded assigned exit function we can skip.
            # self.myLayoutBuilder.assignExitForEvacuationZone()
            # self.myLayoutBuilder.calculatePotentialForSubarea()

            # calcualte static potential matrix before simulation
            self.myLayoutBuilder.calculateStaticPotentialMatrix()
        else:
            logger.info('No active layout builder instance now, please load the layout file and try again')
        
        ## 5. intialize the time tick and kicf off the simulation
        ##    here we need a new thread to run the simulation and track the CPU time tick
        
        # reset the status bar
        self.frame_statusbar.SetStatusText("Time Elapsed : " + "00:00:00 (s)", 1)

        # start the background simulation scheduler.
        self.scheduler = BackgroundScheduler(job_defaults={
            'coalesce': True,
            'misfire_grace_time': 3600  # 1 hour grace time
        })
        
        # Create an event to signal when the task is done
        task_done_event = threading.Event()
        task_done_event.set()  # Initially set the event so the counter can start

        # Add a job to the scheduler that runs every 5 seconds
        self.scheduler.add_job(self.simulation_main, 
                               'interval', 
                               seconds=constants.SIMULATION_TIME_INTERVAL, 
                               id='simulation_main', 
                               args=[task_done_event,datetime.datetime.now()], 
                               max_instances=1)

        # Start the scheduler
        self.scheduler.start()

        # Create and start the daemon thread
        monitor_thread = threading.Thread(target=self.daemon_controller, args=(self.scheduler, task_done_event))
        monitor_thread.daemon = True
        monitor_thread.start()        
        
        # disable the start simulation button and drop down menu
        # menus are stored in array in current LayoutBuilder
        # self.menubar.Menus[0] -> file
        #   self.menubar.Menus[0][0] -> Menu items under File
        #       self.menubar.Menus[0][0].MenuItem[0] -> First menu item
        #       self.menubar.Menus[0][0].MenuItem[1] -> Second menu item
        #   self.menubar.Menus[0][1] -> Menu text only
        # self.menubar.Menus[1] -> Operation
        # self.menubar.Menus[2] -> Help

        self.menubar.Menus[1][0].MenuItems[0].Enable(False)
        self.frame_toolbar.GetToolByPos(3).Enable(False)

        # Enable the pause/stop button from toolbar
        self.frame_toolbar.GetToolByPos(4).Enable(True)
        self.frame_toolbar.GetToolByPos(5).Enable(True)
        self.frame_toolbar.Realize()
        # Enable the pause/stop button from menu
        self.menubar.Menus[1][0].MenuItems[1].Enable(True)
        self.menubar.Menus[1][0].MenuItems[2].Enable(True)

    #---------------------------------------------------------------------------
    ## simulation main thread
    ## will do necessary calculation per each simulation ticker
    ## and adjust the exit choice when the counter % Tau == 0. 
    ## during each ticker's run, will pause the daemon thread so counter will not
    ## increase. in this case, only completed task in each simulation step will
    ## increase the ticker. 
    #---------------------------------------------------------------------------         
    def simulation_main(self, event, start_time):
        ## 6. Exit choice model
        ##    on each defined time interval, calculate K(s)/V(s) and F(s,e)
        ##    K(s) = denote the pedestrian density of subarea s
        ##    V(s) = denote the average movement speed of the pedestrians of subarea s
        ##    F(s,e) = e denote the potential of subarea s ∈ S with respect to exit e ∈ E
        
        global GLOBAL_COUNTER
        if GLOBAL_COUNTER % constants.SIMULATION_CYCLE == 0:
            logger.info(f" Exit Choice Model job for Ticker {str(GLOBAL_COUNTER)} started at {str(datetime.datetime.now())}") 
            # t mod r == 0:
            # need to re-calculate K(s), V(s) and F(s,e)

            # calcuate the V(s):
            self.myLayoutBuilder.calculateAvaragePedestrianSpeed()
            
            # calcuate the F(s,e) and K(s)
            # K(s) can be derived by number of the pedestrian per sub area /  zone size.
            self.myLayoutBuilder.calculatePotentialForSubarea()
            
            # Now we have the potentials of each sub area with respect of each exit stored in an array
            # with the exit id as index: for example: for assigned zone 12. the preferred exit ID = 3.
            # we have all potentials calculated as below.(Sample value)
            # 1 = 1624.8268274026423
            # 2 = 1588.5118274026424
            # 3 = 1669.8476133871948
            # 4 = 1610.2076133871947
            # 5 = 1636.950946720528
            # 6 = 1706.012613387195
            # 7 = 1693.157613387195
            # 8 = 1749.512613387195
            # so now the temp assigned exit e is defined as below:
            # e = arg min F (s,x) for all x ∈ E
            # in above case, the temp assigned exit will be 2. since Exit 2 = 1588 is the minimal potential here. 
            
            # For each subarea s ∈ S, if the temporary assigned exit e is different from the optimal exit 
            # e0 in the last time step, the potential F(s,e), which corresponding to the temporary assigned 
            # exit should be compared with the potential F(s,e0) , which corresponding to the optimal exit 
            # in the last time step. If F(s,e0) − F(s,e) > θ, the temporary assigned exit is set as the
            # destination for all evacuees in this subarea; otherwise they keep to the exit e0.
            self.myLayoutBuilder.assignExitForEvacuationZone()
            logger.info(f" Exit Choice Model job finished for Ticker {str(GLOBAL_COUNTER)} at {str(datetime.datetime.now())}")                        
        else:
            logger.info(f" Pedestrian movement Model job for Ticker : {str(GLOBAL_COUNTER)} started at {str(datetime.datetime.now())})")            

            # each pedestrian can move from current lattice site to the next adjacent lattice site
            # only in horizontal or vertical or diagonal direction when the adjacent lattice site is not occupied
            # or is obstacle. in general, the pedestrian will selet an adjacent cell of smaller potential 
            # with a larger probability. 
            
            # Calculate O(i,j) and fe(i, j) and then update the pedestrian's postiion
            # based on the transition probability as follows:
            
            # P(i0,j0)→P(i,j) = exp(−εf(e(i,j))a(i,j) / Σ(i,j) exp(−εf(e(i,j))a(i,j)
            
            # ε (≥ 0) is a sensitivity parameter scaling the effects of the potential on the transition 
            # probability. 
            # a(i,j) is a binary parameter representing whether a pedestrian can move to the lattice 
            # site (i, j). It is 1 if the neighboring lattice site is empty and 0 otherwise.
            
            # The potential of each lattice site is used to reflect the total effects of the dynamic 
            # potential and the static potential of each lattice site. Therefore, the potential f(e(i,j))
            # can be expressed as follows:
            
            # f(e(i,j)) = δo(i,j)/n(i,j) + ϕ(l(e(i,j)) − l(e(i0,j0))
            
            # o(i,j) denotes the number of lattice sites which are occupied by obstacles or pedestrians 
            # among the neighboring lattice sites of lattice site (i, j). 
            
            # n(i,j) denotes the total number of neighboring lattice sites of lattice site (i, j).
            
            # δ (≥ 0) is a parameter scaling the impacts of the repulsive force among the congested 
            # crowds on the potential.
            
            #l(e(i0,j0)) and l(e(i,j)) denote the feasible distance from current lattice site (i0, j0) 
            # and neighboring lattice site (i, j) to exit e respectively. all cell's feasible distance 
            # with respect of each exit e have been calculated before the simulation.
            # Call calculateStaticPotentialMatrix to get this. 
            
            # ϕ (≥ 0) is a parameter scaling the impacts of the route distance from the lattice site to the exit.
            
            # Calculate o(i,j)/n(i,j) through calculatePedCongestion function.
            self.myLayoutBuilder.calculatePedCongestion()

            # randomly choose from current occupied Automata celluar site and loop for each cell for each clock tick
            # 1. get current index into a arary from the AutomataList. the cell automata should still be in this facility
            # 2. loop through all item from this array index ramdomly and follow above algothrithm
            current_idx_array = self.myLayoutBuilder.getPedestrianIndexArray()
            shuffled_idx_array = np.copy(current_idx_array) # to preserve the original idx array?
            np.random.shuffle(shuffled_idx_array)

            self.myLayoutBuilder.calculateTransitionProbability(shuffled_idx_array)

            # repaint the DC.
            dc = self.get_current_bufferedDC()
            # Repaint the screen based on the updated Layoutmap.
            self.myLayoutBuilder.refreshScreen(dc)

            # Force the system to repaint. 
            self.Refresh()
            self.Update()

            logger.info(f" Pedestrian movement Model job finished for Ticker {str(GLOBAL_COUNTER)} at {str(datetime.datetime.now())}")  
            
        # update the time elapsed
        self.frame_statusbar.SetStatusText("Time Elapsed : " + str(datetime.datetime.now() - start_time) + " (s)", 1)
        self.frame_statusbar.Refresh()
        # Simulate a task that takes some time

        # Signal that the current task is done
        event.set()


    #---------------------------------------------------------------------------
    ## daemon thread
    ## check global counter, use defined time clcye to increase the counter
    ## and exit when all pedestrian are out. 
    #---------------------------------------------------------------------------         
    def daemon_controller(self, scheduler, event):
        while True:
            # Wait for the event to be set before incrementing the counter
            event.wait()
            event.clear()
            global GLOBAL_COUNTER
            GLOBAL_COUNTER += 1
            logger.info(f"Current Simulation Ticker : {GLOBAL_COUNTER}")
            time.sleep(constants.SIMULATION_TIME_INTERVAL)  # Increment the counter per interval        
      
            # # check if we have everyone evacuated
            if self.myLayoutBuilder.isEvacuated():
                logger.info('All Pedestrian evacuated!!')
                scheduler.shutdown(wait=True)
                GLOBAL_COUNTER = 0
                logger.info('Exit current simulation Task!!')
                break          

        # Below codes are ajusting the GUI    
        # when we shut down or exit the scheduler we will reenable the start simulation button
        # from both menu bar and button
        self.menubar.Menus[1][0].MenuItems[0].Enable(True)
        # Disable the pause/stop drop down from menu
        self.menubar.Menus[1][0].MenuItems[1].Enable(False)
        self.menubar.Menus[1][0].MenuItems[2].Enable(False)

        self.frame_toolbar.GetToolByPos(3).Enable(True)
        # disable the pause/stop buttone again
        self.frame_toolbar.GetToolByPos(4).Enable(False)
        self.frame_toolbar.GetToolByPos(5).Enable(False)
        # to display the change.
        self.frame_toolbar.Realize()
        self.frame_statusbar.SetStatusText("Time Elapsed : 0.0(s) ", 1)
