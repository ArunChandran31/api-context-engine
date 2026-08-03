import logging

from app.core.logging import configure_logging

configure_logging()

logger = logging.getLogger("api_context_engine")

logger.debug("Debug message")

logger.info("Information message")

logger.warning("Warning message")

logger.error("Error message")

logger.critical("Critical message")
