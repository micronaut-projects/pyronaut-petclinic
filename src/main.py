"""Logging configuration for Pyronaut PetClinic sample."""

import os

from logback.config import dictConfig


GRAALOS = bool(os.environ.get("OCI_GRAAL_DB_TOKEN", "").strip())

if GRAALOS:
    # Keep native application output on stderr for GraalOS.
    os.dup2(2, 1)


dictConfig(
    {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stderr" if GRAALOS else "ext://sys.stdout",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)
