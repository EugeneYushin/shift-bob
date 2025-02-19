import logging

# DEFAULT_TZ = "America/New_York"


def init_logging() -> None:
    """Configure logging."""
    handler = logging.StreamHandler()
    # gcp timestamp vs asctime
    # gcp severity vs levelname
    fmt = "%(timestamp)s - %(name)s - %(threadName)s - %(severity)s - %(message)s"
    # formatter = structuredlogger.StructuredJsonFormatter(fmt=fmt)
    # handler.setFormatter(formatter)
    # handler.addFilter(InjectingFilter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
