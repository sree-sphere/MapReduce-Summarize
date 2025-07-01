from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_filename='logs//app.log'):
    """
    Configures logging for the application.
    
    :param log_filename: Name of the log file.
    """
    # Set up logging configuration
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a rotating file handler
    try:
        handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=10)
    except FileNotFoundError:
        log_folder = Path(log_filename.split('//')[0])
        log_file = Path(log_filename)
        if not log_folder.exists():
            log_folder.mkdir()
            print(f"Folder '{log_folder}' created.")
        # Create the file if it does not exist
        if not log_file.exists():
            log_file.touch()
            print(f"File '{log_file}' created.")
        handler = RotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=10)

    handler.setLevel(logging.DEBUG)

    # Create a console handler to log messages to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Define the format for log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    # Log a message indicating that logging has been configured
    logger.info("Logging is configured.")

    return logger

# Set up the logger
logger = setup_logging()