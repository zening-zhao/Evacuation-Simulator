import sys
from PySide6.QtWidgets import QApplication, QWidget, QSplitter, QVBoxLayout, QScrollArea, QPushButton
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 500)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        # Draw something on the canvas

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.canvas = Canvas()

        # Create a scroll area for the canvas
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)

        # Create another widget to place on the right side of the splitter
        right_widget = QWidget()
        right_widget.setLayout(QVBoxLayout())
        right_widget.layout().addWidget(QPushButton("Button 1"))
        right_widget.layout().addWidget(QPushButton("Button 2"))

        # Create the splitter and add the widgets
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_area)
        splitter.addWidget(right_widget)

        # Set the main layout
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
