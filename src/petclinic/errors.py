"""Global error views with the reference application's public error details."""

from micronaut.http import HttpStatus
from micronaut.http.exceptions import HttpStatusException


def entity_not_found():
    raise HttpStatusException(HttpStatus.NOT_FOUND, 'Entity not found.')
