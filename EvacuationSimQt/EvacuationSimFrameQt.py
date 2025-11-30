import time
import threading
import os
import numpy as np
import matplotlib as matplotlib
import logging
import LayoutBuilderQt as LayoutBuilderQt
import datetime as datetime
import constants
import math as math
import random
from types import SimpleNamespace
from logger_config import setup_logger
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout, QMessageBox, QFrame, QToolButton, QScrollArea, QPushButton, QColorDialog
from PySide6.QtWidgets import QLineEdit, QFormLayout, QSplitter, QLabel, QHBoxLayout, QToolBar, QStatusBar, QGraphicsView, QGraphicsScene, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QPixmap, QIcon, QAction, QColor, QBrush
from PySide6.QtCore import Qt, QPoint, QSize, QObject, Signal, QEventLoop, QTimer, QThread, QMetaObject,Slot

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
##  GUI related compoment
#---------------------------------------------------------------------------

GLOBAL_TICKER = 0

class EvacuationSimFrameQt(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.setGeometry(100, 100, 1000, 800)  # Initial size of the main window

        self.app = app
        self.setWindowTitle("Evacuation Simulator")
        self.sp = None
        self.layout_panel = None
        self.layout_panel_view = None
        self.configuration_panel = None
        self.frame_menubar = None
        self.frame_statusbar = None
        self.frame_toolbar = None
        self.myLayoutBuilder = None
        self.filepath = None                                # store the filepath of loaded excel file.

        self.configuration_dict = {}                        # configuration items dict
        self.config = None                                  # namespaces that store all configuration items

        self.color_button_list = {}                         # store the dict of all color buttons.
        self.color_text_ctrl_list = {}                      # store the dict of all color_text_ctrl
        self.color_preview_list = {}                        # store the dict of all color preview panel

        self.injected_pedestrian = 0                        # store how many pedestrian has been injected

        #Setup widgets
        self.InitializeComponents()

        # Scheduler setup
        self.scheduler = BackgroundScheduler(job_defaults={
            'coalesce': True,
            'misfire_grace_time': 3600  # 1 hour grace time
        })
        self.scheduler_lock = threading.Lock()  # To ensure the task completes before the next one starts
        self.job_paused = False
        self.start_time = None  # To track the start time of the simulation
        self.monitor_thread = Daemon_Controller(self.scheduler, self.config.SIMULATION_TIME_INTERVAL, self.myLayoutBuilder)
        self.monitor_thread.stop_signal.connect(self.on_scheduler_stopped_by_condition)

        # Timer to control the ticking
        self.ticker_timer = QTimer()
        self.ticker_timer.timeout.connect(self.increment_ticker)

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
        #                    |--configuration_base_panel (with Vboxlayout)
        #                    |            |--Button row (with HBox layout)
        #                    |            |     |- 2 buttons. (Apply, reset)
        #                    |            |--scroll_area
        #                    |                  |--configuration panel
        #                    |                       |-- QLabels (s)
        #                    |                       |-- QLineEdit   (s)
        #                                                   OR
        #                    |                       |-- color_QLineEdit(with color sizer)
        #                    |                                |-- QLineEdit (s)
        #                    |                                |-- Color Preview (s)
        #                    |                                |-- color Button (s)
        #                    |--layout_panel_view (QGraphicsView)
        #                            |-- layout_panel (QGraphicsScene)

        self.sp = QSplitter(Qt.Horizontal)
        # Create left panel
        configuration_base_panel = QWidget()
        configuration_base_panel_layout = QVBoxLayout()
        configuration_base_panel_layout.setContentsMargins(0, 0, 0, 0)
        configuration_base_panel.setLayout(configuration_base_panel_layout)

        # Add 2 buttons to left panel in a single row
        button_row = QHBoxLayout()
        apply_button = QPushButton("Apply Config")
        reset_button = QPushButton("Reset to Default")
        apply_button.clicked.connect(lambda: self.on_apply_config(configuration_colorflag_dict))
        reset_button.clicked.connect(self.on_reset_config)
        button_row.addWidget(apply_button)
        button_row.addWidget(reset_button)
        button_row.setContentsMargins(0, 0, 0, 0)
        # VBox layout first row is button row
        configuration_base_panel_layout.addLayout(button_row)

        ## Left side panel. Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Ensure it resizes to fit content
        # main configuration panel
        self.configuration_panel = QWidget()
        self.configuration_panel.setStyleSheet(f"background-color: #{self.config.LAYOUT_DISPLAY_EMPTY_SPACE};")
        scroll_area.setWidget(self.configuration_panel)
        # Create the configuration panel details
        configuration_panel_Layout = QFormLayout(self.configuration_panel)
        configuration_panel_Layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        configuration_panel_Layout.setContentsMargins(0, 0, 0, 0)

        # add normal configuration items
        for config_key, config_value in configuration_flag_dict.items():
            real_config_key = config_key.removesuffix("_CONFIG")
            real_config_value = self.configuration_dict[real_config_key]
            # left side label
            config_label = QLabel("%s :" % real_config_key.title())
            config_label.setObjectName(real_config_key)
            # right side text area
            lineEdit = QLineEdit()
            lineEdit.setObjectName(real_config_key)
            # Set the minimum width of the QLineEdit
            lineEdit.setMinimumWidth(150)  # Set the smallest width you want
            # Optionally set size policy to minimize horizontal stretch
            lineEdit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            lineEdit.setStyleSheet(f"background-color: #{self.config.LAYOUT_DISPLAY_EMPTY_SPACE};")
            lineEdit.setText(str(real_config_value))

            configuration_panel_Layout.addRow(config_label, lineEdit)

        # add color config items
        for config_key, config_value in configuration_colorflag_dict.items():
            real_config_key = config_key.removesuffix("_COLORCONFIG")
            real_config_value = self.configuration_dict[real_config_key]
            # left side label
            config_label = QLabel("%s :" % real_config_key.title())
            config_label.setObjectName(real_config_key)

            # right side text area
            lineEdit = QLineEdit()
            lineEdit.setObjectName(real_config_key)
            # Set the minimum width of the QLineEdit
            lineEdit.setMinimumWidth(150)  # Set the smallest width you want
            # for color config, will add below customized area:
            lineedit_layout = QHBoxLayout(lineEdit)
            lineedit_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to fit within the QLineEdit
            lineedit_layout.setSpacing(5)  # Add spacing between elements

            color_text_edit = QLineEdit()
            color_text_edit.setObjectName(real_config_key)
            color_text_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            color_text_edit.setStyleSheet(f"background-color: #{self.config.LAYOUT_DISPLAY_EMPTY_SPACE};")
            color_text_edit.setText("#" + str(real_config_value))
            lineedit_layout.addWidget(color_text_edit)
            color_text_edit.textChanged.connect(self.on_hex_input)
            self.color_text_ctrl_list[real_config_key] = color_text_edit
            # Panel for color preview
            color_preview = QFrame()
            color_preview.setObjectName(real_config_key)
            color_preview.setFixedSize(16, 16)
            color_preview.setFrameShape(QFrame.Box)
            color_preview.setStyleSheet(f"background-color: #{str(real_config_value)}")  # Default color preview
            lineedit_layout.addWidget(color_preview)
            self.color_preview_list[real_config_key] = color_preview
            # Image button for color picker
            color_picker_button = QToolButton()
            color_picker_button.setObjectName(real_config_key)
            color_picker_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-color-picker-67.png")))
            color_picker_button.setFixedSize(16, 16)
            lineedit_layout.addWidget(color_picker_button)
            color_picker_button.clicked.connect(self.on_pick_color)
            self.color_button_list[real_config_key] = color_picker_button

            # add current Label and line edit into the layout
            configuration_panel_Layout.addRow(config_label, lineEdit)
        # VBox layout bottom section is the scroll area
        configuration_base_panel_layout.addWidget(scroll_area)

        ## right side panel
        self.layout_panel = QGraphicsScene()
        self.layout_panel.setBackgroundBrush(QBrush(QColor(f"#{self.config.LAYOUT_DISPLAY_EMPTY_SPACE}")))
        self.layout_panel_view = QGraphicsView(self.layout_panel)
        self.layout_panel_view.setRenderHint(QPainter.Antialiasing)
        # Ensure the view starts at the top-left corner
        self.layout_panel_view.centerOn(0, 0)
        self.layout_panel_view.horizontalScrollBar().setValue(0)
        self.layout_panel_view.verticalScrollBar().setValue(0)

        # Add widgets to the splitter
        self.sp.addWidget(configuration_base_panel)
        self.sp.addWidget(self.layout_panel_view)
        desired_left_size = configuration_base_panel.sizeHint().width() + 30 # add 30 buffer here.
        self.sp.setSizes([desired_left_size, self.size().width() - desired_left_size])
        self.sp.setStretchFactor(0, 0)  # Fixed width for the left side
        self.sp.setStretchFactor(1, 1)  # Right side will stretch

        # Set the splitter as the central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.sp)
        self.setCentralWidget(container)

        ## Menu bar
        self.frame_menubar = self.menuBar()
        file_menu = self.frame_menubar.addMenu("File")
        operation_menu = self.frame_menubar.addMenu("Operation")
        help_menu = self.frame_menubar.addMenu("Help")

        ## all menu actions
        self.load_file_layout_action = QAction("Load Floor Layout File", self)
        self.save_animation_action = QAction("Save Animation", self)
        self.start_simulation_action = QAction("Start Simulation", self)
        self.pause_resume_simulation_action = QAction("Pause/Resume Simulation", self)
        self.stop_simulation_action = QAction("Stop Simulation", self)
        self.reset_simulation_action = QAction("Reset Simulation", self)
        self.about_action = QAction("About", self)
        self.exit_action = QAction("Exit", self)

        ## add all actions into each menu
        file_menu.addAction(self.load_file_layout_action)
        file_menu.addAction(self.save_animation_action)
        file_menu.addAction(self.exit_action)
        operation_menu.addAction(self.start_simulation_action)
        operation_menu.addAction(self.pause_resume_simulation_action)
        operation_menu.addAction(self.stop_simulation_action)
        operation_menu.addAction(self.reset_simulation_action)
        help_menu.addAction(self.about_action)

        ## associate the event with the actions
        self.load_file_layout_action.triggered.connect(self.on_menu_file_loadLayout)
        self.save_animation_action.triggered.connect(self.on_menu_file_saveAnimation)
        self.exit_action.triggered.connect(self.on_menu_file_exit)
        self.start_simulation_action.triggered.connect(self.on_menu_operation_startsimulation)
        self.pause_resume_simulation_action.triggered.connect(self.on_menu_operation_pause_resume_simuation)
        self.stop_simulation_action.triggered.connect(self.on_menu_operation_stopsimulation)
        self.about_action.triggered.connect(self.on_menu_help_about)
        self.reset_simulation_action.triggered.connect(self.on_menu_operation_reset)

        ## add Toolbax bar
        self.frame_toolbar = QToolBar("Simulation Toolbar", self)
        self.addToolBar(self.frame_toolbar)
        self.frame_toolbar.setIconSize(QSize(32, 32))
        self.frame_toolbar.setStyleSheet("""
            QToolBar {
                padding: 2px;  /* Adjust padding to fit the icons properly */
            }
            QToolButton {
                border: 2px solid #8f8f91;
                border-radius: 4px;
                background-color: #f0f0f0;
                padding: 2px;  /* Adjust padding to make it fit */
                margin: 2px;
            }
            QToolButton:pressed {
                border-style: inset;
            }
        """)

        ## all toolbar action
        self.load_file_layout_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-open-file-48.png")),
                                                                    "Load Floor Layout File", self)
        self.save_animation_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-save-50.png")),
                                                                    "Save Animation", self)
        self.exit_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-exit-64.png")),
                                                                    "Exit", self)
        self.start_simulation_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-play-48.png")),
                                                                    "Start Simulation", self)
        self.pause_resume_simulation_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-pause-64.png")),
                                                                    "Pause/Resume Simulation", self)
        self.stop_simulation_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-stop-64.png")),
                                                                    "Stop Simulation", self)
        self.about_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "icons8-about-64.png")),
                                                                    "About", self)
        self.reset_toolbar_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                    "bitmaps",
                                                                    "reset.png")),
                                                                    "Reset", self)

        ## toolbar action tooltips
        self.load_file_layout_toolbar_action.setToolTip("Load Floor Layout File")
        self.save_animation_toolbar_action.setToolTip("Save Animation")
        self.exit_toolbar_action.setToolTip("Exit")
        self.start_simulation_toolbar_action.setToolTip("Start Simulation")
        self.pause_resume_simulation_toolbar_action.setToolTip("Pause/Resume Simulation")
        self.stop_simulation_toolbar_action.setToolTip("Stop Simulation")
        self.reset_toolbar_action.setToolTip("Reset Simulation")
        self.about_toolbar_action.setToolTip("About")

        self.frame_toolbar.addAction(self.load_file_layout_toolbar_action)
        self.frame_toolbar.addAction(self.save_animation_toolbar_action)
        self.frame_toolbar.addAction(self.start_simulation_toolbar_action)
        self.frame_toolbar.addAction(self.pause_resume_simulation_toolbar_action)
        self.frame_toolbar.addAction(self.stop_simulation_toolbar_action)
        self.frame_toolbar.addAction(self.reset_toolbar_action)
        # Add a stretchable spacer to push below 2 buttons to right aligned.
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.frame_toolbar.addWidget(spacer)
        self.frame_toolbar.addAction(self.about_toolbar_action)
        self.frame_toolbar.addAction(self.exit_toolbar_action)

        ## associate the event with the actions (Same actions for all menu item and toolbar items)
        self.load_file_layout_toolbar_action.triggered.connect(self.on_menu_file_loadLayout)
        self.save_animation_toolbar_action.triggered.connect(self.on_menu_file_saveAnimation)
        self.exit_toolbar_action.triggered.connect(self.on_menu_file_exit)
        self.start_simulation_toolbar_action.triggered.connect(self.on_menu_operation_startsimulation)
        self.pause_resume_simulation_toolbar_action.triggered.connect(self.on_menu_operation_pause_resume_simuation)
        self.stop_simulation_toolbar_action.triggered.connect(self.on_menu_operation_stopsimulation)
        self.reset_toolbar_action.triggered.connect(self.on_menu_operation_reset)
        self.about_toolbar_action.triggered.connect(self.on_menu_help_about)


        # default enable/disable status
        self.update_menu_and_toolbar_actions(loadEnabled=True,
                                             saveEnabled=False,
                                             startEnabled=False,
                                             pauseresumeEnabled=False,
                                             stopEnabled=False,
                                             resetEnabled=False,
                                             aboutEnabled=True,
                                             exitEnabled=True)

        ## Status Bar
        self.frame_statusbar = QStatusBar()
        self.setStatusBar(self.frame_statusbar)
        self.status_bar_ticker_label = QLabel("Current Ticker : 0")
        self.status_bar_status_label = QLabel("Simulation Status : Idle ")
        self.status_bar_number_of_pedestrian_label = QLabel("# of Pedestrian in the map : - ")
        self.status_bar_number_of_injected_pedestrian_label = QLabel("# of Pedestrian injected into the map : - ")
        self.status_bar_elapsed_time_label = QLabel("Time Elapsed : 00:00:00 (s)")

        # Set fixed height for labels
        self.status_bar_ticker_label.setFixedHeight(20)
        self.status_bar_ticker_label.setFixedWidth(150)
        self.status_bar_status_label.setFixedHeight(20)
        self.status_bar_status_label.setFixedWidth(160)
        self.status_bar_number_of_pedestrian_label.setFixedHeight(20)
        self.status_bar_number_of_pedestrian_label.setFixedWidth(220)
        self.status_bar_number_of_injected_pedestrian_label.setFixedHeight(20)
        self.status_bar_number_of_injected_pedestrian_label.setFixedWidth(230)
        self.status_bar_elapsed_time_label.setFixedHeight(20)
        self.status_bar_elapsed_time_label.setFixedWidth(180)

        self.frame_statusbar.addWidget(self.status_bar_ticker_label)                        # add to align left
        self.frame_statusbar.addWidget(self.status_bar_status_label)                        # add to align right
        self.frame_statusbar.addWidget(self.status_bar_number_of_pedestrian_label)          # add to align right
        self.frame_statusbar.addWidget(self.status_bar_number_of_injected_pedestrian_label) # add to align right
        self.frame_statusbar.addPermanentWidget(self.status_bar_elapsed_time_label)         # add to align right

    #---------------------------------------------------------------------------
    # update all menu & toobar actions status
    #---------------------------------------------------------------------------
    def update_menu_and_toolbar_actions(self,
                                        loadEnabled=True,
                                        saveEnabled=True,
                                        exitEnabled=True,
                                        startEnabled=False,
                                        pauseresumeEnabled=False,
                                        stopEnabled=False,
                                        resetEnabled=False,
                                        aboutEnabled=True):
        # menu bar status
        self.load_file_layout_action.setEnabled(loadEnabled)
        self.save_animation_action.setEnabled(saveEnabled)
        self.exit_action.setEnabled(exitEnabled)
        self.start_simulation_action.setEnabled(startEnabled)
        self.pause_resume_simulation_action.setEnabled(pauseresumeEnabled)
        self.stop_simulation_action.setEnabled(stopEnabled)
        self.reset_simulation_action.setEnabled(resetEnabled)
        self.about_action.setEnabled(aboutEnabled)

        # toolbar status
        self.load_file_layout_toolbar_action.setEnabled(loadEnabled)
        self.save_animation_toolbar_action.setEnabled(saveEnabled)
        self.exit_toolbar_action.setEnabled(exitEnabled)
        self.start_simulation_toolbar_action.setEnabled(startEnabled)
        self.pause_resume_simulation_toolbar_action.setEnabled(pauseresumeEnabled)
        self.stop_simulation_toolbar_action.setEnabled(stopEnabled)
        self.reset_toolbar_action.setEnabled(resetEnabled)
        self.about_toolbar_action.setEnabled(aboutEnabled)

    #---------------------------------------------------------------------------
    # update the statusbar information
    #---------------------------------------------------------------------------
    def update_statusbar_information(self, obj, index):
        #  ticker, status, number_of_pedestrian, time_elapsed
        if index == 0:
            if isinstance(obj, int):
                self.status_bar_ticker_label.setText(f"Current Ticker : {str(obj)}")
            else:
                logging.info("Status Bar update wrong for Current Ticker... skipped")
        elif index == 1:
            if isinstance(obj, str):
                self.status_bar_status_label.setText(f"Simulation Status : {obj}")
            else:
                logging.info("Status Bar update wrong for Simulation Status... skipped")
        elif index == 2:
            if isinstance(obj, int):
                self.status_bar_number_of_pedestrian_label.setText(f"# of Pedestrian in the map : {str(obj)}")
            else:
                logging.info("Status Bar update wrong for Number of Pedestrian in the map... skipped")
        elif index == 3:
            if isinstance(obj, int):
                self.status_bar_number_of_injected_pedestrian_label.setText(f"# of Pedestrian injected into the map : {str(obj)}")
            else:
                logging.info("Status Bar update wrong for Number of Pedestrian injected into the map... skipped")
        elif index == 4:
            if isinstance(obj, str):
                self.status_bar_elapsed_time_label.setText(f"Time Elapsed : {obj} (s)")
            else:
                logging.info("Status Bar update wrong for Time Elapsed... skipped")
        else:
            logging.info("Status Bar update out of index.  skipped")
            pass

    #---------------------------------------------------------------------------
    # event handle for pickup color.
    #---------------------------------------------------------------------------
    def on_pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            name = self.sender().objectName()
            self.color_text_ctrl_list[name].setText(color.name())
            self.color_preview_list[name].setStyleSheet(f"background-color: {color.name()}")

    #---------------------------------------------------------------------------
    # even handle for hex text change
    #---------------------------------------------------------------------------
    def on_hex_input(self):
        # Get the current text from the QLineEdit
        hex_value = self.sender().text().strip()

        # Validate the hex value and update the preview panel
        if self.is_valid_hex_color(hex_value):
            name = self.sender().objectName()
            self.color_preview_list[name].setStyleSheet(f"background-color: {hex_value}")

    #---------------------------------------------------------------------------
    # Check if the input is a valid hex color format (#RRGGBB or RRGGBB)
    #---------------------------------------------------------------------------
    def is_valid_hex_color(self, hex_value):
        if hex_value.startswith("#"):
            hex_value = hex_value[1:]
        return len(hex_value) == 6 and all(c in "0123456789ABCDEFabcdef" for c in hex_value)

    #---------------------------------------------------------------------------
    ##  event handle function when load file
    #---------------------------------------------------------------------------
    def on_menu_file_loadLayout(self, event):
        self.layout_panel.clear() # clear current layout

        file_path, _ = QFileDialog.getOpenFileName(self, "Open xlsx File", "", "All Files (*);;Excel Files (*.xlsx)")

        # Proceed loading the file chosen by the user
        self.filepath = file_path

        if file_path:
            try:
                #now we have the file path
                self.myLayoutBuilder = LayoutBuilderQt.LayoutBuilderQt(file_path, self.layout_panel, self.config)

                # read the layout file
                self.myLayoutBuilder.load_layout_file()

                # reset the current layout size based on the layout size
                adjusted_width = self.myLayoutBuilder.max_column * self.config.LAYOUT_CELL_SIZE + 100
                adjusted_height = self.myLayoutBuilder.max_row * self.config.LAYOUT_CELL_SIZE + 100
                self.layout_panel.setSceneRect(0, 0, adjusted_width, adjusted_height)
                # self.layout_panel_view.fitInView(self.layout_panel.sceneRect(), Qt.KeepAspectRatio)
                desired_left_size = self.configuration_panel.sizeHint().width() + 30 # add 30 buffer here.
                if desired_left_size + adjusted_width > self.width() or self.height() < adjusted_height:
                    self.setGeometry(100, 100, desired_left_size + adjusted_width + 50, adjusted_height + 50)
                    self.sp.setSizes([desired_left_size, adjusted_width])
                else:
                    self.sp.setSizes([desired_left_size, self.width() - desired_left_size ])


                # draw the lay out on scorlled panel & initialize the number of pedestrians
                self.myLayoutBuilder.construct_layoutMap(self.layout_panel)

                # We can enable the start simulation button.
                self.update_menu_and_toolbar_actions(startEnabled=True, saveEnabled=True)

            except IOError:
                logger.error("Cannot open file '%s'." % file_path)

    #---------------------------------------------------------------------------
    ##  below are event handler functions have not been implemented.
    #---------------------------------------------------------------------------
    def on_menu_file_saveAnimation(self, event):
        logger.info("Event handler for 'on_menu_file_saveAnimation' not implemented yet")

    #---------------------------------------------------------------------------
    ##  Exit the application cleanly, stopping all threads and the scheduler.
    #---------------------------------------------------------------------------
    def on_menu_file_exit(self, event):
        logger.info("Event handler for 'Exit'. Exit the application ")
        # Shut down the scheduler and stop the daemon thread

        if self.monitor_thread:
            if self.monitor_thread.isRunning():
                self.monitor_thread.stop()
                self.monitor_thread.wait()  # Ensure the thread finishes cleanly

        if self.scheduler:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)

        # Stop any timers
        if self.ticker_timer:
            if self.ticker_timer.isActive():
                self.ticker_timer.stop()

        # Close the application
        QApplication.instance().quit()

    #---------------------------------------------------------------------------
    ##  Increment the ticker and update the status bar.
    #---------------------------------------------------------------------------
    def increment_ticker(self):
        global GLOBAL_TICKER
        GLOBAL_TICKER += 1
        self.update_statusbar_information(GLOBAL_TICKER, 0)
        self.update_statusbar_information("Running", 1)

    #---------------------------------------------------------------------------
    ##  Same function to cover both menu operation and button pause/Resume
    #---------------------------------------------------------------------------
    def on_menu_operation_pause_resume_simuation(self):
        pause_icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps", "icons8-pause-64.png"))
        resume_icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)),"bitmaps", "iicons8-resume-button-50.png"))
        global GLOBAL_TICKER
        if self.job_paused:
            self.scheduler.resume_job('simulation_main')
            self.ticker_timer.start(self.config.SIMULATION_TIME_INTERVAL * 1000)
            logger.info(f"Current Simulation Job Paused at Ticker : {GLOBAL_TICKER}")
            # swap the pause/resume button to Pause image
            self.pause_resume_simulation_action.setIcon(pause_icon)
            self.update_menu_and_toolbar_actions(startEnabled=False, pauseresumeEnabled=True, stopEnabled=True, resetEnabled=False)
            self.update_statusbar_information("Running", 1)
        else:
            self.scheduler.pause_job('simulation_main')
            self.ticker_timer.stop()
            # swap the pause/resume button to resume image
            self.pause_resume_simulation_action.setIcon(resume_icon)
            logger.info(f"Current Simulation Job Resumed at Ticker : {GLOBAL_TICKER}")
            self.update_menu_and_toolbar_actions(startEnabled=False, pauseresumeEnabled=True, stopEnabled=True, resetEnabled=False)
            self.update_statusbar_information("Paused", 1)
        self.job_paused = not self.job_paused

    #---------------------------------------------------------------------------
    ##  Same function to cover both menu operation and button stop
    #---------------------------------------------------------------------------
    def on_menu_operation_stopsimulation(self, event):
        # # Shut down the scheduler and stop the daemon thread
        # if hasattr(self, 'simulation_main') and self.simulation_main is not None:
        #     if self.simulation_main.running:
        #         self.simulation_main.stop()
        # if hasattr(self, 'daemon_worker') and self.daemon_worker is not None:
        #     if self.daemon_worker.running:
        #         self.daemon_worker.stop()
        # if hasattr(self, 'scheduler') and self.scheduler is not None:
        #     self.scheduler.shutdown(wait=True)
        # if self.pause_event:
        #     self.pause_event.set()  # Ensure threads can exit if paused
        # if hasattr(self, 'daemon_thread') and self.daemon_thread.is_alive():
        #     self.daemon_thread.join()  # Wait for the daemon thread to finish
        # event.accept()
        if self.monitor_thread:
            if self.monitor_thread.isRunning():
                self.monitor_thread.stop()
                self.monitor_thread.wait()  # Ensure the thread finishes cleanly
        if self.scheduler:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)

        # Stop any timers
        if self.ticker_timer:
            if self.ticker_timer.isActive():
                self.ticker_timer.stop()

        self.update_menu_and_toolbar_actions(startEnabled=True, pauseresumeEnabled=False, stopEnabled=False, resetEnabled=True)
        self.update_statusbar_information("Stopped", 1)

    #---------------------------------------------------------------------------
    ##  help about dialog
    #---------------------------------------------------------------------------
    def on_menu_help_about(self, event):
        logger.info("Help Dialpg")
        # Create and display an "About" dialog
        about_dialog = QMessageBox(self)
        about_dialog.setWindowTitle("About")
        about_dialog.setText("Evacuation Simulator")
        about_dialog.setInformativeText("Version 1.0\nAuthor: Pengfei Zhao & Zening Zhao")
        about_dialog.setStandardButtons(QMessageBox.Ok)
        about_dialog.setIcon(QMessageBox.Information)
        about_dialog.exec()

    #---------------------------------------------------------------------------
    ##  apply current constants settings into the constants instance
    #---------------------------------------------------------------------------
    def on_apply_config(self, configuration_colorflag_dict):
        # read all values from the Text Ctrl field.
        # compare it with existing configuration_dict.
        # needs to do some basic data type check.
        error_list = {}
        for child in self.configuration_panel.children():
            # check all line edit area in current configuration dict (in this case will exclude the color ones)
            if isinstance(child, QLineEdit) and child.objectName() + "_COLORCONFIG" not in configuration_colorflag_dict.keys():
                if child.text() != str(self.configuration_dict[child.objectName()]):
                    try:
                        # assign the GUI value to the self.configuration dict
                        self.configuration_dict[child.objectName()] = self.convert_to_number(child.text())
                    except ConversionError as e:
                        error_list[child.objectName()] = f"Cannot assign properly value for : {child.objectName()}, reset to default value : {str(self.configuration_dict[child.objectName()])}"
                        child.setText(str(self.configuration_dict[child.objectName()]))

            # color control items
            if isinstance(child, QLineEdit) and child.objectName() + "_COLORCONFIG" in configuration_colorflag_dict.keys():
                for item in child.children():
                    if isinstance(item, QLineEdit):
                        real_lineEdit = item
                        break #Only one LineEdit here by design
                if real_lineEdit.text() != "#" + str(self.configuration_dict[real_lineEdit.objectName()]):
                    try:
                        self.configuration_dict[real_lineEdit.objectName()] = real_lineEdit.text()
                    except ConversionError as e:
                        error_list[real_lineEdit.objectName()] = f"Cannot assign properly value for : {real_lineEdit.objectName()}, reset to default value : {str(self.configuration_dict[real_lineEdit.objectName()])}"
                        real_lineEdit.setText(str(self.configuration_dict[child.real_lineEdit()]))

        if len(error_list) > 0:
            # Create an error message box
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Error")
            error_dialog.setText(str(error_list))
            error_dialog.setInformativeText("Please check your input and try again.")
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.setDefaultButton(QMessageBox.Ok)

            # Show the error dialog
            error_dialog.exec()

        # refresh the global config item
        self.config = SimpleNamespace(**self.configuration_dict)

        # repaint the layout
        self.reset_gui()

    #---------------------------------------------------------------------------
    ##  reset GUI to original. based on already loaded filepath.
    ##  also will reset all other GUI components.
    #---------------------------------------------------------------------------
    def reset_gui(self):
        self.layout_panel.clear()
        try:
            #now we have the file path
            self.myLayoutBuilder = LayoutBuilderQt.LayoutBuilderQt(self.filepath, self.layout_panel, self.config)

            # read the layout file
            self.myLayoutBuilder.load_layout_file()

            # reset the current layout size based on the layout size
            adjusted_width = self.myLayoutBuilder.max_column * self.config.LAYOUT_CELL_SIZE + 100
            adjusted_height = self.myLayoutBuilder.max_row * self.config.LAYOUT_CELL_SIZE + 100
            self.layout_panel.setSceneRect(0, 0, adjusted_width, adjusted_height)
            # self.layout_panel_view.fitInView(self.layout_panel.sceneRect(), Qt.KeepAspectRatio)
            desired_left_size = self.configuration_panel.sizeHint().width() + 30 # add 30 buffer here.
            if desired_left_size + adjusted_width > self.width() or self.height() < adjusted_height:
                self.setGeometry(100, 100, desired_left_size + adjusted_width + 50, adjusted_height + 50)
                self.sp.setSizes([desired_left_size, adjusted_width])
            else:
                self.sp.setSizes([desired_left_size, self.width() - desired_left_size ])


            # draw the lay out on scorlled panel & initialize the number of pedestrians
            self.myLayoutBuilder.construct_layoutMap(self.layout_panel)

        except IOError:
            logger.error("Cannot open file '%s'." % self.filepath)

        self.injected_pedestrian = 0

        self.update_menu_and_toolbar_actions(startEnabled=True, pauseresumeEnabled=False, stopEnabled=False, resetEnabled=False)
        self.update_statusbar_information(0, 0)
        self.update_statusbar_information("Reset", 1)
        self.update_statusbar_information(0, 2)
        self.update_statusbar_information(0, 3)
        self.update_statusbar_information("00:00:00", 4)

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
        for child in self.configuration_panel.children():
            if isinstance(child, QLineEdit) and child.objectName() + "_COLORCONFIG" not in configuration_colorflag_dict.keys():
                if child.text() != str(self.configuration_dict[child.objectName()]):
                    child.setText(str(self.configuration_dict[child.objectName()]))
            if isinstance(child, QLineEdit) and child.objectName() + "_COLORCONFIG" in configuration_colorflag_dict.keys():
                # color control item
                for item in child.children():
                    if isinstance(item, QLineEdit):
                        real_lineEdit = item
                        break #Only one LineEdit here by design
                if real_lineEdit.text() != "#" + str(self.configuration_dict[real_lineEdit.objectName()]):
                    real_lineEdit.setText("#" + str(self.configuration_dict[real_lineEdit.objectName()]))

        # convert the configuration dict to a namespace so all attribute can
        # be accessed through "." operation, for example self.config.LAYOUT_CELL_SIZE
        # instead of doing self.config.LAYOUT_CELL_SIZE
        self.config = SimpleNamespace(**self.configuration_dict)

        self.reset_gui()

    #---------------------------------------------------------------------------
    ##  reset the simulation
    #---------------------------------------------------------------------------
    def on_menu_operation_reset(self, event):
        logger.info("Simulation reset. Ready to re-rerun.")
        # Clear the canvas and reset the ticker
        self.layout_panel.clear()
        global GLOBAL_TICKER
        GLOBAL_TICKER = 0
        self.start_time = None
        self.job_paused = False

        # Create a new scheduler instance
        self.scheduler = BackgroundScheduler(job_defaults={
            'coalesce': True,
            'misfire_grace_time': 3600  # 1 hour grace time
        })
        self.monitor_thread.set_scheduler(self.scheduler)
        self.update_menu_and_toolbar_actions(startEnabled=True, pauseresumeEnabled=False, stopEnabled=False, resetEnabled=False)
        self.update_statusbar_information(0, 0)
        self.update_statusbar_information("Reset", 1)
        self.update_statusbar_information(0, 2)
        self.update_statusbar_information(0, 3)
        self.update_statusbar_information("00:00:00", 4)

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
            logger.info('calculating Static Potential Matrix...Completed')

            # self.injection_flag = False
            # # check if we have injection points in current map
            # if len(self.myLayoutBuilder.Injection_Dict.keys()) != 0:
            #     number_of_injection_points = math.ceil(self.config.INJECTION_UTILIZATION_RATE * len(self.myLayoutBuilder.Injection_Dict.keys()))
            #     self.picked_injections = random.sample(list(self.myLayoutBuilder.Injection_Dict.keys()), number_of_injection_points)
            #     self.injection_flag = True
            #     self.myLayoutBuilder.ppl_yet_to_be_injected = self.config.NUMBER_OF_PEDESTRIAN_INJECT

        else:
            logger.info('No active layout builder instance now, please load the layout file and try again')

        ## 5. intialize the time tick and kicf off the simulation
        ##    here we need a new thread to run the simulation and track the CPU time tick

        # reset the ticker to 0
        global GLOBAL_TICKER
        GLOBAL_TICKER = 0

        # Schedule a job that triggers every simulation time interval
        self.scheduler.add_job(self.simulation_task,
                            'interval',
                            seconds=self.config.SIMULATION_TIME_INTERVAL,
                            id='simulation_main',
                            max_instances=1)


        if not self.scheduler.running:
            self.start_time = datetime.datetime.now()  # Record the start time
            # Start scheduler, ticker and monitor thread
            self.scheduler.start()
            # self.ticker_timer.start(self.config.SIMULATION_TIME_INTERVAL * 1000)  # setup interval and start the ticker counting
            self.monitor_thread.start()
            self.update_menu_and_toolbar_actions(startEnabled=False, pauseresumeEnabled=True, stopEnabled=True, resetEnabled=False)
            self.update_statusbar_information("Running", 1)

    #---------------------------------------------------------------------------
    ## Main Simulation Logic
    #---------------------------------------------------------------------------
    @Slot()
    def simulation_task(self):
        global GLOBAL_TICKER
        GLOBAL_TICKER += 1
        self.update_statusbar_information(GLOBAL_TICKER, 0)
        with self.scheduler_lock:  # Ensure this job completes before the next one starts
            logger.info(f"simulation_task started for ticker : {GLOBAL_TICKER}")

            if GLOBAL_TICKER % self.config.SIMULATION_CYCLE == 0 and GLOBAL_TICKER !=0 :
                ## 6. Exit choice model
                ##    on each defined time interval, calculate K(s)/V(s) and F(s,e)
                ##    K(s) = denote the pedestrian density of subarea s
                ##    V(s) = denote the average movement speed of the pedestrians of subarea s
                ##    F(s,e) = e denote the potential of subarea s ? S with respect to exit e ? E
                logger.info(f" Exit Choice Model job for Ticker {GLOBAL_TICKER} started at {str(datetime.datetime.now())}")
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
                # e = arg min F (s,x) for all x ? E
                # in above case, the temp assigned exit will be 2. since Exit 2 = 1588 is the minimal potential here.

                # For each subarea s ? S, if the temporary assigned exit e is different from the optimal exit
                # e0 in the last time step, the potential F(s,e), which corresponding to the temporary assigned
                # exit should be compared with the potential F(s,e0) , which corresponding to the optimal exit
                # in the last time step. If F(s,e0) - F(s,e) > ?, the temporary assigned exit is set as the
                # destination for all evacuees in this subarea; otherwise they keep to the exit e0.
                self.myLayoutBuilder.assignExitForEvacuationZone()

                logger.info(f" Exit Choice Model job finished for Ticker {GLOBAL_TICKER} at {str(datetime.datetime.now())}")
            else:
                logger.info(f" Pedestrian movement Model job started for Ticker : {GLOBAL_TICKER} at {str(datetime.datetime.now())})")
                # each pedestrian can move from current lattice site to the next adjacent lattice site
                # only in horizontal or vertical or diagonal direction when the adjacent lattice site is not occupied
                # or is obstacle. in general, the pedestrian will selet an adjacent cell of smaller potential
                # with a larger probability.

                # Calculate O(i,j) and fe(i, j) and then update the pedestrian's postiion
                # based on the transition probability as follows:

                # P(i0,j0)?P(i,j) = exp(-ef(e(i,j))a(i,j) / S(i,j) exp(-ef(e(i,j))a(i,j)

                # e (= 0) is a sensitivity parameter scaling the effects of the potential on the transition
                # probability.
                # a(i,j) is a binary parameter representing whether a pedestrian can move to the lattice
                # site (i, j). It is 1 if the neighboring lattice site is empty and 0 otherwise.

                # The potential of each lattice site is used to reflect the total effects of the dynamic
                # potential and the static potential of each lattice site. Therefore, the potential f(e(i,j))
                # can be expressed as follows:

                # f(e(i,j)) = do(i,j)/n(i,j) + ?(l(e(i,j)) - l(e(i0,j0))

                # o(i,j) denotes the number of lattice sites which are occupied by obstacles or pedestrians
                # among the neighboring lattice sites of lattice site (i, j).

                # n(i,j) denotes the total number of neighboring lattice sites of lattice site (i, j).

                # d (= 0) is a parameter scaling the impacts of the repulsive force among the congested
                # crowds on the potential.

                #l(e(i0,j0)) and l(e(i,j)) denote the feasible distance from current lattice site (i0, j0)
                # and neighboring lattice site (i, j) to exit e respectively. all cell's feasible distance
                # with respect of each exit e have been calculated before the simulation.
                # Call calculateStaticPotentialMatrix to get this.

                # ? (= 0) is a parameter scaling the impacts of the route distance from the lattice site to the exit.

                # Calculate o(i,j)/n(i,j) through calculatePedCongestion function.
                self.myLayoutBuilder.calculatePedCongestion()

                # randomly choose from current occupied Automata celluar site and loop for each cell for each clock tick
                # 1. get current index into a arary from the AutomataList. the cell automata should still be in this facility
                # 2. loop through all item from this array index ramdomly and follow above algothrithm
                current_idx_array = self.myLayoutBuilder.getPedestrianIndexArray()
                shuffled_idx_array = np.copy(current_idx_array) # to preserve the original idx array?
                np.random.shuffle(shuffled_idx_array)

                # self.myLayoutBuilder.calculateTransitionProbability(shuffled_idx_array)

                logger.info(f" Pedestrian movement Model job finished for Ticker {GLOBAL_TICKER} at {str(datetime.datetime.now())}")

            endtime = datetime.datetime.now()
            logger.info(f"simulation_task completed for ticker : {GLOBAL_TICKER}")
            self.update_statusbar_information(str(endtime-self.start_time), 4)

        # Paint the current layout status.

    #---------------------------------------------------------------------------
    #  Handle how to stop the scheduler when stop condition has been fulfilled.
    #---------------------------------------------------------------------------
    @Slot()
    def on_scheduler_stopped_by_condition(self):
        self.stop_scheduler()  # Stop the scheduler and update UI
        self.update_statusbar_information("Stopped", 1)
        self.update_menu_and_toolbar_actions(startEnabled=True, pauseresumeEnabled=False, stopEnabled=False, resetEnabled=True)

    #---------------------------------------------------------------------------
    #  stop the scheduler
    #---------------------------------------------------------------------------
    def stop_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.ticker_timer.stop()
            self.monitor_thread.stop()
            global GLOBAL_TICKER
            GLOBAL_TICKER = 0
            self.update_statusbar_information("Stopped", 1)
            self.update_menu_and_toolbar_actions(startEnabled=True, pauseresumeEnabled=False, stopEnabled=False, resetEnabled=True)

#---------------------------------------------------------------------------
## daemon class
## check global counter, use defined time clcye to increase the counter
## and exit when all pedestrian are out.
#---------------------------------------------------------------------------
class Daemon_Controller(QThread):
    stop_signal = Signal()  # Signal to indicate that the monitoring condition has been met

    def __init__(self, scheduler, SIMULATION_TIME_INTERVAL, myLayoutBuilder):
        super().__init__()
        self.scheduler = scheduler
        self.running = True
        self.SIMULATION_TIME_INTERVAL = SIMULATION_TIME_INTERVAL
        self.myLayoutBuilder = myLayoutBuilder

    def run(self):
        while self.running:
            global GLOBAL_TICKER
            logger.info(f"Current Simulation Ticker is : {str(GLOBAL_TICKER)}")
            if self.scheduler.get_jobs() == [] or self.check_condition_to_stop():
                self.stop_signal.emit()
                logger.info('All Pedestrian evacuated!!')
                self.stop_scheduler()
                logger.info('Exit current simulation Task!!')
                self.running = False
            time.sleep(self.SIMULATION_TIME_INTERVAL)  # Check status in every clock tick

    def check_condition_to_stop(self):
        """Condition to stop the scheduler. Customize this as needed."""
        return False  # Replace with actual condition logic

    def stop_scheduler(self):
        """Stop the scheduler when a condition is met."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

    def stop(self):
        self.running = False

    def set_scheduler(self, scheduler):
        self.scheduler = scheduler
