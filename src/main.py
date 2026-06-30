"""Application entry point for the Pyronaut PetClinic sample.

Pyronaut discovers Python modules that are imported from the application entry
point. Importing ``petclinic.controllers`` registers the HTTP routes, and
importing ``petclinic.seed`` registers the startup event listener that creates
sample data. The rest of the application is reached through Micronaut bean
injection from those modules.
"""

from logback.config import dictConfig

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
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}

dictConfig(LOGGING)

# These imports are intentionally side-effectful: decorators in the imported
# modules declare Micronaut beans, routes, and event listeners.
import petclinic.controllers
import petclinic.seed
