import wx
from EvacuationSimFrameWx import EvacuationSimFrameWx
import logging
from logger_config import setup_logger
from datetime import datetime

setup_logger()
logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------
## Main entry point of the application
#---------------------------------------------------------------------------

def main():
    app = wx.App(0)
    frame = EvacuationSimFrameWx(None, -1, 'Evacuation Simulator')

    frame.Show(True)
    frame.Center()

    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == "__main__":
    logger.info("Starting Evacuation Simultor...")
    main()
    logger.info("Evacuation Simultor Terminated.")

