import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea,
    QSplitter, QWidget, QToolBar, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPolygonItem
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot, QMetaObject, QPointF
from PySide6.QtGui import QColor, QBrush
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time
import threading

class MonitorThread(QThread):
    stop_signal = Signal()  # Signal to indicate that the monitoring condition has been met

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.running = True

    def run(self):
        while self.running:
            if self.scheduler.get_jobs() == [] or self.check_condition_to_stop():
                self.stop_signal.emit()
                self.stop_scheduler()
                self.running = False
            time.sleep(1)  # Check status every second

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

class EvacuationSimFrameQt(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the main layout with a splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Configuration panel
        config_widget = QWidget()
        form_layout = QFormLayout(config_widget)
        for i in range(5):
            form_layout.addRow(QLabel(f"Config Item {i+1}:"), QLineEdit())

        config_scroll_area = QScrollArea()
        config_scroll_area.setWidgetResizable(True)
        config_scroll_area.setWidget(config_widget)

        # Right side: Scrollable area for drawing shapes
        self.canvas_widget = QGraphicsView()
        self.canvas_scene = QGraphicsScene()
        self.canvas_widget.setScene(self.canvas_scene)
        self.canvas_scroll_area = QScrollArea()
        self.canvas_scroll_area.setWidgetResizable(True)
        self.canvas_scroll_area.setWidget(self.canvas_widget)

        # Add widgets to the splitter
        splitter.addWidget(config_scroll_area)
        splitter.addWidget(self.canvas_scroll_area)
        splitter.setSizes([300, 700])  # Initial sizes

        self.setCentralWidget(splitter)

        # Toolbar and buttons
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_scheduler)
        toolbar.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause_resume)
        toolbar.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_scheduler)
        toolbar.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)
        toolbar.addWidget(self.reset_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_application)
        toolbar.addWidget(self.exit_button)

        # Status bar
        self.statusBar().showMessage("Ready | Ticker: 0 | Status: Ready | Time Elapsed: 0s | Info: -")

        # Scheduler setup
        self.scheduler = BackgroundScheduler()
        self.scheduler_lock = threading.Lock()  # To ensure the task completes before the next one starts
        self.ticker = 0
        self.job_paused = False
        self.start_time = None  # To track the start time of the simulation
        self.monitor_thread = MonitorThread(self.scheduler)
        self.monitor_thread.stop_signal.connect(self.on_scheduler_stopped_by_condition)

        # Timer to control the ticking
        self.ticker_timer = QTimer()
        self.ticker_timer.timeout.connect(self.increment_ticker)

        # Initial button states
        self.update_button_states(start_enabled=True, pause_enabled=False, stop_enabled=False, reset_enabled=False)

        self.setWindowTitle("Evacuation Simulation")
        self.setGeometry(100, 100, 1000, 600)

    def update_button_states(self, start_enabled, pause_enabled, stop_enabled, reset_enabled):
        """Update the enabled/disabled state of the control buttons."""
        self.start_button.setEnabled(start_enabled)
        self.pause_button.setEnabled(pause_enabled)
        self.stop_button.setEnabled(stop_enabled)
        self.reset_button.setEnabled(reset_enabled)

    def update_status_bar(self, message=""):
        """Update the status bar with ticker, status, time elapsed, and additional info."""
        elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
        status_message = f"Ticker: {self.ticker} | Status: {message} | Time Elapsed: {elapsed_time}s | Info: -"
        self.statusBar().showMessage(status_message)

    def start_scheduler(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self.start_time = time.time()  # Record the start time
            self.monitor_thread.start()
            self.update_button_states(start_enabled=False, pause_enabled=True, stop_enabled=True, reset_enabled=False)
            self.update_status_bar("Running")

        self.scheduler.add_job(
            lambda: QMetaObject.invokeMethod(self, "draw_complex_shapes", Qt.QueuedConnection),
            trigger=IntervalTrigger(seconds=2),  # Adjust interval as needed
            id='draw_job'
        )
        self.ticker_timer.start(1000)  # 1-second interval

    def stop_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.ticker_timer.stop()
            self.monitor_thread.stop()
            self.update_button_states(start_enabled=False, pause_enabled=False, stop_enabled=False, reset_enabled=True)
            self.update_status_bar("Stopped")

    def reset_simulation(self):
        # Clear the canvas and reset the ticker
        self.canvas_scene.clear()
        self.ticker = 0
        self.start_time = None
        self.statusBar().showMessage("Simulation reset. Ready to start.")
        self.job_paused = False
        self.pause_button.setText("Pause")

        # Create a new scheduler instance
        self.scheduler = BackgroundScheduler()
        self.monitor_thread.set_scheduler(self.scheduler)
        self.update_button_states(start_enabled=True, pause_enabled=False, stop_enabled=False, reset_enabled=False)
        self.update_status_bar("Reset")

    def toggle_pause_resume(self):
        if self.job_paused:
            self.scheduler.resume_job('draw_job')
            self.ticker_timer.start(1000)
            self.pause_button.setText("Pause")
            self.update_button_states(start_enabled=False, pause_enabled=True, stop_enabled=True, reset_enabled=False)
            self.update_status_bar("Running")
        else:
            self.scheduler.pause_job('draw_job')
            self.ticker_timer.stop()
            self.pause_button.setText("Resume")
            self.update_button_states(start_enabled=False, pause_enabled=True, stop_enabled=True, reset_enabled=False)
            self.update_status_bar("Paused")
        self.job_paused = not self.job_paused

    @Slot()
    def on_scheduler_stopped_by_condition(self):
        """Handle the scheduler stop when a condition is met in the monitor thread."""
        self.stop_scheduler()  # Stop the scheduler and update UI
        self.update_status_bar("Stopped by Condition")
        self.update_button_states(start_enabled=False, pause_enabled=False, stop_enabled=False, reset_enabled=True)

    @Slot()
    def draw_complex_shapes(self):
        with self.scheduler_lock:  # Ensure this job completes before the next one starts
            start_time = time.time()

            # Simulate a complex shape generation with intensive calculations
            num_shapes = 20
            for _ in range(num_shapes):
                points = []
                center_x = random.randint(100, 4000)
                center_y = random.randint(100, 4000)
                for i in range(360):
                    angle_rad = math.radians(i)
                    radius = 50 + 30 * math.sin(5 * angle_rad)  # Complex pattern
                    x = center_x + radius * math.cos(angle_rad)
                    y = center_y + radius * math.sin(angle_rad)
                    points.append(QPointF(x, y))
                polygon = QGraphicsPolygonItem()
                polygon.setPolygon(points)

                # Set a random color for the shape
                color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                polygon.setBrush(QBrush(color))

                self.canvas_scene.addItem(polygon)

            # Check if special drawing is needed
            if self.ticker % 12 == 0:
                # Draw a special shape (e.g., a larger shape with a distinct color)
                special_color = QColor(255, 0, 0)  # Red for the special shape
                special_polygon = QGraphicsPolygonItem()
                special_points = []
                center_x = random.randint(100, 4000)
                center_y = random.randint(100, 4000)
                for i in range(360):
                    angle_rad = math.radians(i)
                    radius = 100 + 50 * math.cos(3 * angle_rad)
                    x = center_x + radius * math.cos(angle_rad)
                    y = center_y + radius * math.sin(angle_rad)
                    special_points.append(QPointF(x, y))
                special_polygon.setPolygon(special_points)
                special_polygon.setBrush(QBrush(special_color))
                self.canvas_scene.addItem(special_polygon)

            # Force the scene to repaint
            self.canvas_scene.update()
            self.canvas_widget.viewport().update()

            # Ensure the task duration is logged
            duration = time.time() - start_time
            self.update_status_bar(f"Running | Last Task Duration: {duration:.2f}s")

    def increment_ticker(self):
        """Increment the ticker and update the status bar."""
        self.ticker += 1
        self.update_status_bar("Running")

    def exit_application(self):
        """Exit the application cleanly, stopping all threads and the scheduler."""
        if self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()  # Ensure the thread finishes cleanly

        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        # Stop any timers
        if self.ticker_timer.isActive():
            self.ticker_timer.stop()

        # Close the application
        self.update_status_bar("Exiting")
        QApplication.instance().quit()

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EvacuationSimFrameQt()
    window.show()
    sys.exit(app.exec())
