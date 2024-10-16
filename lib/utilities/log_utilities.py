import logging

import os
import sys

from lib.utilities.os_utilities import get_root_path


def get_log_file_path(create_log_dir: bool = True) -> str:
    path = os.path.join(
        get_root_path(),
        "logs",
        "logs.log"
    )

    if create_log_dir:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    return path


def get_log_level() -> int:
    return logging.DEBUG if os.getenv("DEV") else logging.INFO


def get_log_format() -> str:
    return '%(asctime)s - %(name)s - %(levelname)s - %(module)s - Line: %(lineno)d - File: %(filename)s - %(message)s'


def _handle_exception(exc_type, exc_value, exc_traceback):
    """
    Глобальный обработчик всех необработанных исключений, который пишет их в лог-файл.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Пропускаем KeyboardInterrupt для возможности прерывания программы
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger("MatchMoveExporter")
    logger.critical("Необработанное исключение", exc_info=(exc_type, exc_value, exc_traceback))


def setup_or_get_logger(force_setup: bool = False, use_console_handler: bool = False):
    """
    If exists, return logger for MatchMoveExporter or set up a new one.
    :param force_setup: if logger already exists - remove it and set up a new one.
    :param use_console_handler: adds output steam handler to console
    :return:
    """
    logger_name = "MatchMoveExporter"
    logger = logging.getLogger(logger_name)

    # clear handlers
    if logger.hasHandlers():
        if not force_setup:
            logger.info(f"{logger_name} returned.")
            return logger

        # Закрываем и удаляем все существующие обработчики
        for handler in logger.handlers:
            handler.close()  # Закрываем поток обработчика
        logger.handlers.clear()  # Удаляем обработчики

    # set log level
    logger.setLevel(get_log_level())

    # file_handler
    file_handler = logging.FileHandler(get_log_file_path())
    file_handler.setLevel(get_log_level())
    file_handler.setFormatter(logging.Formatter(get_log_format()))
    logger.addHandler(file_handler)

    # console_handler
    if use_console_handler:
        console_handler = logging.StreamHandler(sys.stderr)  # sys.stdout
        console_handler.setFormatter(logging.Formatter(get_log_format()))
        logger.addHandler(console_handler)

    # catch all exceptions to log file
    sys.excepthook = _handle_exception

    logger.info(f"New {logger_name} logger set up.")

    return logger
