import logging
import os

def get_logger(name: str, level=logging.INFO, log_to_file=False, log_file_path='monitor.log'):
    """
    Configures and returns a logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if logger already configured
    if not logger.handlers:
        logger.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler (optional)
        if log_to_file:
            # Ensure the log directory exists if a specific path is given
            if os.path.dirname(log_file_path):
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            fh = logging.FileHandler(log_file_path)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
    return logger

if __name__ == '__main__':
    # Example usage:
    logger = get_logger(__name__, level=logging.DEBUG, log_to_file=True, log_file_path='app.log')
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    another_logger = get_logger('another_module', level=logging.INFO)
    another_logger.info("Message from another logger.")
