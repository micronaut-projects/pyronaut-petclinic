"""Welcome HTTP routes and helpers."""

from micronaut.http.annotation import Get
from micronaut.views import View


@Get("/")
@View("welcome")
def welcome() -> dict:
    """Render the welcome page.

    Returning a dict gives the view renderer its model. This page has no dynamic
    data, so the model is empty.
    """

    return {}
