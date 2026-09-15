"""Logging configuration for Pyronaut PetClinic sample.
"""

import os

from logback.config import dictConfig

GRAALOS = bool(os.environ.get("OCI_GRAAL_DB_TOKEN", "").strip())
if GRAALOS:
    # GraalOS collects native application output from stderr.
    os.dup2(2, 1)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
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
            "stream": "ext://sys.stderr" if GRAALOS else "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    },
    "loggers": {
        "io.micronaut.web.router": {
            # change to TRACE to view HTTP routes
            "level": "INFO",
            "handlers": ["console"]
        }
    }
}

dictConfig(LOGGING)
