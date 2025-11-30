import wx.lib.sized_controls as sized_ctrls
import wx
import wx.adv
import time
import math as math
import random
import threading
import os
import numpy as np
import matplotlib as matplotlib
import logging
import LayoutBuilderWx as LayoutBuilderWx
import datetime as datetime
import constants
from wx.lib.scrolledpanel import ScrolledPanel
from ThemeColorConverter import ThemeColorConverter
from logger_config import setup_logger
from apscheduler.schedulers.background import BackgroundScheduler
from types import SimpleNamespace

# Custom logging filter to suppress specific messages
class SkipFilter(logging.Filter):
    def filter(self, record):
        return "skipped: maximum number of running instances reached" not in record.getMessage()

class ConversionError(Exception):
    pass

setup_logger()
logger = logging.getLogger(__name__)
logger.addFilter(SkipFilter())
logger.setLevel(logging.DEBUG)
# logging.getLogger('apscheduler.scheduler').propagate = False

# Get the logger for APScheduler
apscheduler_logger = logging.getLogger('apscheduler')

# Set the log level to WARNING or higher to suppress INFO and DEBUG messages
apscheduler_logger.setLevel(logging.ERROR)

#---------------------------------------------------------------------------
##  Evacuation Simulator Frame GUI.
#---------------------------------------------------------------------------

class EvacuationSimFrameWx(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame .__init__(self, None, -1, title, size=(1000, 800), style=wx.DEFAULT_FRAME_STYLE | wx.WS_EX_PROCESS_UI_UPDATES) ## Initial size
        # TODO: add a icon for simulator
        #self.SetIcon(wx.Icon('./icons/wxwin.ico', wx.BITMAP_TYPE_ICO))
        self.layout_panel = None                            # main canvas
        self.configuration_panel = None                     # configuration items
        self.menubar = None                                 # top menu bar
        self.frame_statusbar = None                         # bottom status bar
        self.frame_toolbar = None                           # toolbar. icon based button
        self.filepath = None                                # store the filepath of loaded excel file.

        self.myLayoutBuilder = None                         # major data structure to store the entire Layout structure
        self.scheduler = None                               # background scheduler for the major simulation task
        self.daemon_thread = None                           # daemon thread

        self.start_time = None                              # to store the simulation start time. will set when simulation started.

        self.ticker = 0                                     # simulation ticker. main control element for the entire simulation
        self.pause_event = None                             # event for pause/resume the simulation progress
        self.stop_event = None                              # event for stop the simulation progress
        self.refresh_complete = threading.Event()           # event for each screen refresh step.
        self.task_done_event = None                         # event to indicate current schedulered task is done

        self.configuration_dict = {}                        # configuration items dict
        self.config = None                                  # namespaces that store all configuration items

        self.color_button_list = {}                         # store the dict of all color buttons.
        self.color_text_ctrl_list = {}                      # store the dict of all color_text_ctrl
        self.color_preview_list = {}                        # store the dict of all color preview panel

        self.layout_bitmap = None                           # bitmap to store the current layout simulation status
        self.use_bitmap = True                              # flag to test bitmap.

        self.injected_pedestrian = 0                        # store how many pedestrian has been injected

        #Setup widgets
        self.InitializeComponents()

    #---------------------------------------------------------------------------
    ##  intiliazed all widgets
    #---------------------------------------------------------------------------
    def InitializeComponents(self):

        # define all configuration items that can be configure on the fly.
        configuration_flag_dict = {}                   # all configurable items
        configuration_colorflag_dict = {}              # color related flag items only.

        constants_dict = {attr: getattr(constants, attr) for attr in dir(constants) if attr.isupper()}
        configuration_flag_dict = {k: v for k, v in constants_dict.items() if k.endswith("_CONFIG")}
        configuration_colorflag_dict = {k: v for k, v in constants_dict.items() if k.endswith("_COLORCONFIG")}
        self.configuration_dict = {k: constants_dict[k] for k in set(constants_dict.keys()
                                                                     - set(configuration_flag_dict.keys()))
                                                                     - set(configuration_colorflag_dict.keys())}
        # convert the configuration dict to a namespace so all attribute can
        # be accessed through "." operation, for example self.config.LAYOUT_CELL_SIZE
        # instead of doing self.config.LAYOUT_CELL_SIZE
        self.config = SimpleNamespace(**self.configuration_dict)

        # GUI structure
        #               splitter (sp)
        #                    |--config_base_panel (with left vertical sizer)
        #                    |            |--Button panel (with left vertical sizer)
        #                    |            |     |- buttons. (Apply, reset and re-paint) each button with button_sizer
        #                    |            |--scrolled_window (with scrolled sizer) (also will with left vertical sizer)
        #                    |                  |--from panel (size Type = From) (also will add into scrolled sizer)
        #                    |                       |-- StaticText (s)
        #                    |                       |-- TextCtrl   (s)
        #                                                   OR
        #                    |                       |-- color_panel(with color sizer)
        #                    |                                |-- TextCtrl (s)
        #                    |                                |-- Color Preview (s)
        #                    |                                |-- color Button (s)
        #                    |--layout_panel
        #                            |-- main canvas for the map

        sp = wx.SplitterWindow(self)
        ## Left side panel
        config_base_panel = wx.Panel(sp, 1)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        config_base_panel.SetSizer(left_sizer)

        # put the buttons on top of all configuration items.
        # Create a sub-panel for buttons
        button_panel = sized_ctrls.SizedPanel(config_base_panel, 1)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_panel.SetSizer(button_sizer)

        apply_button = wx.Button(button_panel, label="Apply Config")
        reset_button = wx.Button(button_panel, label="Reset To Default")
        # repaint_button = wx.Button(button_panel, label="Re-Paint Map")

        apply_button.Bind(wx.EVT_BUTTON, self.on_apply_config)
        reset_button.Bind(wx.EVT_BUTTON, self.on_reset_config)
        # repaint_button.Bind(wx.EVT_BUTTON, self.on_repaint_config)

        left_sizer.Add(button_panel, 0, wx.EXPAND)

        # configuration panel
        config_scrolled_panel = wx.ScrolledWindow(config_base_panel, style=wx.SUNKEN_BORDER | wx.HSCROLL | wx.VSCROLL)
        config_scrolled_panel.SetScrollRate(5, 5)
        scrolled_sizer = wx.BoxSizer(wx.VERTICAL)
        config_scrolled_panel.SetSizer(scrolled_sizer)

        self.configuration_panel = sized_ctrls.SizedPanel(config_scrolled_panel, style=wx.SUNKEN_BORDER)
        self.configuration_panel.SetSizerType("form")
        self.configuration_panel.SetBackgroundColour(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_DISPLAY_EMPTY_SPACE)))

        max_label_width = 0
        max_text_ctrl_width = 0

        # check the configuration_flag_dict and add all configuration items
        for config_key, config_value in configuration_flag_dict.items():
            real_config_key = config_key.removesuffix("_CONFIG")
            real_config_value = self.configuration_dict[real_config_key]
            # add all items
            lbltext = "%s :" % real_config_key.title()
            lbl = wx.StaticText(self.configuration_panel, label=lbltext)
            lbl.SetSizerProps(valign="center")
            txt = wx.TextCtrl(self.configuration_panel, name=real_config_key)
            txt.SetValue(str(real_config_value))
            txt.SetSizerProps(expand=True)
            if lbl.GetSize().GetWidth() > max_label_width:
                max_label_width = lbl.GetSize().GetWidth()
            if txt.GetSize().GetWidth() > max_text_ctrl_width:
                max_text_ctrl_width = txt.GetSize().GetWidth()

        # check color related configuration items
        for config_key, config_value in configuration_colorflag_dict.items():
            real_config_key = config_key.removesuffix("_COLORCONFIG")
            real_config_value = self.configuration_dict[real_config_key]
            # we need to add color pick editor here
            # if configuration has _CONFIG = True but _COLORCONFIG = False, it will be set in else part only
            lbltext = "%s :" % real_config_key.title()
            lbl = wx.StaticText(self.configuration_panel, label=lbltext)
            lbl.SetSizerProps(valign="center")

            # Create color panel and sizer for components
            color_panel = wx.Panel(self.configuration_panel, 1)
            color_sizer = wx.BoxSizer(wx.HORIZONTAL)
            color_panel.SetSizer(color_sizer)

            # Text control for hex color input
            color_text_ctrl = wx.TextCtrl(color_panel, style=wx.TE_PROCESS_ENTER)
            color_text_ctrl.Bind(wx.EVT_TEXT, self.on_hex_input)
            color_text_ctrl.SetValue("#" + str(real_config_value))
            color_text_ctrl.SetName(real_config_key)
            color_sizer.Add(color_text_ctrl, 1, wx.EXPAND | wx.ALL, 3)
            self.color_text_ctrl_list[real_config_key] = color_text_ctrl

            # Color preview panel (same size as button)
            color_preview = wx.Panel(color_panel, size=(16, 16))
            color_preview.SetBackgroundColour("#" + str(real_config_value))
            color_preview.Label = real_config_key
            color_sizer.Add(color_preview, 0, wx.LEFT | wx.ALL, 3)
            self.color_preview_list[real_config_key] = color_preview

            # Create a bitmap button for color picker icons8-color-picker-67.png
            bmp = wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-color-picker-67.png"),wx.BITMAP_TYPE_PNG).Scale(16, 16, wx.IMAGE_QUALITY_HIGH)
            color_button = wx.BitmapButton(color_panel, bitmap=wx.Bitmap(bmp))
            color_button.Bind(wx.EVT_BUTTON, self.on_pick_color)
            color_sizer.Add(color_button, 0, wx.LEFT | wx.ALL, 3)
            color_button.Label = real_config_key
            self.color_button_list[real_config_key] = color_button

            # Adjust the size of the color panel to match other text controls
            color_panel.SetSizerProps(expand=True)
            if lbl.GetSize().GetWidth() > max_label_width:
                max_label_width = lbl.GetSize().GetWidth()
            if color_text_ctrl.GetSize().GetWidth() > max_text_ctrl_width:
                max_text_ctrl_width = color_text_ctrl.GetSize().GetWidth()

        # Add the form panel to the scrolled window's sizer
        scrolled_sizer.Add(self.configuration_panel, 1, wx.EXPAND)

        # Add the scrolled window to the left panel's sizer
        left_sizer.Add(config_scrolled_panel, 1, wx.EXPAND)

        ## right side panel
        self.layout_panel = wx.ScrolledWindow(sp, style=wx.SUNKEN_BORDER | wx.HSCROLL | wx.VSCROLL)
        self.layout_panel.SetScrollRate(10, 10)
        self.layout_panel.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)
        self.layout_panel.SetBackgroundColour(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_DISPLAY_EMPTY_SPACE)))
        self.layout_panel.Bind(wx.EVT_PAINT, self.on_paint)
        # Create a sizer for the right scrolled window
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.layout_panel.SetSizer(right_sizer)

        ## Insert into the split vertical panels
        # based on calculated the maximum width needed for the configuration panel
        buffer = 85  # Add some buffer for padding and spacing
        sp.SplitVertically(config_base_panel, self.layout_panel, max_label_width + max_text_ctrl_width + buffer) # Split the window left and right.
        sp.SetSashGravity(0)
        sp.SetMinimumPaneSize(max_label_width + max_text_ctrl_width + buffer)         # Minimum size of subwindow.

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
        self.frame_statusbar.SetFieldsCount(6)
        self.frame_statusbar.SetStatusWidths([10, 120, 150, 250, 250, 220])
        # TODO : Status bar will update current run time, cpu tick etc.
        self.frame_statusbar.SetStatusText("", 0) ## give the toolbar tooltiphelp some default spaces. Wxpython bug..
        self.frame_statusbar.SetStatusText("Current Ticker : 0", 1)
        self.frame_statusbar.SetStatusText("Simuation Status : Idle", 2)
        self.frame_statusbar.SetStatusText("# of Pedestrian in the map : - ", 3)
        self.frame_statusbar.SetStatusText("# of Pedestrian injected into the map : -", 4)
        self.frame_statusbar.SetStatusText("Time Elapsed : " + "00:00:00 (s)", 5)
        self.SetStatusBar(self.frame_statusbar)

        ## Toolbax bar
        self.frame_toolbar = wx.ToolBar(self)
        self.frame_toolbar.SetToolBitmapSize((32, 32))
        self.frame_toolbar.SetBackgroundColour(wx.Colour("#E0E0E0"))     # Light grey background
        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Load Layout",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-open-file-48.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Load Layout","")
        self.Bind(wx.EVT_TOOL,self.on_menu_file_loadLayout, id = tool.GetId())

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Save Animation",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-save-50.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Save Animation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_file_saveAnimation, id = tool.GetId())

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Start Simulation",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-play-48.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Start Simulation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_startsimulation, id = tool.GetId())
        tool.Enable(False) # disable the start button, only will be enabled after we load the layout.

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Resume/Pause Simulation",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-pause-64.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Resume/Pause Simulation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_pause_resume_simuation, id = tool.GetId())
        tool.Enable(False) #default to disable stop/pause simulation button

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Stop Simulation",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-stop-64.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Stop Simulation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_stopsimulation, id = tool.GetId())
        tool.Enable(False) #default to disable stop/pause simulation button

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Reset Simulation",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","reset.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Reset Simulation","")
        self.Bind(wx.EVT_TOOL,self.on_menu_operation_resetsimulation, id = tool.GetId())
        tool.Enable(False) #default to disable stop/pause simulation button

        # Add a stretchable space
        self.frame_toolbar.AddStretchableSpace()

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "Exit Simulator",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-exit-64.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"Exit Simulator","")
        self.Bind(wx.EVT_TOOL,self.on_menu_file_exit, id = tool.GetId())

        tool = self.frame_toolbar.AddTool(wx.ID_ANY, "About",
                                     wx.Image(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps","icons8-about-64.png"),wx.BITMAP_TYPE_PNG).ConvertToBitmap(),
                                     wx.NullBitmap, wx.ITEM_NORMAL,"About","")
        self.Bind(wx.EVT_TOOL,self.on_menu_help_about, id = tool.GetId())

        self.SetToolBar(self.frame_toolbar)
        self.frame_toolbar.Realize()

        # Handle program exit issue
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # some changes to avoid flickering
        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)


    #---------------------------------------------------------------------------
    ##  color picker for chose different color combination about the GUI
    #---------------------------------------------------------------------------
    def on_pick_color(self, event):
        """Open a color picker dialog and update both text control and color preview."""
        color_data = wx.ColourData()
        color_dialog = wx.ColourDialog(self, color_data)
        if color_dialog.ShowModal() == wx.ID_OK:
            color_data = color_dialog.GetColourData()
            color = color_data.GetColour()
            # Convert color to hex and update the text control and preview panel
            hex_value = f"#{color.GetAsString(wx.C2S_HTML_SYNTAX)[1:]}"
            color_button = event.GetEventObject()
            self.color_text_ctrl_list[color_button.Label].SetValue(hex_value)
            self.color_preview_list[color_button.Label].SetBackgroundColour(hex_value)
            self.color_preview_list[color_button.Label].Refresh()

    #---------------------------------------------------------------------------
    ##  allow user to type in the hex code of RGB to see the color in text field.
    #---------------------------------------------------------------------------
    def on_hex_input(self, event):
        # get the text field that been typed here
        text_field = event.GetEventObject()
        hex_value = text_field.GetValue().strip()
        try:
            if self.is_valid_hex_color(hex_value):
                self.color_preview_list[text_field.GetName()].SetBackgroundColour(hex_value)
                self.color_preview_list[text_field.GetName()].Refresh()
        except:
            pass  # Ignore if color_preview is not there yet.

    #---------------------------------------------------------------------------
    ##  quick check if current hex color is valid
    #---------------------------------------------------------------------------
    def is_valid_hex_color(self, hex_color):
        """Check if the input is a valid hex color format."""
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
        return len(hex_color) == 6 and all(c in "0123456789ABCDEFabcdef" for c in hex_color)

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
            self.filepath = fileDialog.GetPath()
            try:
                #now we have the file path
                self.myLayoutBuilder = LayoutBuilderWx.LayoutBuilderWx(self.filepath, self.layout_panel, self.config)

                # read the layout file
                self.myLayoutBuilder.load_layout_file()

                # draw the lay out on scorlled panel & initialize the number of pedestrians
                self.myLayoutBuilder.construct_layoutMap()
            except IOError:
                wx.LogError("Cannot open file '%s'." % self.filepath)

        # enable the start simulation button.
        self.frame_toolbar.GetToolByPos(2).Enable(True)
        # enable the reset simulation button.
        self.frame_toolbar.GetToolByPos(5).Enable(True)
        self.frame_toolbar.Realize()
        # Enable the Start button from menu
        self.menubar.Menus[1][0].MenuItems[0].Enable(True)

        # make sure the layout panel can at least show current layout map.
        self.update_virtual_size(self.layout_panel)

        # update current layout panel
        self.layout_panel.Layout()
        self.layout_panel.Refresh()

    def update_virtual_size(self, canvas):
        """ Updates the virtual size based on the maximum extents of the shapes. """
        virtual_width = canvas.GetSize().width
        virtual_height = canvas.GetSize().height
        # Ensure virtual size is at least slightly larger than the largest shape positions
        new_virtual_width = max(virtual_width, self.myLayoutBuilder.max_column * self.config.LAYOUT_CELL_SIZE + 50)
        new_virtual_height = max(virtual_height, self.myLayoutBuilder.max_row * self.config.LAYOUT_CELL_SIZE + 50)

        # Update the virtual size if needed for the layout panel
        if new_virtual_width != virtual_width or new_virtual_height != virtual_height:
            virtual_width, virtual_height = new_virtual_width, new_virtual_height
            canvas.SetVirtualSize((virtual_width, virtual_height))

        # update the entire Frame size
        # we compare the current entire framesize' width with the left side width + updated left side width
        # for height just compare the original height with new height.
        new_frame_width = max(self.GetSize().width, virtual_width  + self.Children[0].Children[0].GetSize().width)
        new_frame_height = max(self.GetSize().height, virtual_height)

        # Set the new size of the frame
        self.SetSize((new_frame_width, new_frame_height))
        self.Layout()  # Refresh layout

        canvas.SetVirtualSize(canvas.GetSizer().GetMinSize())
    #---------------------------------------------------------------------------
    ##  save the animation?
    #---------------------------------------------------------------------------
    def on_menu_file_saveAnimation(self, event):
        logger.info("Event handler for 'on_menu_file_saveAnimation' not implemented yet")
        event.Skip()

    #---------------------------------------------------------------------------
    ##  exit the simulator
    #---------------------------------------------------------------------------
    def on_menu_file_exit(self, event):
        logger.info("Event handler for 'on_menu_file_exit' invoked.")
        self.Destroy()
        wx.Exit()  # Exit the application
        os._exit(0) # force to exit???

    #---------------------------------------------------------------------------
    ##  pause/resume thje simulation
    #---------------------------------------------------------------------------
    def on_menu_operation_pause_resume_simuation(self, event):
        if self.pause_event.is_set():
            logger.info("Current simulation progress Paused")
            self.pause_event.clear()
            self.frame_statusbar.SetStatusText("Simuation Status : Paused", 2)
            # after stop the simulation or pause the simulation, we can reset the simulation
            self.frame_toolbar.GetToolByPos(5).Enable(True) # reset button
            self.frame_toolbar.Realize()
        else:
            logger.info("Current simulation progress resumed")
            self.pause_event.set()
            self.refresh_complete.set()
            self.frame_statusbar.SetStatusText(" Simuation Status : Running", 2)
            # after resume the simulation we cannot reset the simulation
            self.frame_toolbar.GetToolByPos(5).Enable(False) # reset button
            self.frame_toolbar.Realize()

    #---------------------------------------------------------------------------
    ##  completely stop current simuation
    #---------------------------------------------------------------------------
    def on_menu_operation_stopsimulation(self, event):
        logger.info("Simulation Stopped.")

        self.stop_event.set()
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
        if self.daemon_thread:
            self.daemon_thread.join()  # Wait for the thread to finish

        # Wait for the current task to complete
        self.task_done_event.wait()

        self.ticker = 0
        self.frame_statusbar.SetStatusText(f"Current Ticker: {str(self.ticker)}", 1)
        self.frame_statusbar.SetStatusText("Simuation Status : Stopped", 2)
        # self.frame_statusbar.SetStatusText("Number of Pedestrian in the map : - ", 3)
        # self.frame_statusbar.SetStatusText("Time Elapsed : " + "00:00:00 (s)", 4)
        # after stop the simulation or pause the simulation, we can reset the simulation
        self.frame_toolbar.GetToolByPos(5).Enable(True) # reset button
        self.frame_toolbar.Realize()

    #---------------------------------------------------------------------------
    ##  completely reset current simuation
    #---------------------------------------------------------------------------
    def on_menu_operation_resetsimulation(self, event):
        logger.info("Simulation Resetted.")
        # TODO: to reset the simulation
        # 1. repaint the layout
        # 2. reset everything to beginning.
        # 3. restart all thread so start button can functionaly from very beginning
        self.reset_gui()

    #---------------------------------------------------------------------------
    ##  About dialog
    #---------------------------------------------------------------------------
    def on_menu_help_about(self, event):
        logger.info("Displaying About Information")
        # Create an AboutDialogInfo object
        info = wx.adv.AboutDialogInfo()
        info.SetName("Evacuation Simulator")
        info.SetVersion("1.0")
        info.SetDescription("Evacuation Simulation is based on : \n  \
                             An evacuation guidance model for heterogeneous populations \n \
                             in large-scale pedestrian facilities with multiple exits")
        info.SetCopyright("(C) 2024 Zen Company")
        info.SetWebSite("https://www.xxxx.com")
        info.AddDeveloper("Zening Zhao & Pengfei Zhao")

        # Show the About dialog
        wx.adv.AboutBox(info)

    #---------------------------------------------------------------------------
    ##  apply current constants settings into the constants instance
    #---------------------------------------------------------------------------
    def on_apply_config(self, event):
        # read all values from the Text Ctrl field.
        # compare it with existing configuration_dict.
        # needs to do some basic data type check.
        error_list = {}
        for child in self.configuration_panel.Children:
            if isinstance(child, wx._core.TextCtrl): # check all Text Ctrl area
                if child.Value != str(self.configuration_dict[child.Name]):
                    try:
                        self.configuration_dict[child.Name] = self.convert_to_number(child.Value)
                    except ConversionError as e:
                        error_list[child.Name] = f"Cannot assign properly value for : {child.Name}, reset to default value : {str(self.configuration_dict[child.Name])}"
                        child.Value = str(self.configuration_dict[child.Name])

            if isinstance(child, wx._core.Panel): # color control item
                # at this moment, the color panel contains these info:
                # WindowList: [<wx._core.TextCtrl object at 0x000001C100698EF0>, <wx._core.BitmapButton object at 0x000001C100699010>]
                # here is a little bit tricky... the constant file doesn't have # prefix. will fix this.
                if child.Children[0].Value != "#" + str(self.configuration_dict[child.Children[1].Label]):
                    self.configuration_dict[child.Children[1].Label] = child.Children[0].Value[1:]
        if len(error_list) > 0:
            # Create a warning dialog
            dialog = wx.MessageDialog(
                self,
                "\n".join(error_list.values()),
                "Warning",
                wx.OK | wx.ICON_WARNING
            )
            # Show the dialog
            dialog.ShowModal()
            dialog.Destroy()

        # refresh the global config item
        self.config = SimpleNamespace(**self.configuration_dict)

        # At this moment, we can reset the GUI.
        self.reset_gui()

    #---------------------------------------------------------------------------
    ##  reset GUI to original. based on already loaded filepath.
    ##  also will reset all other GUI components.
    #---------------------------------------------------------------------------
    def reset_gui(self):
        try:
            #now we have the file path
            self.myLayoutBuilder = LayoutBuilderWx.LayoutBuilderWx(self.filepath, self.layout_panel, self.config)

            # read the layout file
            self.myLayoutBuilder.load_layout_file()

            # draw the lay out on scorlled panel & initialize the number of pedestrians
            self.myLayoutBuilder.construct_layoutMap()
        except IOError:
            wx.LogError("Cannot open file '%s'." % self.filepath)

        # enable the start simulation button.
        self.frame_toolbar.GetToolByPos(2).Enable(True)
        # enable the reset simulation button.
        self.frame_toolbar.GetToolByPos(5).Enable(True)
        self.frame_toolbar.Realize()
        # Enable the Start button from menu
        self.menubar.Menus[1][0].MenuItems[0].Enable(True)

        # make sure the layout panel can at least show current layout map.
        self.update_virtual_size(self.layout_panel)

        # update current layout panel
        self.layout_panel.Layout()
        self.layout_panel.Refresh()

        self.injected_pedestrian = 0

        self.frame_statusbar.SetStatusText(f"Current Ticker: 0", 1)
        self.frame_statusbar.SetStatusText("Simuation Status : Idle", 2)
        self.frame_statusbar.SetStatusText("Number of Pedestrian in the map : - ", 3)
        self.frame_statusbar.SetStatusText("# of Pedestrian injected into the map : -", 4)
        self.frame_statusbar.SetStatusText("Time Elapsed : " + "00:00:00 (s)", 5)

    #---------------------------------------------------------------------------
    ##  determine basic data type (int, float only)
    #---------------------------------------------------------------------------
    def convert_to_number(self, value):
        try:
            # Try converting to an integer
            return int(value)
        except ValueError:
            pass

        try:
            # Try converting to a float
            return float(value)
        except ValueError:
            pass

        raise ConversionError(f"Cannot convert '{value}' to a number.")

    #---------------------------------------------------------------------------
    ##  reset all constants values to default
    #---------------------------------------------------------------------------
    def on_reset_config(self, event):
        # read the constants into configuration_dict to reset all to default
        # loop through all items in current configuration panels
        # check the values of each item and compare with the configuration dict.
        # if any values changed, replace the textctrl displayed value with
        # the values from configuration dict.

        configuration_flag_dict = {}                   # all configurable items
        configuration_colorflag_dict = {}              # color related flag items only.

        constants_dict = {attr: getattr(constants, attr) for attr in dir(constants) if attr.isupper()}
        configuration_flag_dict = {k: v for k, v in constants_dict.items() if k.endswith("_CONFIG")}
        configuration_colorflag_dict = {k: v for k, v in constants_dict.items() if k.endswith("_COLORCONFIG")}
        self.configuration_dict = {k: constants_dict[k] for k in set(constants_dict.keys()
                                                                     - set(configuration_flag_dict.keys()))
                                                                     - set(configuration_colorflag_dict.keys())}

        # reset to default value on GUI
        for child in self.configuration_panel.Children:
            if isinstance(child, wx._core.TextCtrl): # check all Text Ctrl area
                if child.Value != str(self.configuration_dict[child.Name]):
                    child.Value = str(self.configuration_dict[child.Name])
            if isinstance(child, wx._core.Panel): # color control item
                # at this moment, the color panel contains these info:
                # WindowList: [<wx._core.TextCtrl object at 0x000001C100698EF0>, <wx._core.BitmapButton object at 0x000001C100699010>]
                # here is a little bit tricky... the constant file doesn't have # prefix. will fix this.
                if child.Children[0].Value != "#" + str(self.configuration_dict[child.Children[1].Label]):
                    child.Children[0].Value = "#" + self.configuration_dict[child.Children[1].Label]

        # convert the configuration dict to a namespace so all attribute can
        # be accessed through "." operation, for example self.config.LAYOUT_CELL_SIZE
        # instead of doing self.config.LAYOUT_CELL_SIZE
        self.config = SimpleNamespace(**self.configuration_dict)

        # At this moment, we can reset the GUI.
        self.reset_gui()

    # #---------------------------------------------------------------------------
    # ##  repaint layout based on current configurations
    # #---------------------------------------------------------------------------
    # def on_repaint_config(self, event):
    #     self.layout_panel.Refresh()
    #     self.layout_panel.Update()

    # #---------------------------------------------------------------------------
    # ## TODO: how to resolve the screen not refresh properly issue?
    # #---------------------------------------------------------------------------
    # def on_scroll(self, event):
    #     dx, dy = self.layout_panel.GetScrollPixelsPerUnit()
    #     pos = self.layout_panel.GetScrollPos(wx.VERTICAL)
    #     self.layout_panel.ScrollWindow(0, -dy * (event.GetPosition() - pos))
    #     self.layout_panel.SetScrollPos(wx.VERTICAL, event.GetPosition())

    #---------------------------------------------------------------------------
    ## when closed the wx frame. needs to destory the entire instance
    #---------------------------------------------------------------------------
    def on_close(self, event):
        logger.info(f"Current Simulation Main Thread will be terminated...")
        self.Destroy()
        wx.Exit()  # Exit the application
        os._exit(0) # force to exit???


    def prepare_simulation_bitmap(self, mem_dc):
        verticle_lines = []
        horizontal_lines = []
        if self.myLayoutBuilder:
            for row in self.myLayoutBuilder.LayoutMap[self.myLayoutBuilder.min_row - 1:]:
                for cell in row[self.myLayoutBuilder.min_column - 1:]:
                    # for border/obstacle/exit, draw solid rectangle
                    if cell.type in (self.config.LAYOUT_CELL_TYPE_BORDER, self.config.LAYOUT_CELL_TYPE_OBSTACLE,
                                     self.config.LAYOUT_CELL_TYPE_EXIT, self.config.LAYOUT_CELL_TYPE_INJECTION_CELL):
                        mem_dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.getColor(cell.type))), 1, wx.PENSTYLE_TRANSPARENT))
                        mem_dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.getColor(cell.type))),wx.BRUSHSTYLE_SOLID))
                        mem_dc.DrawRectangle(cell.column * self.config.LAYOUT_CELL_SIZE,
                                        cell.row * self.config.LAYOUT_CELL_SIZE,
                                        self.config.LAYOUT_CELL_SIZE,
                                        self.config.LAYOUT_CELL_SIZE)
                    else:
                        verticle_lines.append((
                                        cell.column * self.config.LAYOUT_CELL_SIZE,
                                        cell.row * self.config.LAYOUT_CELL_SIZE,
                                        cell.column * self.config.LAYOUT_CELL_SIZE + self.config.LAYOUT_CELL_SIZE,
                                        cell.row * self.config.LAYOUT_CELL_SIZE
                                        ))
                        horizontal_lines.append((
                                        cell.column * self.config.LAYOUT_CELL_SIZE,
                                        cell.row * self.config.LAYOUT_CELL_SIZE,
                                        cell.column * self.config.LAYOUT_CELL_SIZE,
                                        cell.row * self.config.LAYOUT_CELL_SIZE + self.config.LAYOUT_CELL_SIZE
                                        ))
            mem_dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(cell.color)), 1, wx.PENSTYLE_DOT))
            mem_dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(cell.color)),wx.BRUSHSTYLE_VERTICAL_HATCH))
            mem_dc.DrawLineList(verticle_lines + horizontal_lines)

            # plot the pedstrain
            EllipseList_Senior = []
            EllipseList = []
            for i in range(len(self.myLayoutBuilder.AutomataList)):
                # here adjust the start size and cell size to make the graph more precise
                # We draw the pedestrian inside of each cell. Not cover the border.
                if self.myLayoutBuilder.AutomataList[i].occupied: # only setup the spot that is occupied. (not border/exit/obstacle)
                    if self.myLayoutBuilder.AutomataList[i].velocity_mode == 2: # senior people
                        EllipseList_Senior.append(((self.myLayoutBuilder.AutomataList[i].y) * self.config.LAYOUT_CELL_SIZE + 1,
                                                    (self.myLayoutBuilder.AutomataList[i].x) * self.config.LAYOUT_CELL_SIZE + 1,
                                                    self.config.LAYOUT_CELL_SIZE - 2,
                                                    self.config.LAYOUT_CELL_SIZE - 2))
                    else:
                        EllipseList.append(((self.myLayoutBuilder.AutomataList[i].y) * self.config.LAYOUT_CELL_SIZE + 1,
                                            (self.myLayoutBuilder.AutomataList[i].x) * self.config.LAYOUT_CELL_SIZE + 1,
                                            self.config.LAYOUT_CELL_SIZE - 2,
                                            self.config.LAYOUT_CELL_SIZE - 2))
            mem_dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_NON_SENIOR_COLOR)), 1, wx.PENSTYLE_SOLID))
            mem_dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_NON_SENIOR_COLOR)), wx.BRUSHSTYLE_SOLID))
            mem_dc.DrawEllipseList(EllipseList)
            mem_dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_SENIOR_COLOR)), 1, wx.PENSTYLE_SOLID))
            mem_dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_SENIOR_COLOR)), wx.BRUSHSTYLE_SOLID))
            mem_dc.DrawEllipseList(EllipseList_Senior)

    #---------------------------------------------------------------------------
    ## on_paint. will automatically draw the buffered content on screen.
    ## don't need to be called explicity but underlying will just draw the screen
    ## based on the buffer
    #---------------------------------------------------------------------------
    def on_paint(self, event):
        logger.info(f"In Event handler for 'on_paint'. Current Client Size: {self.layout_panel.GetClientSize()}")

        dc = wx.BufferedPaintDC(self.layout_panel)
        self.layout_panel.PrepareDC(dc)  # Adjusts for scrolled position
        dc.Clear()

        if self.use_bitmap:
            logger.info("Using Bitmap to re-paint the screen")
            self.layout_bitmap = wx.Bitmap(self.layout_panel.Size)
            mem_dc = wx.MemoryDC(self.layout_bitmap)
            mem_dc.Clear()
            self.prepare_simulation_bitmap(mem_dc)
            dc.Blit(0,0,self.layout_panel.GetSize().width,self.layout_panel.GetSize().height,mem_dc,0,0)
            mem_dc.SelectObject(wx.NullBitmap)
        else: # normal paint
            logger.info("Using normal buffered DC to re-paint the screen")
            # if self.ticker != 0:
            verticle_lines = []
            horizontal_lines = []
            if self.myLayoutBuilder:
                for row in self.myLayoutBuilder.LayoutMap[self.myLayoutBuilder.min_row - 1:]:
                    for cell in row[self.myLayoutBuilder.min_column - 1:]:
                        # for border/obstacle/exit, draw solid rectangle
                        if cell.type in (self.config.LAYOUT_CELL_TYPE_BORDER, self.config.LAYOUT_CELL_TYPE_OBSTACLE,
                                         self.config.LAYOUT_CELL_TYPE_EXIT, self.config.LAYOUT_CELL_TYPE_INJECTION_CELL,
                                         self.config.LAYOUT_CELL_TYPE_EMPTY_SPACE_NO_PED):
                            dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.getColor(cell.type))), 1, wx.PENSTYLE_TRANSPARENT))
                            dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.getColor(cell.type))),wx.BRUSHSTYLE_SOLID))
                            dc.DrawRectangle(cell.column * self.config.LAYOUT_CELL_SIZE,
                                            cell.row * self.config.LAYOUT_CELL_SIZE,
                                            self.config.LAYOUT_CELL_SIZE,
                                            self.config.LAYOUT_CELL_SIZE)
                        else:
                            verticle_lines.append((
                                            cell.column * self.config.LAYOUT_CELL_SIZE,
                                            cell.row * self.config.LAYOUT_CELL_SIZE,
                                            cell.column * self.config.LAYOUT_CELL_SIZE + self.config.LAYOUT_CELL_SIZE,
                                            cell.row * self.config.LAYOUT_CELL_SIZE
                                            ))
                            horizontal_lines.append((
                                            cell.column * self.config.LAYOUT_CELL_SIZE,
                                            cell.row * self.config.LAYOUT_CELL_SIZE,
                                            cell.column * self.config.LAYOUT_CELL_SIZE,
                                            cell.row * self.config.LAYOUT_CELL_SIZE + self.config.LAYOUT_CELL_SIZE
                                            ))
                dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(cell.color)), 1, wx.PENSTYLE_DOT))
                dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(cell.color)),wx.BRUSHSTYLE_VERTICAL_HATCH))
                dc.DrawLineList(verticle_lines + horizontal_lines)

                # plot the pedstrain
                EllipseList_Senior = []
                EllipseList = []
                JustInjectedCells = []
                for i in range(len(self.myLayoutBuilder.AutomataList)):
                    # here adjust the start size and cell size to make the graph more precise
                    # We draw the pedestrian inside of each cell. Not cover the border.
                    if self.myLayoutBuilder.AutomataList[i].occupied: # only setup the spot that is occupied. (not border/exit/obstacle)
                        if self.myLayoutBuilder.AutomataList[i].just_injected_flag:
                            JustInjectedCells.append(((self.myLayoutBuilder.AutomataList[i].y) * self.config.LAYOUT_CELL_SIZE + 1,
                                                            (self.myLayoutBuilder.AutomataList[i].x) * self.config.LAYOUT_CELL_SIZE + 1,
                                                            self.config.LAYOUT_CELL_SIZE - 2,
                                                            self.config.LAYOUT_CELL_SIZE - 2))
                        else:
                            if self.myLayoutBuilder.AutomataList[i].velocity_mode == 2: # senior people
                                EllipseList_Senior.append(((self.myLayoutBuilder.AutomataList[i].y) * self.config.LAYOUT_CELL_SIZE + 1,
                                                            (self.myLayoutBuilder.AutomataList[i].x) * self.config.LAYOUT_CELL_SIZE + 1,
                                                            self.config.LAYOUT_CELL_SIZE - 2,
                                                            self.config.LAYOUT_CELL_SIZE - 2))
                            else:
                                EllipseList.append(((self.myLayoutBuilder.AutomataList[i].y) * self.config.LAYOUT_CELL_SIZE + 1,
                                                    (self.myLayoutBuilder.AutomataList[i].x) * self.config.LAYOUT_CELL_SIZE + 1,
                                                    self.config.LAYOUT_CELL_SIZE - 2,
                                                    self.config.LAYOUT_CELL_SIZE - 2))
                dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_NON_SENIOR_COLOR)), 1, wx.PENSTYLE_SOLID))
                dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_NON_SENIOR_COLOR)), wx.BRUSHSTYLE_SOLID))
                dc.DrawEllipseList(EllipseList)
                dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_SENIOR_COLOR)), 1, wx.PENSTYLE_SOLID))
                dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_SENIOR_COLOR)), wx.BRUSHSTYLE_SOLID))
                dc.DrawEllipseList(EllipseList_Senior)
                dc.SetPen(wx.Pen(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_INJECTED_COLOR)), 1, wx.PENSTYLE_SOLID))
                dc.SetBrush(wx.Brush(wx.Colour(*ThemeColorConverter.hex_to_rgb(self.config.LAYOUT_INJECTED_COLOR)), wx.BRUSHSTYLE_SOLID))
                dc.DrawEllipseList(JustInjectedCells)

        self.refresh_complete.set()

    #---------------------------------------------------------------------------
    ## return the hex color string defined in configuration for current cell Type.
    ## will be hardcoded mapping now. might need further improvement.
    #---------------------------------------------------------------------------
    def getColor(self, cell_type):
        if cell_type == self.config.LAYOUT_CELL_TYPE_BORDER:
            return self.config.LAYOUT_DISPLAY_BORDER
        if cell_type == self.config.LAYOUT_CELL_TYPE_OBSTACLE:
            return self.config.LAYOUT_DISPLAY_OBSTACLE
        if cell_type == self.config.LAYOUT_CELL_TYPE_EXIT:
            return self.config.LAYOUT_DISPLAY_EXIT
        if cell_type == self.config.LAYOUT_CELL_TYPE_INJECTION_CELL:
            return self.config.LAYOUT_DISPLAY_INJECTION_CELL
        if cell_type == self.config.LAYOUT_CELL_TYPE_EMPTY_SPACE_NO_PED:
            return self.config.LAYOUT_DISPLAY_EMPTY_SPACE_NO_PED
        return "000000"  # default to black

    #---------------------------------------------------------------------------
    ## clear the screen after stop
    #---------------------------------------------------------------------------
    def clear_shapes(self):
        self.refresh_complete.clear()
        self.layout_panel.Refresh()
        self.layout_panel.Update()


    #---------------------------------------------------------------------------
    ## start simulation event handler (click the button or from the drop down menu)
    #---------------------------------------------------------------------------
    def on_menu_operation_startsimulation(self, event):
        logger.info('Start the Evacuation Simulation...')
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
            # calcualte static potential matrix before simulation
            self.myLayoutBuilder.calculateStaticPotentialMatrix()

            self.injection_flag = False
            # check if we have injection points in current map
            if len(self.myLayoutBuilder.Injection_Dict.keys()) != 0:
                number_of_injection_points = math.ceil(self.config.INJECTION_UTILIZATION_RATE * len(self.myLayoutBuilder.Injection_Dict.keys()))
                self.picked_injections = random.sample(list(self.myLayoutBuilder.Injection_Dict.keys()), number_of_injection_points)
                self.injection_flag = True
                self.myLayoutBuilder.ppl_yet_to_be_injected = self.config.NUMBER_OF_PEDESTRIAN_INJECT
        else:
            logger.info('No active layout builder instance now, please load the layout file and try again')


        ## 5. intialize the time tick and kicf off the simulation
        ##    here we need a new thread to run the simulation and track the CPU time tick

        self.ticker = 0
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.refresh_complete = threading.Event()
        self.task_done_event = threading.Event()
        self.pause_event.set()   # start in the running state.
        self.refresh_complete.set() # initially set to allow the first updates.

        # Initialize scheduler
        self.scheduler = BackgroundScheduler(job_defaults={
            'coalesce': True,
            'misfire_grace_time': 3600  # 1 hour grace time
        })
        self.start_time = datetime.datetime.now()

        # Schedule a job that triggers every simulation time interval
        self.scheduler.add_job(self.simulation_main,
                            'interval',
                            seconds=self.config.SIMULATION_TIME_INTERVAL,
                            id='simulation_main',
                            args=[self.start_time],
                            max_instances=1)
        self.scheduler.start()

        # initialize the daemon
        self.daemon_thread = threading.Thread(target=self.daemon_controller, daemon=True)
        self.daemon_thread.start()

        # disable the start simulation button from menu bar and toolbar
        self.menubar.Menus[1][0].MenuItems[0].Enable(False)
        self.frame_toolbar.GetToolByPos(2).Enable(False) # start button
        self.frame_toolbar.GetToolByPos(5).Enable(False) # reset button

        # Enable the pause/stop button from toolbar
        self.frame_toolbar.GetToolByPos(3).Enable(True)  #pause/resume
        self.frame_toolbar.GetToolByPos(4).Enable(True)  #stop
        self.frame_toolbar.Realize()

        # Enable the pause/stop button from menu
        self.menubar.Menus[1][0].MenuItems[1].Enable(True) #pause/resume
        self.menubar.Menus[1][0].MenuItems[2].Enable(True) #stop

    #---------------------------------------------------------------------------
    ## simulation main thread
    ## will do necessary calculation per each simulation ticker
    ## and adjust the exit choice when the counter % Tau == 0.
    ## during each ticker's run, will pause the daemon thread so counter will not
    ## increase. in this case, only completed task in each simulation step will
    ## increase the ticker.
    #---------------------------------------------------------------------------
    def simulation_main(self, start_time):
        ## 6. Exit choice model
        ##    on each defined time interval, calculate K(s)/V(s) and F(s,e)
        ##    K(s) = denote the pedestrian density of subarea s
        ##    V(s) = denote the average movement speed of the pedestrians of subarea s
        ##    F(s,e) = e denote the potential of subarea s ∈ S with respect to exit e ∈ E

        self.pause_event.wait()  # Wait if paused
        if self.stop_event.is_set():
            return
        self.refresh_complete.wait() # Wait for the paint event to complete
        self.refresh_complete.clear() # Clear the event to block further updates

        if self.ticker % self.config.SIMULATION_CYCLE == 0:
            logger.info(f" Exit Choice Model job for Ticker {str(self.ticker)} started at {str(datetime.datetime.now())}")
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
            logger.info(f" Exit Choice Model job finished for Ticker {str(self.ticker)} at {str(datetime.datetime.now())}")

        ## Pedestrian movement model
        logger.info(f" Pedestrian movement Model job for Ticker : {str(self.ticker)} started at {str(datetime.datetime.now())})")

        # clean up previous just injected cell's color indication flag
        for auto in self.myLayoutBuilder.AutomataList:
            if auto.just_injected_flag:
                auto.just_injected_flag = False

        # inject pedestrian
        if self.injection_flag:
        # if False:
            logger.info("Injecting Pedestrian...")
            self.injected_pedestrian += self.myLayoutBuilder.InjectPedestrian(self.picked_injections)

        # each pedestrian can move from current lattice site to the next adjacent lattice site
        # only in horizontal or vertical or diagonal direction when the adjacent lattice site is not occupied
        # or is not obstacle. in general, the pedestrian will selet an adjacent cell of smaller potential
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

        logger.info(f" Pedestrian movement Model job finished for Ticker {str(self.ticker)} at {str(datetime.datetime.now())}")

        self.ticker += 1 # Increase the ticker!

        # if screen_refresh_flag:
        #     wx.CallAfter(self.myLayoutBuilder.refreshScreen())
        # wx.CallAfter(self.test_refresh)
        # self.refresh_complete.clear()
        # self.layout_panel.Refresh()
        # self.layout_panel.Update()  # Force immediate redraw
        # update the time elapsed

        # wx.CallAfter(self.frame_statusbar.SetStatusText(f"Current Ticker: {str(self.ticker)}", 0))
        # wx.CallAfter(self.frame_statusbar.SetStatusText("Time Elapsed : " + str(datetime.datetime.now() - start_time) + " (s)", 3))
        # # wx.CallAfter((self.frame_statusbar.Refresh()))

        # self.refresh_complete.clear()
        remained_pedestrian = len(self.myLayoutBuilder.getPedestrianIndexArray())
        logger.info(f" Remained Pedestrian : {remained_pedestrian}")
        wx.CallAfter(self.update_canvas)
        wx.CallAfter(self.update_statusbar, start_time, remained_pedestrian, self.injected_pedestrian)
        # Signal that the task is done
        self.task_done_event.set()

    def update_statusbar(self, start_time, remained_pedestrian, injected_pedestrian):
        self.frame_statusbar.SetStatusText(f"Current Ticker: {str(self.ticker)}", 1)
        if self.stop_event.is_set():
            self.frame_statusbar.SetStatusText("Simuation Status : Stopped", 2)
        elif not self.pause_event.is_set():
            self.frame_statusbar.SetStatusText("Simuation Status : Paused", 2)
        else:
            self.frame_statusbar.SetStatusText("Simuation Status : Running", 2)
        self.frame_statusbar.SetStatusText(f"Number of Pedestrian in the map : {remained_pedestrian}", 3)
        self.frame_statusbar.SetStatusText(f"# of Pedestrian injected into the map : {injected_pedestrian}", 4)
        self.frame_statusbar.SetStatusText(f"Time Elapsed :  {str(datetime.datetime.now() - start_time)} (s)", 5)

    def update_canvas(self):
        self.layout_panel.Refresh()
        self.layout_panel.Update()

    #---------------------------------------------------------------------------
    ## daemon thread
    ## check global counter, use defined time clcye to increase the counter
    ## and exit when all pedestrian are out.
    #---------------------------------------------------------------------------
    def daemon_controller(self):
        while not self.stop_event.is_set():
            self.pause_event.wait()
            if self.stop_event.is_set():
                return
            logger.info(f"Current Simulation Ticker : {str(self.ticker)}")
            # wx.CallAfter(self.frame_statusbar.SetStatusText(f"Time Elapsed :  {str(datetime.datetime.now() - self.start_time)} (s)", 4))
            # self.frame_statusbar.SetStatusText(f"Time Elapsed :  {str(datetime.datetime.now() - self.start_time)} (s)", 4)
            time.sleep(self.config.SIMULATION_TIME_INTERVAL)  # Check every half second
            # Stop the scheduler when ticker reaches 60 for demonstration
            if self.myLayoutBuilder.isEvacuated():
                logger.info('All Pedestrian evacuated!!')
                wx.CallAfter(self.stop_scheduler)
                logger.info('Exit current simulation Task!!')
                # wx.CallAfter(self.sim_gui_menu_update())

        # # Below codes are ajusting the GUI
        # # when we shut down or exit the scheduler we will reenable the start simulation button
        # # from both menu bar and button
        # self.menubar.Menus[1][0].MenuItems[0].Enable(True)
        # self.frame_toolbar.GetToolByPos(2).Enable(True) # Start button
        # # Disable the pause/stop drop down from menu
        # self.menubar.Menus[1][0].MenuItems[1].Enable(False)
        # self.menubar.Menus[1][0].MenuItems[2].Enable(False)

        # # disable the pause/stop buttone again
        # self.frame_toolbar.GetToolByPos(3).Enable(False)  #pause/Resume
        # self.frame_toolbar.GetToolByPos(4).Enable(False)  #stop
        # # to display the change.
        # self.frame_toolbar.Realize()
        # # self.frame_statusbar.SetStatusText("Time Elapsed : 0.0(s) ", 1)

    def sim_gui_menu_update(self):
        # Below codes are ajusting the GUI
        # when we shut down or exit the scheduler we will reenable the start simulation button
        # from both menu bar and button
        self.menubar.Menus[1][0].MenuItems[0].Enable(True)
        self.frame_toolbar.GetToolByPos(2).Enable(True) # Start button
        self.frame_toolbar.GetToolByPos(5).Enable(True) # reset button
        # Disable the pause/stop drop down from menu
        self.menubar.Menus[1][0].MenuItems[1].Enable(False)
        self.menubar.Menus[1][0].MenuItems[2].Enable(False)

        # disable the pause/stop buttone again
        self.frame_toolbar.GetToolByPos(3).Enable(False)  #pause/Resume
        self.frame_toolbar.GetToolByPos(4).Enable(False)  #stop
        # to display the change.
        self.frame_toolbar.Realize()
        # self.frame_statusbar.SetStatusText("Time Elapsed : 0.0(s) ", 1)

    #---------------------------------------------------------------------------
    ## daemon thread call to stop the scheduler.
    #---------------------------------------------------------------------------
    def stop_scheduler(self):
        self.stop_event.set()
        logger.info(f"Stopped Current Simulation scheduler")
        # Only shut down if the scheduler is running
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
            self.frame_statusbar.SetStatusText("Simuation Status : Completed", 2)

    #---------------------------------------------------------------------------
    ##  event handle function to update the time elapse on status bar
    #---------------------------------------------------------------------------
    def update_time_elapse(self, event):
        elapsed = (datetime.datetime.now() - self.start_time).seconds
        self.frame_statusbar.SetStatusText(f"Time Elapsed: {elapsed}s", 5)
