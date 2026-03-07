import logging

# SDK convention: use NullHandler so the consuming application controls log output.
# Users who want logs should add their own handler:
#   logging.getLogger("khaya").addHandler(logging.StreamHandler())
logger = logging.getLogger("khaya")
logger.addHandler(logging.NullHandler())
