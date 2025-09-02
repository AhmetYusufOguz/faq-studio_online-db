import logging
import sys

def setup_logger():
    logger = logging.getLogger("faqstudio")
    logger.setLevel(logging.INFO)

    # double-handler yaratmamak için önce temizle
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s :: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger()