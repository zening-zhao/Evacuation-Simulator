import sys
import logging
from PySide6 import QtWidgets
from EvacuationSimFrameQt import EvacuationSimFrameQt
from logger_config import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------
## Main entry point of the application
#---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Evacuation Simultor...")
    app = QtWidgets.QApplication(sys.argv)
    window = EvacuationSimFrameQt(app)
    window.show()
    sys.exit(app.exec())
    logger.info("Evacuation Simultor Terminated.")
