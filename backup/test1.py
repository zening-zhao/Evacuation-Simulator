import sys
import random
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QSplitter, QLabel, QStatusBar
from PySide6.QtCore import QTimer, QThread, Signal, Qt
from PySide6.QtGui import QPainter, QPixmap, QColor

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

        # Create a splitter
        splitter = QSplitter(Qt.Horizontal)

        # Create the left panel for buttons
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Create buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start)
        left_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause_resume)
        left_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop)
        left_layout.addWidget(self.stop_button)

        # Create the right panel for drawing
        self.right_panel = QLabel()
        self.right_panel.setFixedSize(400, 300)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)

        # Set the central widget
        self.setCentralWidget(splitter)

        # Create a status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Timer for GUI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)

    def on_start(self):
        if not self.timer.isActive():
            self.start_time = time.time()
            self.timer.start(1000)  # Update every second

            # Start the worker thread
            self.worker_thread = WorkerThread(self.start_time)
            self.worker_thread.update_time.connect(self.update_time_elapsed)
            self.worker_thread.start()

    def on_pause_resume(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.timer.start(1000)
            self.pause_button.setText("Pause")

    def on_stop(self):
        self.timer.stop()
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait()
        self.ticker = 0
        self.status_bar.showMessage("Stopped")
        self.right_panel.clear()

    def update_gui(self):
        self.ticker += 1
        self.status_bar.showMessage(f"Ticker: {self.ticker}")
        self.draw_shapes()

    def update_time_elapsed(self, elapsed_time):
        self.status_bar.showMessage(f"Time Elapsed: {elapsed_time}s", 1)

    def draw_shapes(self):
        # Create a new QPixmap with the size of the right panel
        pixmap = QPixmap(self.right_panel.size())
        pixmap.fill(QColor("white"))

        # Use QPainter to draw on the QPixmap
        painter = QPainter(pixmap)
        if painter.isActive():
            painter.setBrush(QColor("red") if self.ticker % 12 == 0 else QColor("blue"))
            for _ in range(5):
                x, y = random.randint(0, 300), random.randint(0, 200)
                w, h = random.randint(10, 50), random.randint(10, 50)
                painter.drawRect(x, y, w, h)
            painter.end()

        # Set the QPixmap to the QLabel
        self.right_panel.setPixmap(pixmap)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
