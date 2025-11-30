import wx
import random
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread, Event
import time

class DrawPanel(wx.ScrolledWindow):
    """ Scrollable panel for drawing shapes with refresh synchronization. """
    def __init__(self, *args, **kw):
        super(DrawPanel, self).__init__(*args, **kw)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
        self.shapes = []  # Store shapes for persistent drawing
        self.refresh_complete = Event()  # Event to synchronize refresh completion

        # Initial virtual size larger than the visible area for scrolling
        self.default_virtual_width = 1000
        self.default_virtual_height = 1000
        self.SetVirtualSize((self.default_virtual_width, self.default_virtual_height))
        self.SetScrollRate(20, 20)  # Scroll step size

        self.Bind(wx.EVT_PAINT, self.on_paint)

    def add_shape(self, special=False):
        """ Adds a shape and triggers repaint. """
        pos = (random.randint(10, 980), random.randint(10, 980))
        color = wx.Colour(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        size = (random.randint(20, 50), random.randint(20, 50))
        shape_type = 'special' if special else 'normal'

        self.shapes.append((pos, size, color, shape_type))
        self.update_virtual_size()  # Adjust virtual size based on shapes
        self.refresh_complete.clear()  # Clear event before starting refresh
        self.Refresh()
        self.Update()  # Force immediate redraw

    def clear_shapes(self):
        """ Clears all shapes from the canvas and refreshes it. """
        self.shapes.clear()
        self.update_virtual_size()  # Reset virtual size
        self.refresh_complete.clear()  # Clear event before starting refresh
        self.Refresh()
        self.Update()  # Force immediate redraw

    def update_virtual_size(self):
        """ Updates the virtual size to fit all shapes while keeping scrollbars enabled. """
        max_x = max((pos[0] + size[0] for pos, size, _, _ in self.shapes), default=0)
        max_y = max((pos[1] + size[1] for pos, size, _, _ in self.shapes), default=0)
        new_virtual_width = max(self.default_virtual_width, max_x + 100)
        new_virtual_height = max(self.default_virtual_height, max_y + 100)
        self.SetVirtualSize((new_virtual_width, new_virtual_height))

    def on_paint(self, event):
        """ Draw shapes on the canvas and signal refresh completion. """
        dc = wx.BufferedPaintDC(self)  # Use buffered DC for double buffering
        self.PrepareDC(dc)
        dc.Clear()  # Clear the background

        for pos, size, color, shape_type in self.shapes:
            dc.SetBrush(wx.Brush(color))
            if shape_type == 'special':
                dc.DrawCircle(pos[0], pos[1], size[0] // 2)
            else:
                dc.DrawRectangle(pos[0], pos[1], size[0], size[1])

        self.refresh_complete.set()  # Signal that refresh is complete

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        self.init_ui()
        
        # Initialize scheduler, stop event, and pause event
        self.scheduler = BackgroundScheduler()
        self.ticker_count = 0
        self.stop_event = Event()
        self.pause_event = Event()

        # Initialize daemon thread
        self.daemon_thread = Thread(target=self.monitor_ticker, daemon=True)
        self.daemon_thread.start()

    def init_ui(self):
        # Menu Bar and Status Bar
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, 'Quit\tCtrl+Q')
        menubar.Append(file_menu, '&File')
        self.SetMenuBar(menubar)

        self.CreateStatusBar()
        self.SetStatusText("Ready")

        # Toolbar with buttons for control
        toolbar = self.CreateToolBar()
        self.pause_btn = toolbar.AddTool(wx.ID_ANY, "Pause", wx.Bitmap(16, 16))
        self.stop_btn = toolbar.AddTool(wx.ID_ANY, "Stop", wx.Bitmap(16, 16))
        toolbar.Realize()

        # Event Bindings for Toolbar Buttons
        self.Bind(wx.EVT_TOOL, self.on_pause_resume, self.pause_btn)
        self.Bind(wx.EVT_TOOL, self.on_stop, self.stop_btn)

        # Splitter Window
        splitter = wx.SplitterWindow(self)
        self.config_panel = wx.Panel(splitter)
        self.draw_panel = DrawPanel(splitter)
        self.draw_panel.Bind(wx.EVT_PAINT, self.draw_panel.on_paint)
        splitter.SplitVertically(self.config_panel, self.draw_panel)
        splitter.SetMinimumPaneSize(200)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def monitor_ticker(self):
        """ Daemon thread to monitor the ticker count and stop the scheduler if needed. """
        while not self.stop_event.is_set():
            self.pause_event.wait()  # Pauses daemon thread if pause_event is not set
            time.sleep(0.5)
            if self.ticker_count >= 60:
                wx.CallAfter(self.stop_scheduler)

    def start_scheduler(self):
        """ Starts the scheduler and schedules the main task. """
        self.scheduler.add_job(self.on_tick, 'interval', seconds=1)
        self.scheduler.start()

    def stop_scheduler(self):
        """ Stops the scheduler, resets ticker, and updates UI. """
        self.scheduler.shutdown(wait=False)
        self.scheduler = BackgroundScheduler()  # Reinitialize scheduler for a clean restart
        self.ticker_count = 0
        self.draw_panel.clear_shapes()
        self.SetStatusText("Scheduler stopped and reset")

    def on_tick(self):
        """ Scheduled task for drawing shapes on the canvas. """
        # Wait for the previous refresh to complete before incrementing the ticker
        self.draw_panel.refresh_complete.wait()
        self.ticker_count += 1
        wx.CallAfter(self.update_canvas)

    def update_canvas(self):
        """ Adds a shape to the canvas and updates the status bar. """
        special = self.ticker_count % 12 == 0
        self.draw_panel.add_shape(special=special)
        self.SetStatusText(f"Tick count: {self.ticker_count}")

    def on_pause_resume(self, event):
        """ Toggles between pause and resume. """
        if not self.pause_event.is_set():
            self.pause_event.clear()
            self.scheduler.pause()  # Pauses the main scheduler task
            self.SetStatusText("Paused")
        else:
            self.pause_event.set()
            self.scheduler.resume()  # Resumes the main scheduler task
            self.SetStatusText("Resumed")

    def on_stop(self, event):
        """ Stops everything and resets to initial state. """
        self.pause_event.set()  # Ensures daemon can exit from wait
        self.stop_event.set()  # Signals daemon to stop
        self.stop_scheduler()  # Stops the main scheduler and clears everything

    def on_close(self, event):
        """ Cleanup on close. """
        self.stop_event.set()  # Ensures daemon stops
        self.scheduler.shutdown()
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, title="APScheduler with wxPython", size=(800, 600))
        frame.Bind(wx.EVT_CLOSE, frame.on_close)
        frame.Show()
        return True

if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
    
import inspect

def foo(a, b):
    frame = inspect.currentframe().f_back  # Get caller's frame
    variables = {name: value for name, value in frame.f_locals.items() if value in {a, b}}
    
    # Extract variable names matching the passed values
    arg_names = {name for name, value in variables.items() if value == a or value == b}
    print(arg_names)

# Example usage
variable_1 = 1
variable_2 = 2
foo(variable_1, variable_2)