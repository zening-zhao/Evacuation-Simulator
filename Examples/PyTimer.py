import sys
import time
import random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QStatusBar, QSplitter,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QFormLayout
)
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QImage, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

class CalculationThread(QThread):
    calculation_done = Signal()

    def __init__(self, ticker, shapes):
        super().__init__()
        self.ticker = ticker
        self.shapes = shapes
        self.running = True

    def run(self):
        print(f"Running calculation for ticker {self.ticker}")
        # Simulate complex calculation
        time.sleep(0.5)  # Simulate time-consuming calculation
        if self.ticker % 12 == 0:
            # Special calculation route
            self.shapes.clear()  # Clear shapes every 12 ticks
        else:
            # Add new shapes
            for _ in range(5):
                x, y = random.randint(0, 700), random.randint(0, 500)
                w, h = random.randint(10, 50), random.randint(10, 50)
                color = QColor("red") if self.ticker % 12 == 0 else QColor("blue")
                rect = QRect(x, y, w, h)
                self.shapes.append({'rect': rect, 'color': color})
        self.calculation_done.emit()

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ticker = 0
        self.shapes = []  # Store shapes to preserve them
        self.scheduler = None
        self.calculation_thread = None

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        edit_menu = menu_bar.addMenu("Edit")

        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Add Start, Pause, Stop, Reset actions to toolbar
        self.start_action = QAction("Start", self)
        self.start_action.triggered.connect(self.on_start)
        self.pause_action = QAction("Pause", self)
        self.pause_action.triggered.connect(self.on_pause_resume)
        self.stop_action = QAction("Stop", self)
        self.stop_action.triggered.connect(self.on_stop)
        self.reset_action = QAction("Reset", self)
        self.reset_action.triggered.connect(self.on_reset)

        toolbar.addAction(self.start_action)
        toolbar.addAction(self.pause_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.reset_action)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create status bar fields
        self.ticker_label = QLabel("Ticker: 0")
        self.status_label = QLabel("Status: Stopped")
        self.progress_label = QLabel("Progress: 0%")
        self.time_elapsed_label = QLabel("Time Elapsed: 0s")

        self.status_bar.addWidget(self.ticker_label, 1)
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addWidget(self.progress_label, 1)
        self.status_bar.addWidget(self.time_elapsed_label, 1)

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)

        # Create left panel with form layout
        left_panel = QWidget()
        form_layout = QFormLayout()
        left_panel.setLayout(form_layout)

        # Add configuration fields
        for i in range(5):
            label = QLabel(f"Config {i+1}:")
            text_field = QLineEdit()
            form_layout.addRow(label, text_field)

        # Create right panel (canvas area) with scroll area
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.canvas = QLabel()
        self.canvas.setFixedSize(800, 600)  # Larger size for scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])  # Initial sizes
        splitter.setHandleWidth(5)  # Show splitter bar

        # Set central widget
        self.setCentralWidget(splitter)

        # Timer for GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(1000)  # Update every second

        # Initialize button states
        self.update_button_states()

    def update_button_states(self):
        self.start_action.setEnabled(self.scheduler is None)
        self.pause_action.setEnabled(self.scheduler is not None)
        self.stop_action.setEnabled(self.scheduler is not None)
        self.reset_action.setEnabled(self.scheduler is None and self.ticker > 0)

    def on_start(self):
        if self.scheduler is None:
            self.start_time = time.time()
            self.scheduler = BackgroundScheduler()
            self.job = self.scheduler.add_job(self.run_calculation, IntervalTrigger(seconds=1))
            self.scheduler.start()
            print("Scheduler started")
            self.status_label.setText("Status: Running")
            self.update_button_states()

    def on_pause_resume(self):
        if self.job:
            if self.job.next_run_time:
                self.job.pause()
                self.status_label.setText("Status: Paused")
                self.pause_action.setText("Resume")
            else:
                self.job.resume()
                self.status_label.setText("Status: Running")
                self.pause_action.setText("Pause")

    def on_stop(self):
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
        self.status_label.setText("Status: Stopped")
        self.update_button_states()

    def on_reset(self):
        self.ticker = 0
        self.ticker_label.setText("Ticker: 0")
        self.progress_label.setText("Progress: 0%")
        self.shapes.clear()
        self.canvas.clear()
        self.update_button_states()

    def run_calculation(self):
        print("Running calculation")
        self.ticker += 1
        self.ticker_label.setText(f"Ticker: {self.ticker}")

        if self.calculation_thread is None or not self.calculation_thread.isRunning():
            self.calculation_thread = CalculationThread(self.ticker, self.shapes)
            self.calculation_thread.calculation_done.connect(self.update_canvas)
            self.calculation_thread.start()

    def update_canvas(self):
        # Create a new QPixmap with the size of the canvas
        pixmap = QPixmap(self.canvas.size())
        pixmap.fill(QColor("white"))

        # Use QPainter to draw on the QPixmap
        painter = QPainter(pixmap)
        for shape in self.shapes:
            painter.setBrush(shape['color'])
            painter.drawRect(shape['rect'])
        painter.end()

        # Set the QPixmap to the QLabel
        self.canvas.setPixmap(pixmap)

    def update_gui(self):
        if self.scheduler and self.scheduler.running:
            elapsed_time = int(time.time() - self.start_time)
            self.time_elapsed_label.setText(f"Time Elapsed: {elapsed_time}s")
            progress = (self.ticker % 12) * 100 // 12
            self.progress_label.setText(f"Progress: {progress}%")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
