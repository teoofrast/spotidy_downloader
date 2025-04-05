import logging
import logging.handlers
import os

def setup_logger(name, log_file='logs/app.log', level=logging.INFO):
    """Настраивает и возвращает логгер."""

    # Создаем директорию для логов, если она не существует
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(filename)s:%(lineno)d - %(message)s')

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=7
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger
