# logger_config.py
import logging
import os
from datetime import datetime

def setup_logger(level=logging.INFO):
    """Function to set up a logger."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    entry_file_directory = os.path.dirname(os.path.abspath(__file__))
    log_file = f'EvacuationSimQt_{timestamp}.log'

    # Construct the log file path
    log_file_path = os.path.join(entry_file_directory, log_file)

    logger = logging.getLogger()

    # Check if handlers are already added
    if not logger.handlers:
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        formatter = logging.Formatter(format)
        handler = logging.FileHandler(log_file_path)
        handler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(handler)

    return log_file
