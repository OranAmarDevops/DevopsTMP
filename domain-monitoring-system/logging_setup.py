import logging
import os
import sys


def configure_logging(service_name, settings, service_root):
    logging_settings = settings["logging"]
    log_level = getattr(
        logging,
        logging_settings["level"].upper()
    )

    log_directory = logging_settings["directory"]
    if not os.path.isabs(log_directory):
        log_directory = os.path.join(
            service_root,
            log_directory
        )

    os.makedirs(log_directory, exist_ok=True)

    log_file = os.path.join(
        log_directory,
        logging_settings["file_name"]
    )

    formatter = logging.Formatter(
        fmt=logging_settings["format"],
        datefmt=logging_settings["date_format"]
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    service_logger = logging.getLogger(service_name)
    service_logger.setLevel(log_level)
    service_logger.propagate = False

    for handler in service_logger.handlers[:]:
        service_logger.removeHandler(handler)
        handler.close()

    service_logger.addHandler(stream_handler)
    service_logger.addHandler(file_handler)

    service_logger.info(
        "%s logging initialized; file=%s level=%s",
        service_name,
        log_file,
        logging_settings["level"].upper()
    )

    return service_logger
