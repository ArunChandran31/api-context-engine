import logging
import sys

from app.core.config import settings


class RAGLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        extra_fields = []

        for field in (
            "cache_hit",
            "cache_get_ms",
            "retrieval_ms",
            "cache_set_ms",
            "total_ms",
            "result_count",
            "cache_key",
        ):
            if hasattr(record, field):
                extra_fields.append(f"{field}={getattr(record, field)}")

        if extra_fields:
            message += " | " + " | ".join(extra_fields)

        return message


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RAGLogFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )
