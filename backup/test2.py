import sys
import random
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QStatusBar, QSplitter,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QColorDialog, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect

class WorkerThread(QThread):
    update_time = Signal(int)

    def __init__(self, start_time):
        super().__init__()
        self.start_time = start_time
        self.running = True

    def run(self):
        while self.running:
            elapsed_time = int(time.time() - self.start_time)
            self.update_time.emit(elapsed_time)
            time.sleep(1)

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ticker = 0
        self.start_time = None
        self.worker_thread = None
        self.shapes = []  # Store shapes to preserve them

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        edit_menu = menu_bar.addMenu("Edit")

        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Add Start, Pause, Stop actions to toolbar
        start_action = QAction("Start", self)
        start_action.triggered.connect(self.on_start)
        pause_action = QAction("Pause", self)
        pause_action.triggered.connect(self.on_pause_resume)
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.on_stop)

        toolbar.addAction(start_action)
        toolbar.addAction(pause_action)
        toolbar.addAction(stop_action)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Create status bar fields
        self.ticker_label = QLabel("Ticker: 0")
        self.simulation_status_label = QLabel("Status: Stopped")
        self.people_count_label = QLabel("People: 0")
        self.time_elapsed_label = QLabel("Time Elapsed: 0s")

        self.status_bar.addPermanentWidget(self.ticker_label)
        self.status_bar.addPermanentWidget(self.simulation_status_label)
        self.status_bar.addPermanentWidget(self.people_count_label)
        self.status_bar.addPermanentWidget(self.time_elapsed_label)

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)

        # Create left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Add buttons to left panel in a single row
        button_row = QHBoxLayout()
        button1 = QPushButton("Button 1")
        button2 = QPushButton("Button 2")
        button3 = QPushButton("Button 3")
        button_row.addWidget(button1)
        button_row.addWidget(button2)
        button_row.addWidget(button3)
        left_layout.addLayout(button_row)

        # Add configuration area with grid layout
        config_area = QWidget()
        config_layout = QGridLayout()
        config_area.setLayout(config_layout)

        # Add configuration fields
        for i in range(3):
            label = QLabel(f"Config {i+1}:")
            text_field = QLineEdit()
            config_layout.addWidget(label, i, 0)
            config_layout.addWidget(text_field, i, 1)

        # Add color configuration
        color_label = QLabel("Color:")
        color_text = QLineEdit()
        color_preview = QFrame()
        color_preview.setFixedSize(20, 20)
        color_preview.setStyleSheet("background-color: #FFFFFF")
        color_button = QPushButton("Pick Color")
        color_button.clicked.connect(lambda: self.pick_color(color_text, color_preview))
        config_layout.addWidget(color_label, 3, 0)
        config_layout.addWidget(color_text, 3, 1)
        config_layout.addWidget(color_preview, 3, 2)
        config_layout.addWidget(color_button, 3, 3)

        left_layout.addWidget(config_area)

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

    def pick_color(self, color_text, color_preview):
        color = QColorDialog.getColor()
        if color.isValid():
            color_text.setText(color.name())
            color_preview.setStyleSheet(f"background-color: {color.name()}")

    def on_start(self):
        if not self.timer.isActive():
            self.start_time = time.time()
            self.timer.start(1000)  # Update every second
            self.simulation_status_label.setText("Status: Running")

            # Start the worker thread
            self.worker_thread = WorkerThread(self.start_time)
            self.worker_thread.update_time.connect(self.update_time_elapsed)
            self.worker_thread.start()

    def on_pause_resume(self):
        if self.timer.isActive():
            self.timer.stop()
            self.simulation_status_label.setText("Status: Paused")
        else:
            self.timer.start(1000)
            self.simulation_status_label.setText("Status: Running")

    def on_stop(self):
        self.timer.stop()
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
        self.ticker = 0
        self.simulation_status_label.setText("Status: Stopped")
        self.ticker_label.setText("Ticker: 0")
        self.shapes.clear()
        self.canvas.clear()

    def update_gui(self):
        self.ticker += 1
        self.ticker_label.setText(f"Ticker: {self.ticker}")
        self.draw_shapes()

    def update_time_elapsed(self, elapsed_time):
        self.time_elapsed_label.setText(f"Time Elapsed: {elapsed_time}s")

    def draw_shapes(self):
        # Create a new QPixmap with the size of the canvas
        pixmap = QPixmap(self.canvas.size())
        pixmap.fill(QColor("white"))

        # Use QPainter to draw on the QPixmap
        painter = QPainter(pixmap)

        # Redraw existing shapes
        for shape in self.shapes:
            painter.setBrush(shape['color'])
            painter.drawRect(QRect(*shape['rect']))

        # Add new shapes
        if self.ticker % 12 == 0:
            self.shapes.clear()  # Clear shapes every 12 ticks
        else:
            for _ in range(5):
                x, y = random.randint(0, 700), random.randint(0, 500)
                w, h = random.randint(10, 50), random.randint(10, 50)
                color = QColor("red") if self.ticker % 12 == 0 else QColor("blue")
                rect = (x, y, w, h)
                self.shapes.append({'rect': rect, 'color': color})
                painter.setBrush(color)
                painter.drawRect(QRect(x, y, w, h))

        painter.end()

        # Set the QPixmap to the QLabel
        self.canvas.setPixmap(pixmap)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
