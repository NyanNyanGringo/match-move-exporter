"""
DO NOT IMPORT THIS FILE

This file is part of nuke_utilities. It used in get_export_pyscript() function.
"""
import sys

import nuke

from lib.utilities.log_utilities import setup_or_get_logger


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=True)
LOGGER.info("Nuke works good!")
NUKE_SCRIPT = sys.argv[1]


nuke.scriptOpen(NUKE_SCRIPT)


node = nuke.createNode("Blur")
LOGGER.info(f"Blur node created: {node.name()}")


nuke.scriptSave(NUKE_SCRIPT)
