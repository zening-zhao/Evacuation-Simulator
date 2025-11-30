import wx
import threading
import time
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

class Shape:
    def __init__(self, rect, color):
        self.rect = rect
        self.color = color

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxPython GUI", size=(800, 600))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Splitter
        self.splitter = wx.SplitterWindow(self.panel)

        # Left panel for configuration items
        self.config_panel = wx.Panel(self.splitter)
        self.config_sizer = wx.BoxSizer(wx.VERTICAL)
        self.config_panel.SetSizer(self.config_sizer)

        self.config_sizer.Add(wx.StaticText(self.config_panel, label="Config Item 1:"), 0, wx.ALL, 5)
        self.config_sizer.Add(wx.TextCtrl(self.config_panel), 0, wx.EXPAND | wx.ALL, 5)
        self.config_sizer.Add(wx.StaticText(self.config_panel, label="Config Item 2:"), 0, wx.ALL, 5)
        self.config_sizer.Add(wx.TextCtrl(self.config_panel), 0, wx.EXPAND | wx.ALL, 5)
        self.config_sizer.Add(wx.StaticText(self.config_panel, label="Config Item 3:"), 0, wx.ALL, 5)
        self.config_sizer.Add(wx.TextCtrl(self.config_panel), 0, wx.EXPAND | wx.ALL, 5)

        # Right panel for canvas with scrollbars
        self.canvas_panel = wx.ScrolledWindow(self.splitter, style=wx.HSCROLL | wx.VSCROLL)
        self.canvas_panel.SetScrollRate(20, 20)
        self.canvas_panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.shapes = []

        self.splitter.SplitVertically(self.config_panel, self.canvas_panel)
        self.splitter.SetSashGravity(0.3)

        self.sizer.Add(self.splitter, 1, wx.EXPAND)
        self.panel.SetSizer(self.sizer)

        # Menu bar
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "Exit")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        # Toolbar
        toolbar = self.CreateToolBar()
        start_tool = toolbar.AddTool(wx.ID_ANY, "Start", wx.Bitmap(16, 16))
        pause_tool = toolbar.AddTool(wx.ID_ANY, "Pause", wx.Bitmap(16, 16))
        toolbar.Realize()

        self.Bind(wx.EVT_TOOL, self.on_start, start_tool)
        self.Bind(wx.EVT_TOOL, self.on_pause, pause_tool)

        # Status bar
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-1, -2])
        self.status_bar.SetStatusText("Ticker: 0", 0)
        self.status_bar.SetStatusText("Time Elapsed: 0s", 1)

        # Timer for updating time elapsed
        self.start_time = datetime.now()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_time, self.timer)
        self.timer.Start(1000)

        # Initialize variables
        self.ticker = 0
        self.lock = threading.Lock()
        self.task_event = threading.Event()
        self.pause_event = threading.Event()
        self.shutdown_event = threading.Event()

        self.pause_event.set()

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
    def on_start(self, event):
        if not hasattr(self, 'worker'):
            self.worker = threading.Thread(target=self.run_worker)
            self.worker.start()

        if not hasattr(self, 'scheduler'):
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(self.task_event.set, 'interval', seconds=1)
            self.scheduler.start()

        if not hasattr(self, 'daemon_worker'):
            self.daemon_worker = threading.Thread(target=self.run_daemon)
            self.daemon_worker.start()

    def on_pause(self, event):
        if self.pause_event.is_set():
            self.pause_event.clear()
        else:
            self.pause_event.set()

    def run_worker(self):
        while not self.shutdown_event.is_set():
            self.task_event.wait()
            self.pause_event.wait()
            with self.lock:
                current_ticker = self.ticker
            wx.CallAfter(self.status_bar.SetStatusText, f"Ticker: {current_ticker}", 0)
            if current_ticker % 12 == 0:
                self.special_task()
            else:
                x, y, w, h = random.randint(0, 800), random.randint(0, 800), random.randint(20, 50), random.randint(20, 50)
                shape = Shape((x, y, w, h), wx.Colour(0, 0, 255))
                wx.CallAfter(self.add_shape, shape)
            self.task_event.clear()
            time.sleep(1)

    def run_daemon(self):
        while not self.shutdown_event.is_set():
            with self.lock:
                self.ticker += 1
            time.sleep(1)

    def special_task(self):
        shape = Shape((random.randint(0, 800), random.randint(0, 800), random.randint(20, 50), random.randint(20, 50)), wx.Colour(255, 0, 0))
        wx.CallAfter(self.add_shape, shape)

    def add_shape(self, shape):
        self.shapes.append(shape)
        self.update_virtual_size()
        self.canvas_panel.Refresh()

    def update_virtual_size(self):
        max_x = max((shape.rect[0] + shape.rect[2] for shape in self.shapes), default=0)
        max_y = max((shape.rect[1] + shape.rect[3] for shape in self.shapes), default=0)
        self.canvas_panel.SetVirtualSize((max_x, max_y))

    def update_time(self, event):
        elapsed = (datetime.now() - self.start_time).seconds
        self.status_bar.SetStatusText(f"Time Elapsed: {elapsed}s", 1)

    def on_paint(self, event):
        dc = wx.PaintDC(self.canvas_panel)
        self.canvas_panel.DoPrepareDC(dc)
        dc.Clear()
        for shape in self.shapes:
            dc.SetBrush(wx.Brush(shape.color))
            dc.DrawRectangle(*shape.rect)

    def on_close(self, event):
        self.shutdown_event.set()
        if hasattr(self, 'scheduler') and self.scheduler.running:
            self.scheduler.shutdown(wait=False)  # Ensure scheduler is shut down
        if hasattr(self, 'worker') and self.worker.is_alive():
            self.worker.join(timeout=1)  # Use timeout to avoid blocking
        if hasattr(self, 'daemon_worker') and self.daemon_worker.is_alive():
            self.daemon_worker.join(timeout=1)  # Use timeout to avoid blocking
        self.Destroy()

app = wx.App(False)
frame = MainFrame()
frame.Show()
app.MainLoop()
