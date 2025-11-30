import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QToolBar
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Create an "About" action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        toolbar.addAction(about_action)

        # Set the main window properties
        self.setWindowTitle("About Dialog Example")
        self.setGeometry(100, 100, 600, 400)

    def show_about_dialog(self):
        # Create and display an "About" dialog
        about_dialog = QMessageBox(self)
        about_dialog.setWindowTitle("About")
        about_dialog.setText("This is an example application using PySide6.")
        about_dialog.setInformativeText("Version 1.0\nAuthor: Your Name")
        about_dialog.setStandardButtons(QMessageBox.Ok)
        about_dialog.setIcon(QMessageBox.Information)
        about_dialog.exec()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
